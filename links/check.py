"""The links module's check against the outside world (spec line 4).

    python -m links.check [--schema scratch_links]        exits 1 on any failure

1. Every row of the three old ledgers is copied once: the count in
   `old_decisions` per ledger equals the old database's own count, and so
   does the count withdrawn (each build brings the copy level, so the two
   counts are of the same thing; a decision the old estate made since the
   last build is named as such, not as a missing copy).
2. No confirming address is anything but a company's registered office,
   and none comes from a monthly file dated on or after 18 November 2026,
   the day director address suppression begins (plan 4.3: an address a
   director substituted after that day must never confirm a link).
3. The published views answer with the tables' counts (links, groups,
   decisions), so the board reads what was built.
4. The rows have read every published view they name as it stands now:
   each view counted again equals what the last gather read, and the
   catch log reconciles (read = written + set aside).
5. No reading of the review agent has become a decision while the apply
   switch (`links.SETTINGS["review_applies"]`) is off, and every decision
   the agent made names a passing score of the judgment that made it
   (track C: until it passes, verdicts are recorded and never applied).
"""
from __future__ import annotations

import datetime as dt
import json
import sys

import links
from links import old, rows, rules

SUPPRESSION_DAY = dt.date(2026, 11, 18)


def check_old_copy(oldconn, conn, s: str) -> list:
    """Like with like: the old rows up to the copy's highest old id, and
    those withdrawn, against the copy's; the rows the old estate added
    since the copy was brought level are counted beside, as the next
    build's to copy."""
    out = []
    for table in old.LEDGERS:
        ours, ours_w, top = conn.execute(f"""SELECT count(*), count(*) FILTER (WHERE coalesce(copied->>'withdrawn_at', '') <> ''),
                                                   coalesce(max(split_part(old_id, ':', 2)::bigint), 0)
                                            FROM {s}.old_decisions WHERE source = %s""", (table,)).fetchone()
        theirs, theirs_w, since = oldconn.execute(f"""SELECT count(*) FILTER (WHERE id <= %s), count(*) FILTER (WHERE id <= %s AND withdrawn_at IS NOT NULL),
                                                             count(*) FILTER (WHERE id > %s)
                                                      FROM registers.{table}""", (top, top, top)).fetchone()
        out.append({"check": f"old ledger copied: {table}", "old_database": int(theirs), "copied": int(ours),
                    "withdrawn_old": int(theirs_w), "withdrawn_copied": int(ours_w), "highest_old_id_copied": int(top),
                    "decided_since_the_copy": int(since),
                    "ok": int(theirs) == int(ours) and int(theirs_w) == int(ours_w)})
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


def check_rows_current(conn, s: str) -> list:
    """The rows have read every published view they name, and none has
    grown since: each view's rows, counted again now, equal what the last
    gather read (its catch log: read = written + set aside). A lane that
    loaded rows after the links last ran fails here (card: the links held a
    donor key read before party-returns-5 fixed the row)."""
    out = []
    logged = {v: (int(r), int(w), int(a)) for v, r, w, a in conn.execute(f"SELECT view, read, written, set_aside FROM {s}.rows_catch").fetchall()}
    for register, view, sql in rows.SOURCES:
        now = int(conn.execute(f"SELECT count(*) FROM ({sql}) q").fetchone()[0])
        held = int(conn.execute(f"SELECT count(*) FROM {s}.rows WHERE view = %s", (view,)).fetchone()[0])
        read, written, aside = logged.get(view, (0, 0, 0))
        out.append({"check": f"{register}.{view}: the rows read the view as it stands", "published_now": now, "read_last": read,
                    "written": written, "set_aside": aside, "held": held,
                    "ok": now == read and held == written and read == written + aside})
    return out


def check_review_switch(conn, s: str, applies: bool = None) -> list:
    """A reading never becomes a decision while the switch is off; and each
    decision the agent made rests on a score that passed."""
    from links import review
    applies = review.applies() if applies is None else applies
    made = conn.execute(f"SELECT count(*) FROM {s}.decisions WHERE made_by LIKE 'review-agent@%%'").fetchone()[0]
    unscored = conn.execute(f"""SELECT count(*) FROM {s}.decisions d WHERE d.made_by LIKE 'review-agent@%%'
                                AND NOT EXISTS (SELECT 1 FROM {s}.scores sc WHERE sc.run_id = d.made_on->'applied_under'->>'score_run' AND sc.passed)""").fetchone()[0]
    return [{"check": "no review-agent reading became a decision while the switch is off", "switch": "on" if applies else "off",
             "review_agent_decisions": int(made), "ok": applies or int(made) == 0},
            {"check": "every review-agent decision names a passing score", "without_a_passing_score": int(unscored), "ok": int(unscored) == 0}]


def run(conn, s: str, oldconn=None, pub: str = "pub") -> list:
    out = []
    if oldconn is not None:
        out += check_old_copy(oldconn, conn, s)
    out += check_addresses(conn, s)
    out += check_published(conn, s, pub)
    out += check_rows_current(conn, s)
    out += check_review_switch(conn, s)
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
