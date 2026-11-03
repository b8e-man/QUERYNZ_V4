"""Loading (step 8.3): `build(conn, schema)` reads each source's newest finished pull, page by page, into the reading's
tables under `schema`; `publish(conn, staging)` moves them into `linz` and makes the views, in one transaction. A source
with no finished pull yet is not loaded, and its view stays as it was published (or empty).

Rebuilt whole every load (regenerable). Rows landed equal rows read plus set aside; the check holds it.

The private sources (capture.PRIVATE_SOURCES) are read into the lane's private schema (`linz_private`; a staging
schema's is `<staging>_private`), and once all three have a finished pull each title's street address is joined there,
title → unit of property → address id → address (`title_addresses`, `JOINED_BY`): a join on ids, no geometry. Nothing
private is published; `publish.sql` makes no view of it.

    python -m registers.linz.load [--schema staging_…|scratch_…]
    python -m registers.linz.load --job

Every line printed is a count.
"""
import argparse
import json
import os
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.linz import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "linz"
PRIVATE = "linz_private"
JOB = "qv4-linz-load"
STAGING = "staging_linz_load"
READING = ("titles", "owners", "place_names", "read_set_aside", "loaded_pulls")
PRIVATE_READING = ("property_titles", "property_addresses", "addresses", "title_addresses")
SOURCES = ("titles", "owners", "place_names", "property_titles", "property_addresses", "addresses")
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "titles": ("key",) + read.KEEP["titles"][1] + _CITE,
    "owners": ("key", "title_key", "kind", "name") + read.KEEP["owners"][1] + _CITE,
    "place_names": ("key",) + read.KEEP["place_names"][1] + _CITE,
    "property_titles": ("key",) + read.KEEP["property_titles"][1] + _CITE,
    "property_addresses": ("key",) + read.KEEP["property_addresses"][1] + _CITE,
    "addresses": ("key",) + read.KEEP["addresses"][1] + _CITE,
}
TITLE_ADDRESS_COLUMNS = ("title_no", "address_id", "full_address", "address_lifecycle", "unit_of_property_id", "joined_by",
                         "titles_on_property", "addresses_on_property", "property_title_key", "property_address_key",
                         "address_key", "property_title_document", "property_address_document", "address_document")
#: how a title's address is joined: through the property spine, on ids, no geometry
JOINED_BY = ("property spine: table 113970 title_no → unit_of_property_id → table 115638 address_id → layer 123113 "
             "full_address")


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table_of(schema: str, source: str) -> str:
    """Where a source's rows go: a private source's into the schema's private twin."""
    return f"{private_of(schema)}.{source}" if source in capture.PRIVATE_SOURCES else f"{schema}.{source}"


def join_sql(private: str) -> str:
    """Each title's street address, one row per title and address id, from the three private sources in `private`."""
    cols = ", ".join(TITLE_ADDRESS_COLUMNS)
    return f"""
INSERT INTO {private}.title_addresses ({cols})
SELECT DISTINCT ON (pt.title_no, a.address_id)
       pt.title_no, a.address_id, a.full_address, a.address_lifecycle, pt.unit_of_property_id, %s,
       tc.n, ac.n, pt.key, pa.key, a.key, pt.document, pa.document, a.document
FROM {private}.property_titles pt
JOIN {private}.property_addresses pa ON pa.unit_of_property_id = pt.unit_of_property_id
JOIN {private}.addresses a ON a.address_id = pa.address_id
JOIN (SELECT unit_of_property_id, count(DISTINCT title_no)::int AS n FROM {private}.property_titles GROUP BY 1) tc
  ON tc.unit_of_property_id = pt.unit_of_property_id
JOIN (SELECT unit_of_property_id, count(DISTINCT address_id)::int AS n FROM {private}.property_addresses GROUP BY 1) ac
  ON ac.unit_of_property_id = pt.unit_of_property_id
ORDER BY pt.title_no, a.address_id, pt.unit_of_property_id, pt.key, pa.key"""


def profile_version() -> int:
    from support import profiles
    v = profiles.reading_version(read.PROFILE)
    if v is not None:
        return int(v)
    with open(os.path.join(HERE, "profile-proposed.jsonl"), encoding="utf-8") as f:
        return max(json.loads(l)["version"] for l in f if l.strip() and json.loads(l)["slug"] == read.PROFILE)


