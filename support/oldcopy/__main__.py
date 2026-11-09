"""python -m support.oldcopy tables|files|status (support/oldcopy/__init__.py has the commands and the limits)."""
import argparse
import os
import sys

from psycopg import sql

from support import db
from support.oldcopy import INVENTORY, LEDGER, OLD_DATABASES, ensure_ledger, inventory, off_peak

DEST_DB = os.environ.get("QV4_OLDCOPY_DB") or db.LIVE


def _old(name):
    from support.oldcopy.tables import prepare_source
    if name not in OLD_DATABASES:
        raise SystemExit(f"support.oldcopy: {name} is not an old database ({', '.join(OLD_DATABASES)})")
    return prepare_source(db.connect(db.OLD_READ_KEY, name, connect_timeout=10))   # the read-only old login only


def _new():
    from support.oldcopy.tables import prepare_dest
    return prepare_dest(db.connect(db.OWNER_KEY, DEST_DB, connect_timeout=10))


def _inv(path):
    if not os.path.exists(path):
        raise SystemExit(f"support.oldcopy: no inventory at {path}")
    return inventory.load(path)


def _any_hour(a) -> bool:
    """--any-hour, or a queued row's args {"any_hour": true} (QV4_ARGS from the worker): a run asked for by day."""
    import json
    try:
        queued = json.loads(os.environ.get("QV4_ARGS") or "{}").get("any_hour") is True
    except (ValueError, AttributeError):
        queued = False
    return bool(a.any_hour) or queued


def _stop(any_hour):
    return (lambda: False) if any_hour else (lambda: not off_peak())


def cmd_tables(a) -> int:
    from support.oldcopy import tables as T
    todo, skipped = inventory.tables(_inv(a.inventory), OLD_DATABASES)
    by_piece = {t.piece: t for t in todo}
    if a.pieces:
        with _new() as dst:
            ensure_ledger(dst)
            dst.commit()
            for t in todo:
                caught = [T.cursor_of(dst, LEDGER, t.piece, i)[1] for i in range(len(t.ranges))]
                if not all(caught) or a.again:
                    print(t.piece)
        return 0
    if not a.piece:
        for name, st, why in skipped:
            print(f"skipped {name} [{st}]: {why}")
        print(f"support.oldcopy: {len(todo)} table(s) to copy, {len(skipped)} skipped")
        return 0
    spec = by_piece.get(a.piece)
    if spec is None:
        why = next((f"[{st}] {w}" for n, st, w in skipped if n == a.piece), "not in the inventory")
        print(f"support.oldcopy: {a.piece} is not copied: {why}")
        return 0 if a.piece in {n for n, _, _ in skipped} else 2
    with _old(spec.database) as src:
        if a.dry_run:
            with db.connect(db.READ_KEY, DEST_DB, connect_timeout=10) as types_in:   # the read login: nothing written
                try:
                    T.dry_run(src, spec, rows=a.rows, types_in=types_in)
                except T.Refused as exc:
                    print(f"support.oldcopy: {spec.piece} would be refused: {exc}")
            return 0
        if not _any_hour(a) and not off_peak():
            print("support.oldcopy: outside the off-peak hours; nothing started")
            return 0
        with _new() as dst:
            ensure_ledger(dst)
            dst.commit()
            try:
                out = T.copy_table(src, dst, spec, rows=a.rows, budget_s=a.budget_s, stop=_stop(_any_hour(a)))
            except T.Refused as exc:
                print(f"support.oldcopy: {spec.piece} refused: {exc}")
                return 0                       # recorded; a refusal is a report, not a failed night
            except T.Mismatch as exc:
                print(f"support.oldcopy: MISMATCH {exc}")
                return 1
    print(f"support.oldcopy: {spec.piece}: {out}")
    return 0


def cmd_files(a) -> int:
    from support.oldcopy import files as F
    todo, skipped = inventory.stores(_inv(a.inventory))
    if a.store:
        todo = [s for s in todo if s.name == a.store]
    for name, st, why in skipped:
        print(f"skipped store {name} [{st}]: {why}")
    if not _any_hour(a) and not off_peak():
        print("support.oldcopy: outside the off-peak hours; nothing started")
        return 0
    stop = _stop(_any_hour(a))
    import time
    t0 = time.monotonic()
    with _new() as conn:
        ensure_ledger(conn)
        conn.commit()
        for s in todo:
            left = a.budget_s - (time.monotonic() - t0)
            if left <= 0 or stop():
                break
            F.copy_store(conn, s, batch=a.batch, budget_s=left, stop=stop)
    return 0


def cmd_status(a) -> int:
    with db.connect(db.OWNER_KEY, DEST_DB, connect_timeout=10) as conn:
        ensure_ledger(conn)
        conn.commit()
        L = sql.Identifier(LEDGER)
        for q in ("SELECT piece, sum(batches), sum(rows), bool_and(caught_up) FROM {}.cursors GROUP BY piece ORDER BY piece",
                  "SELECT piece, count(*) FILTER (WHERE NOT ok) FROM {}.batches GROUP BY piece HAVING count(*) FILTER (WHERE NOT ok) > 0",
                  "SELECT piece, why FROM {}.refusals ORDER BY refusal_id DESC LIMIT 50",
                  "SELECT store, outcome, count(*) FROM {}.files GROUP BY store, outcome ORDER BY store, outcome"):
            for r in conn.execute(sql.SQL(q).format(L)):
                print(" | ".join(str(x) for x in r))
            print("--")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m support.oldcopy")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tables")
    t.add_argument("--inventory", default=INVENTORY)
    t.add_argument("--pieces", action="store_true", help="the tables not yet caught up, one piece key a line")
    t.add_argument("--again", action="store_true", help="with --pieces: list caught-up tables too (new rows since)")
    t.add_argument("--piece", help="database:schema.table")
    t.add_argument("--dry-run", action="store_true", help="rows and md5 at the source; nothing written")
    t.add_argument("--rows", type=int, default=5000)
    t.add_argument("--budget-s", type=float, default=1200)
    t.add_argument("--any-hour", action="store_true", help="a hand run outside the off-peak hours")
    f = sub.add_parser("files")
    f.add_argument("--inventory", default=INVENTORY)
    f.add_argument("--store")
    f.add_argument("--batch", type=int, default=200)
    f.add_argument("--budget-s", type=float, default=3000)
    f.add_argument("--any-hour", action="store_true")
    sub.add_parser("status")
    a = p.parse_args(argv)
    return {"tables": cmd_tables, "files": cmd_files, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
