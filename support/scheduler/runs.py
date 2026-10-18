"""THE RUN LEDGER — what each job actually did (carried from ops/fleet/runs.py).

Ruling 329 (Arthur, 2026-09-22): *"we want these jobs to have their own
history log so we can trouble shoot them."*

WHY RUNS AND NOT JUST ERRORS. An error log has no denominator. 1,555
`Connection refused` calls sat in a call ledger for weeks because a
call-level error belongs to no run: 1,555 out of how many? Unanswerable.

APPEND-ONLY, TWO ROWS PER RUN. `begin()` writes a `start` row and `finish()`
an `end` row, joined by `run_id`. A run with a start and no end is a CRASH,
visibly: `unfinished()` is the first thing to look at when a job "did
nothing last night". A LEDGER WRITE FAILURE NEVER TAKES A JOB DOWN.

STEP 2 ADDS the peak memory of each run and whether it passed its declared
figure (step 2.6: the figure is then corrected), and the queue row the run
served. The file is the journal on the box; the worker also writes the
same rows to `scheduler.runs` in the database (`queue.py`), which is the
record that moves with the database when a box is lost.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import logging
import os
import pathlib
import uuid

from support.scheduler import LIVE

log = logging.getLogger("scheduler.runs")

LEDGER = pathlib.Path(LIVE) / "scheduler" / "job-runs.jsonl"
ENV = "QV4_JOB_RUNS_LEDGER"

OK, FAILED, REFUSED, PARTIAL, LAPSED = "ok", "failed", "refused", "partial", "lapsed"


def _path(ledger: pathlib.Path | None) -> pathlib.Path:
    """`QV4_JOB_RUNS_LEDGER` overrides, so a test never writes the real history."""
    return pathlib.Path(ledger) if ledger else pathlib.Path(os.environ.get(ENV, LEDGER))


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _append(row: dict, ledger: pathlib.Path | None = None) -> None:
    p = _path(ledger)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            f.write(json.dumps(row, default=str) + "\n")
    except OSError as e:                      # noqa: BLE001
        log.error("job-run ledger unwritable (%s); the run proceeds", e)


def begin(job_type: str, lane: str = "-", *, args: dict | None = None, card: str | None = None,
          requested_model: str | None = None, queue_id: int | None = None, box: str | None = None,
          ledger: pathlib.Path | None = None) -> str:
    """Record that a run STARTED. Returns its run id."""
    run_id = uuid.uuid4().hex[:16]
    _append({"kind": "start", "run_id": run_id, "at": _now(), "job_type": job_type, "lane": lane, "card": card,
             "box": box, "queue_id": queue_id, "requested_model": requested_model, "args": args or {}}, ledger)
    return run_id


def finish(run_id: str, *, outcome: str, n_in: int | None = None, n_out: int | None = None,
           served_model: str | None = None, error: str | None = None, note: str | None = None,
           calls: int | None = None, calls_failed: int | None = None, peak_mb: int | None = None,
           declared_mb: int | None = None, ledger: pathlib.Path | None = None) -> None:
    """Record that a run ENDED. `peak_mb` is the run's measured peak memory
    and `declared_mb` what its job declared; a peak above the declaration is
    flagged so the figure is corrected (step 2.6)."""
    _append({"kind": "end", "run_id": run_id, "at": _now(), "outcome": outcome, "n_in": n_in, "n_out": n_out,
             "served_model": served_model, "error": error, "note": note, "calls": calls, "calls_failed": calls_failed,
             "peak_mb": peak_mb, "declared_mb": declared_mb,
             "over_declared": (peak_mb is not None and declared_mb is not None and peak_mb > declared_mb)}, ledger)


def placement(card: str, action: str, job_type: str | None, why: str, profile: str | None = None,
              ledger: pathlib.Path | None = None) -> None:
    """Record a PLACEMENT decision: the ledgered, reversible swap (hard
    limit 25). The planner's `why` is written verbatim."""
    _append({"kind": "placement", "at": _now(), "card": card, "action": action, "job_type": job_type,
             "profile": profile, "why": why}, ledger)


