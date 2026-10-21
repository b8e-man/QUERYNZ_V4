"""Loading (plan 1b.7): `build(conn, schema, entries)` reads the listed
entries into the reading's tables under `schema`; `publish(conn, staging)`
moves them into `hdc_decisions` and its private twin and makes the views,
in one transaction. sample.py uses the same `build`.

What is read: every entry the newest finished pass of each listing lists,
dated from 2017 (ruling 71), at the newest hash held for it. So a page the
Commissioner takes down leaves the views at the next load. An entry listed
and not yet captured is a ledger line ('not captured'), never a row. Items
in equal pages read plus set aside plus not captured; the build raises if
they do not.

HELD with the capture (`capture.authorisation`): the job loads nothing, and
`publish` publishes nothing, until the position carries an `authorised:`
line. A session's load into a scratch or staging schema of the sample
database is not held: it reads the proof.

    python -m registers.hdc_decisions.load [--schema scratch_…] [--database querynz_v4_sample]
    python -m registers.hdc_decisions.load --job

Every line printed is a count.
"""
import argparse
import os
import re
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.hdc_decisions import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "hdc_decisions"
JOB = "qv4-hdc-decisions-load"
STAGING = "staging_hdc_decisions_load"
TABLES = ("read_items", "decisions", "providers", "read_set_aside")
PRIVATE_TABLES = ("page_addresses",)
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "read_items": ("list", "slug", "pass_id", "document", "state", "providers"),
    "decisions": ("key", "slug", "kind_of_page", "case_number", "case_numbers", "web_id", "decided_on", "kind", "findings",
                  "provider_kinds", "occupations", "rights_tagged", "rights_breached", "recommendation_headings",
                  "recommended_to", "named_roles", "naming_grounds", "names_removed", "providers_named", "url") + _CITE,
    "providers": ("key", "decision_key", "ordinal", "name", "abbreviation", "also_called", "found_by", "findings",
                  "rights_breached", "recommended", "company_number", "charity_number", "decided_on") + _CITE,
    "read_set_aside": ("document", "place", "stage", "reason"),
    "page_addresses": ("key", "slug", "url", "document"),
}
_NAMES = re.compile(rf"(?<![A-Za-z0-9_]){SCHEMA}(_private)?\.")


def table(schema: str, t: str) -> str:
    """The lane's own tables by name (the private one in the twin); elsewhere with the lane's prefix."""
    if schema == SCHEMA and t in PRIVATE_TABLES:
        return f"{SCHEMA}_private.{t}"
    return capture.table(schema, t)


def sql(name: str, schema: str = SCHEMA) -> str:
    """tables.sql's reading part, or publish.sql, for `schema` (prefixed names outside the lane's own schema)."""
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    if name == "tables.sql":
        text = capture.READING + text.split(capture.READING, 1)[1]
    pre = "" if schema == SCHEMA else f"{SCHEMA}_"
    return _NAMES.sub(lambda m: f"{schema}{'_private' if m.group(1) and schema == SCHEMA else ''}.{pre}", text)


def create_tables(conn, schema: str) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    if schema == SCHEMA:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}_private")
    for t in TABLES + PRIVATE_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t)} CASCADE")
    conn.execute(sql("tables.sql", schema))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def kind_of(lst: str) -> str:
    return "case study" if lst == "case-studies" else "decision"


def build(conn, schema: str, entries: list, read_bytes=read_bytes) -> dict:
    """`entries`: [(list, slug, url, sha256 or None, pass_id)], one per listed entry dated from 2017."""
    t0 = time.monotonic()
    create_tables(conn, schema)
    T = lambda t: table(schema, t)
    ledger, decisions, providers, asides, private = [], [], [], [], []
    for lst, slug, url, sha, pass_id in entries:
        if sha is None:
            ledger.append({"list": lst, "slug": slug, "pass_id": pass_id, "document": None, "state": "not captured",
                           "providers": 0})
            continue
        out = read.read_page(read_bytes(sha), sha, slug, url, kind=kind_of(lst))
        asides += out["set_aside"]
        if out["decision"] is None or out["decision"]["decided_on"] < read.SINCE:
            if out["decision"] is not None:
                asides.append({"document": sha, "place": out["decision"]["place"], "stage": "window",
                               "reason": "dated before 2017 (ruling 71)"})
            ledger.append({"list": lst, "slug": slug, "pass_id": pass_id, "document": sha, "state": "set aside",
                           "providers": 0})
            continue
        decisions.append(out["decision"])
        providers += out["providers"]
        private += out["private"]
        ledger.append({"list": lst, "slug": slug, "pass_id": pass_id, "document": sha, "state": "read",
                       "providers": len(out["providers"])})
    if len(ledger) != len({(e[0], e[1]) for e in entries}):
        raise AssertionError(f"{SCHEMA}: {len(entries)} entries listed, {len(ledger)} in the ledger")
    return {"decisions": _copy(conn, T("decisions"), COLUMNS["decisions"], decisions),
            "providers": _copy(conn, T("providers"), COLUMNS["providers"], providers),
            "set_aside": _copy(conn, T("read_set_aside"), COLUMNS["read_set_aside"], asides),
            "private": _copy(conn, T("page_addresses"), COLUMNS["page_addresses"], private),
            "listed": _copy(conn, T("read_items"), COLUMNS["read_items"], ledger),
            "not_captured": sum(1 for l in ledger if l["state"] == "not captured"),
            "seconds": round(time.monotonic() - t0, 1)}


