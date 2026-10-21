"""Loading (plan 1b.7): `load(conn, schema)` builds the reading's tables under
`schema` from the files the capture lists, and `publish(conn, staging)` moves
them into `tenders` and makes the views, in one transaction. `fill` in
sample.py uses the same `build`.

Which files: per era, the newest capture run that holds all four of the
era's data files (a release), so a refresh stopped half-way never mixes two
quarters. The historic era's one release is the old estate's copy.

Idempotent per listing: the reading's tables are dropped and made again and
every row read again from the same files inside one transaction, so a second
load gives the same rows under the same keys (only `loaded_at` moves). The
capture's tables are never touched. Items in equal items out plus items set
aside, file by file, in the `read_files` ledger.

    python -m registers.tenders.load [--schema scratch_tenders_full] [--database querynz_v4_sample]
    python -m registers.tenders.load --job      # build in staging, check, publish only on green

Every line printed is a count.
"""
import argparse
import json
import os
import re
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.tenders import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "tenders"
PRIVATE = "tenders_private"
JOB = "qv4-tenders-load"
SCRATCH = "scratch_tenders_full"
STAGING = "staging_tenders_load"
TABLES = ("notices", "suppliers", "read_files", "read_set_aside", "read_notes")
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "notices": ("key", "rfx_id", "era", "posting_agency", "department", "rfx_type", "competition_type",
                "tender_coverage", "prequalification_required", "title", "reference_number", "opened_on", "closed_on",
                "awarded_on", "award_type", "awarded_amount_as_published", "value_nzd", "value_note", "regions",
                "categories", "suppliers_named", "report_date") + _CITE,
    "suppliers": ("key", "notice_key", "rfx_id", "era", "business_name", "nzbn_as_published", "nzbn", "nzbn_form",
                  "country", "report_date") + _CITE,
    "read_files": ("document", "set_name", "era", "profile", "records", "typed", "set_aside", "skipped",
                   "report_date"),
    "read_set_aside": ("set_name", "era", "document", "place", "stage", "reason"),
    "read_notes": ("note", "count"),
}
JSON_COLUMNS = ("categories",)


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.tenders_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


_NAMES = re.compile(r"(?<![A-Za-z0-9_])tenders(_private)?\.")


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    """A file of this lane's SQL under `schema`; for tables.sql, the
    reading's part only (the capture makes its own)."""
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
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(json.dumps(row.get(c), ensure_ascii=False) if c in JSON_COLUMNS else row.get(c)
                               for c in cols))
            n += 1
    return n


def build(conn, schema: str, listed: dict, read_bytes=read_bytes, only: dict = None, shared: bool = False) -> dict:
    """Read the listed files into the tables under `schema`. `listed`:
    (set, era) → sha256. Returns the counts."""
    t0 = time.monotonic()
    create_tables(conn, schema, shared)
    files = {k: (sha, read_bytes(sha)) for k, sha in listed.items()}
    r = read.read(files, only)
    T = lambda t: table(schema, t, shared)
    counts = {"notices": _copy(conn, T("notices"), COLUMNS["notices"], r.notices),
              "suppliers": _copy(conn, T("suppliers"), COLUMNS["suppliers"], r.suppliers),
              "files": _copy(conn, T("read_files"), COLUMNS["read_files"], r.ledger),
              "set_aside": _copy(conn, T("read_set_aside"), COLUMNS["read_set_aside"], r.set_aside)}
    _copy(conn, T("read_notes"), COLUMNS["read_notes"], ({"note": k, "count": v} for k, v in sorted(r.notes.items())))
    counts["records_in"] = sum(l["records"] for l in r.ledger)
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return counts


def releases(conn, schema: str = SCHEMA) -> dict:
    """era → (run_id, {(set, era): sha256}): the newest run holding all four
    of the era's data files."""
    rows = conn.execute(f"SELECT run_id, set_name, era, sha256, file_id FROM {schema}.capture_files "
                        "WHERE role = 'data' ORDER BY run_id, file_id").fetchall()
    runs = {}
    for run_id, s, era, sha, _ in rows:
        runs.setdefault((era, run_id), {})[(s, era)] = sha
    out = {}
    for (era, run_id), got in sorted(runs.items(), key=lambda kv: kv[0][1]):
        if len(got) == len(read.SETS):
            out[era] = (run_id, got)
    return out


def listings(conn, schema: str = SCHEMA) -> dict:
    """(set, era) → sha256 for every file this reading reads."""
    out = {}
    for _, got in releases(conn, schema).values():
        out.update(got)
    return out


def load(conn, schema: str, log=print) -> int:
    """Every listed file, read, under `schema` (the merge gate's staging
    step). Returns the rows typed."""
    started = jobrun.now()
    counts = build(conn, schema, listings(conn))
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("tenders: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["notices"] + counts["suppliers"]


def publish(conn, staging: str, log=print) -> None:
    """The reading's tables from `staging` into `tenders`, and the views of
    publish.sql, in one transaction. The capture's tables stay."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"tenders: published from {staging}")


def unchanged(conn, listed: dict) -> bool:
    """True when the published reading read exactly the files listed now
    (register rule 10: rebuild only what changed)."""
    if conn.execute("SELECT to_regclass(%s)", (f"{SCHEMA}.read_files",)).fetchone()[0] is None:
        return False
    held = {r[0] for r in conn.execute(f"SELECT document FROM {SCHEMA}.read_files")}
    return held == set(listed.values())


def job(log=print) -> int:
    """qv4-tenders-load: build in STAGING of querynz_v4, hold it to the
    reading's own checks, publish only then."""
    from support import db
    from registers.tenders import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        listed = listings(conn)
        if unchanged(conn, listed):
            log("tenders: the listing is the one published; nothing loaded")
            jobrun.record(JOB, True, "unchanged: the listing is the one published", started, {})
            return 0
        with conn.transaction():
            counts = build(conn, STAGING, listed)
        problems = check.reading(conn, STAGING, listed)
        detail = (f"{counts['notices']} notices, {counts['suppliers']} suppliers, {counts['set_aside']} set aside; "
                  + ("; ".join(problems) or "reconciles"))
        if problems:
            log("tenders: RED, nothing published: " + detail)
            jobrun.record(JOB, False, "nothing published: " + detail, started, {})
            return 1
        publish(conn, STAGING, log)
    log("tenders: published: " + detail)
    jobrun.record(JOB, True, "published: " + detail, started, counts)
    return 0


def main(argv=None) -> int:
    from support import db
    ap = argparse.ArgumentParser(prog="python -m registers.tenders.load")
    ap.add_argument("--schema", default=SCRATCH)
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--job", action="store_true", help="qv4-tenders-load: build, check and publish into querynz_v4")
    a = ap.parse_args(argv)
    if a.job:
        return job()
    if not a.schema.startswith(("scratch_", "staging_")):
        print("tenders: a session loads only a scratch or staging schema")
        return 2
    with db.connect(db.READ_KEY, "querynz_v4") as src:
        src.execute("SET statement_timeout = '60s'")
        listed = listings(src)
    with db.connect(db.OWNER_KEY, a.database) as conn:
        with conn.transaction():
            counts = build(conn, a.schema, listed)
            conn.execute(sql("publish.sql", a.schema).replace("pub.", f"{a.schema}.pub_"))
    for k, v in counts.items():
        print(f"tenders: {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
