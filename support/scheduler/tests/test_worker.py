"""The worker against a real queue (the sample database, a scratch schema;
slow): it claims only what it can run, runs under the limits, records the
run, and two workers finish a job between them when one stops mid-piece."""
from __future__ import annotations

import datetime as dt
import os
import time
import uuid

import pytest

import support.db as db
from support.scheduler import queue as q
from support.scheduler import registry as reg
from support.scheduler.worker import Worker

pytestmark = pytest.mark.slow
DB = "querynz_v4_sample"


def connect():
    c = db.connect(db.OWNER_KEY, DB, autocommit=True)
    c.execute("SET statement_timeout = 30000")
    return c


@pytest.fixture(scope="module")
def conn():
    try:
        c = connect()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"no sample database here: {type(exc).__name__}")
    yield c
    c.close()


@pytest.fixture
def s(conn):
    schema = f"scratch_schedwork_{os.getpid()}_{uuid.uuid4().hex[:6]}"
    q.tables(conn, schema)
    yield schema
    conn.execute(f"DROP SCHEMA {schema} CASCADE")


def rehearsal_registry():
    """The shipped catalogue without its timetabled and standing jobs, so a
    test never queues the real report job (which writes under <live>)."""
    return {n: j for n, j in reg.load().items() if not (j.every_s or j.at_utc or j.wanted)}


def worker(name, s, **kw):
    alarms = []
    kw.setdefault("registry", rehearsal_registry())
    w = Worker(name, "node2", database=DB, schema=s, alarm=lambda t, b: alarms.append((t, b)), log=lambda m: None,
               connect=connect, **kw)
    w.alarms = alarms
    w.start()
    return w


def wait_for(pred, timeout=60):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if pred():
            return True
        time.sleep(0.5)
    return False


def row(conn, s, qid):
    r = conn.execute(f"SELECT state, outcome, detail, pieces_done, lease_owner FROM {s}.queue WHERE id = %s", (qid,)).fetchone()
    return dict(zip(("state", "outcome", "detail", "pieces_done", "lease_owner"), r))


def test_a_worker_registers_a_probed_profile_and_runs_a_job_to_a_record(conn, s):
    w = worker("node2", s)
    ws = {x["name"]: x for x in q.workers(conn, s)}
    assert ws["node2"]["profile"]["cores"] and ws["node2"]["profile"]["programs"]["pdftotext"]
    cards = q.cards(conn, s, "node2")
    assert any(c["reserved"] for c in cards if c["card"] == 0) or not cards
    qid = q.enqueue(conn, s, "qv4-rehearsal-sleep", registry=w.registry)
    w.tick()
    assert qid in w.running
    assert wait_for(lambda: row(conn, s, qid)["state"] == "done", 30)
    r = conn.execute(f"SELECT outcome, exit_code, peak_mb, declared_mb, worker FROM {s}.runs WHERE queue_id = %s", (qid,)).fetchone()
    assert r[0] == "ok" and r[1] == 0 and r[2] > 0 and r[3] == 204 and r[4] == "node2"
    assert w.alarms == []


def test_a_job_needing_a_program_this_box_lacks_is_never_claimed(conn, s):
    """The done-when item: the second worker hides the headed browser and
    is offered nothing; the first takes the job."""
    blind = worker("node2-b", s, hide_programs=["google-chrome"])
    qid = q.enqueue(conn, s, "qv4-rehearsal-needs-program", registry=blind.registry)
    assert "qv4-rehearsal-needs-program" not in blind.eligible()
    for _ in range(3):
        blind.tick()
    assert row(conn, s, qid)["state"] == "queued"
    sighted = worker("node2", s)
    sighted.tick()
    assert row(conn, s, qid)["lease_owner"] == "node2"
    assert wait_for(lambda: row(conn, s, qid)["state"] == "done", 30)


