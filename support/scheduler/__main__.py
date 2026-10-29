"""The scheduler's command line.

  python -m support.scheduler check                 the catalogue and the profiles: problems and warnings
  python -m support.scheduler tables [--database D] create the scheduler's tables (querynz_v4 by default)
  python -m support.scheduler status [--database D] the queue, the workers, the cards, the last swaps and runs
  python -m support.scheduler enqueue JOB [--class C] [--args JSON] [--pieces K ...] [--due ISO]
  python -m support.scheduler cancel ID --why WHY
  python -m support.scheduler probe                 this box's hardware profile
  python -m support.scheduler worker --name N [--box B] [--once] [--hide-program P ...]
  python -m support.scheduler report                the qv4-scheduler-report job
  python -m support.scheduler memory                the memory raises jobs.toml has not folded yet (ruling 115)
  python -m support.scheduler hold-profile          the standing job that keeps a profile on a card
  python -m support.scheduler rehearse ...          the rehearsal jobs (sleep, burn memory; bench: pages at once)
  python -m support.scheduler reread-piece SHA      one document of a re-read (qv4-reread)
  python -m support.scheduler read-pages SHA --profile SLUG   every image page of one document (qv4-read-pages)
  python -m support.scheduler embed-piece SHA       one document of a bulk embedding (qv4-embed)
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
    for name in ("tables", "status", "report", "memory"):
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
    p.add_argument("what", choices=("sleep", "burn", "fail", "model", "served", "page", "bench"))
    p.add_argument("--seconds", type=float, default=5.0)
    p.add_argument("--mb", type=int, default=50)
    p.add_argument("--streams", type=int, default=8, help="bench: requests at once")
    p.add_argument("--prompt-tokens", type=int, default=4000, help="bench: a page's size, in tokens")
    p.add_argument("--answer-tokens", type=int, default=128, help="bench: the answer's budget")
    p.add_argument("--out", help="bench: also write the result here")
    p.add_argument("key", nargs="?")
    p = sub.add_parser("reread-piece")
    p.add_argument("key", help="the document's sha256")
    p.add_argument("--pixels", action="store_true")
    p.add_argument("--database", default="querynz_v4")
    p = sub.add_parser("read-pages")
    p.add_argument("key", help="the document's sha256")
    p.add_argument("--profile", required=True, help="the document profile the readings are stored under")
    p.add_argument("--dpi", type=int, default=300)
    p = sub.add_parser("embed-piece")
    p.add_argument("key", help="the document's sha256")
    p = sub.add_parser("rereads")
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
        from support.scheduler.worker import memory_lines, report
        conn = _conn(a.database)
        print(report(conn, a.schema))
        for line in memory_lines(q.unfolded_raises(conn, a.schema)):
            print(line)
        return 0
    if a.cmd == "memory":
        from support.scheduler.worker import memory_lines
        for line in memory_lines(q.unfolded_raises(_conn(a.database), a.schema)):
            print(line)
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
        if a.what == "model":
            # one real call through the model client to the card the worker gave us;
            # the client refuses an answer from any model but the profile's
            from support import modelclient
            # the profile's own request (QV4_MODEL_REQUEST: thinking off for the reader, on with a budget for
            # review), so the rehearsal proves the call a lane on that profile makes
            extra = {"temperature": 0.0, **json.loads(os.environ.get("QV4_MODEL_REQUEST") or "{}")}
            extra["max_tokens"] = min(int(extra.get("max_tokens") or 300), 300) if "thinking_token_budget" not in extra \
                else int(extra["thinking_token_budget"]) + 300
            out = modelclient.chat(os.environ["QV4_MODEL_URL"], lane="rehearsal", model=os.environ["QV4_MODEL"],
                                   messages=[{"role": "user", "content": "Reply with the single word READY."}],
                                   extra=extra, timeout=300)
            msg = out["choices"][0]["message"]
            content, thought = (msg.get("content") or "").strip(), (msg.get("reasoning_content") or "").strip()
            print(f"rehearsal: {out.get('model')} answered {len(content)} chars of content and {len(thought)} of reasoning "
                  f"on card {os.environ.get('QV4_CARD')} ({os.environ.get('QV4_PROFILE')})")
            return 0 if (content or thought) else 4
        if a.what == "bench":
            # page-sized requests at once through the model client, from what the worker set (ruling 121)
            from support.scheduler import bench
            res = bench.from_env(a.streams, a.prompt_tokens, a.answer_tokens, out_path=a.out)
            print(f"bench: {res['streams']} streams, {res['answered']} answered, {res['wall_seconds']} s; "
                  f"{res['prompt_tokens_a_second']} prompt and {res['completion_tokens_a_second']} completion tokens a second")
            if not res["size_ok"]:
                print(f"bench: the server counted {res['prompt_tokens_each']} prompt tokens for {a.prompt_tokens} asked")
            return 0 if res["answered"] == res["streams"] and res["size_ok"] else 4
        if a.what == "served":
            # the profile is loaded and advertises the model the catalogue names (read back, never assumed)
            from support.scheduler import probe
            got = probe.ask_server(int(os.environ["QV4_MODEL_PORT"]))
            print(f"rehearsal: card {os.environ.get('QV4_CARD')} serves {got['served']!r}, {got['total']} slot(s)")
            return 0 if got["served"] == os.environ["QV4_MODEL"] else 4
        if a.what == "page":
            # one scanned page through the page-reader profile on our card: counts only, never the text
            import tempfile
            from support.docread import pagereader
            from support.docstore import landing
            sha = json.loads(os.environ.get("QV4_ARGS") or "{}").get("sha256") or a.key
            data = landing.read_bytes(sha)
            with tempfile.TemporaryDirectory() as td:
                png = pagereader.render(data, 1, td, 300)
                text = pagereader.read_page(png, url=os.environ["QV4_MODEL_URL"], model=os.environ["QV4_MODEL"])
            print(f"rehearsal: page 1 of {sha[:12]} read to {len(text)} characters by {os.environ['QV4_MODEL']} on card "
                  f"{os.environ.get('QV4_CARD')}")
            return 0 if text.strip() else 4
        return 3
    if a.cmd == "reread-piece":
        from support.scheduler import reread
        line = reread.piece(a.key, conn=_conn(a.database), url=os.environ["QV4_MODEL_URL"], model=os.environ["QV4_MODEL"],
                            pixels=a.pixels, run_id=os.environ.get("QV4_RUN_ID", ""))
        print(f"reread: {line['document'][:12]} {line['party'] or '?'} {line['year'] or '?'}: published {line['published']}, "
              f"new {line['new']}, {'EQUAL' if line['equal'] else 'DIFFERENT'} ({line['model']}, {line['read_from']})")
        return 0
    if a.cmd == "read-pages":
        from support.scheduler import reread
        line = reread.read_pages(a.key, profile=a.profile, url=os.environ["QV4_MODEL_URL"], model=os.environ["QV4_MODEL"],
                                 dpi=a.dpi, run_id=os.environ.get("QV4_RUN_ID", ""))
        print(f"read-pages: {line['document'][:12]} {line['profile']}: {line['pages']} page(s), {line['images']} image(s), "
              f"{line['read_now']} read now, {line['replayed']} replayed, unread {line['unread']} ({line['model']} at {os.environ.get('QV4_MODEL_PORT')})")
        return 1 if line["unread"] else 0
    if a.cmd == "embed-piece":
        from support.scheduler import embed
        line = embed.piece(a.key, url=os.environ["QV4_MODEL_URL"].replace("/chat/completions", "/embeddings"),
                           model=os.environ["QV4_MODEL"], run_id=os.environ.get("QV4_RUN_ID", ""))
        print(f"embed: {line['document'][:12]}: {line['embedded']} page(s) embedded, {line['replayed']} already stored, "
              f"{line['thin']} with no text layer ({line['model']}, {line['dims']} dims)")
        return 0
    if a.cmd == "rereads":
        from support.scheduler import reread
        print(json.dumps(reread.summary(), indent=1))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
