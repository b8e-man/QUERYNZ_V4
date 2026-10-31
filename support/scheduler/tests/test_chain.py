"""The chain runs itself (31 October, Arthur 08:40: "a pipeline that is
continuously gathering, ingesting, OCRing and reading names"), on the fake
worker: an in-memory queue stands in for the scheduler's tables, the runner
is a fake that returns a result at once, no model, no card, no second
passes.

What is proven here: a pieced row claimed with no pieces builds them from
its type's `pieces_command`; a command that prints nothing finishes the row
"nothing waiting"; a finished row queues its `then` jobs with one in flight
and says so in its detail; a pieced row's pieces run `concurrency` at a
time, cut to the profile's streams less the other rows' pieces in flight;
a draining card finishes the pieces in flight and takes no more; two
failures in a row give the row back; the catalogue checks refuse the shapes
that would fail at the claim."""
from __future__ import annotations

import dataclasses
import datetime as dt
import threading
import uuid

import pytest

from support.scheduler import __main__ as cli
from support.scheduler import queue as rq
from support.scheduler import registry as reg
from support.scheduler import runner
from support.scheduler import worker as wk
from support.scheduler.tests.test_night_window import PROFILES

JOBS = """
version = 1
[queueing]
slice_seconds = 3600
drain_not_kill = true
min_queue_to_evict = 8
max_wait_seconds = 1800
piece_seconds = 300
due_horizon_seconds = 7200
memory_reserve_gb = 24
lease_seconds = 90
policy = "priority-ordered-round-robin"

[jobs.qv4-load]
needs = "processor"
memory_gb = 1.0
deadline_s = 900
query_timeout_s = 300
class = "due"
priority = 1
command = ["true"]
at_utc = "15:00"
then = ["qv4-read", "qv4-scan"]

[jobs.qv4-read]
needs = "model-profile"
profile = "text-reader"
memory_gb = 0.5
deadline_s = 900
query_timeout_s = 300
priority = 2
command = ["python", "-m", "nothing", "--piece"]
pieces_command = ["python", "-c", "print('a'); print('b'); print(''); print('c'); print('b')"]
pieces = true
can_share = true
concurrency = 4

[jobs.qv4-scan]
needs = "processor"
memory_gb = 0.3
deadline_s = 600
query_timeout_s = 300
priority = 3
command = ["true"]

[jobs.qv4-empty]
needs = "model-profile"
profile = "text-reader"
memory_gb = 0.5
deadline_s = 900
query_timeout_s = 300
priority = 4
command = ["true"]
pieces_command = ["python", "-c", "pass"]
pieces = true
can_share = true
concurrency = 4

[jobs.qv4-listed]
needs = "model-profile"
profile = "review"
memory_gb = 0.5
deadline_s = 900
query_timeout_s = 300
priority = 5
command = ["true"]
pieces = true
can_share = true
concurrency = 3
threads = 2

[jobs.qv4-broken]
needs = "model-profile"
profile = "text-reader"
memory_gb = 0.5
deadline_s = 900
query_timeout_s = 300
priority = 6
command = ["true"]
pieces_command = ["python", "-c", "import sys; sys.exit(3)"]
pieces = true
can_share = true
"""

UTC = dt.timezone.utc


# ── the in-memory queue ──────────────────────────────────────────────────────

