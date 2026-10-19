"""The links module's check against the outside world (spec line 4).

    python -m links.check [--schema scratch_links]        exits 1 on any failure

1. Every row of the three old ledgers is copied once: the count in
   `old_decisions` per ledger equals the old database's own count.
2. No confirming address is anything but a company's registered office,
   and none comes from a monthly file dated on or after 18 November 2026,
   the day director address suppression begins (plan 4.3: an address a
   director substituted after that day must never confirm a link).
3. The published views answer with the tables' counts (links, groups,
   decisions), so the board reads what was built.
"""
from __future__ import annotations

import datetime as dt
import json
import sys

import links
from links import old, rules

SUPPRESSION_DAY = dt.date(2026, 11, 18)


def check_old_copy(oldconn, conn, s: str) -> list:
    out = []
    for table in old.LEDGERS:
        theirs = oldconn.execute(f"SELECT count(*) FROM registers.{table}").fetchone()[0]
        ours = conn.execute(f"SELECT count(*) FROM {s}.old_decisions WHERE source = %s", (table,)).fetchone()[0]
        out.append({"check": f"old ledger copied: {table}", "old_database": int(theirs), "copied": int(ours), "ok": int(theirs) == int(ours)})
    return out


def check_addresses(conn, s: str) -> list:
    bad_kind = conn.execute(f"SELECT count(*) FROM {s}.entity_addresses WHERE kind <> 'registered office'").fetchone()[0]
    late = conn.execute(f"""
        SELECT count(*) FROM {s}.links l
        WHERE l.rule = %s AND EXISTS (
            SELECT 1 FROM {s}.entity_addresses a
            WHERE a.address_key = l.evidence->>'shared_address'
              AND (a.started_on >= %s OR substring(a.last_file FROM '[0-9]{{4}}-[0-9]{{2}}') >= %s))""",
        (rules.RULE_ADDRESS, SUPPRESSION_DAY, SUPPRESSION_DAY.strftime("%Y-%m"))).fetchone()[0]
    return [{"check": "every address the rules read is a registered office", "other_kinds": int(bad_kind), "ok": bad_kind == 0},
            {"check": "no confirming address from on or after 18 November 2026", "links_with_a_late_address": int(late), "ok": late == 0}]


def check_published(conn, s: str, pub: str = "pub") -> list:
    out = []
    for view, table in (("links", "links"), ("groups", "groups"), ("decisions", "decisions")):
        exists = conn.execute("SELECT 1 FROM information_schema.views WHERE table_schema = %s AND table_name = %s", (pub, view)).fetchone()
        if not exists:
            out.append({"check": f"{pub}.{view} published", "ok": False, "note": "view missing"})
            continue
        a = conn.execute(f"SELECT count(*) FROM {pub}.{view}").fetchone()[0]
        b = conn.execute(f"SELECT count(*) FROM {s}.{table}").fetchone()[0]
        out.append({"check": f"{pub}.{view} answers with the table's count", "view": int(a), "table": int(b), "ok": int(a) == int(b)})
    return out


def run(conn, s: str, oldconn=None, pub: str = "pub") -> list:
    out = []
    if oldconn is not None:
        out += check_old_copy(oldconn, conn, s)
    out += check_addresses(conn, s)
    out += check_published(conn, s, pub)
    return out


def main(argv=None) -> int:
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    s = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    pub = argv[argv.index("--pub") + 1] if "--pub" in argv else "pub"
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn, db.connect(db.OLD_READ_KEY, old.OLD_DB) as oldconn:
        conn.execute("SET statement_timeout = '300s'")
        results = run(conn, s, oldconn, pub)
    print(json.dumps(results, indent=1))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
