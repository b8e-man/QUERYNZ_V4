"""Loading (plan 1b.7): `load(conn, schema)` builds the reading's tables under
`schema` from the files the capture lists, and `publish(conn, staging)` moves
them into `contract_disclosures` and makes the views, in one transaction.
`fill` in sample.py uses the same `build`.

Which files: the newest landing of each catalogue resource (role `data`).
Where the capture has never run (its table absent), the tables are made
empty, so the gate's staging step publishes empty views and the first
monthly run fills them. Idempotent: the reading's tables are dropped and
made again from the same files in one transaction. Cells in equal rows out
plus rows set aside, file by file, in the `read_files` ledger.

    python -m registers.contract_disclosures.load [--schema scratch_…] [--database querynz_v4_sample]
    python -m registers.contract_disclosures.load --job      # build in staging, check, publish only on green

Every line printed is a count.
"""
import argparse
import os
import re
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.contract_disclosures import read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "contract_disclosures"
PRIVATE = "contract_disclosures_private"
JOB = "qv4-contract-disclosures-load"
STAGING = "staging_contract_disclosures_load"
TABLES = ("costs", "read_files", "read_set_aside")
READING = "-- ── the reading"
COLUMNS = {
    "costs": ("key", "agency", "level", "region", "territorial_authority", "contract_class", "financial_year",
              "year_ended", "active_claims_as_published", "total_costs_as_published", "active_claims",
              "total_costs_nzd", "suppressed", "licence", "attribution", "document", "page", "place", "read_from",
              "reader", "profile", "profile_version"),
    "read_files": ("document", "package", "profile", "data_rows", "cells_read", "set_aside", "reference", "period",
                   "extracted_on"),
    "read_set_aside": ("document", "place", "stage", "reason"),
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the lane's
    tables carry its name."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


_NAMES = re.compile(r"(?<![A-Za-z0-9_])contract_disclosures(_private)?\.")


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    if name == "tables.sql":
        text = READING + text.split(READING, 1)[1]
    pre = f"{SCHEMA}_" if shared else ""
    return _NAMES.sub(lambda m: f"{private_of(schema) if m.group(1) else schema}.{pre}", text)


def create_tables(conn, schema: str, shared: bool = False) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    if not shared:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def build(conn, schema: str, listed: dict, read_bytes=read_bytes, shared: bool = False) -> dict:
    """Read the listed files (sha256 → package) into the tables under `schema`."""
    t0 = time.monotonic()
    create_tables(conn, schema, shared)
    T = lambda t: table(schema, t, shared)
    counts = {"files": 0, "rows": 0, "set_aside": 0}
    for sha, package in sorted(listed.items()):
        try:
            r = read.read(sha, read_bytes(sha))
        except read.NotTheShape as exc:
            _copy(conn, T("read_set_aside"), COLUMNS["read_set_aside"],
                  [{"document": sha, "place": "", "stage": "recognise", "reason": str(exc)[:500]}])
            counts["set_aside"] += 1
            continue
        n = _copy(conn, T("costs"), COLUMNS["costs"], r.rows)
        _copy(conn, T("read_set_aside"), COLUMNS["read_set_aside"], r.set_aside)
        _copy(conn, T("read_files"), COLUMNS["read_files"], [{
            "document": sha, "package": package, "profile": read.PROFILE, "data_rows": len(r.rows) // 10,
            "cells_read": len(r.rows), "set_aside": len(r.set_aside), **r.meta}])
        counts["files"] += 1
        counts["rows"] += n
        counts["set_aside"] += len(r.set_aside)
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return counts


def listings(conn, schema: str = SCHEMA) -> dict:
    """sha256 → package for the newest landing of each data resource; {} where the capture never ran."""
    if conn.execute("SELECT to_regclass(%s)", (f"{schema}.capture_files",)).fetchone()[0] is None:
        return {}
    rows = conn.execute(f"SELECT DISTINCT ON (coalesce(resource_id, url)) sha256, package FROM {schema}.capture_files "
                        "WHERE role = 'data' ORDER BY coalesce(resource_id, url), file_id DESC").fetchall()
    return {sha: package for sha, package in rows}


def load(conn, schema: str, log=print) -> int:
    """Every listed file, read, under `schema` (the merge gate's staging step)."""
    started = jobrun.now()
    counts = build(conn, schema, listings(conn))
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log(f"{SCHEMA}: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["rows"]


def publish(conn, staging: str, log=print) -> None:
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"{SCHEMA}: published from {staging}")


def unchanged(conn, listed: dict) -> bool:
    if conn.execute("SELECT to_regclass(%s)", (f"{SCHEMA}.read_files",)).fetchone()[0] is None:
        return False
    return {r[0] for r in conn.execute(f"SELECT document FROM {SCHEMA}.read_files")} == set(listed)


def job(log=print) -> int:
    """qv4-contract-disclosures-load: build in STAGING, hold it to the check, publish only then."""
    from support import db
    from registers.contract_disclosures import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '300s'")
        listed = listings(conn)
        if unchanged(conn, listed):
            log(f"{SCHEMA}: the listing is the one published; nothing loaded")
            jobrun.record(JOB, True, "unchanged: the listing is the one published", started, {})
            return 0
        with conn.transaction():
            counts = build(conn, STAGING, listed)
        problems = check.reading(conn, STAGING)
        detail = f"{counts['rows']} rows from {counts['files']} files; " + ("; ".join(problems) or "reconciles")
        if problems:
            log(f"{SCHEMA}: RED, nothing published: " + detail)
            jobrun.record(JOB, False, "nothing published: " + detail, started, {})
            return 1
        publish(conn, STAGING, log)
    log(f"{SCHEMA}: published: " + detail)
    jobrun.record(JOB, True, "published: " + detail, started, counts)
    return 0


def main(argv=None) -> int:
    from support import db
    ap = argparse.ArgumentParser(prog="python -m registers.contract_disclosures.load")
    ap.add_argument("--schema", default="scratch_procurement_1_cd")
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--capture-schema", default=None, help="where the capture's record is (default: --schema)")
    ap.add_argument("--job", action="store_true")
    a = ap.parse_args(argv)
    if a.job:
        return job()
    if not a.schema.startswith(("scratch_", "staging_")):
        print(f"{SCHEMA}: a session loads only a scratch or staging schema")
        return 2
    with db.connect(db.OWNER_KEY, a.database) as conn:
        listed = listings(conn, a.capture_schema or a.schema)
        with conn.transaction():
            counts = build(conn, a.schema, listed)
            conn.execute(sql("publish.sql", a.schema).replace("pub.", f"{a.schema}.pub_"))
    for k, v in counts.items():
        print(f"{SCHEMA}: {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