class FakeQueue:
    """The queue module's functions the worker calls, on dicts. Every state
    change the real tables would make is made here, so a test reads the row
    and its pieces as `status` would."""

    def __init__(self):
        self.rows: dict[int, dict] = {}
        self.pieces: dict[int, list[dict]] = {}
        self.runs: dict[str, dict] = {}
        self.workers: dict[str, dict] = {}
        self.timetable: dict = {}
        self.raises: list[dict] = []
        self.lock = threading.Lock()
        self.next_id = 1

    utcnow = staticmethod(rq.utcnow)

    # tables, workers, the clock: nothing to do on the fake
    def tables(self, conn, schema):
        pass

    def register(self, conn, schema, name, box, profile, now=None):
        self.workers[name] = {"name": name, "box": box, "state": "up"}

    def heartbeat(self, conn, schema, name, now=None, profile=None):
        pass

    def reap(self, conn, schema, now=None):
        return []

    def silent_workers(self, conn, schema, **kw):
        return []

    def enqueue_due(self, conn, schema, registry=None, **kw):
        return []

    def enqueue_standing(self, conn, schema, registry=None, **kw):
        return []

    def working_figures(self, conn, schema):
        return {}

    def raise_for_row(self, conn, schema, qid):
        return None

    def stop_worker(self, conn, schema, name, now=None):
        return 0

    def cards(self, conn, schema, box=None):
        return []

    # the queue proper
    def enqueue(self, conn, schema, job, *, args=None, cls=None, priority=None, due_at=None, not_before=None, pieces=None,
                created_by="", standing=False, timetable_slot=None, registry=None, now=None, then_of=None):
        jt = registry.get(job) if registry else None
        pieces = list(pieces or [])
        source = rq.pieces_source_for(jt, pieces)
        with self.lock:
            qid = self.next_id
            self.next_id += 1
            self.rows[qid] = {"id": qid, "job": job, "args": args or {}, "cls": cls or (jt.cls if jt else "whenever"),
                              "priority": priority if priority is not None else (jt.priority if jt else 99), "state": "queued",
                              "due_at": due_at, "not_before": not_before, "created_by": created_by, "pieces_total": len(pieces),
                              "pieces_done": 0, "standing": standing, "timetable_slot": timetable_slot, "pieces_source": source,
                              "then_of": then_of, "in_flight": None, "detail": "", "outcome": None, "token": None, "owner": None,
                              "attempts": 0}
            self.pieces[qid] = [{"piece": i, "key": str(k), "state": "todo", "attempts": 0, "worker": None, "seconds": None,
                                 "detail": ""} for i, k in enumerate(pieces, 1)]
        return qid

    def claim(self, conn, schema, worker, eligible, *, lease_s, now=None, exclude_ids=None):
        with self.lock:
            cands = [r for r in self.rows.values() if r["state"] == "queued" and r["job"] in eligible]
            if not cands:
                return None
            r = min(cands, key=lambda r: ({"waiting": 0, "due": 1}.get(r["cls"], 2), r["priority"], r["id"]))
            r["state"], r["token"], r["owner"] = "leased", uuid.uuid4(), worker
            r["attempts"] += 1
            return {**{k: r[k] for k in ("id", "job", "args", "cls", "priority", "due_at", "attempts", "pieces_total", "pieces_done",
                                          "standing", "timetable_slot", "pieces_source")}, "token": r["token"]}

    def _own(self, qid, token):
        r = self.rows.get(qid)
        return r is not None and r["state"] == "leased" and r["token"] == token

    def renew(self, conn, schema, qid, token, *, lease_s, now=None):
        return self._own(qid, token)

    def complete(self, conn, schema, qid, token, *, outcome, detail="", now=None):
        with self.lock:
            if not self._own(qid, token):
                return False
            r = self.rows[qid]
            r["state"] = "done" if outcome == "ok" else "failed"
            r["outcome"] = outcome
            r["detail"] = " | ".join(x for x in (r["detail"], detail) if x)
            r["token"] = None
            return True

    def requeue(self, conn, schema, qid, token, *, detail="", not_before=None, now=None):
        with self.lock:
            if not self._own(qid, token):
                return False
            r = self.rows[qid]
            r.update(state="queued", token=None, owner=None, not_before=not_before,
                     detail=" | ".join(x for x in (r["detail"], detail) if x))
            for p in self.pieces[qid]:
                if p["state"] == "running":
                    p["state"] = "todo"
            return True

    def next_piece(self, conn, schema, qid, token, worker, now=None):
        with self.lock:
            if not self._own(qid, token):
                return None
            for p in self.pieces[qid]:
                if p["state"] == "todo":
                    p.update(state="running", worker=worker)
                    p["attempts"] += 1
                    return {"piece": p["piece"], "key": p["key"], "attempts": p["attempts"]}
            return None

    def finish_piece(self, conn, schema, qid, token, piece, *, ok, seconds, detail="", now=None):
        with self.lock:
            if not self._own(qid, token):
                return False
            p = self.pieces[qid][piece - 1]
            p["seconds"], p["detail"] = seconds, detail
            if ok:
                p["state"] = "done"
                self.rows[qid]["pieces_done"] += 1
            else:
                p["state"] = "failed" if p["attempts"] >= 3 else "todo"
            return True

    def pieces_left(self, conn, schema, qid):
        out = {"todo": 0, "running": 0, "done": 0, "failed": 0}
        for p in self.pieces[qid]:
            out[p["state"]] += 1
        return out

    def add_pieces(self, conn, schema, qid, token, keys, now=None):
        with self.lock:
            if not self._own(qid, token):
                return -1
            if self.rows[qid]["pieces_total"]:
                return 0
            self.pieces[qid] = [{"piece": i, "key": str(k), "state": "todo", "attempts": 0, "worker": None, "seconds": None,
                                 "detail": ""} for i, k in enumerate(keys, 1)]
            self.rows[qid].update(pieces_total=len(keys), pieces_source="command")
            return len(keys)

    def set_in_flight(self, conn, schema, qid, n):
        self.rows[qid]["in_flight"] = n

    def then_rows(self, conn, schema, qid, jt, *, registry=None, now=None, created_by=""):
        if not jt.then:
            return []
        lines = []
        for name in jt.then:
            if name not in registry:
                lines.append(f"then: {name} is not in the catalogue; not queued")
                continue
            have = [r for r in self.rows.values() if r["job"] == name and r["state"] in ("queued", "leased")]
            if have:
                h = min(have, key=lambda r: r["id"])
                lines.append(f"then: {name} already {'queued' if h['state'] == 'queued' else 'running'} as row {h['id']}")
                continue
            try:
                new = self.enqueue(conn, schema, name, cls="whenever", created_by=created_by or f"then of row {qid}",
                                   registry=registry, then_of=qid)
            except ValueError as exc:
                lines.append(f"then: {name} not queued: {exc}")
                continue
            lines.append(f"then: queued row {new}" if len(jt.then) == 1 else f"then: {name} queued as row {new}")
        if lines:
            r = self.rows[qid]
            r["detail"] = " | ".join(x for x in (r["detail"], " | ".join(lines)) if x)
        return lines

    # runs and raises
    def run_begin(self, conn, schema, run_id, **fields):
        self.runs[run_id] = {"run_id": run_id, **fields}

    def run_end(self, conn, schema, run_id, **fields):
        self.runs[run_id].update(fields)

    def raise_memory(self, conn, schema, **kw):
        rz = {"id": len(self.raises) + 1, "raised_gb": 1.0, "applied": True, "requeued_id": kw["qid"] if kw.get("pieced") else None,
              "origin_queue_id": kw["qid"], "note": "row given back with its pieces' progress, to run at 1 GB"}
        self.raises.append(rz)
        return rz

    # what status reads
    def status(self, conn, schema, limit=20):
        recent = []
        for r in sorted(self.rows.values(), key=lambda r: -r["id"])[:limit]:
            recent.append({"id": r["id"], "job": r["job"], "state": r["state"], "lease_owner": r["owner"], "pieces_done": r["pieces_done"],
                           "pieces_total": r["pieces_total"], "outcome": r["outcome"], "created_at": None, "finished_at": None,
                           "pieces_source": r["pieces_source"], "in_flight": r["in_flight"], "then_of": r["then_of"],
                           "pieces_running": sum(1 for p in self.pieces[r["id"]] if p["state"] == "running"),
                           "then_rows": [x["id"] for x in self.rows.values() if x["then_of"] == r["id"]]})
        return {"recent": recent}


