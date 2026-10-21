"""Loading (plan 1b.7): `build(conn, schema, answers)` reads the listed
answers into the reading's tables under `schema` and its private twin;
`publish(conn, staging)` moves them into `limited_partnerships` and makes
the views, in one transaction. sample.py uses the same `build`.

Idempotent per listing: the reading's tables are dropped and made again and
every answer read again, so a second load of the same listing gives the
same rows under the same keys (only `loaded_at` moves). Of several answers
for one partnership the newest asked is read and the older are superseded
(counted in the ledger). Roles in equal partners typed plus other roles plus
set aside, answer by answer; the build raises if one does not reconcile.

    python -m registers.limited_partnerships.load [--schema scratch_…] [--database querynz_v4_sample]
    python -m registers.limited_partnerships.load --job     # build in staging, check, publish

Every line printed is a count.
"""
import argparse
import collections
import os
import re
import sys
import time
from zoneinfo import ZoneInfo

from support import jobrun
from support.docstore.landing import read_bytes
from registers.limited_partnerships import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "limited_partnerships"
PRIVATE = "limited_partnerships_private"
JOB = "qv4-limited-partnerships-load"
STAGING = "staging_limited_partnerships_load"
TABLES = ("read_answers", "partnerships", "partners", "read_set_aside")
PRIVATE_TABLES = ("addresses",)
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "read_answers": ("document", "nzbn", "asked_at", "superseded", "recognised", "roles", "partners", "other_roles", "set_aside"),
    "partnerships": ("key", "nzbn", "number", "name", "name_withheld", "kind", "entity_type", "type_description",
                     "status", "status_code", "registered_on", "country_of_origin", "registered_office",
                     "office_since", "asked_on") + _CITE,
    "partners": ("key", "partnership_key", "nzbn", "role_id", "kind", "full_name", "first_name", "middle_names",
                 "last_name", "body_nzbn", "suppressed", "current", "status", "started_on", "ended_on",
                 "dates_stated", "asked_on") + _CITE,
    "read_set_aside": ("document", "place", "stage", "reason"),
    "addresses": ("key", "address_type", "address", "document", "place"),
}
NZ = ZoneInfo("Pacific/Auckland")


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    where = private_of(schema) if t in PRIVATE_TABLES else schema
    return f"{where}.{SCHEMA}_{t}" if shared else f"{where}.{t}"


_NAMES = re.compile(r"(?<![A-Za-z0-9_])limited_partnerships(_private)?\.")


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
    for t in TABLES + PRIVATE_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def build(conn, schema: str, answers: list, read_bytes=read_bytes, shared: bool = False, version: int = None) -> dict:
    """`answers`: [(sha256, nzbn, asked_at)] as the listing names them. The
    newest answer per partnership is read; the rest are superseded."""
    t0 = time.monotonic()
    version = version or read.profile_version()
    create_tables(conn, schema, shared)
    T = lambda t: table(schema, t, shared)
    newest = {}
    for sha, nzbn, at in answers:
        if nzbn not in newest or at > newest[nzbn][1]:
            newest[nzbn] = (sha, at)
    rows = collections.defaultdict(list)
    ledger, seen = [], set()
    for sha, nzbn, at in sorted(answers, key=lambda a: (a[1], a[2])):
        if sha in seen:
            continue
        seen.add(sha)
        if newest[nzbn][0] != sha:
            ledger.append({"document": sha, "nzbn": nzbn, "asked_at": at, "superseded": True, "recognised": False, "roles": 0,
                           "partners": 0, "other_roles": 0, "set_aside": 0})
            continue
        out = read.read_answer(read_bytes(sha), sha, at.astimezone(NZ).date(), version)
        if out["partnership"] is not None and out["partnership"]["nzbn"] != nzbn:
            out = {**out, "partnership": None, "partners": [], "addresses": [], "roles": 0, "other_roles": 0,
                   "set_aside": [{"document": sha, "place": "answer", "stage": "key",
                                  "reason": "the answer is for another NZBN than the one asked"}]}
        if out["partnership"]:
            rows["partnerships"].append(out["partnership"])
        rows["partners"] += out["partners"]
        rows["addresses"] += out["addresses"]
        rows["read_set_aside"] += out["set_aside"]
        role_asides = sum(1 for a in out["set_aside"] if a["place"].startswith("roles["))
        if out["roles"] != len(out["partners"]) + out["other_roles"] + role_asides:
            raise AssertionError(f"{SCHEMA}: answer {sha[:12]} does not reconcile (roles in ≠ typed + other + set aside)")
        ledger.append({"document": sha, "nzbn": nzbn, "asked_at": at, "superseded": False,
                       "recognised": out["partnership"] is not None, "roles": out["roles"],
                       "partners": len(out["partners"]), "other_roles": out["other_roles"], "set_aside": role_asides})
    counts = {t: _copy(conn, T(t), COLUMNS[t], rows[t]) for t in ("partnerships", "partners", "read_set_aside", "addresses")}
    counts["answers"] = _copy(conn, T("read_answers"), COLUMNS["read_answers"], ledger)
    counts["superseded"] = sum(1 for l in ledger if l["superseded"])
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return counts


def listing(conn, schema: str = SCHEMA) -> list:
    """Every answer the capture landed: [(sha256, nzbn, asked_at)]."""
    return [tuple(r) for r in conn.execute(
        f"SELECT sha256, nzbn, asked_at FROM {schema}.capture_asks WHERE status = 200 AND sha256 IS NOT NULL "
        "ORDER BY asked_at")]


def load(conn, schema: str, log=print) -> int:
    """The merge gate's staging step (support/staging): every landed answer, read under `schema`.
    Problems the reading's check finds are logged, as the job logs them. Added by the integrator at the merge of sanctions-1."""
    from registers.limited_partnerships import check
    listed = listing(conn)
    counts = build(conn, schema, listed)
    problems = check.reading(conn, schema)
    log(f"{SCHEMA}: {counts['partnerships']} partnerships, {counts['partners']} general partners, "
        f"{counts['read_set_aside']} set aside into {schema}; " + ("; ".join(problems) or "reconciles"))
    return counts["partnerships"] + counts["partners"]


def publish(conn, staging: str, log=print) -> None:
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES + PRIVATE_TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"{SCHEMA}: published from {staging}")


def unchanged(conn, listed: list) -> bool:
    if conn.execute("SELECT to_regclass(%s)", (f"{SCHEMA}.read_answers",)).fetchone()[0] is None:
        return False
    held = {r[0] for r in conn.execute(f"SELECT document FROM {SCHEMA}.read_answers")}
    return held == {sha for sha, _, _ in listed}


def job(log=print) -> int:
    """qv4-limited-partnerships-load: build in STAGING, hold it to the
    reading's own checks, publish only then."""
    from support import db
    from registers.limited_partnerships import check
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
        detail = (f"{counts['partnerships']} partnerships, {counts['partners']} general partners, "
                  f"{counts['read_set_aside']} set aside; " + ("; ".join(problems) or "reconciles"))
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
    ap = argparse.ArgumentParser(prog="python -m registers.limited_partnerships.load")
    ap.add_argument("--schema", default="scratch_limited_partnerships_full")
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--capture-database", default="querynz_v4", help="where the capture's listing is")
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
