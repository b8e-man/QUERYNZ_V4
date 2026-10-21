"""Loading (plan 1b.7): `build(conn, schema, pages)` reads the listed
decisions-list pages into the reading's tables under `schema`;
`publish(conn, staging)` moves them into `building_practitioners` and makes
the views, in one transaction. sample.py uses the same `build`.

Idempotent per listing: the reading's tables are dropped and made again and
every page read again. Pages are read newest landed first, so a decision
read again on an older page (a pass's pages shift when the Board adds a
decision mid-pass, and every weekly pass reads them all again) is counted as
superseded, not read twice. Items in equal decisions typed plus superseded
plus set aside, page by page; the build raises if a page does not reconcile.

    python -m registers.building_practitioners.load [--schema scratch_…] [--database querynz_v4_sample]
    python -m registers.building_practitioners.load --job

Every line printed is a count.
"""
import argparse
import os
import re
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.building_practitioners import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "building_practitioners"
PRIVATE = "building_practitioners_private"
JOB = "qv4-building-practitioners-load"
STAGING = "staging_building_practitioners_load"
TABLES = ("read_pages", "decisions", "practitioners", "read_set_aside")
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "read_pages": ("document", "pass_id", "stated", "items", "typed", "superseded", "set_aside"),
    "decisions": ("key", "complaint_number", "citation", "decision_kind", "name", "lbp_number", "suppressed", "region",
                  "licence_classes", "decided_on", "penalties", "grounds", "upheld", "decision_url", "pdf_url") + _CITE,
    "read_set_aside": ("document", "place", "stage", "reason"),
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


_NAMES = re.compile(r"(?<![A-Za-z0-9_])building_practitioners(_private)?\.")


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    if name == "tables.sql":
        text = capture.READING + text.split(capture.READING, 1)[1]
    pre = f"{SCHEMA}_" if shared else ""
    return _NAMES.sub(lambda m: f"{private_of(schema) if m.group(1) else schema}.{pre}", text)


def create_tables(conn, schema: str, shared: bool = False) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def build(conn, schema: str, pages: list, read_bytes=read_bytes, shared: bool = False, version: int = None) -> dict:
    """`pages`: [(sha256, pass_id)] oldest landed first; read newest first."""
    t0 = time.monotonic()
    version = version or read.profile_version()
    create_tables(conn, schema, shared)
    T = lambda t: table(schema, t, shared)
    seen, rows, asides, ledger = set(), [], [], []
    for sha, pass_id in reversed(list(dict.fromkeys(pages))):
        out = read.read_page(read_bytes(sha), sha, version)
        typed = superseded = 0
        for r in out["rows"]:
            if r["key"] in seen:
                superseded += 1
                continue
            seen.add(r["key"])
            rows.append(r)
            typed += 1
        asides += out["set_aside"]
        item_asides = sum(1 for a in out["set_aside"] if a["place"].startswith("item["))
        if out["stated"] is not None and out["items"] != typed + superseded + item_asides:
            raise AssertionError(f"{SCHEMA}: page {sha[:12]} does not reconcile")
        ledger.append({"document": sha, "pass_id": pass_id, "stated": out["stated"][1] if out["stated"] else None,
                       "items": out["items"], "typed": typed, "superseded": superseded, "set_aside": item_asides})
    return {"decisions": _copy(conn, T("decisions"), COLUMNS["decisions"], rows),
            "set_aside": _copy(conn, T("read_set_aside"), COLUMNS["read_set_aside"], asides),
            "pages": _copy(conn, T("read_pages"), COLUMNS["read_pages"], ledger),
            "superseded": sum(l["superseded"] for l in ledger), "practitioners": 0,
            "seconds": round(time.monotonic() - t0, 1)}


def listing(conn, schema: str = SCHEMA) -> list:
    """The pages of the newest finished pass and of any pass begun after it, oldest landed first."""
    r = conn.execute(f"SELECT max(pass_id) FROM {schema}.capture_passes WHERE finished_at IS NOT NULL").fetchone()
    since = r[0] if r and r[0] is not None else 0
    return [tuple(x) for x in conn.execute(
        f"SELECT sha256, pass_id FROM {schema}.capture_pages WHERE pass_id >= %s ORDER BY pass_id, page_no", (since,))]


def publish(conn, staging: str, log=print) -> None:
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"{SCHEMA}: published from {staging}")


def unchanged(conn, listed: list) -> bool:
    if conn.execute("SELECT to_regclass(%s)", (f"{SCHEMA}.read_pages",)).fetchone()[0] is None:
        return False
    return {r[0] for r in conn.execute(f"SELECT document FROM {SCHEMA}.read_pages")} == {s for s, _ in listed}


def job(log=print) -> int:
    """qv4-building-practitioners-load: build in staging, hold it to the reading's checks, publish only then."""
    from support import db
    from registers.building_practitioners import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        listed = listing(conn)
        if unchanged(conn, listed):
            log(f"{SCHEMA}: the listing is the one published; nothing loaded")
            jobrun.record(JOB, True, "unchanged: the listing is the one published", started, {})
            return 0
        with conn.transaction():
            counts = build(conn, STAGING, listed)
        problems = check.reading(conn, STAGING)
        detail = f"{counts['decisions']} decisions, {counts['set_aside']} set aside; " + ("; ".join(problems) or "reconciles")
        if problems:
            log(f"{SCHEMA}: RED, nothing published: " + detail)
            jobrun.record(JOB, False, "nothing published: " + detail, started, {})
            return 1
        publish(conn, STAGING, log)
    jobrun.record(JOB, True, "published: " + detail, started, counts)
    log(f"{SCHEMA}: published: " + detail)
    return 0


def main(argv=None) -> int:
    from support import db
    ap = argparse.ArgumentParser(prog="python -m registers.building_practitioners.load")
    ap.add_argument("--schema", default="scratch_building_practitioners_full")
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--capture-database", default="querynz_v4")
    ap.add_argument("--capture-schema", default=SCHEMA)
    ap.add_argument("--job", action="store_true")
    a = ap.parse_args(argv)
    if a.job:
        return job()
    if not a.schema.startswith(("scratch_", "staging_")):
        print(f"{SCHEMA}: a session loads only a scratch or staging schema")
        return 2
    key = db.READ_KEY if a.capture_database == "querynz_v4" else db.OWNER_KEY
    with db.connect(key, a.capture_database) as src:
        listed = listing(src, a.capture_schema)
    with db.connect(db.OWNER_KEY, a.database) as conn:
        with conn.transaction():
            counts = build(conn, a.schema, listed)
    for k, v in counts.items():
        print(f"{SCHEMA}: {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