class FakeRunner:
    """`runner.run` without a child: the result is decided by the piece key
    (`fail-…` fails, `mem-…` is stopped at its ceiling, anything else is ok)
    and every call waits at a barrier when one is set, so N pieces in flight
    at once is proven by the barrier opening and serial pieces by it not."""

    def __init__(self):
        self.calls: list[dict] = []
        self.barrier: threading.Barrier | None = None
        self.gate: threading.Event | None = None
        self.sem: threading.Semaphore | None = None      # one release lets one piece through
        self.honour_tick = True                          # False: a child that never notices the stop
        self.lock = threading.Lock()
        self.in_flight = 0
        self.peak = 0

    def __call__(self, argv, *, deadline_s, ceiling_mb, query_timeout_s=None, env=None, cwd=None, tick=None, log=None, nice=0):
        key = argv[-1]
        with self.lock:
            self.in_flight += 1
            self.peak = max(self.peak, self.in_flight)
            self.calls.append({"key": key, "env": dict(env or {}), "argv": list(argv)})
        try:
            if self.barrier is not None:
                try:
                    self.barrier.wait(timeout=5)
                except threading.BrokenBarrierError:
                    return runner.Result(1, 0.1, 10, "failed", "the barrier did not open: pieces ran one after another")
            if self.gate is not None:
                self.gate.wait(timeout=5)
            if self.sem is not None:
                self.sem.acquire(timeout=5)
            if self.honour_tick and tick is not None and tick() is False:
                return runner.Result(-15, 0.1, 10, "failed", "stopped: the lease was lost or the worker is stopping", "lease")
            if key.startswith("fail"):
                return runner.Result(3, 0.1, 10, "failed", "exit 3")
            if key.startswith("mem"):
                return runner.Result(-9, 0.1, 999, "failed", "stopped at 999 MB: over its ceiling", "memory")
            return runner.Result(0, 0.1, 10, "ok")
        finally:
            with self.lock:
                self.in_flight -= 1


def table(*cards, profile="flash-next", draining=False):
    return [{"card": c, "reserved": False, "profile": profile, "port": 8060, "draining": draining, "slots": 16} for c in cards]