def create_tables(conn, schema: str) -> None:
    private = private_of(schema)
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private}")
    for t in READING:
        conn.execute(f"DROP TABLE IF EXISTS {schema}.{t} CASCADE")
    for t in PRIVATE_READING:
        conn.execute(f"DROP TABLE IF EXISTS {private}.{t} CASCADE")
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        conn.execute(f.read().replace("CREATE TABLE linz_private.", f"CREATE TABLE {private}.")
                     .replace("CREATE TABLE linz.", f"CREATE TABLE {schema}."))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def build(conn, schema: str, read_bytes=read_bytes, version: int = None, sources=SOURCES, log=print) -> dict:
    t0 = time.monotonic()
    version = version or profile_version()
    create_tables(conn, schema)
    counts, read_pages = {"seconds": 0}, []
    for source in sources:
        pages = capture.latest_pages(conn, source)
        if not pages:
            counts[f"{source}.pull"] = "none finished"
            continue
        pull_id = pages[0][3]
        stated = conn.execute(f"SELECT stated FROM {capture.SCHEMA}.pulls WHERE pull_id = %s", (pull_id,)).fetchone()[0]
        landed = read_n = aside_n = 0
        for document, start_index, n_rows, _ in pages:
            rows, aside = read.read_page(read_bytes(document), source, document, version, start_index)
            landed += n_rows
            if rows or not aside:
                read_pages.append((document, source))
            read_n += _copy(conn, table_of(schema, source), COLUMNS[source], rows)
            aside_n += _copy(conn, f"{schema}.read_set_aside", ("source", "document", "place", "stage", "reason"),
                             [dict(a, source=source) for a in aside])
        conn.execute(f"INSERT INTO {schema}.loaded_pulls VALUES (%s, %s, %s, %s, %s, %s)",
                     (source, pull_id, stated, landed, read_n, aside_n))
        counts.update({f"{source}.pull": pull_id, f"{source}.stated": stated, f"{source}.landed": landed,
                       f"{source}.read": read_n, f"{source}.set_aside": aside_n})
        log(f"{SCHEMA}: {source}: {read_n:,} read, {aside_n} set aside of {landed:,} landed ({pull_id})")
    if all(f"{s}.read" in counts for s in capture.PRIVATE_SOURCES):
        counts.update(join_addresses(conn, private_of(schema)))
        log(f"{SCHEMA}: title_addresses: {counts['title_addresses.rows']:,} rows, "
            f"{counts['title_addresses.titles']:,} titles with an address")
    # what each page has had extracted, by field (docs.extractions, a ledger: never wiped)
    from support.docstore import extraction
    from registers.linz import extracts
    ledger = extraction.record_many(conn, extracts.extracted(read_pages))
    counts.update({"extractions": ledger["rows"], "extractions written": ledger["written"],
                   "extractions not held": ledger["not held"]})
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return counts


def join_addresses(conn, private: str) -> dict:
    """Join each title's street address in `private`; counts only."""
    for q in (f"CREATE INDEX ON {private}.property_titles (unit_of_property_id)",
              f"CREATE INDEX ON {private}.property_addresses (unit_of_property_id)",
              f"CREATE INDEX ON {private}.addresses (address_id)"):
        conn.execute(q)
    rows = conn.execute(join_sql(private), (JOINED_BY,)).rowcount
    titles = conn.execute(f"SELECT count(DISTINCT title_no) FROM {private}.title_addresses").fetchone()[0]
    return {"title_addresses.rows": rows, "title_addresses.titles": titles}


def load(conn, schema: str, log=print) -> int:
    """The merge gate's staging step (support/staging)."""
    from registers.linz import check
    conn.execute(capture.capture_sql())
    counts = build(conn, schema, log=log)
    problems = check.reading(conn, schema)
    log(f"{SCHEMA}: into {schema}; " + ("; ".join(problems) or "reconciles"))
    return sum(v for k, v in counts.items() if k.endswith(".read"))


