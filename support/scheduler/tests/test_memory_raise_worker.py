"""Ruling 115 end to end (the sample database, a scratch schema; slow): a
toy job allocates past a small ceiling, the worker raises its working figure
and runs it again; twice at most per first row, never over the box's budget,
never for a job's own error; the raise is listed until jobs.toml meets it,
and a restarted worker places by it."""
from __future__ import annotations

import dataclasses
import io
import json
import os
import pathlib
import re
import uuid
from contextlib import redirect_stdout

import pytest

import support.db as db
from support.scheduler import queue as q
from support.scheduler import registry as reg
from support.scheduler import runs
from support.scheduler.__main__ import main
from support.scheduler.worker import Worker, report

pytestmark = pytest.mark.slow
DB = "querynz_v4_sample"
BURN = "qv4-rehearsal-burn"                   # declares 0.1 GB: a ceiling of 128 MB


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
    schema = f"scratch_schedraise_{os.getpid()}_{uuid.uuid4().hex[:6]}"
    q.tables(conn, schema)
    yield schema
    conn.execute(f"DROP SCHEMA {schema} CASCADE")


def toy_registry(mb: int = 200, command: tuple = None) -> dict:
    """The rehearsal catalogue with the burn job allocating `mb` for a few
    seconds (long enough for the half-second measurement to see it)."""
    out = {n: j for n, j in reg.load().items() if not (j.every_s or j.at_utc or j.wanted)}
    out[BURN] = dataclasses.replace(out[BURN], command=command or (
        "python", "-m", "support.scheduler", "rehearse", "burn", "--mb", str(mb), "--seconds", "3"))
    return out


def worker(s, registry, name="node2"):
    alarms = []
    w = Worker(name, "node2", database=DB, schema=s, registry=registry, alarm=lambda t, b: alarms.append((t, b)),
               log=lambda m: None, connect=connect)
    w.alarms = alarms
    w.start()
    return w


def settle(w, conn, s, timeout=120):
    """Tick until nothing is queued or running: every re-run has had its go."""
    import time
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        w.tick()
        busy = conn.execute(f"SELECT count(*) FROM {s}.queue WHERE state IN ('queued', 'leased')").fetchone()[0]
        if not busy and not w.running:
            return
        time.sleep(0.5)
    raise AssertionError("the queue did not settle")


def rows(conn, s):
    return [dict(zip(("id", "state", "detail", "created_by"), r)) for r in
            conn.execute(f"SELECT id, state, detail, created_by FROM {s}.queue ORDER BY id").fetchall()]


def raises(conn, s):
    keys = ("id", "queue_id", "origin_queue_id", "peak_mb", "ceiling_mb", "held_gb", "raised_gb", "applied", "requeued_id", "note")
    return [dict(zip(keys, r)) for r in conn.execute(f"SELECT {', '.join(keys)} FROM {s}.memory_raises ORDER BY id").fetchall()]


def test_a_job_killed_at_its_ceiling_is_queued_once_with_the_doubled_figure_and_runs(conn, s):
    w = worker(s, toy_registry(200))
    first = q.enqueue(conn, s, BURN, args={"k": 1}, registry=w.registry)
    settle(w, conn, s)
    a, b = rows(conn, s)
    assert a["id"] == first and a["state"] == "failed" and "memory raise" in a["detail"]
    assert b["state"] == "done" and b["created_by"] == f"memory raise of row {first}"
    assert conn.execute(f"SELECT args FROM {s}.queue WHERE id = %s", (b["id"],)).fetchone()[0] == {"k": 1}
    rz, = raises(conn, s)
    assert (rz["queue_id"], rz["origin_queue_id"], rz["ceiling_mb"], rz["held_gb"], rz["raised_gb"], rz["applied"],
            rz["requeued_id"]) == (first, first, 128, pytest.approx(0.1), 0.5, True, b["id"])
    assert rz["peak_mb"] > 128
    run = conn.execute(f"SELECT outcome, declared_mb, working_mb, raise_id FROM {s}.runs WHERE queue_id = %s",
                       (b["id"],)).fetchone()
    assert run == ("ok", 102, 512, rz["id"])
    end = [r for r in runs.rows() if r.get("kind") == "end" and r.get("rerun_of_raise") == rz["id"]]
    assert end and end[-1]["outcome"] == "ok" and end[-1]["working_mb"] == 512
    assert w.alarms == []                         # a re-run that came good raises no alarm
    assert w.working_gb(w.registry[BURN]) == 0.5