@pytest.fixture
def fake(tmp_path, monkeypatch):
    fq, fr = FakeQueue(), FakeRunner()
    monkeypatch.setattr(wk, "q", fq)
    monkeypatch.setattr(wk.runner, "run", fr)
    (tmp_path / "jobs.toml").write_text(JOBS)
    (tmp_path / "profiles.toml").write_text(PROFILES.replace('[profiles.text-reader]\non = "flash-next"\nmodel = "qwen4exp"\nslots = 16',
                                                             '[profiles.text-reader]\non = "flash-next"\nmodel = "qwen4exp"\nstreams = 8\nslots = 16'))
    registry = reg.load(tmp_path / "jobs.toml")
    profiles = reg.profiles(tmp_path / "profiles.toml")
    logs, alarms = [], []
    w = wk.Worker("node2", "node2", registry=registry, profiles=profiles, rules=reg.queueing(tmp_path / "jobs.toml"),
                  connect=lambda: None, alarm=lambda t, b: alarms.append((t, b)), log=logs.append)
    w.profile = {"programs": {"radiance": "/u", "qv4-llama-server-built": "/x"}, "memory_total_gb": 125, "cores": 32}
    w.retry_pause_s = 0.0
    cards = table(0, 1)
    monkeypatch.setattr(w, "cards_here", lambda: cards)
    monkeypatch.setattr(w, "available_gb", lambda: 50.0)
    w.logs, w.alarms, w.cards_table = logs, alarms, cards
    w.conn = None
    return w, fq, fr


def run_to_end(w, qid, timeout=10):
    """Claim through a tick and wait for the row's thread."""
    w.tick()
    r = w.running.get(qid)
    assert r is not None, f"row {qid} was not claimed: eligible {w.eligible()}"
    r.thread.join(timeout)
    assert not r.thread.is_alive(), "the row's runner did not finish"
    w._reap_threads()
    return r


# ── pieces from a command ────────────────────────────────────────────────────

def test_a_pieced_row_claimed_with_no_pieces_builds_them_from_its_pieces_command(fake):
    w, fq, fr = fake
    qid = fq.enqueue(None, "s", "qv4-read", registry=w.registry)
    assert fq.rows[qid]["pieces_source"] == "command" and fq.rows[qid]["pieces_total"] == 0
    run_to_end(w, qid)
    row = fq.rows[qid]
    assert row["state"] == "done" and row["outcome"] == "ok" and row["detail"] == "pieces done 3, failed 0"
    assert [p["key"] for p in fq.pieces[qid]] == ["a", "b", "c"], "blank lines and the repeat dropped"
    assert row["pieces_total"] == 3 and row["pieces_done"] == 3 and row["pieces_source"] == "command"
    assert sorted(c["key"] for c in fr.calls) == ["a", "b", "c"]
    # the pieces command ran in the job's environment and is a run of its own, piece 0
    cmd = [r for r in fq.runs.values() if r.get("piece") == 0]
    assert len(cmd) == 1 and cmd[0]["outcome"] == "ok" and cmd[0]["job"] == "qv4-read"
    assert [r["piece"] for r in fq.runs.values() if r.get("piece")] == [1, 2, 3]
    for c in fr.calls:
        assert c["env"]["QV4_JOB"] == "qv4-read" and c["env"]["QV4_MODEL"] == "qwen4exp" and c["env"]["QV4_PIECE_KEY"] == c["key"]
    assert any("3 piece(s) from its pieces_command" in m for m in w.logs)
    assert w.alarms == []


def test_a_command_that_prints_nothing_finishes_the_row_done_at_once(fake):
    w, fq, fr = fake
    qid = fq.enqueue(None, "s", "qv4-empty", registry=w.registry)
    run_to_end(w, qid)
    row = fq.rows[qid]
    assert (row["state"], row["outcome"], row["detail"]) == ("done", "ok", "nothing waiting")
    assert fr.calls == [] and fq.pieces[qid] == [] and row["pieces_total"] == 0
    assert qid not in w.running, "it holds no card: the row is gone from the worker's running set"
    assert w.alarms == []


def test_a_pieces_command_that_fails_fails_the_row_with_the_exit_and_alarms(fake):
    w, fq, fr = fake
    qid = fq.enqueue(None, "s", "qv4-broken", registry=w.registry)
    run_to_end(w, qid)
    row = fq.rows[qid]
    assert row["state"] == "failed" and row["detail"] == "pieces_command exit 3 (its stderr is in the journal)"
    assert fr.calls == [] and len(w.alarms) == 1 and "exit 3" in w.alarms[0][1]


def test_a_row_given_back_with_pieces_does_not_run_the_command_again(fake):
    w, fq, fr = fake
    qid = fq.enqueue(None, "s", "qv4-read", registry=w.registry)
    # as a first worker left it: the pieces set from the command, one still to do, the row given back
    fq.pieces[qid] = [{"piece": 1, "key": "x", "state": "todo", "attempts": 0, "worker": None, "seconds": None, "detail": ""}]
    fq.rows[qid].update(pieces_total=1, pieces_source="command")
    run_to_end(w, qid)
    assert [c["key"] for c in fr.calls] == ["x"] and not [r for r in fq.runs.values() if r.get("piece") == 0]