def listing(conn, schema: str = SCHEMA) -> list:
    """Every entry the newest finished pass of each listing lists, dated from 2017, with the newest hash held for it."""
    T = lambda t: capture.table(schema, t)
    if conn.execute("SELECT to_regclass(%s)", (T("capture_passes"),)).fetchone()[0] is None:
        return []
    out = []
    names = [r[0] for r in conn.execute(f"SELECT DISTINCT list FROM {T('capture_passes')} ORDER BY list")]
    for name in names:
        r = conn.execute(f"SELECT max(pass_id) FROM {T('capture_passes')} WHERE list = %s AND finished_at IS NOT NULL",
                         (name,)).fetchone()
        if not r or r[0] is None:
            continue
        out += [tuple(x) for x in conn.execute(
            f"SELECT l.list, l.slug, l.url, (SELECT i.sha256 FROM {T('capture_items')} i WHERE i.list = l.list "
            f"AND i.slug = l.slug ORDER BY i.at DESC LIMIT 1), l.pass_id FROM {T('capture_listed')} l "
            "WHERE l.pass_id = %s AND (l.listed_on IS NULL OR l.listed_on >= %s) ORDER BY l.ordinal", (r[0], read.SINCE))]
    return out


def publish(conn, staging: str, log=print) -> None:
    if not capture.authorisation():
        log(f"{SCHEMA}: held: the Commissioner's written permission is not on file (copyright 3.2); nothing published")
        return
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES + PRIVATE_TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"{SCHEMA}: published from {staging}")


def load(conn, schema: str, log=print) -> int:
    """The merge gate's staging step: held, the tables are made empty under `schema` and nothing is read."""
    if not capture.authorisation():
        create_tables(conn, schema)
        log(f"{SCHEMA}: held: the Commissioner's written permission is not on file (copyright 3.2); nothing loaded")
        return 0
    counts = build(conn, schema, listing(conn))
    log(f"{SCHEMA}: {counts['decisions']} decisions, {counts['providers']} providers into {schema}")
    return counts["decisions"] + counts["providers"]


def unchanged(conn, listed: list) -> bool:
    if conn.execute("SELECT to_regclass(%s)", (f"{SCHEMA}.read_items",)).fetchone()[0] is None:
        return False
    held = {(r[0], r[1], r[2]) for r in conn.execute(f"SELECT list, slug, document FROM {SCHEMA}.read_items")}
    return held == {(e[0], e[1], e[3]) for e in listed}


def job(log=print) -> int:
    """qv4-hdc-decisions-load: build in staging, hold it to the reading's checks, publish only then."""
    from support import db
    from registers.hdc_decisions import check
    started = jobrun.now()
    if not capture.authorisation():
        log(f"{SCHEMA}: held: the Commissioner's written permission is not on file (copyright 3.2); nothing loaded")
        jobrun.record(JOB, True, "held: no authorisation on file", started, {})
        return 0
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        listed = listing(conn)
        if not listed:
            log(f"{SCHEMA}: no finished pass of a listing is held; nothing loaded")
            jobrun.record(JOB, False, "no finished pass of a listing is held", started, {})
            return 1
        if unchanged(conn, listed):
            log(f"{SCHEMA}: the listing is the one published; nothing loaded")
            jobrun.record(JOB, True, "unchanged: the listing is the one published", started, {})
            return 0
        with conn.transaction():
            counts = build(conn, STAGING, listed)
        problems = check.reading(conn, STAGING)
        detail = (f"{counts['decisions']} decisions, {counts['providers']} providers, {counts['set_aside']} set aside, "
                  f"{counts['not_captured']} not captured; " + ("; ".join(problems) or "reconciles"))
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
    ap = argparse.ArgumentParser(prog="python -m registers.hdc_decisions.load")
    ap.add_argument("--schema", default="scratch_hdc_decisions_full")
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--capture-database", default="querynz_v4_sample")
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
