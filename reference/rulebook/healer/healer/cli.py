"""healer CLI — the executing lanes (moved from reviewer.cli in B4,
2026-08-22; the subcommands, flags and defaults are unchanged so the
units only change the module name).

  healer mint-lane  [--judge-limit N] [--concurrency N]   post-mint healing cycle
  healer crawler    [--judge-limit N] [--concurrency N]   common-sense graph auditor (one cycle)
  healer crawler-merge [--cap N]                          R3 merge actuator (refuter-gated since B4b; hand tranches)
  healer reread     [--cap N]                             re-read taxonomised debris against its source document
  healer dense-validation --url U [--model M] [--n N]     R3a: re-judge a verdict sample at a second endpoint
  healer repair                                           truncated-name repair lane
  healer heal [--apply]                                   claim-tier heals (R1-R5, Shane Jones scope)
  healer hygiene [--apply]                                entity-name whitespace normalize (T7.10 straggler heal)
  healer resubject [--apply] [--all-surnames]             first-queue re-subjecting rules R7/R8 (the subcommand existed; this line did not, queue 8 2026-09-18)

Every lane mutates the graph only through claim_graph's gates
(remediate / merge), reversibly and ledgered; the boundary test pins it.
"""
from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    ap = argparse.ArgumentParser(prog="healer", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("mint-lane",
                       help="post-mint healing cycle: screen fresh mints, "
                            "LLM-judge, execute calibrated verdicts (no "
                            "human gate — Arthur 2026-08-14)")
    p.add_argument("--judge-limit", type=int, default=200)
    p.add_argument("--concurrency", type=int, default=6)
    p = sub.add_parser("crawler",
                       help="common-sense graph auditor: deterministic heals + "
                            "LLM type-sanity findings (Arthur 2026-08-14)")
    p.add_argument("--judge-limit", type=int, default=100)
    p.add_argument("--concurrency", type=int, default=6)
    p = sub.add_parser("dense-validation",
                       help="R3a: re-judge a seeded verdict sample with a second model at an explicit endpoint")
    p.add_argument("--url", required=True)
    p.add_argument("--model", default=None)
    p.add_argument("--n", type=int, default=300)
    p.add_argument("--seed", type=int, default=20260822)
    p.add_argument("--resume", default=None,
                   help="a r3a-partial-*.json from a killed run: keep its verdicts, judge only the rest")
    p = sub.add_parser("crawler-merge",
                       help="R3 merge actuator: drain observed mistyped-duplicate "
                            "verdicts as verdict-backed reversible merges — "
                            "hand-driven tranches only (ruling 31, 2026-08-22)")
    p.add_argument("--cap", type=int, default=500)
    sub.add_parser("repair", help="truncated-name repair lane (evidence-first, "
                                  "mechanical; merge-preferred; automatic)")
    p = sub.add_parser("reread", help="re-read taxonomised extraction debris against "
                                      "the SOURCE DOCUMENT it came from (Arthur 2026-09-21)")
    p.add_argument("--cap", type=int, default=None,
                   help="entities re-read this run (default: the lane's own cap)")
    p = sub.add_parser("heal", help="claim-tier heals (dry run unless --apply)")
    p.add_argument("--apply", action="store_true")
    p = sub.add_parser("resubject", help="first-queue re-subjecting rules R7/R8 "
                                         "(dry run unless --apply)")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--all-surnames", action="store_true",
                   help="measure R8 over every single-token surname (dry run only)")
    p = sub.add_parser("hygiene", help="entity-name whitespace normalize "
                                       "(T7.10 straggler heal; dry run unless --apply)")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--limit", type=int, default=5000)
    args = ap.parse_args()
    # the lanes report through logging.INFO (counts per heal, judge, execute)
    # — the journal is the record; the first cycle under this CLI ran silent
    # for want of this line (2026-08-22 09:41)
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.cmd == "heal":
        from . import heal
        heal.run(apply=args.apply)
        return
    if args.cmd == "resubject":
        from claim_graph import store
        from . import resubject
        with store.connect() as conn:
            counts = resubject.run(conn, apply=args.apply, all_surnames=args.all_surnames)
            if args.apply:
                conn.commit()
        print(json.dumps({"apply": args.apply, **counts}))
        return
    if args.cmd == "hygiene":
        from claim_graph import store
        from . import hygiene
        with store.connect() as conn:
            stats = hygiene.heal_whitespace_names(conn, apply=args.apply, limit=args.limit)
        print(json.dumps({"apply": args.apply, **stats}))
        return

    from reviewer.graph_handle import ReconnectingGraph   # sanctioned crossing
    g = ReconnectingGraph()   # batch runs survive a DB restart (found live)
    try:
        if args.cmd == "mint-lane":
            from . import mint_lane
            mint_lane.run(g, judge_limit=args.judge_limit,
                          concurrency=args.concurrency)
        elif args.cmd == "crawler":
            from . import crawler
            crawler.run(g, judge_limit=args.judge_limit,
                        concurrency=args.concurrency)
        elif args.cmd == "dense-validation":
            from . import dense_validation
            doc, path = dense_validation.run(g, args.url, args.model, n=args.n, seed=args.seed,
                                             resume=args.resume)
            print(json.dumps({k: doc[k] for k in ("n", "errors", "agreement", "dissent_rate", "per_pattern")}
                             | {"artifact": path}, indent=1))
        elif args.cmd == "crawler-merge":
            from . import crawler, mint_lane
            mint_lane.ensure_schema(g)
            print(json.dumps(crawler.merge_duplicates(g, cap=args.cap)))
        elif args.cmd == "repair":
            from . import mint_lane, repair
            mint_lane.ensure_schema(g)
            print(json.dumps(repair.run(g)))
        elif args.cmd == "reread":
            from . import mint_lane, reread
            mint_lane.ensure_schema(g)
            print(json.dumps(reread.run_reread(
                g, **({"cap": args.cap} if args.cap else {}))))
    finally:
        g.close()


if __name__ == "__main__":
    sys.exit(main())