def test_the_enqueue_of_a_pieced_job_with_neither_pieces_nor_command_is_refused(fake):
    w, fq, fr = fake
    with pytest.raises(ValueError, match="qv4-listed is cut into pieces and names no pieces_command"):
        fq.enqueue(None, "s", "qv4-listed", registry=w.registry)
    qid = fq.enqueue(None, "s", "qv4-listed", pieces=["p1"], registry=w.registry)
    assert fq.rows[qid]["pieces_source"] == "listed"
    assert rq.pieces_source_for(w.registry["qv4-scan"], []) is None, "a job not cut into pieces has no source"


# ── then ─────────────────────────────────────────────────────────────────────

def test_a_finished_row_queues_its_then_jobs_once_each_and_says_so(fake):
    w, fq, fr = fake
    load = fq.enqueue(None, "s", "qv4-load", registry=w.registry)
    run_to_end(w, load)
    row = fq.rows[load]
    assert row["state"] == "done"
    read, scan = load + 1, load + 2
    assert row["detail"] == f"then: qv4-read queued as row {read} | then: qv4-scan queued as row {scan}"
    assert fq.rows[read]["job"] == "qv4-read" and fq.rows[read]["cls"] == "whenever" and fq.rows[read]["pieces_total"] == 0
    assert fq.rows[read]["pieces_source"] == "command" and fq.rows[read]["then_of"] == load
    assert fq.rows[read]["created_by"] == f"then of row {load}"
    assert fq.rows[scan]["job"] == "qv4-scan" and fq.rows[scan]["then_of"] == load
    assert sum(1 for m in w.logs if "then:" in m) == 2
    # a second load while the reader is still queued and the scan is running: one in flight each
    fq.rows[scan]["state"] = "leased"
    load2 = fq.enqueue(None, "s", "qv4-load", registry=w.registry)
    run_to_end(w, load2)
    assert fq.rows[load2]["detail"] == f"then: qv4-read already queued as row {read} | then: qv4-scan already running as row {scan}"
    assert len(fq.rows) == 4, "nothing new was queued"


def test_a_failed_load_queues_nothing_but_a_reader_with_failed_pieces_still_does(fake, monkeypatch):
    w, fq, fr = fake
    # a load that fails: no then
    load = fq.enqueue(None, "s", "qv4-load", registry=w.registry)
    fail = w.registry["qv4-load"]
    w.registry["qv4-load"] = dataclasses.replace(fail, command=("false",))
    monkeypatch.setattr(fr, "__call__", lambda *a, **k: runner.Result(1, 0.1, 5, "failed", "exit 1"), raising=False)
    monkeypatch.setattr(wk.runner, "run", lambda *a, **k: runner.Result(1, 0.1, 5, "failed", "exit 1"))
    run_to_end(w, load)
    assert fq.rows[load]["state"] == "failed" and "then" not in fq.rows[load]["detail"] and len(fq.rows) == 1
    # a pieced row with a failed piece: done for then's purpose (the failed piece is the lane's to look at)
    monkeypatch.setattr(wk.runner, "run", fr)
    w.registry["qv4-read"] = dataclasses.replace(w.registry["qv4-read"], then=("qv4-scan",))
    read = fq.enqueue(None, "s", "qv4-read", pieces=["ok1", "fail-1"], registry=w.registry)
    run_to_end(w, read)
    row = fq.rows[read]
    assert row["state"] == "queued" and "2 pieces failed in a row" in row["detail"], "as before: the bad piece twice gives the row back"
    assert len(fq.rows) == 2, "a row given back queues nothing"
    row["not_before"] = None
    run_to_end(w, read)
    assert row["state"] == "failed" and row["detail"].endswith(f"pieces done 1, failed 1 | then: queued row {read + 1}")
    assert fq.rows[read + 1]["job"] == "qv4-scan" and fq.rows[read + 1]["then_of"] == read
    assert fq.pieces[read][1]["attempts"] == 3 and fq.pieces[read][1]["state"] == "failed", "the failed piece was retried as before"


def test_a_then_target_without_a_command_is_a_line_not_a_crash(fake):
    w, fq, fr = fake
    w.registry["qv4-load"] = dataclasses.replace(w.registry["qv4-load"], then=("qv4-listed", "qv4-nowhere"))
    load = fq.enqueue(None, "s", "qv4-load", registry=w.registry)
    run_to_end(w, load)
    d = fq.rows[load]["detail"]
    assert d.startswith("then: qv4-listed not queued: qv4-listed is cut into pieces and names no pieces_command")
    assert d.endswith("then: qv4-nowhere is not in the catalogue; not queued") and len(fq.rows) == 1


# ── pieces in flight ─────────────────────────────────────────────────────────

def test_the_pieces_of_one_row_run_concurrency_at_a_time(fake):
    w, fq, fr = fake
    fr.barrier = threading.Barrier(4)     # opens only when four pieces are in flight at once
    qid = fq.enqueue(None, "s", "qv4-read", pieces=[f"k{i}" for i in range(8)], registry=w.registry)
    run_to_end(w, qid)
    row = fq.rows[qid]
    assert row["state"] == "done" and row["pieces_done"] == 8, row["detail"]
    assert fr.peak == 4, "four in flight, never five: the job's concurrency"
    assert row["in_flight"] is None, "cleared at the close"
    assert [r["piece"] for r in sorted(fq.runs.values(), key=lambda r: r["piece"])] == list(range(1, 9)), "a run record a piece"


