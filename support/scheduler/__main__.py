"""The scheduler's command line.

  python -m support.scheduler check                 the catalogue and the profiles: problems and warnings
  python -m support.scheduler tables [--database D] create the scheduler's tables (querynz_v4 by default)
  python -m support.scheduler status [--database D] the queue, the workers, the cards, the last swaps and runs
  python -m support.scheduler enqueue JOB [--class C] [--args JSON] [--pieces K ...] [--due ISO]
  python -m support.scheduler cancel ID --why WHY
  python -m support.scheduler probe                 this box's hardware profile
  python -m support.scheduler worker --name N [--box B] [--once] [--hide-program P ...]
  python -m support.scheduler report                the qv4-scheduler-report job
  python -m support.scheduler hold-profile          the standing job that keeps a profile on a card
  python -m support.scheduler rehearse ...          the rehearsal jobs (sleep, burn memory)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time

from support.scheduler import SCHEMA
from support.scheduler import queue as q
from support.scheduler import registry as reg


def _conn(database: str):
    import support.db as db
    conn = db.connect(db.OWNER_KEY, database, autocommit=True)
    conn.execute("SET statement_timeout = 30000")
    return conn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m support.scheduler", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    for name in ("tables", "status", "report"):
        p = sub.add_parser(name)
        p.add_argument("--database", default="querynz_v4")
        p.add_argument("--schema", default=SCHEMA)
    p = sub.add_parser("enqueue")
    p.add_argument("job")
    p.add_argument("--database", default="querynz_v4")
    p.add_argument("--schema", default=SCHEMA)
    p.add_argument("--class", dest="cls")
    p.add_argument("--args", default="{}")
    p.add_argument("--pieces", nargs="*", default=None)
    p.add_argument("--due")
    p.add_argument("--by", default=os.environ.get("USER", "cli"))
    p = sub.add_parser("cancel")
    p.add_argument("id", type=int)
    p.add_argument("--why", required=True)
    p.add_argument("--database", default="querynz_v4")
    p.add_argument("--schema", default=SCHEMA)
    sub.add_parser("probe")
    p = sub.add_parser("worker")
    p.add_argument("--name", required=True)
    p.add_argument("--box")
    p.add_argument("--database", default="querynz_v4")
    p.add_argument("--schema", default=SCHEMA)
    p.add_argument("--once", action="store_true", help="one tick, then exit (a test)")
    p.add_argument("--tick", type=float, default=5.0)
    p.add_argument("--hide-program", action="append", default=[], help="rehearsal: pretend this box lacks a program")
    p.add_argument("--no-cards", action="store_true", help="do not manage this box's cards")
    sub.add_parser("hold-profile")
    p = sub.add_parser("rehearse")
    p.add_argument("what", choices=("sleep", "burn", "fail"))
    p.add_argument("--seconds", type=float, default=5.0)
    p.add_argument("--mb", type=int, default=50)
    p.add_argument("key", nargs="?")
    a = ap.parse_args(argv)

    if a.cmd == "check":
        probs, warns = reg.problems(), reg.warnings()
        for x in probs:
            print("PROBLEM " + x)
        for x in warns:
            print("warning " + x)
        print(f"scheduler: {len(reg.load())} job types, {len(reg.profiles())} profiles, "
              f"{'green' if not probs else str(len(probs)) + ' problem(s)'}")
        return 1 if probs else 0
    if a.cmd == "probe":
        from support.scheduler import probe
        print(json.dumps(probe.profile(), indent=1))
        return 0
    if a.cmd == "tables":
        conn = _conn(a.database)
        q.tables(conn, a.schema)
        n = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = %s", (a.schema,)).fetchone()[0]
        print(f"scheduler: {n} tables in {a.database}.{a.schema}")
        return 0
    if a.cmd == "status":
        st = q.status(_conn(a.database), a.schema)
        print(json.dumps(st, default=str, indent=1))
        return 0
    if a.cmd == "report":
        from support.scheduler.worker import report
        print(report(_conn(a.database), a.schema))
        return 0
    if a.cmd == "enqueue":
        registry = reg.load()
        if a.job not in registry:
            print(f"no job type {a.job!r} in the catalogue", file=sys.stderr)
            return 2
        due = dt.datetime.fromisoformat(a.due) if a.due else None
        qid = q.enqueue(_conn(a.database), a.schema, a.job, args=json.loads(a.args), cls=a.cls, due_at=due, pieces=a.pieces,
                        created_by=a.by, registry=registry)
        print(f"queued {a.job} as row {qid}" + (f" with {len(a.pieces)} pieces" if a.pieces else ""))
        return 0
    if a.cmd == "cancel":
        ok = q.cancel(_conn(a.database), a.schema, a.id, a.why)
        print("cancelled" if ok else "not cancelled: not queued or leased")
        return 0 if ok else 1
    if a.cmd == "worker":
        from support.scheduler.worker import Worker
        mgr = None
        if not a.no_cards:
            from support.scheduler.cards import Manager
            mgr = Manager()
        w = Worker(a.name, a.box, database=a.database, schema=a.schema, tick_s=a.tick, hide_programs=a.hide_program,
                   cards_manager=mgr)
        if a.once:
            w.start()
            w.tick()
            return 0
        w.run_forever()
        return 0
    if a.cmd == "hold-profile":
        # the standing job that keeps a profile resident: it does nothing but
        # hold its lease; the card manager keeps the profile loaded for it
        import signal
        stop = []
        signal.signal(signal.SIGTERM, lambda *_: stop.append(1))
        while not stop:
            time.sleep(1)
        return 0
    if a.cmd == "rehearse":
        if a.what == "sleep":
            time.sleep(a.seconds)
            return 0
        if a.what == "burn":
            block = bytearray(a.mb * 1024 * 1024)
            block[::4096] = b"1" * len(block[::4096])
            time.sleep(a.seconds)
            return 0
        return 3
    return 2


if __name__ == "__main__":
    sys.exit(main())