@dataclasses.dataclass(frozen=True)
class Run:
    run_id: str
    job_type: str
    lane: str
    started: str
    finished: str | None = None
    card: str | None = None
    box: str | None = None
    queue_id: int | None = None
    requested_model: str | None = None
    served_model: str | None = None
    outcome: str | None = None
    n_in: int | None = None
    n_out: int | None = None
    calls: int | None = None
    calls_failed: int | None = None
    peak_mb: int | None = None
    declared_mb: int | None = None
    note: str | None = None
    error: str | None = None
    args: dict = dataclasses.field(default_factory=dict)

    @property
    def unfinished(self) -> bool:
        """A start with no end. The job died, was killed, or the box went down."""
        return self.finished is None

    @property
    def model_is_known(self) -> bool:
        return self.served_model is not None

    @property
    def over_declared(self) -> bool:
        return self.peak_mb is not None and self.declared_mb is not None and self.peak_mb > self.declared_mb


def rows(ledger: pathlib.Path | None = None) -> list[dict]:
    p = _path(ledger)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue                          # a torn line is not a reason to fail
        if isinstance(r, dict):
            out.append(r)
    return out


def runs(ledger: pathlib.Path | None = None) -> list[Run]:
    """Every run, starts joined to ends. Order preserved; a repeated end is the last word."""
    starts: dict[str, dict] = {}
    order: list[str] = []
    ends: dict[str, dict] = {}
    for r in rows(ledger):
        if r.get("kind") == "start" and r.get("run_id"):
            starts[r["run_id"]] = r
            order.append(r["run_id"])
        elif r.get("kind") == "end" and r.get("run_id"):
            ends[r["run_id"]] = r
    out = []
    for rid in order:
        s, e = starts[rid], ends.get(rid, {})
        out.append(Run(run_id=rid, job_type=s.get("job_type", "?"), lane=s.get("lane", "?"), started=s.get("at", ""),
                       finished=e.get("at"), card=s.get("card"), box=s.get("box"), queue_id=s.get("queue_id"),
                       requested_model=s.get("requested_model"), served_model=e.get("served_model"),
                       outcome=e.get("outcome"), n_in=e.get("n_in"), n_out=e.get("n_out"), calls=e.get("calls"),
                       calls_failed=e.get("calls_failed"), peak_mb=e.get("peak_mb"), declared_mb=e.get("declared_mb"),
                       note=e.get("note"), error=e.get("error"), args=s.get("args") or {}))
    return out


def unfinished(ledger: pathlib.Path | None = None) -> list[Run]:
    return [r for r in runs(ledger) if r.unfinished]


def failures(ledger: pathlib.Path | None = None) -> list[Run]:
    return [r for r in runs(ledger) if r.outcome in (FAILED, REFUSED)]


def for_job(job_type: str, ledger: pathlib.Path | None = None) -> list[Run]:
    return [r for r in runs(ledger) if r.job_type == job_type]


def over_declared(ledger: pathlib.Path | None = None) -> list[Run]:
    """Runs whose peak passed the job's declared memory (step 2.6): the
    declaration is wrong and is corrected from these."""
    return [r for r in runs(ledger) if r.over_declared]


def summary(ledger: pathlib.Path | None = None) -> dict[str, dict]:
    """Per job type: runs, outcomes, unfinished, model known, peaks. The
    denominator an error log cannot give you."""
    out: dict[str, dict] = {}
    for r in runs(ledger):
        s = out.setdefault(r.job_type, {"runs": 0, "ok": 0, "failed": 0, "unfinished": 0, "model_unknown": 0,
                                        "over_declared": 0, "peak_mb": None})
        s["runs"] += 1
        if r.unfinished:
            s["unfinished"] += 1
        elif r.outcome == OK:
            s["ok"] += 1
        elif r.outcome in (FAILED, REFUSED):
            s["failed"] += 1
        if not r.unfinished and not r.model_is_known:
            s["model_unknown"] += 1
        if r.over_declared:
            s["over_declared"] += 1
        if r.peak_mb is not None:
            s["peak_mb"] = max(s["peak_mb"] or 0, r.peak_mb)
    return out
