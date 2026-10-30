"""support/scheduler: the one service that places every job on a graphics
card or on the processor (plan step 2). Extended from the old fleet service
(`ops/fleet` at the frozen tag), not started again.

    registry.py   the job catalogue and the model profiles, from jobs.toml
                  and profiles.toml (carried: ops/fleet/jobs.py)
    policy.py     the nine rules for sharing the cards; pure
                  (carried: ops/fleet/schedule.py, rules 1-5; 6-9 new)
    runs.py       the run ledger: two rows per run, a start with no end is
                  a crash (carried: ops/fleet/runs.py; peak memory added)
    queue.py      the one job queue, in the database: leases, fencing
                  tokens, pieces, the timetable, standing counts
    probe.py      the hardware profile, probed never typed
                  (carried: ops/fleet/probe.py's parsers)
    runner.py     one job or piece as a child process: memory ceiling,
                  deadline, query time limit, peak memory
    cards.py      what each card holds; the model server beside the old
                  one; every swap in the ledger with its reason; the
                  standing server's night window acted on (ruling 129)
    night.py      the night window's clock: whether a moment is inside
                  the hours of jobs.toml [night_window], or Arthur's word
                  (`night open` / `night close`) says so; pure
    worker.py     the worker: one per box (two on node2 for the rehearsal)

The job contract is docs/contracts/job.md; `support.jobspec` is the
declaration and `support.jobrun` the step 1 run record this replaces.
Hard limits 23 (`qv4-` prefix) and 25 (one profile per card, every swap
recorded) bind everything here.
"""
import os

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
SCHEMA = "scheduler"
