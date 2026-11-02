"""Loading (step 8.3): `build(conn, schema)` reads each source's newest finished pull, page by page, into the reading's
tables under `schema`; `publish(conn, staging)` moves them into `linz` and makes the views, in one transaction. A source
with no finished pull yet is not loaded, and its view stays as it was published (or empty).

Rebuilt whole every load (regenerable). Rows landed equal rows read plus set aside; the check holds it.

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
JOB = "qv4-linz-load"
STAGING = "staging_linz_load"
READING = ("titles", "owners", "place_names", "read_set_aside", "loaded_pulls")
SOURCES = ("titles", "owners", "place_names")
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "titles": ("key",) + read.KEEP["titles"][1] + _CITE,
    "owners": ("key", "title_key", "kind", "name") + read.KEEP["owners"][1] + _CITE,
    "place_names": ("key",) + read.KEEP["place_names"][1] + _CITE,
}


def profile_version() -> int:
    from support import profiles
    try:
        return int(profiles.current()[read.PROFILE]["version"])
    except KeyError:
        with open(os.path.join(HERE, "profile-proposed.jsonl"), encoding="utf-8") as f:
            return max(json.loads(l)["version"] for l in f if l.strip() and json.loads(l)["slug"] == read.PROFILE)


def create_tables(conn, schema: str) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for t in READING:
        conn.execute(f"DROP TABLE IF EXISTS {schema}.{t} CASCADE")
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        conn.execute(f.read().replace("CREATE TABLE linz.", f"CREATE TABLE {schema}."))


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
    counts = {"seconds": 0}
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
            read_n += _copy(conn, f"{schema}.{source}", COLUMNS[source], rows)
            aside_n += _copy(conn, f"{schema}.read_set_aside", ("source", "document", "place", "stage", "reason"),
                             [dict(a, source=source) for a in aside])
        conn.execute(f"INSERT INTO {schema}.loaded_pulls VALUES (%s, %s, %s, %s, %s, %s)",
                     (source, pull_id, stated, landed, read_n, aside_n))
        counts.update({f"{source}.pull": pull_id, f"{source}.stated": stated, f"{source}.landed": landed,
                       f"{source}.read": read_n, f"{source}.set_aside": aside_n})
        log(f"{SCHEMA}: {source}: {read_n:,} read, {aside_n} set aside of {landed:,} landed ({pull_id})")
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return counts


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
)


def publish(conn, staging: str, log=print) -> None:
    """The staged sources replace the lane's; a source the staging did not load keeps what is published."""
    staged = {r[0] for r in conn.execute(f"SELECT source FROM {staging}.loaded_pulls")}
    with conn.transaction():
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        exists = conn.execute("SELECT to_regclass('linz.loaded_pulls') IS NOT NULL").fetchone()[0]
        if not exists:
            create_tables(conn, SCHEMA)
        for t in ("read_set_aside", "loaded_pulls"):
            conn.execute(f"DELETE FROM {SCHEMA}.{t} WHERE source = ANY(%s)", (sorted(staged),))
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        for source in sorted(staged):
            conn.execute(f"TRUNCATE {SCHEMA}.{source}")
            conn.execute(f"INSERT INTO {SCHEMA}.{source} SELECT * FROM {staging}.{source}")
        for q in INDEXES:
            conn.execute(q)
        with open(os.path.join(HERE, "publish.sql"), encoding="utf-8") as f:
            conn.execute(f.read())
    log(f"{SCHEMA}: published {', '.join(sorted(staged)) or 'nothing'} from {staging}")


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