def test_a_job_past_its_ceiling_is_stopped_and_flagged_and_the_box_stays_up(conn, s):
    w = worker("node2", s)
    qid = q.enqueue(conn, s, "qv4-rehearsal-burn", registry=w.registry)
    w.tick()
    assert wait_for(lambda: row(conn, s, qid)["state"] == "failed", 60)
    r = conn.execute(f"SELECT outcome, detail, peak_mb, declared_mb, error FROM {s}.runs WHERE queue_id = %s", (qid,)).fetchone()
    assert r[0] == "failed" and r[1] == "memory" and r[2] > r[3] and "over its ceiling" in r[4]
    assert q.over_declared(conn, s)[0]["job"] == "qv4-rehearsal-burn"
    assert w.alarms and "qv4-rehearsal-burn failed" in w.alarms[0][0]


def test_a_worker_stopped_mid_job_loses_at_most_one_piece_and_the_other_finishes(conn, s):
    """Step 2.8 end to end: ten pieces; worker A does some and is stopped on
    a piece; worker B takes the lease and finishes the rest. A stops
    deliberately, so no alarm is raised."""
    a = worker("node2", s)
    b = worker("node2-b", s)
    qid = q.enqueue(conn, s, "qv4-rehearsal-pieces", pieces=[f"p{i}" for i in range(1, 11)], registry=a.registry)
    a.tick()
    assert row(conn, s, qid)["lease_owner"] == "node2"
    assert wait_for(lambda: row(conn, s, qid)["pieces_done"] >= 2, 30)
    done_at_stop = row(conn, s, qid)["pieces_done"]
    a.stop()
    a._finish_stop()
    r = row(conn, s, qid)
    assert r["state"] == "queued" and r["pieces_done"] in (done_at_stop, done_at_stop + 1)
    assert q.pieces_left(conn, s, qid)["running"] == 0
    for _ in range(3):
        b.tick()
    assert row(conn, s, qid)["lease_owner"] == "node2-b"
    assert wait_for(lambda: row(conn, s, qid)["state"] == "done", 90)
    assert row(conn, s, qid)["pieces_done"] == 10
    by = dict(conn.execute(f"SELECT worker, count(*) FROM {s}.pieces WHERE queue_id = %s GROUP BY worker", (qid,)).fetchall())
    assert by.get("node2", 0) >= 2 and by.get("node2-b", 0) >= 1 and sum(by.values()) == 10
    assert a.alarms == [] and b.alarms == []
    ws = {x["name"]: x for x in q.workers(conn, s)}
    assert ws["node2"]["state"] == "stopped"


def test_silence_is_alarmed_by_the_other_worker_but_a_stop_is_not(conn, s):
    a = worker("node2", s, alarm_after_s=1)
    b = worker("node2-b", s, alarm_after_s=1)
    time.sleep(1.5)
    a.tick()
    assert [t for t, _ in a.alarms] == ["qv4 node2: worker node2-b silent"]
    a.tick()
    assert len(a.alarms) == 1, "once"
    b.tick()                                   # b comes back: cleared, and b sees a fresh a
    assert b.alarms == []
    b.stop()
    b._finish_stop()
    time.sleep(1.5)
    a.tick()
    assert len(a.alarms) == 1, "a deliberate stop never alarms"


def test_a_timetabled_job_runs_on_whichever_worker_is_up(conn, s, tmp_path):
    """Step 2.12: the clock is in the queue. With worker A stopped, B
    queues the due slot and runs it with no hand step."""
    toml = open(reg.JOBS, encoding="utf-8").read().replace('every_s = 120\nenabled = false', 'every_s = 120')
    p = tmp_path / "jobs.toml"
    p.write_text(toml)
    registry = {n: j for n, j in reg.load(p).items() if n == "qv4-rehearsal-tick" or not (j.every_s or j.at_utc or j.wanted)}
    # the clock already knows the job (a job new to it would wait for its next slot): one slot owed
    conn.execute(f"INSERT INTO {s}.timetable (job, last_slot, last_by, clock) VALUES ('qv4-rehearsal-tick', %s, 'test', %s)",
                 (q.utcnow() - dt.timedelta(seconds=600), q.clock_of(registry["qv4-rehearsal-tick"])))
    a = worker("node2", s, registry=registry)
    a.stop()
    a._finish_stop()
    b = worker("node2-b", s, registry=registry)
    b.tick()
    qid = conn.execute(f"SELECT id FROM {s}.queue WHERE job = 'qv4-rehearsal-tick'").fetchone()[0]
    assert row(conn, s, qid)["lease_owner"] == "node2-b"
    assert wait_for(lambda: row(conn, s, qid)["state"] == "done", 30)


