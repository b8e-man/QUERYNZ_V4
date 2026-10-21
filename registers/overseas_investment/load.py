"""Loading (plan 1b.7): `build(conn, schema, entries)` reads the listed
summaries into the reading's tables under `schema`; `publish(conn, staging)`
moves them into `overseas_investment` and its private twin and makes the
views, in one transaction. sample.py uses the same `build`.

What is read: every (summary page, case number) row the newest finished
pass of each year's listing lists, at the newest hash held for the page. A
page that carries two case numbers is read once; each of its rows is a
ledger line, and the parties are counted on the first. So a summary the
office takes down leaves the views at the next load. A row listed and not
yet captured is a ledger line ('not captured'), never a decision. Rows in
equal rows read plus set aside plus not captured; the build raises if they
do not.

    python -m registers.overseas_investment.load [--schema scratch_…] [--database querynz_v4_sample]
    python -m registers.overseas_investment.load --job

Every line printed is a count.
"""
import argparse
import os
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.overseas_investment import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "overseas_investment"
JOB = "qv4-overseas-investment-load"
STAGING = "staging_overseas_investment_load"
TABLES = ("read_items", "decisions", "parties", "investments", "read_set_aside")
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "read_items": ("list", "slug", "case_number", "pass_id", "document", "state", "parties"),
    "decisions": ("key", "slug", "url", "case_numbers", "case_number", "kind", "outcome", "granted", "section",
                  "decision_maker", "decided_on", "pathway", "investment_class", "investment", "addresses_withheld",
                  "areas_stated", "area_ha", "consideration_heading", "consideration_stated", "consideration_nzd",
                  "consideration_withheld", "penalty_stated", "notification_number", "parent_case",
                  "applicant_listed", "rationale", "headings", "attachments") + _CITE,
    "parties": ("key", "decision_key", "ordinal", "role", "role_stated", "name", "withheld", "withheld_by", "status",
                "trust", "organisation", "company_number", "ownership_lines", "origins", "shares", "ownership_scope")
               + _CITE,
    "investments": ("key", "investment_stated", "document"),
    "read_set_aside": ("document", "place", "stage", "reason"),
}
table = capture.table


def sql(name: str, schema: str = SCHEMA) -> str:
    """tables.sql's reading part, or publish.sql, for `schema` (prefixed names outside the lane's own schema)."""
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    if name == "tables.sql":
        text = capture.READING + text.split(capture.READING, 1)[1]
    return capture.rewrite(text, schema)


def create_tables(conn, schema: str) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {capture.private_of(schema)}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t)} CASCADE")
    conn.execute(sql("tables.sql", schema))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def build(conn, schema: str, entries: list, read_bytes=read_bytes) -> dict:
    """`entries`: [(list, slug, case_number, url, sha256 or None, pass_id)], one per listed row."""
    t0 = time.monotonic()
    create_tables(conn, schema)
    T = lambda t: table(schema, t)
    ledger, decisions, parties, private, asides = [], [], [], [], []
    done = {}                                   # slug → the page's reading, so a page with two case numbers is read once
    for lst, slug, case, url, sha, pass_id in entries:
        line = {"list": lst, "slug": slug, "case_number": case, "pass_id": pass_id, "document": sha, "parties": 0}
        if sha is None:
            ledger.append({**line, "state": "not captured"})
            continue
        if slug not in done:
            out = read.read_summary(read_bytes(sha), sha, slug, url)
            done[slug] = out
            asides += out["set_aside"]
            if out["decision"] is not None:
                decisions.append(out["decision"])
                parties += out["parties"]
                private += out["private"]
                line["parties"] = len(out["parties"])
        out = done[slug]
        if out["decision"] is None:
            ledger.append({**line, "state": "set aside"})
        elif case not in out["decision"]["case_numbers"]:
            ledger.append({**line, "state": "set aside"})
            asides.append({"document": sha, "place": f"summary={slug}", "stage": "case number",
                           "reason": f"listed under {case}; the page states {', '.join(out['decision']['case_numbers'])}"})
        else:
            ledger.append({**line, "state": "read"})
    if len(ledger) != len({(e[0], e[1], e[2]) for e in entries}):
        raise AssertionError(f"{SCHEMA}: {len(entries)} rows listed, {len(ledger)} in the ledger")
    return {"decisions": _copy(conn, T("decisions"), COLUMNS["decisions"], decisions),
            "parties": _copy(conn, T("parties"), COLUMNS["parties"], parties),
            "private": _copy(conn, T("investments"), COLUMNS["investments"], private),
            "set_aside": _copy(conn, T("read_set_aside"), COLUMNS["read_set_aside"], asides),
            "listed": _copy(conn, T("read_items"), COLUMNS["read_items"], ledger),
            "not_captured": sum(1 for l in ledger if l["state"] == "not captured"),
            "seconds": round(time.monotonic() - t0, 1)}


def listing(conn, schema: str = SCHEMA) -> list:
    """Every row the newest finished pass of each year's listing lists, with the newest hash held for its page."""
    T = lambda t: table(schema, t)
    out = []
    for lst in capture.lists():
        r = conn.execute(f"SELECT max(pass_id) FROM {T('capture_passes')} WHERE list = %s AND finished_at IS NOT NULL",
                         (lst.name,)).fetchone()
        if not r or r[0] is None:
            continue
        out += [tuple(x) for x in conn.execute(
            f"SELECT l.list, l.slug, l.case_number, l.url, (SELECT i.sha256 FROM {T('capture_items')} i "
            f"WHERE i.slug = l.slug ORDER BY i.at DESC LIMIT 1), l.pass_id FROM {T('capture_listed')} l "
            "WHERE l.pass_id = %s ORDER BY l.ordinal", (r[0],))]
    return out


def publish(conn, staging: str, log=print) -> None:
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"{SCHEMA}: published from {staging}")


def unchanged(conn, listed: list) -> bool:
    if conn.execute("SELECT to_regclass(%s)", (f"{SCHEMA}.read_items",)).fetchone()[0] is None:
        return False
    held = {tuple(r) for r in conn.execute(f"SELECT list, slug, case_number, document FROM {SCHEMA}.read_items")}
    return held == {(e[0], e[1], e[2], e[4]) for e in listed}


def job(log=print) -> int:
    """qv4-overseas-investment-load: build in staging, hold it to the reading's checks, publish only then."""
    from support import db
    from registers.overseas_investment import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        listed = listing(conn)
        if not listed:
            log(f"{SCHEMA}: no finished pass of any year's listing is held; nothing loaded")
            jobrun.record(JOB, False, "no finished pass of the listing is held", started, {})
            return 1
        if unchanged(conn, listed):
            log(f"{SCHEMA}: the listing is the one published; nothing loaded")
            jobrun.record(JOB, True, "unchanged: the listing is the one published", started, {})
            return 0
        with conn.transaction():
            counts = build(conn, STAGING, listed)
        problems = check.reading(conn, STAGING)
        detail = (f"{counts['decisions']} decisions, {counts['parties']} parties, {counts['set_aside']} set aside, "
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
    ap = argparse.ArgumentParser(prog="python -m registers.overseas_investment.load")
    ap.add_argument("--schema", default="scratch_overseas_investment_full")
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
