"""Loading: `build(conn, schema)` reads the capture's ledger (schema `insolvency`: calls, search_seen, removals) into the
reading's tables under `schema`; `publish(conn, staging)` moves them into `insolvency` and makes the views, in one
transaction. Rebuilt whole every load (regenerable); the ledger is never touched by a load.

Every estate any answer named is read into a row, or is unanswered (named, with no answer to read), or set aside: in
equals out, or the build raises. Nothing is withheld (ruling 142, 4 November 2026): the terms of holding a copy are flags
on the row (read.removed, read.suppressed, the annulment, read.shown_until; the views give `past_window` on the day they
are read), and a suppressed estate's names are kept by key in `insolvency_private.suppressed_names`.

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
from support.docstore.landing import read_bytes
from registers.insolvency import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = capture.SCHEMA
JOB = "qv4-insolvency-load"
STAGING = "staging_insolvency_load"
TABLES = ("estates", "unanswered", "set_aside")
PRIVATE_TABLES = ("suppressed_names",)
COLUMNS = {
    "estates": ("key", "estate_number", "kind", "register", "name", "alternate_names", "trading_names", "organisation_name",
                "nzbn", "company_number", "insolvency_type", "status", "adjudicated_on", "discharged_on", "discharge_type",
                "discharge_suspended", "annulled_on", "multiple", "occupation", "court", "office", "partnered_estates",
                "shown_until", "window_unknown", "suppressed", "suppressed_said", "removed_on", "removal_seen_at",
                "absent_since", "read_from", "document", "page", "place", "reader", "profile", "profile_version"),
    "unanswered": ("estate_number", "reason", "document"),
    "suppressed_names": ("key", "estate_number", "suppressed_said", "name", "alternate_names", "trading_names",
                         "organisation_name"),
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
    each that gave an answer (a 200), or the latest 404 where none did, absent: {estate: at} a 404 after that answer,
    search: {estate: (at, sha)} the latest search page naming each, removals: {estate: [(seen_at, removed_on)]}}. A
    document withdrawn by the removals before 4 November 2026 is read like any other (ruling 142: a removal is a flag)."""
    conn.execute(capture.ledger_sql(schema))
    estates = dict(conn.execute(f"SELECT estate, register FROM {schema}.search_seen").fetchall())
    removals = {}
    for e, seen, removed_on in conn.execute(f"SELECT estate, seen_at, removed_on FROM {schema}.removals "
                                            f"ORDER BY seen_at").fetchall():
        removals.setdefault(e, []).append((seen, removed_on))
    calls = conn.execute(f"SELECT estate, at, status, document FROM {schema}.calls WHERE why IN ('detail', 'lookup') "
                         f"AND estate IS NOT NULL AND status IN (200, 404) ORDER BY estate, at DESC").fetchall()
    details, absent = {}, {}
    for e, at, status, sha in calls:
        estates.setdefault(e, "Insolvency")
        if status == 404:
            if e not in details:
                absent.setdefault(e, at)
            continue
        if sha and e not in details:
            details[e] = (at, status, sha)
    for e, at in absent.items():
        if e not in details:
            details[e] = (at, 404, None)
    absent = {e: at for e, at in absent.items() if details[e][1] == 200 and at > details[e][0]}
    for (e,) in conn.execute(f"SELECT DISTINCT estate FROM {schema}.calls WHERE why IN ('detail', 'lookup') "
                             f"AND estate IS NOT NULL").fetchall():
        estates.setdefault(e, "Insolvency")
    search = {e: (at, sha) for e, at, sha in conn.execute(
        f"SELECT s.estate, c.at, c.document FROM {schema}.search_seen s JOIN {schema}.calls c ON c.id = s.call "
        f"WHERE c.document IS NOT NULL").fetchall()}
    return {"estates": estates, "details": details, "absent": absent, "search": search, "removals": removals}