def test_the_in_flight_figure_is_the_concurrency_cut_to_the_streams_the_other_rows_leave(fake):
    w, fq, fr = fake
    jt = w.registry["qv4-read"]
    a = wk.Running({"id": 1, "args": {}}, jt)
    assert w.in_flight_cap(a) == 4, "alone: the job's concurrency"
    b = wk.Running({"id": 2, "args": {}}, jt)
    b.in_flight = 6
    w.running = {1: a, 2: b}
    assert w.in_flight_cap(a) == 2, "8 streams less 6 in flight on the other row"
    b.in_flight = 8
    assert w.in_flight_cap(a) == 1, "never under 1: a row always moves"
    # a view on the same server counts, with its threads; a job on another profile does not
    w.running = {1: a, 3: wk.Running({"id": 3, "args": {}}, w.registry["qv4-listed"])}
    w.running[3].in_flight = 3                       # 3 pieces x 2 threads = 6 requests on flash-next
    assert w.in_flight_cap(a) == 2
    w.running = {1: a, 4: wk.Running({"id": 4, "args": {}}, w.registry["qv4-scan"])}
    w.running[4].in_flight = 1
    assert w.in_flight_cap(a) == 4, "a processor job holds no stream"
    # a job not cut into pieces counts as one request while it runs
    lt = w.registry["qv4-listed"]
    c = wk.Running({"id": 5, "args": {}}, lt)
    assert w.in_flight_cap(c) == 3, "its own concurrency: 3 pieces x 2 threads = 6 of 16 slots (no streams stated on review)"
    assert w.streams_of("review") == 16 and w.streams_of("text-reader") == 8 and w.streams_of("page-reader") == 1


def test_the_figure_is_written_to_the_row_while_it_runs(fake):
    w, fq, fr = fake
    fr.gate = threading.Event()           # pieces wait here until the test has looked
    qid = fq.enqueue(None, "s", "qv4-read", pieces=[f"k{i}" for i in range(6)], registry=w.registry)
    w.tick()
    r = w.running[qid]
    for _ in range(200):
        if fr.in_flight >= 4:
            break
        threading.Event().wait(0.01)
    assert fr.in_flight == 4 and fq.rows[qid]["in_flight"] == 4 and r.in_flight == 4
    st = fq.status(None, "s")
    assert cli.row_lines(st["recent"]) == [f"row {qid} qv4-read leased on node2: pieces 0/6 (listed), in flight 4 (4 running)"]
    fr.gate.set()
    r.thread.join(10)
    assert fq.rows[qid]["state"] == "done" and fq.rows[qid]["pieces_done"] == 6


def test_a_draining_card_finishes_the_pieces_in_flight_and_takes_no_more(fake):
    w, fq, fr = fake
    fr.gate = threading.Event()
    qid = fq.enqueue(None, "s", "qv4-read", pieces=[f"k{i}" for i in range(6)], registry=w.registry)
    w.tick()
    r = w.running[qid]
    for _ in range(200):
        if fr.in_flight >= 4:
            break
        threading.Event().wait(0.01)
    for c in w.cards_table:
        c["draining"] = True
    fr.gate.set()
    r.thread.join(10)
    row = fq.rows[qid]
    assert row["state"] == "queued" and row["pieces_done"] == 4, "the four in flight finished; no fifth started"
    assert row["detail"] == "no card on node2 holds profile text-reader now; given back with its progress"
    assert fq.pieces_left(None, "s", qid) == {"todo": 2, "running": 0, "done": 4, "failed": 0}
    assert len(fr.calls) == 4


def test_two_failures_in_a_row_give_the_row_back_for_two_minutes(fake):
    w, fq, fr = fake
    qid = fq.enqueue(None, "s", "qv4-read", pieces=["fail-1", "fail-2", "fail-3", "fail-4", "ok-5"], registry=w.registry)
    run_to_end(w, qid)
    row = fq.rows[qid]
    assert row["state"] == "queued" and "pieces failed in a row (exit 3); retried in 2 minutes" in row["detail"]
    assert row["not_before"] is not None and row["not_before"] > rq.utcnow() + dt.timedelta(seconds=100)
    assert fq.pieces_left(None, "s", qid)["running"] == 0, "nothing left running when the row was given back"


def test_a_piece_stopped_at_its_ceiling_gives_the_row_back_after_the_others_finish(fake):
    w, fq, fr = fake
    qid = fq.enqueue(None, "s", "qv4-read", pieces=["mem-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6"], registry=w.registry)
    run_to_end(w, qid)
    row = fq.rows[qid]
    assert row["state"] == "queued" and "memory raise 1: row given back" in row["detail"]
    assert len(fq.raises) == 1 and fq.pieces_left(None, "s", qid)["running"] == 0
    assert fq.rows[qid]["pieces_done"] >= 3 and len(fr.calls) <= 5, "the pieces in flight finished; no new one past the stop"


