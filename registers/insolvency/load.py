"""Loading: `build(conn, schema)` reads the capture's ledger (schema `insolvency`: calls, search_seen, removals) into the
reading's tables under `schema`; `publish(conn, staging)` moves them into `insolvency` and makes the views, in one
transaction. Rebuilt whole every load (regenerable); the ledger is never touched by a load.

Every estate any answer named is published, or withheld with its reason, or set aside: in equals out, or the build raises.
The terms of holding a copy are applied here as read's rules: removed after our latest answer, suppressed, annulled, past
its display window; the views apply the window again on the day they are read (`shown_until >= current_date`).

    python -m registers.insolvency.load [--schema staging_…]      build into a staging schema and check, no publish
    python -m registers.insolvency.load --job                     build, check, publish only on green
"""
import argparse
import datetime as dt
import json
import os
import sys
import time

from support import jobrun
from support.docstore.landing import documents_of, read_bytes
from registers.insolvency import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = capture.SCHEMA
JOB = "qv4-insolvency-load"
STAGING = "staging_insolvency_load"
TABLES = ("estates", "withheld", "set_aside")
COLUMNS = {
    "estates": ("key", "estate_number", "kind", "register", "name", "alternate_names", "trading_names", "organisation_name",
                "nzbn", "company_number", "insolvency_type", "status", "adjudicated_on", "discharged_on", "discharge_type",
                "discharge_suspended", "annulled_on", "multiple", "occupation", "court", "office", "partnered_estates",
                "shown_until", "read_from", "document", "page", "place", "reader", "profile", "profile_version"),
    "withheld": ("estate_number", "reason", "document"),
    "set_aside": ("document", "place", "stage", "reason"),
}


def profile_version(slug: str = read.PROFILES["estate"]) -> int:
    from support import profiles
    try:
        return int(profiles.current()[slug]["version"])
    except KeyError:
        with open(os.path.join(HERE, "profile-proposed.jsonl"), encoding="utf-8") as f:
            return max(json.loads(l)["version"] for l in f if l.strip() and json.loads(l)["slug"] == slug)


def reading_sql(schema: str) -> str:
    return "CREATE SCHEMA IF NOT EXISTS " + schema + ";\n" + \
        capture.tables_sql(schema).split("-- the reading: rebuilt whole by every load")[1]


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def ledger(conn, schema: str = SCHEMA) -> dict:
    """What the capture holds: {estates: {estate: register}, details: {estate: (at, status, sha)} the latest detail call
    each, search: {estate: (at, sha)} the latest search page naming each, removals: {estate: [seen_at]}}. A detail
    answer withdrawn by a removal counts again only when it was asked after that removal (a correction the register
    answers with the same bytes lands as the same document, already withdrawn)."""
    conn.execute(capture.ledger_sql(schema))
    estates = dict(conn.execute(f"SELECT estate, register FROM {schema}.search_seen").fetchall())
    removals = {}
    for e, seen in conn.execute(f"SELECT estate, seen_at FROM {schema}.removals").fetchall():
        removals.setdefault(e, []).append(seen)
    calls = conn.execute(f"SELECT estate, at, status, document FROM {schema}.calls WHERE why IN ('detail', 'lookup') "
                         f"AND estate IS NOT NULL AND status IN (200, 404) ORDER BY estate, at DESC").fetchall()
    gone = {s for s, d in documents_of([c[3] for c in calls], conn).items() if d["withdrawn"]}
    details = {}
    for e, at, status, sha in calls:
        estates.setdefault(e, "Insolvency")
        if e in details:
            continue
        if sha in gone and not at > max(removals.get(e) or [at]):
            continue
        details[e] = (at, status, sha)
    for (e,) in conn.execute(f"SELECT DISTINCT estate FROM {schema}.calls WHERE why IN ('detail', 'lookup') "
                             f"AND estate IS NOT NULL").fetchall():
        estates.setdefault(e, "Insolvency")
    search = {e: (at, sha) for e, at, sha in conn.execute(
        f"SELECT s.estate, c.at, c.document FROM {schema}.search_seen s JOIN {schema}.calls c ON c.id = s.call "
        f"WHERE c.document IS NOT NULL").fetchall()}
    return {"estates": estates, "details": details, "search": search, "removals": removals}