def test_a_second_kill_doubles_again_and_a_third_stays_failed(conn, s):
    w = worker(s, toy_registry(2200))             # past 128 MB, then 640, then 1,920
    first = q.enqueue(conn, s, BURN, registry=w.registry)
    settle(w, conn, s, timeout=180)
    r1, r2, r3 = rows(conn, s)
    assert [r["state"] for r in (r1, r2, r3)] == ["failed", "failed", "failed"]
    z1, z2, z3 = raises(conn, s)
    assert (z1["raised_gb"], z2["raised_gb"], z3["raised_gb"]) == (0.5, 1.5, 4.0)
    assert (z2["ceiling_mb"], z3["ceiling_mb"]) == (640, 1920)
    assert {z["origin_queue_id"] for z in (z1, z2, z3)} == {first}
    assert (z1["requeued_id"], z2["requeued_id"], z3["requeued_id"]) == (r2["id"], r3["id"], None)
    assert "stays failed: raised 2 times already" in z3["note"] and "stays failed" in r3["detail"]
    assert len(w.alarms) == 1 and "qv4-rehearsal-burn failed" in w.alarms[0][0] and "raised 2 times" in w.alarms[0][1]
    assert w.working_gb(w.registry[BURN]) == 4.0  # the next run is placed at the measured floor's double


def test_the_second_raise_runs_when_the_doubled_figure_is_enough(conn, s):
    w = worker(s, toy_registry(900))              # past 128 and 640 MB, under 1,920
    q.enqueue(conn, s, BURN, registry=w.registry)
    settle(w, conn, s, timeout=120)
    assert [r["state"] for r in rows(conn, s)] == ["failed", "failed", "done"]
    assert [z["raised_gb"] for z in raises(conn, s)] == [0.5, 1.5] and w.alarms == []


def test_a_raise_over_the_box_budget_stays_failed_with_the_note(conn, s):
    w = worker(s, toy_registry(200))
    w.memory_budget_gb = lambda: 0.4              # the 0.5 GB raise does not fit
    q.enqueue(conn, s, BURN, registry=w.registry)
    settle(w, conn, s)
    r, = rows(conn, s)
    z, = raises(conn, s)
    assert r["state"] == "failed" and not z["applied"] and z["requeued_id"] is None
    assert "over the box's budget of 0.4 GB" in z["note"] and "over the box's budget" in r["detail"]
    assert w.alarms and "over the box's budget" in w.alarms[0][1]
    assert w.working_gb(w.registry[BURN]) == pytest.approx(0.1)


def test_a_job_failing_by_its_own_exit_code_is_not_re_run(conn, s):
    w = worker(s, toy_registry(command=("python", "-m", "support.scheduler", "rehearse", "fail")))
    q.enqueue(conn, s, BURN, registry=w.registry)
    settle(w, conn, s)
    r, = rows(conn, s)
    assert r["state"] == "failed" and r["detail"] == "exit 3" and raises(conn, s) == []
    assert w.alarms


def test_the_report_and_memory_list_an_unfolded_raise_until_jobs_toml_meets_it(conn, s, tmp_path, monkeypatch):
    w = worker(s, toy_registry(200))
    q.enqueue(conn, s, BURN, registry=w.registry)
    settle(w, conn, s)

    def memory_cmd() -> str:
        out = io.StringIO()
        with redirect_stdout(out):
            assert main(["memory", "--database", DB, "--schema", s]) == 0
        return out.getvalue()

    listed = memory_cmd()
    assert "1 raise(s) not yet folded" in listed and f"fold: [jobs.{BURN}] memory_gb = 0.5" in listed
    path = report(conn, s, path=str(tmp_path / "scheduler.json"))
    rec = json.loads(pathlib.Path(path).read_text())
    assert [x["job"] for x in rec["memory_raises"]] == [BURN] and rec["memory_raises"][0]["raised_gb"] == 0.5

    # the integrator folds it: jobs.toml declares at least the raised figure
    folded = tmp_path / "jobs.toml"
    text = reg.JOBS.read_text()
    block = re.search(rf"\[jobs\.{BURN}\][^\[]*", text).group(0)
    folded.write_text(text.replace(block, block.replace("memory_gb = 0.1", "memory_gb = 0.5")))
    monkeypatch.setattr(reg, "JOBS", folded)
    assert reg.load()[BURN].memory_gb == 0.5
    assert "no raise waits to be folded" in memory_cmd()
    rec = json.loads(pathlib.Path(report(conn, s, path=str(tmp_path / "scheduler.json"))).read_text())
    assert rec["memory_raises"] == []


def test_the_working_figure_survives_a_worker_restart_and_places_the_job(conn, s):
    w = worker(s, toy_registry(200))
    q.enqueue(conn, s, BURN, registry=w.registry)
    settle(w, conn, s)
    w.stop()
    w._finish_stop()
    again = worker(s, toy_registry(200))          # a new process: nothing carried in memory
    jt = again.registry[BURN]
    assert again.raised == {BURN: 0.5} and again.working_gb(jt) == 0.5
    # placement uses the working figure: room for 0.1 GB but not 0.5 waits
    again.available_gb = lambda: 0.3
    assert BURN not in again.eligible()
    again.available_gb = lambda: 0.6
    assert BURN in again.eligible()
