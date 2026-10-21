"""The lane's one figure against the outside world (contract: the lane).

The source's own count is the Companies Office's: the registered limited
partnerships its monthly file names (`pub.companies`, 4,114 on 21 October
2026), which is this lane's frame. Exit 1 on any of:

  1. a frame partnership never answered and never set aside (the capture has
     not reached it): the lane is not yet a copy of the register
  2. of the partnerships answered, the share the register calls Registered
     differs from the file's count by more than `TOLERANCE` (the file is
     monthly; the register moves between files)
  3. the reading does not reconcile: an answer's roles in ≠ general
     partners typed + other roles + set aside, or a published partner view
     shows a name the register withholds, or a view carries an address
     column other than the partnership's registered office

While the first nights are still asking, 1 is red, and that is correct: a
lane fed by part of its frame is not green. Every line printed is a count.

    python -m registers.limited_partnerships.check [--schema limited_partnerships]
"""
import argparse
import json
import sys

from registers.limited_partnerships import capture

SCHEMA = "limited_partnerships"
TOLERANCE = 0.01
ADDRESSISH = ("address", "street", "postal", "residential", "home", "email", "phone")


def reading(conn, schema: str = SCHEMA, shared: bool = False) -> list:
    """Problems with a built reading (empty when it holds)."""
    from registers.limited_partnerships import load
    T = lambda t: load.table(schema, t, shared)
    out = []
    bad = conn.execute(f"SELECT count(*) FROM {T('read_answers')} WHERE NOT superseded AND recognised AND "
                       "roles <> partners + other_roles + set_aside").fetchone()[0]
    if bad:
        out.append(f"{bad} answers do not reconcile")
    typed = conn.execute(f"SELECT count(*) FROM {T('partners')}").fetchone()[0]
    said = conn.execute(f"SELECT coalesce(sum(partners), 0) FROM {T('read_answers')}").fetchone()[0]
    if typed != said:
        out.append(f"{typed} partner rows against {said} in the ledger")
    return out


def views(conn) -> list:
    """Problems with the published views."""
    out = []
    n = conn.execute("SELECT count(*) FROM pub.limited_partnership_partners WHERE suppressed AND "
                     "(first_name IS NOT NULL OR last_name IS NOT NULL OR full_name <> 'name withheld by the register')"
                     ).fetchone()[0]
    if n:
        out.append(f"{n} withheld partner names shown on pub.limited_partnership_partners")
    for v in ("limited_partnerships", "limited_partnership_partners"):
        cols = [r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = "
                                           "'pub' AND table_name = %s", (v,))]
        extra = [c for c in cols if any(w in c for w in ADDRESSISH) and c != "registered_office"]
        if extra:
            out.append(f"pub.{v} carries {', '.join(extra)}")
    return out


def outside(conn, schema: str = SCHEMA) -> dict:
    frame = set(capture.frame(conn))
    answered = {r[0]: r[1] for r in conn.execute(f"SELECT nzbn, status FROM {schema}.partnerships")}
    not_found = {r[0] for r in conn.execute(f"SELECT DISTINCT nzbn FROM {schema}.capture_asks WHERE status = 404")}
    aside = {r[0] for r in conn.execute(f"SELECT DISTINCT item FROM {schema}.capture_set_aside")}
    unreached = frame - set(answered) - not_found - aside
    registered = sum(1 for n, s in answered.items() if n in frame and s == "Registered")
    reached = len(frame) - len(unreached)
    share_ok = reached == 0 or abs(registered - (reached - len(frame & not_found))) <= TOLERANCE * len(frame)
    return {"frame": len(frame), "answered": len(frame & set(answered)), "not_found": len(frame & not_found),
            "set_aside": len(frame & aside - set(answered)), "unreached": len(unreached),
            "registered_per_register": registered, "ok": not unreached and share_ok}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.limited_partnerships.check")
    ap.add_argument("--schema", default=SCHEMA)
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.READ_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        if conn.execute("SELECT to_regclass(%s)", (f"{a.schema}.read_answers",)).fetchone()[0] is None:
            print(f"{SCHEMA}: check: nothing published yet (no load has run)")
            return 1
        out = outside(conn, a.schema)
        problems = reading(conn, a.schema) + views(conn)
    out["problems"] = problems
    print(f"{SCHEMA}: check: " + json.dumps(out))
    return 0 if out["ok"] and not problems else 1


if __name__ == "__main__":
    sys.exit(main())
