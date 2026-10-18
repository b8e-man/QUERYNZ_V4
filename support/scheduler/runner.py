"""ONE JOB, OR ONE PIECE, AS A CHILD PROCESS (the old run wrapper
ops/fleet/runjob.py, moved inside the worker; plan steps 2.4 to 2.8).

What the machinery gives every run:

- A HARD CEILING ON MEMORY (2.6). The child's tree is measured every half
  second by PSS from `/proc/<pid>/smaps_rollup` (size a fleet on Pss, not
  RSS: twelve shards once showed 33 GB summed in `ps` against 8 GB true).
  Past the ceiling the job is stopped — TERM, then KILL — and the box is
  not. The run record keeps the peak, and a peak above the declared figure
  is flagged so the figure is corrected. The ceiling is the DECLARED memory
  times a margin, never "what the box has free": a cap above what the box
  can spare is a comment, not a control.
- A DEADLINE (2.4). TERM at the deadline, KILL twenty seconds later (the
  model server hangs about 45 s after a stop signal; the old estate learned
  to stop with a 20 s limit and then kill).
- A QUERY TIME LIMIT UNDER THE DEADLINE, in the child's `PGOPTIONS`, so a
  job killed at its deadline does not leave its query running.
- THE LEASE. A `tick` callback runs every poll; it renews the lease and
  returns False when the lease is lost, and the child is then stopped: a
  zombie must not keep writing after another worker has taken the job.
- THE EXIT CODE IS THE CHILD'S, unchanged; its output is not captured
  (it flows to the worker's journal); a command that never starts still
  leaves a record.
"""
from __future__ import annotations

import dataclasses
import os
import signal
import subprocess
import time

POLL_S = 0.5
KILL_GRACE_S = 20.0
CEILING_MARGIN = 1.25         # the ceiling is the declared memory plus a quarter


@dataclasses.dataclass
class Result:
    code: int | None            # the child's exit code; negative = signal; None = never started
    seconds: float
    peak_mb: int
    outcome: str                # ok | failed | refused
    error: str | None = None
    stopped_for: str | None = None   # memory | deadline | lease | stop | None


def pss_mb(pid: int) -> int:
    """Proportional set size of one process in MB; 0 when it is gone."""
    try:
        with open(f"/proc/{pid}/smaps_rollup", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Pss:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        return 0
    return 0


def descendants(pid: int) -> list[int]:
    """The process tree under `pid`, from /proc/<pid>/task/*/children."""
    out, todo = [], [pid]
    while todo:
        p = todo.pop()
        try:
            tasks = os.listdir(f"/proc/{p}/task")
        except OSError:
            continue
        for t in tasks:
            try:
                with open(f"/proc/{p}/task/{t}/children", encoding="utf-8") as f:
                    kids = [int(x) for x in f.read().split()]
            except (OSError, ValueError):
                kids = []
            out.extend(kids)
            todo.extend(kids)
    return out


def tree_mb(pid: int) -> int:
    return pss_mb(pid) + sum(pss_mb(k) for k in descendants(pid))


def _stop(child: subprocess.Popen, grace: float = KILL_GRACE_S) -> None:
    """TERM, wait up to `grace`, then KILL. The child's own children get the
    same, so a job's helper processes do not outlive it."""
    kids = descendants(child.pid)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            child.send_signal(sig)
        except Exception:  # noqa: BLE001 — already gone
            pass
        for k in kids:
            try:
                os.kill(k, sig)
            except OSError:
                pass
        try:
            child.wait(timeout=grace)
            return
        except subprocess.TimeoutExpired:
            continue


def run(argv: list[str], *, deadline_s: float, ceiling_mb: int | None, query_timeout_s: int | None = None,
        env: dict | None = None, cwd: str | None = None, tick=None, popen=None, poll_s: float = POLL_S,
        grace_s: float = KILL_GRACE_S, log=None) -> Result:
    """Run `argv` under the limits. `tick()` is called every poll and may
    return False to stop the child (the lease was lost, the worker is
    stopping)."""
    full_env = dict(os.environ)
    full_env.update(env or {})
    if query_timeout_s:
        # libpq honours PGOPTIONS unless the connection string carries its own
        # options= (trap: an options string in the URL discards the environment)
        full_env["PGOPTIONS"] = f"-c statement_timeout={int(query_timeout_s) * 1000}"
    t0 = time.monotonic()
    try:
        child = (popen or subprocess.Popen)(argv, env=full_env, cwd=cwd)
    except (OSError, ValueError) as e:
        return Result(None, 0.0, 0, "failed", f"{type(e).__name__}: {str(e)[:300]}", None)

    peak, stopped_for = 0, None
    while True:
        try:
            code = child.wait(timeout=poll_s)
            break
        except subprocess.TimeoutExpired:
            pass
        now_mb = tree_mb(child.pid)
        peak = max(peak, now_mb)
        elapsed = time.monotonic() - t0
        if ceiling_mb is not None and now_mb > ceiling_mb:
            stopped_for = "memory"
        elif elapsed >= deadline_s:
            stopped_for = "deadline"
        elif tick is not None and tick() is False:
            stopped_for = "lease"
        if stopped_for:
            if log:
                log(f"stopping the child: {stopped_for} ({now_mb} MB, {elapsed:.0f}s)")
            _stop(child, grace_s)
            code = child.returncode
            break

    seconds = round(time.monotonic() - t0, 1)
    if stopped_for == "memory":
        return Result(code, seconds, peak, "failed", f"stopped at {peak} MB: over its ceiling of {ceiling_mb} MB", "memory")
    if stopped_for == "deadline":
        return Result(code, seconds, peak, "failed", f"stopped at its deadline of {deadline_s:.0f}s", "deadline")
    if stopped_for == "lease":
        return Result(code, seconds, peak, "failed", "stopped: the lease was lost or the worker is stopping", "lease")
    if code == 0:
        return Result(0, seconds, peak, "ok")
    if code is not None and code < 0:
        return Result(code, seconds, peak, "failed", f"killed by signal {-code}")
    return Result(code, seconds, peak, "failed", f"exit {code}")


def ceiling_for(declared_gb: float, margin: float = CEILING_MARGIN) -> int:
    """The memory ceiling in MB for a job declaring `declared_gb` per worker."""
    return int(declared_gb * 1024 * margin)