def build(conn, schema: str, held: dict = None, read_bytes=read_bytes, today: dt.date = None, version: int = None,
          ledger_schema: str = SCHEMA) -> dict:
    t0 = time.monotonic()
    today = today or capture.now_nz().date()
    held = held if held is not None else ledger(conn, ledger_schema)
    version = version or profile_version()
    conn.execute(reading_sql(schema))
    rows, withheld, aside = [], [], []
    pages = {}
    for estate, register in sorted(held["estates"].items()):
        det = held["details"].get(estate)
        if det and det[1] == 404:
            withheld.append({"estate_number": estate, "reason": "absent from the register when last asked", "document": None})
            continue
        if det and det[2]:
            at, sha = det[0], det[2]
            e, read_from, place = json.loads(read_bytes(sha)), "detail", None
        elif estate in held["search"]:
            at, sha = held["search"][estate]
            if sha not in pages:
                pages[sha] = {int(r["estateNumber"]): r for r in read.search_results(read_bytes(sha))[0]}
            e, read_from, place = pages[sha].get(estate), "search", f"estateNumber={estate}"
            if e is None:
                aside.append({"document": sha, "place": place, "stage": "read",
                              "reason": "the search page the ledger names does not carry the estate"})
                continue
        elif estate in held["removals"]:
            withheld.append({"estate_number": estate, "reason": "removed or corrected; nothing answered since", "document": None})
            continue
        else:
            aside.append({"document": None, "place": f"estate {estate}", "stage": "read", "reason": "no answer held"})
            continue
        if read.removed(estate, at, held["removals"]):
            withheld.append({"estate_number": estate, "reason": "removed or corrected after our latest answer", "document": sha})
            continue
        why = read.why_withheld(e, register, today)
        if why:
            withheld.append({"estate_number": estate, "reason": why, "document": sha})
            continue
        rows.append(read.estate_row(e, register=register, read_from=read_from, document=sha, version=version, place=place))
    if len(held["estates"]) != len(rows) + len(withheld) + len(aside):
        raise AssertionError(f"{SCHEMA}: {len(held['estates'])} estates in, {len(rows)} read + {len(withheld)} withheld + "
                             f"{len(aside)} set aside")
    return {"estates": len(held["estates"]),
            "published": _copy(conn, f"{schema}.estates", COLUMNS["estates"], rows),
            "withheld": _copy(conn, f"{schema}.withheld", COLUMNS["withheld"], withheld),
            "set_aside": _copy(conn, f"{schema}.set_aside", COLUMNS["set_aside"], aside),
            "seconds": round(time.monotonic() - t0, 1)}


def publish(conn, staging: str, log=print, schema: str = SCHEMA, views: bool = True) -> None:
    """Into `schema` in one transaction; an estate the removals named after the answer its staged row was read from
    (the removals job may run between the build and this) is taken out again before the views are made."""
    with conn.transaction():
        conn.execute(reading_sql(schema))
        for t in TABLES:
            conn.execute(f"INSERT INTO {schema}.{t} SELECT * FROM {staging}.{t}")
        conn.execute(f"DELETE FROM {schema}.estates e USING {schema}.removals r WHERE r.estate = e.estate_number AND "
                     f"r.seen_at >= (SELECT max(c.at) FROM {schema}.calls c WHERE c.document = e.document)")
        if views:
            with open(os.path.join(HERE, "publish.sql"), encoding="utf-8") as f:
                conn.execute(f.read())
    log(f"{SCHEMA}: published from {staging}")


def job(log=print) -> int:
    """qv4-insolvency-load: build in staging, hold it to the checks, publish only then."""
    from support import db
    from registers.insolvency import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        with conn.transaction():
            counts = build(conn, STAGING)
        problems = check.reading(conn, STAGING)
        detail = (f"{counts['estates']} estates: {counts['published']} published, {counts['withheld']} withheld, "
                  f"{counts['set_aside']} set aside; " + ("; ".join(problems) or "reconciles"))
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
    from registers.insolvency import check
    ap = argparse.ArgumentParser(prog="python -m registers.insolvency.load")
    ap.add_argument("--schema", default="staging_insolvency_session")
    ap.add_argument("--job", action="store_true")
    a = ap.parse_args(argv)
    if a.job:
        return job()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        with conn.transaction():
            counts = build(conn, a.schema)
        problems = check.reading(conn, a.schema)
    print(f"{SCHEMA}: {counts} into {a.schema}; " + ("; ".join(problems) or "reconciles"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