INDEXES = (
    "CREATE INDEX IF NOT EXISTS linz_titles_title_no ON linz.titles (title_no)",
    "CREATE INDEX IF NOT EXISTS linz_owners_title_no ON linz.owners (title_no)",
    "CREATE INDEX IF NOT EXISTS linz_owners_name ON linz.owners (lower(name))",
    "CREATE INDEX IF NOT EXISTS linz_place_names_name ON linz.place_names (lower(name))",
    "CREATE INDEX IF NOT EXISTS linz_title_addresses_title_no ON linz_private.title_addresses (title_no)",
    "CREATE INDEX IF NOT EXISTS linz_title_addresses_address ON linz_private.title_addresses (address_id)",
)


def publish(conn, staging: str, log=print) -> None:
    """The staged sources replace the lane's; a source the staging did not load keeps what is published."""
    staged = {r[0] for r in conn.execute(f"SELECT source FROM {staging}.loaded_pulls")}
    joined = capture.PRIVATE_SOURCES <= staged
    with conn.transaction():
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {PRIVATE}")
        exists = conn.execute("SELECT to_regclass('linz.loaded_pulls') IS NOT NULL").fetchone()[0]
        if not exists:
            create_tables(conn, SCHEMA)
        if conn.execute("SELECT to_regclass('linz_private.title_addresses') IS NULL").fetchone()[0]:
            with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
                sql = f.read()
            conn.execute(sql[sql.index("CREATE TABLE linz_private."):])
        for t in ("read_set_aside", "loaded_pulls"):
            conn.execute(f"DELETE FROM {SCHEMA}.{t} WHERE source = ANY(%s)", (sorted(staged),))
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        for source in sorted(staged | ({"title_addresses"} if joined else set())):
            private = source in capture.PRIVATE_SOURCES or source == "title_addresses"
            to, frm = (PRIVATE, private_of(staging)) if private else (SCHEMA, staging)
            conn.execute(f"TRUNCATE {to}.{source}")
            conn.execute(f"INSERT INTO {to}.{source} SELECT * FROM {frm}.{source}")
        for q in INDEXES:
            conn.execute(q)
        with open(os.path.join(HERE, "publish.sql"), encoding="utf-8") as f:
            conn.execute(f.read())
    log(f"{SCHEMA}: published {', '.join(sorted(staged)) or 'nothing'} from {staging}"
        + ("; title_addresses joined, kept private" if joined else ""))


def job(log=print) -> int:
    """qv4-linz-load: build in staging, hold it to the checks, publish only then."""
    from support import db
    from registers.linz import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '1800s'")
        conn.execute(capture.capture_sql())
        with conn.transaction():
            counts = build(conn, STAGING, log=log)
        problems = check.reading(conn, STAGING)
        detail = ", ".join(f"{k} {v:,}" if isinstance(v, int) else f"{k} {v}" for k, v in counts.items()
                           if k.endswith((".read", ".set_aside", ".stated")) or v == "none finished")
        detail += "; " + ("; ".join(problems) or "reconciles")
        if problems:
            log(f"{SCHEMA}: RED, nothing published: " + detail)
            jobrun.record(JOB, False, "nothing published: " + detail, started, {})
            return 1
        publish(conn, STAGING, log)
    jobrun.record(JOB, True, "published: " + detail, started, {k: v for k, v in counts.items() if isinstance(v, int)})
    log(f"{SCHEMA}: published: " + detail)
    return 0


def main(argv=None) -> int:
    from support import db
    ap = argparse.ArgumentParser(prog="python -m registers.linz.load")
    ap.add_argument("--schema", default="staging_linz_session")
    ap.add_argument("--job", action="store_true")
    a = ap.parse_args(argv)
    if a.job:
        return job()
    if not a.schema.startswith(("scratch_", "staging_")):
        print(f"{SCHEMA}: a session loads only a scratch or staging schema")
        return 2
    from registers.linz import check
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '1800s'")
        conn.execute(capture.capture_sql())
        with conn.transaction():
            counts = build(conn, a.schema)
        problems = check.reading(conn, a.schema)
    for k, v in counts.items():
        print(f"{SCHEMA}: {k}: {v}")
    print(f"{SCHEMA}: check: " + ("; ".join(problems) or "reconciles"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