def test_a_stopping_worker_gives_the_row_back_with_its_progress(fake):
    w, fq, fr = fake
    fr.gate = threading.Event()
    qid = fq.enqueue(None, "s", "qv4-read", pieces=[f"k{i}" for i in range(6)], registry=w.registry)
    w.tick()
    r = w.running[qid]
    for _ in range(200):
        if fr.in_flight >= 4:
            break
        threading.Event().wait(0.01)
    w.stop()
    fr.gate.set()
    r.thread.join(10)
    row = fq.rows[qid]
    assert row["state"] == "queued" and row["detail"] == "worker stopping" and fq.pieces_left(None, "s", qid)["running"] == 0


def test_the_runner_itself_starts_no_piece_once_the_worker_is_stopping(fake):
    """The children are told to stop through their tick; this proves the
    RUNNER stops starting pieces on its own, with children that never
    notice: four in flight, the worker stops, the four finish one by one,
    and no fifth is started."""
    w, fq, fr = fake
    fr.honour_tick = False
    fr.sem = threading.Semaphore(0)
    qid = fq.enqueue(None, "s", "qv4-read", pieces=[f"k{i}" for i in range(6)], registry=w.registry)
    w.tick()
    r = w.running[qid]
    for _ in range(200):
        if fr.in_flight >= 4:
            break
        threading.Event().wait(0.01)
    assert fr.in_flight == 4
    w.stop()
    for _ in range(10):                      # more than enough releases: a mutant that starts a fifth still ends
        fr.sem.release()
    r.thread.join(10)
    row = fq.rows[qid]
    assert len(fr.calls) == 4 and row["pieces_done"] == 4, "the four in flight finished; no fifth was started"
    assert row["state"] == "queued" and row["detail"] == "worker stopping"
    assert fq.pieces_left(None, "s", qid) == {"todo": 2, "running": 0, "done": 4, "failed": 0}


# ── the catalogue's checks ───────────────────────────────────────────────────

def problems(tmp_path, jobs: str, profiles: str = PROFILES) -> list[str]:
    (tmp_path / "j.toml").write_text(jobs)
    (tmp_path / "p.toml").write_text(profiles)
    return reg.problems(tmp_path / "j.toml", tmp_path / "p.toml")


def test_check_refuses_a_pieces_command_on_a_job_not_cut_into_pieces_and_a_then_to_nowhere(tmp_path):
    assert problems(tmp_path, JOBS) == []
    bad = JOBS.replace('command = ["true"]\n\n[jobs.qv4-empty]', 'command = ["true"]\npieces_command = ["x"]\n\n[jobs.qv4-empty]')
    assert problems(tmp_path, bad) == ["qv4-scan: pieces_command on a job that is not cut into pieces (pieces = true)"]
    bad = JOBS.replace('then = ["qv4-read", "qv4-scan"]', 'then = ["qv4-read", "qv4-nowhere", "qv4-load", "qv4-listed"]')
    assert problems(tmp_path, bad) == [
        "qv4-load: then names 'qv4-nowhere', which is not in the catalogue",
        "qv4-load: then names itself",
        "qv4-load: then names 'qv4-listed', a pieced job with no pieces_command, so a row of it queued with no pieces would be refused"]
    bad = JOBS.replace('then = ["qv4-read", "qv4-scan"]', 'then = ["qv4-read"]').replace(
        'priority = 2\ncommand = ["python", "-m", "nothing", "--piece"]', 'priority = 2\nevery_s = 3600\ncommand = ["python", "-m", "nothing", "--piece"]')
    assert problems(tmp_path, bad) == ["qv4-load: then names 'qv4-read', which has a clock or a wanted count of its own"]


def test_check_holds_concurrency_times_threads_under_the_profiles_streams(tmp_path):
    profiles = PROFILES.replace('[profiles.text-reader]\non = "flash-next"\nmodel = "qwen4exp"\nslots = 16',
                                '[profiles.text-reader]\non = "flash-next"\nmodel = "qwen4exp"\nstreams = 8\nslots = 16')
    assert problems(tmp_path, JOBS, profiles) == []
    assert problems(tmp_path, JOBS.replace("concurrency = 4\n\n[jobs.qv4-scan]", "concurrency = 9\n\n[jobs.qv4-scan]"), profiles) == [
        "qv4-read: concurrency 9 x threads 1 = 9 pieces in flight on one row is over profile text-reader's 8 streams"]
    assert problems(tmp_path, JOBS.replace("concurrency = 3\nthreads = 2", "concurrency = 3\nthreads = 6"), profiles) == [
        "qv4-listed: concurrency 3 x threads 6 = 18 pieces in flight on one row is over profile review's 16 streams"]
    assert problems(tmp_path, JOBS.replace("concurrency = 3\nthreads = 2", "concurrency = 3\nthreads = 0"), profiles) == [
        "qv4-listed: threads from 1"]
    assert problems(tmp_path, JOBS.replace('priority = 3\ncommand = ["true"]', 'priority = 3\nthreads = 2\ncommand = ["true"]'), profiles) == [
        "qv4-scan: threads says what one piece keeps open; the job is not cut into pieces"]
    over = profiles.replace("streams = 8", "streams = 17")
    assert problems(tmp_path, JOBS, over) == [
        "profile text-reader: streams 17 is over its server's 16 slots: the server would queue the rest"]
    assert reg.streams_of(reg.profiles(tmp_path / "p.toml"), "text-reader") == 17