def build(conn, schema: str, held: dict = None, read_bytes=read_bytes, today: dt.date = None, version: int = None,
          ledger_schema: str = SCHEMA) -> dict:
    t0 = time.monotonic()
    today = today or capture.now_nz().date()
    held = held if held is not None else ledger(conn, ledger_schema)
    version = version or profile_version()
    conn.execute(reading_sql(schema))
    rows, unanswered, aside, private = [], [], [], []
    pages = {}
    for estate, register in sorted(held["estates"].items()):
        det = held["details"].get(estate)
        e = None
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
        elif det and det[1] == 404:
            unanswered.append({"estate_number": estate, "reason": "absent from the register when asked; no answer held",
                               "document": None})
            continue
        elif estate in held["removals"]:
            unanswered.append({"estate_number": estate, "reason": "named by the removals; no answer held",
                               "document": None})
            continue
        else:
            aside.append({"document": None, "place": f"estate {estate}", "stage": "read", "reason": "no answer held"})
            continue
        row = read.estate_row(e, register=register, read_from=read_from, document=sha, version=version, place=place)
        after = [(seen, on) for seen, on in held["removals"].get(estate, ()) if seen >= at]
        if after and read.removed(estate, at, {estate: [seen for seen, _ in after]}):
            row["removal_seen_at"], row["removed_on"] = after[-1]
        row["absent_since"] = held.get("absent", {}).get(estate)
        names = read.private_names(row)
        if names:
            private.append(names)
        rows.append(row)
    if len(held["estates"]) != len(rows) + len(unanswered) + len(aside):
        raise AssertionError(f"{SCHEMA}: {len(held['estates'])} estates in, {len(rows)} read + {len(unanswered)} unanswered "
                             f"+ {len(aside)} set aside")
    return {"estates": len(held["estates"]),
            "read": _copy(conn, f"{schema}.estates", COLUMNS["estates"], rows),
            "suppressed": _copy(conn, f"{capture.private_of(schema)}.suppressed_names", COLUMNS["suppressed_names"], private),
            "past_window": sum(1 for r in rows if r["window_unknown"] or (r["shown_until"] and r["shown_until"] < today)),
            "removed": sum(1 for r in rows if r["removal_seen_at"]),
            "unanswered": _copy(conn, f"{schema}.unanswered", COLUMNS["unanswered"], unanswered),
            "set_aside": _copy(conn, f"{schema}.set_aside", COLUMNS["set_aside"], aside),
            "seconds": round(time.monotonic() - t0, 1)}


def flag_removals(conn, schema: str = SCHEMA) -> int:
    """Every row the removals named at or after the answer it was read from, flagged with the latest such naming (the
    removals job may run between a build and its publish). The rows flagged."""
    return conn.execute(
        f"UPDATE {schema}.estates e SET removal_seen_at = r.seen_at, removed_on = r.removed_on FROM (SELECT DISTINCT ON "
        f"(r.estate) r.estate, r.seen_at, r.removed_on FROM {schema}.removals r JOIN {schema}.estates x ON x.estate_number "
        f"= r.estate WHERE r.seen_at >= (SELECT max(c.at) FROM {schema}.calls c WHERE c.document = x.document) ORDER BY "
        f"r.estate, r.seen_at DESC) r WHERE r.estate = e.estate_number AND e.removal_seen_at IS DISTINCT FROM r.seen_at"
    ).rowcount


def publish(conn, staging: str, log=print, schema: str = SCHEMA, views: bool = True) -> None:
    """Into `schema` (and the suppressed names into its private schema) in one transaction; an estate the removals named
    after the answer its staged row was read from (the removals job may run between the build and this) is flagged
    before the views are made."""
    with conn.transaction():
        conn.execute(reading_sql(schema))
        for t in TABLES:
            conn.execute(f"INSERT INTO {schema}.{t} SELECT * FROM {staging}.{t}")
        for t in PRIVATE_TABLES:
            conn.execute(f"INSERT INTO {capture.private_of(schema)}.{t} SELECT * FROM {capture.private_of(staging)}.{t}")
        flag_removals(conn, schema)
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
        detail = (f"{counts['estates']} estates: {counts['read']} read ({counts['suppressed']} suppressed, "
                  f"{counts['past_window']} past their window, {counts['removed']} named by the removals, all kept and "
                  f"flagged), {counts['unanswered']} unanswered, {counts['set_aside']} set aside; " + ("; ".join(problems) or "reconciles"))
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
