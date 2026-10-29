"""python -m support.mcpsource: the pull, as the job `qv4-mcp-pull` runs it (ruling 96).

    python -m support.mcpsource                         every corpus, live (the job)
    python -m support.mcpsource --database querynz_v4_sample --schema scratch_mcp_1_pull --runs PATH
                                                        a session's proof: the sample database, its own run file
    python -m support.mcpsource --corpus beehive        one corpus
    python -m support.mcpsource --retry-caught          each catch line asked for again
    python -m support.mcpsource --rewalk                every corpus walked again to its cursor (changes in place)
    python -m support.mcpsource --no-files              the records and change feeds only; no file fetched
    python -m support.mcpsource --adopt SCHEMA          the integrator, once: a session's pull carried live
                                                        (resumable: a rerun after a kill finishes the rest)

The files a record points at (ruling 126) are fetched after the records of
every corpus, in what is left of --budget-s. Prints counts only, never a
record (hard limit 11). Exit 1 when the run is red: a corpus failed, a
record or a file was caught, or a field is new to us; for --adopt, a count
of the source and the live record that differs.
"""
import argparse
import sys

from support import mcpsource as M
from support.mcpsource.client import TIMEOUT_S


def log(line: str) -> None:
    print(line, flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="support.mcpsource")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default=M.SCHEMA)
    ap.add_argument("--corpus", action="append", help="only this corpus (repeatable)")
    ap.add_argument("--budget-s", type=float, default=None, help="stop taking pages after this long")
    ap.add_argument("--pause-s", type=float, default=M.PAUSE_S)
    ap.add_argument("--timeout-s", type=float, default=TIMEOUT_S)
    ap.add_argument("--runs", help="the run-record file (default: the live record, for the live database only)")
    ap.add_argument("--retry-caught", action="store_true")
    ap.add_argument("--rewalk", action="store_true", help="walk each corpus again from 0 to its cursor (weekly): "
                    "lands records the MCP changed in place; the cursor does not move")
    ap.add_argument("--adopt", metavar="SAMPLE_SCHEMA")
    ap.add_argument("--store", default="docs", help="the adopt's store schema on --database (a scratch one for a proof)")
    ap.add_argument("--batch", type=int, default=M.ADOPT_BATCH, help="the adopt's documents per batch")
    ap.add_argument("--no-changes", action="store_true", help="the cursor only; skip the change feed")
    ap.add_argument("--no-files", action="store_true", help="skip the download step (the files records point at)")
    a = ap.parse_args(argv)
    from support import db, jobrun
    if a.adopt:
        with db.connect(db.OWNER_KEY, "querynz_v4_sample", autocommit=True) as src, \
                db.connect(db.OWNER_KEY, a.database, autocommit=True) as dst:
            dst.execute("SET synchronous_commit = off")     # a batch lost to a crash is copied again by the rerun
            res = M.adopt(src, dst, a.adopt, a.schema, log=log, batch=a.batch, dst_store=a.store)
        print(f"{M.SOURCE}: adopt {'ok' if res['ok'] else 'RED'}: {res['documents']['asked']} documents "
              f"({res['documents']['copied']} copied, {res['documents']['held']} already held) and "
              + ", ".join(f"{x} {v['source']}" for x, v in res["tables"].items())
              + f" into {a.database}.{a.schema} in {res['seconds']} s")
        return 0 if res["ok"] else 1
    started = jobrun.now()
    client = M.Client(timeout=a.timeout_s)
    with db.connect(db.OWNER_KEY, a.database, autocommit=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        # every landing is its own commit; a crash can lose only the last moment's, in order, so the cursor
        # never runs past a page whose rows were lost, and the bytes are already on disk
        conn.execute("SET synchronous_commit = off")
        t = M.Tables(conn, a.schema)
        t.create()
        if not t.try_lock():
            print(f"{M.SOURCE}: another pull holds {a.schema}; this one asks for nothing")
            return 0
        try:
            if a.retry_caught:
                n = M.retry_caught(conn, client, a.schema, log=log)
                print(f"{M.SOURCE}: {n['asked']} caught records asked again, {n['landed']} landed")
                return 0
            try:
                res = M.pull_all(conn, client, a.schema, only=a.corpus, log=log, budget_s=a.budget_s,
                                 pause_s=a.pause_s, rewalk=a.rewalk, follow=not a.no_changes, files=not a.no_files)
            except (M.McpError, M.ShapeError) as e:     # `corpora` itself did not answer: a red run, recorded
                detail = f"`corpora` failed: {type(e).__name__}: {e}"[:2000]
                print(f"{M.SOURCE}: RED: {detail}")
                if a.runs or a.database == "querynz_v4":
                    jobrun.record(M.JOB, False, detail, started, {}, path=a.runs)
                return 1
        finally:
            t.unlock()
    ok = M.outcome(res)
    detail = M.summary(res) + f"; {client.calls} calls, into {a.database}.{a.schema}"
    print(f"{M.SOURCE}: {'ok' if ok else 'RED'}: {detail}")
    figures = {f"{k}_{f}": v.get(f) for k, v in res.items() for f in ("landed", "held", "caught", "drift", "to")
               if f in v}
    figures.update({f"{k}_files_{f}": v["files"].get(f) for k, v in res.items() if v.get("files")
                    for f in ("landed", "held", "caught", "waiting", "calls")})
    if a.runs or a.database == "querynz_v4":
        jobrun.record(M.JOB, ok, detail[:2000], started, figures, path=a.runs)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