def test_the_shipped_catalogue_wires_the_chain():
    jts, profs = reg.load(), reg.profiles()
    assert reg.problems() == []
    # the name pass sits between the load and its reader (31 October 2026): load, sightings, reader
    assert jts["qv4-courts-load"].then == ("qv4-sightings-courts",)
    assert jts["qv4-sightings-courts"].then == ("qv4-courts-read",)
    for lane in ("beehive", "hansard", "parliament"):
        assert jts[f"qv4-{lane}-load"].then == (f"qv4-sightings-{lane}",), lane
    assert jts["qv4-links-build"].then == ("qv4-sightings-forms",)
    assert set(jts["qv4-sightings-forms"].then) == {f"qv4-sightings-{x}" for x in ("beehive", "hansard", "parliament", "courts")}
    assert jts["qv4-courts-read"].pieces_command == ("python", "-m", "registers.courts.model_read", "--pieces")
    assert jts["qv4-courts-read"].concurrency * jts["qv4-courts-read"].threads <= reg.streams_of(profs, "text-reader") == 8
    for load in ("qv4-disclosures-load", "qv4-candidate-returns-load", "qv4-tenders-load", "qv4-iwi-directory-load", "qv4-charities-load"):
        assert jts[load].then == ("qv4-scan-rerun",), load
    assert jts["qv4-scan-rerun"].cls == "whenever" and not jts["qv4-scan-rerun"].then
    assert jts["qv4-mcp-pull"].then == (), "the loads stay on their nightly clock"


def test_the_cli_enqueue_refuses_a_pieced_job_with_no_pieces_and_no_command(tmp_path, monkeypatch, capsys):
    (tmp_path / "jobs.toml").write_text(JOBS)
    monkeypatch.setattr(reg, "JOBS", tmp_path / "jobs.toml")
    monkeypatch.setattr(cli, "_conn", lambda database: None)
    fq = FakeQueue()
    monkeypatch.setattr(cli, "q", fq)
    assert cli.main(["enqueue", "qv4-listed"]) == 2
    assert "not queued: qv4-listed is cut into pieces and names no pieces_command" in capsys.readouterr().err
    assert cli.main(["enqueue", "qv4-read"]) == 0
    assert "queued qv4-read as row 1; its pieces_command lists the pieces at the claim" in capsys.readouterr().out
    assert cli.main(["enqueue", "qv4-listed", "--pieces", "a", "b"]) == 0
    assert "with 2 pieces" in capsys.readouterr().out


def test_status_lines_name_the_source_the_flight_and_the_then_rows():
    recent = [
        {"id": 9, "job": "qv4-scan", "state": "queued", "lease_owner": None, "pieces_done": 0, "pieces_total": 0, "outcome": None,
         "pieces_source": None, "in_flight": None, "then_of": 7, "pieces_running": 0, "then_rows": []},
        {"id": 8, "job": "qv4-courts-read", "state": "leased", "lease_owner": "node2", "pieces_done": 120, "pieces_total": 685,
         "outcome": None, "pieces_source": "command", "in_flight": 8, "then_of": 7, "pieces_running": 7, "then_rows": []},
        {"id": 7, "job": "qv4-courts-load", "state": "done", "lease_owner": None, "pieces_done": 0, "pieces_total": 0, "outcome": "ok",
         "pieces_source": None, "in_flight": None, "then_of": None, "pieces_running": 0, "then_rows": [8, 9]},
        {"id": 6, "job": "qv4-reread", "state": "queued", "lease_owner": None, "pieces_done": 0, "pieces_total": 3, "outcome": None,
         "pieces_source": "listed", "in_flight": None, "then_of": None, "pieces_running": 0, "then_rows": []},
    ]
    assert cli.row_lines(recent) == [
        "row 9 qv4-scan queued; then of row 7",
        "row 8 qv4-courts-read leased on node2: pieces 120/685 (command), in flight 8 (7 running); then of row 7",
        "row 6 qv4-reread queued: pieces 0/3 (listed)",
    ]