def test_a_run_of_short_pieces_keeps_the_lease(conn, s):
    """Card the-worker-s-lease-lapses-under-a-run-of-short-pieces: pieces of about
    four seconds under a 24 s lease (renewal due every 8 s) must renew between
    pieces, so the worker's own reaper never takes the row and no piece is
    killed for a lost lease. Before the fix the clock restarted with every
    piece and the lease lapsed after three of them."""
    import dataclasses
    rules = dataclasses.replace(reg.queueing(), lease_seconds=24)
    w = worker("node2", s, rules=rules)
    qid = q.enqueue(conn, s, "qv4-rehearsal-pieces", pieces=[f"p{i}" for i in range(1, 11)], registry=w.registry)
    w.tick()
    assert row(conn, s, qid)["lease_owner"] == "node2"
    t0 = time.monotonic()
    while row(conn, s, qid)["state"] != "done" and time.monotonic() - t0 < 120:
        w.tick()                      # the reaper runs here: a lapsed lease would be taken back
        time.sleep(1)
    w.stop()
    assert row(conn, s, qid)["state"] == "done" and row(conn, s, qid)["pieces_done"] == 10
    runs_ = conn.execute(f"SELECT outcome, detail FROM {s}.runs WHERE queue_id = %s", (qid,)).fetchall()
    assert len(runs_) == 10 and all(o == "ok" for o, _ in runs_), runs_
    assert not any(d == "lease" for _, d in runs_)


def test_a_lease_taken_after_a_long_load_is_stamped_from_the_clock_at_the_claim(conn, s):
    """Card the-lease-lapses-while-a-large-model-loads: the tick read its clock once,
    the card manager then spent 124 s loading the 35B model, and the claim stamped
    its lease from that stale clock, so the lease had lapsed before the first piece
    started and the next tick's reaper took the row (twice on 19 October). A fake
    card manager takes two leases to load; one claim, a live lease, zero reaps."""
    import dataclasses
    rules = dataclasses.replace(reg.queueing(), lease_seconds=3)

    class SlowCards:
        loads = 0

        def start(self, worker):
            pass

        def tick(self, worker, now):
            if not self.loads:                      # the one long load, then nothing
                self.loads += 1
                time.sleep(2 * rules.lease_seconds + 1)

        def stop_all(self, worker, why=""):
            pass

    w = worker("node2", s, rules=rules, cards_manager=SlowCards())
    qid = q.enqueue(conn, s, "qv4-rehearsal-sleep", registry=w.registry)
    w.tick()                                        # the load, then the claim
    r = conn.execute(f"SELECT lease_owner, lease_until, attempts FROM {s}.queue WHERE id = %s", (qid,)).fetchone()
    assert r[0] == "node2" and r[2] == 1
    assert r[1] > q.utcnow(), f"the lease was stamped from a clock {q.utcnow() - r[1]} stale"
    w.tick()                                        # the reaper runs here
    assert row(conn, s, qid)["lease_owner"] == "node2", "reaped by its own worker"
    assert wait_for(lambda: row(conn, s, qid)["state"] == "done", 30)
    assert row(conn, s, qid)["detail"] in (None, "") or "lease lapsed" not in row(conn, s, qid)["detail"]
    assert conn.execute(f"SELECT attempts FROM {s}.queue WHERE id = %s", (qid,)).fetchone()[0] == 1
