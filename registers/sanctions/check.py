"""The lane's one figure per list against the outside world (contract: the lane).

  nz-police-tsa  the current Resolution 1373 designations read from the
                 workbook against the count the Police's own 1373 page states
                 ("New Zealand currently has N non-UN listed entities")
  mfat-russia    the current listings against the Total row's figure, where
                 the workbook carries one
  un-sc          the XML states no total: every INDIVIDUAL and ENTITY is a
                 listing or a catch-log line, and the list's own
                 dateGenerated is within `FRESH_DAYS` of the load

Exit 1 on any difference, on a list not read (held on its terms, or never
landed: a lane fed by nothing is not green), on a reading that does not
reconcile, and on a view carrying an address-like or document-number column.
Every line printed is a count.

    python -m registers.sanctions.check
"""
import argparse
import datetime as dt
import json
import sys

from registers.sanctions import capture

SCHEMA = "sanctions"
FRESH_DAYS = 14
FORBIDDEN = ("address", "street", "city", "postal", "passport", "document_number", "national_id", "comment")


def reading(conn, schema: str = SCHEMA, shared: bool = False) -> list:
    from registers.sanctions import load
    T = lambda t: load.table(schema, t, shared)
    out = []
    for list_id, n, ended in conn.execute(f"SELECT list_id, listings, ended FROM {T('lists')}"):
        got = conn.execute(f"SELECT count(*) FILTER (WHERE status = 'designated'), count(*) FILTER (WHERE status <> "
                           f"'designated') FROM {T('listings')} WHERE list_id = %s", (list_id,)).fetchone()
        if tuple(got) != (n, ended):
            out.append(f"{list_id}: {got[0]} + {got[1]} listing rows against {n} + {ended} in its list line")
    return out


def outside(conn, schema: str = SCHEMA, today: dt.date = None, shared: bool = False) -> dict:
    from registers.sanctions import load
    T = lambda t: load.table(schema, t, shared)
    today = today or dt.date.today()
    lists = {r[0]: r for r in conn.execute(f"SELECT list_id, version, stated, listings, stated_where FROM {T('lists')}")}
    per, ok = {}, True
    for list_id in capture.LISTS:
        if list_id not in lists:
            per[list_id] = {"ok": False, "detail": "not read: held on its publisher's terms, or never landed"}
            ok = False
            continue
        _, version, stated, n, where = lists[list_id]
        if list_id == "nz-police-tsa":
            cur = conn.execute(f"SELECT count(*) FROM {T('listings')} WHERE list_id = 'nz-police-tsa' AND status = "
                               "'designated' AND key LIKE 'sanctions/nz-police-tsa/1373/%%'").fetchone()[0]
            per[list_id] = {"ok": stated is not None and cur == stated, "stated": stated, "where": where,
                            "current_1373": cur, "listings": n}
        elif list_id == "mfat-russia":
            per[list_id] = {"ok": stated is not None and n == stated, "stated": stated, "where": where, "listings": n}
        else:
            day = None
            try:
                day = dt.date.fromisoformat((version or "")[:10])
            except ValueError:
                pass
            per[list_id] = {"ok": day is not None and (today - day).days <= FRESH_DAYS, "version": version,
                            "listings": n, "detail": "the XML states no total; reconciled item by item at load"}
        ok = ok and per[list_id]["ok"]
    return {"ok": ok, "lists": per}


def views(conn, prefix: str = "pub.") -> list:
    schema, _, stem = prefix.rstrip(".").partition(".")
    out = []
    for v in ("sanctions_listings", "sanctions_lists"):
        cols = [r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s "
                                           "AND table_name = %s", (schema or "pub", (stem + v) if stem else v))]
        bad = [c for c in cols if any(w in c for w in FORBIDDEN)]
        if bad:
            out.append(f"{v} carries {', '.join(bad)}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.sanctions.check")
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.READ_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        if conn.execute("SELECT to_regclass('sanctions.lists')").fetchone()[0] is None:
            out = {"ok": False, "detail": "nothing published: every list is held or none is landed"}
        else:
            out = outside(conn)
            out["problems"] = reading(conn) + views(conn)
            out["ok"] = out["ok"] and not out["problems"]
    print(f"{SCHEMA}: check: " + json.dumps(out, default=str))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
