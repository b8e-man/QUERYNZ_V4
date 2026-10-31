"""The queue's safety model, against a real database (the sample database,
in this session's scratch schema; marked slow because it needs one).

Leases lapse and the work is re-offered; a fencing token makes a zombie's
completion a no-op; pieces keep their progress; a timetable slot is queued
once however many workers notice it; a deliberate stop never looks like a
death."""
from __future__ import annotations

import datetime as dt
import os
import uuid

import pytest

import support.db as db
from support.scheduler import queue as q
from support.scheduler import registry as reg
from support.scheduler.tests import fixtures as fx

pytestmark = pytest.mark.slow
T0 = dt.datetime(2026, 10, 18, 12, 0, 0, tzinfo=dt.timezone.utc)


def secs(n):
    return T0 + dt.timedelta(seconds=n)


@pytest.fixture(scope="module")
def conn():
    try:
        c = db.connect(db.OWNER_KEY, "querynz_v4_sample", autocommit=True)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"no sample database here: {type(exc).__name__}")
    yield c
    c.close()


@pytest.fixture
def s(conn):
    schema = f"scratch_schedtest_{os.getpid()}_{uuid.uuid4().hex[:6]}"
    q.tables(conn, schema)
    yield schema
    conn.execute(f"DROP SCHEMA {schema} CASCADE")


@pytest.fixture
def cat(tmp_path):
    j, p = fx.write(tmp_path)
    return reg.load(j)


ALL = ["doc", "rev", "reason", "emb", "cpu"]


def test_the_most_urgent_eligible_row_is_claimed_first(conn, s, cat):
    """Class first (someone waiting), then due time, then priority, then age;
    and only among the job types the worker can run."""
    a = q.enqueue(conn, s, "emb", registry=cat, now=secs(0))
    b = q.enqueue(conn, s, "doc", registry=cat, now=secs(1))
    c = q.enqueue(conn, s, "rev", cls="due", due_at=secs(600), registry=cat, now=secs(2))
    d = q.enqueue(conn, s, "reason", cls="waiting", registry=cat, now=secs(3))
    got = [q.claim(conn, s, "w", ALL, lease_s=60, now=secs(10))["id"] for _ in range(4)]
    assert got == [d, c, b, a]
    assert q.claim(conn, s, "w", ALL, lease_s=60, now=secs(10)) is None
    e = q.enqueue(conn, s, "cpu", registry=cat, now=secs(4))
    assert q.claim(conn, s, "w", ["doc"], lease_s=60, now=secs(10)) is None, "not eligible: not offered"
    assert q.claim(conn, s, "w", ["cpu"], lease_s=60, now=secs(10))["id"] == e


def test_not_before_holds_a_row_back(conn, s, cat):
    a = q.enqueue(conn, s, "cpu", not_before=secs(100), registry=cat, now=secs(0))
    assert q.claim(conn, s, "w", ALL, lease_s=60, now=secs(50)) is None
    assert q.claim(conn, s, "w", ALL, lease_s=60, now=secs(100))["id"] == a


def test_the_fence_makes_a_zombies_completion_a_no_op(conn, s, cat):
    """The lease lapses, the other worker takes the row, the first worker
    wakes and tries to finish: rowcount 0, nothing changes."""
    qid = q.enqueue(conn, s, "cpu", registry=cat, now=secs(0))
    first = q.claim(conn, s, "w1", ALL, lease_s=60, now=secs(0))
    assert first["id"] == qid and first["attempts"] == 1
    assert q.renew(conn, s, qid, first["token"], lease_s=60, now=secs(30))
    reaped = q.reap(conn, s, now=secs(200))
    assert [r["id"] for r in reaped] == [qid]
    second = q.claim(conn, s, "w2", ALL, lease_s=60, now=secs(200))
    assert second["id"] == qid and second["attempts"] == 2
    assert q.renew(conn, s, qid, first["token"], lease_s=60, now=secs(201)) is False
    assert q.complete(conn, s, qid, first["token"], outcome="ok", now=secs(202)) is False
    assert q.complete(conn, s, qid, second["token"], outcome="ok", now=secs(203)) is True
    row = conn.execute(f"SELECT state, lease_owner, detail FROM {s}.queue WHERE id = %s", (qid,)).fetchone()
    assert row[0] == "done" and row[1] == "w2" and "lease lapsed from w1" in (row[2] or "")


def test_a_lease_that_is_renewed_is_not_reaped(conn, s, cat):
    qid = q.enqueue(conn, s, "cpu", registry=cat, now=secs(0))
    c = q.claim(conn, s, "w1", ALL, lease_s=60, now=secs(0))
    q.renew(conn, s, qid, c["token"], lease_s=60, now=secs(59))
    assert q.reap(conn, s, now=secs(100)) == []
    assert q.reap(conn, s, now=secs(120)) != []


def test_pieces_record_progress_and_a_death_loses_at_most_one(conn, s, cat):
    """Rule 7 and step 2.8: five pieces; the first worker finishes two and
    dies on the third; the second worker finds exactly three left, the one
    in flight among them."""
    qid = q.enqueue(conn, s, "doc", pieces=["d1", "d2", "d3", "d4", "d5"], registry=cat, now=secs(0))
    c1 = q.claim(conn, s, "w1", ALL, lease_s=60, now=secs(0))
    for _ in range(2):
        p = q.next_piece(conn, s, qid, c1["token"], "w1", now=secs(1))
        assert q.finish_piece(conn, s, qid, c1["token"], p["piece"], ok=True, seconds=1.0, now=secs(2))
    p3 = q.next_piece(conn, s, qid, c1["token"], "w1", now=secs(3))
    assert p3["piece"] == 3 and p3["key"] == "d3"
    assert q.pieces_left(conn, s, qid) == {"todo": 2, "running": 1, "done": 2, "failed": 0}
    reaped = q.reap(conn, s, now=secs(500))
    assert reaped[0]["pieces_lost"] == [3] and reaped[0]["pieces_done"] == 2
    c2 = q.claim(conn, s, "w2", ALL, lease_s=60, now=secs(500))
    assert c2["pieces_done"] == 2
    assert q.next_piece(conn, s, qid, c1["token"], "w1", now=secs(501)) is None, "the zombie gets no piece"
    keys = []
    while (p := q.next_piece(conn, s, qid, c2["token"], "w2", now=secs(502))):
        keys.append(p["key"])
        q.finish_piece(conn, s, qid, c2["token"], p["piece"], ok=True, seconds=1.0, now=secs(503))
    assert keys == ["d3", "d4", "d5"]
    assert q.pieces_left(conn, s, qid)["done"] == 5
    assert q.complete(conn, s, qid, c2["token"], outcome="ok", now=secs(504))
    assert conn.execute(f"SELECT pieces_done FROM {s}.queue WHERE id = %s", (qid,)).fetchone()[0] == 5


def test_a_failed_piece_is_retried_and_stays_failed_after_three(conn, s, cat):
    qid = q.enqueue(conn, s, "doc", pieces=["bad"], registry=cat, now=secs(0))
    c = q.claim(conn, s, "w1", ALL, lease_s=60, now=secs(0))
    for attempt in range(1, 4):
        p = q.next_piece(conn, s, qid, c["token"], "w1", now=secs(attempt))
        assert p and p["attempts"] == attempt
        q.finish_piece(conn, s, qid, c["token"], p["piece"], ok=False, seconds=1.0, detail="boom", now=secs(attempt))
    assert q.next_piece(conn, s, qid, c["token"], "w1", now=secs(9)) is None
    assert q.pieces_left(conn, s, qid) == {"todo": 0, "running": 0, "done": 0, "failed": 1}


def test_requeue_gives_the_row_back_with_its_progress(conn, s, cat):
    qid = q.enqueue(conn, s, "doc", pieces=["a", "b"], registry=cat, now=secs(0))
    c = q.claim(conn, s, "w1", ALL, lease_s=60, now=secs(0))
    p = q.next_piece(conn, s, qid, c["token"], "w1", now=secs(1))
    q.finish_piece(conn, s, qid, c["token"], p["piece"], ok=True, seconds=1.0, now=secs(2))
    q.next_piece(conn, s, qid, c["token"], "w1", now=secs(3))
    assert q.requeue(conn, s, qid, c["token"], detail="stopping", not_before=secs(10), now=secs(4))
    assert q.pieces_left(conn, s, qid) == {"todo": 1, "running": 0, "done": 1, "failed": 0}
    assert q.claim(conn, s, "w2", ALL, lease_s=60, now=secs(5)) is None
    assert q.claim(conn, s, "w2", ALL, lease_s=60, now=secs(10))["pieces_done"] == 1


def test_a_deliberate_stop_releases_leases_and_never_alarms(conn, s, cat):
    """The silence check alarms for a worker that was `up` and went quiet,
    once; a worker that said it was stopping is not silent, and a heartbeat
    clears an alarm."""
    q.register(conn, s, "node2", "node2", {"cores": 32}, now=secs(0))
    q.register(conn, s, "node2-b", "node2", {"cores": 32}, now=secs(0))
    qid = q.enqueue(conn, s, "cpu", registry=cat, now=secs(0))
    q.claim(conn, s, "node2-b", ALL, lease_s=600, now=secs(0))
    assert q.stop_worker(conn, s, "node2-b", now=secs(1)) == 1
    assert conn.execute(f"SELECT state FROM {s}.queue WHERE id = %s", (qid,)).fetchone()[0] == "queued"
    assert q.silent_workers(conn, s, after_s=300, me="node2", now=secs(1000)) == [], "stopped is not silent"
    q.register(conn, s, "node2-b", "node2", {}, now=secs(1000))
    assert q.silent_workers(conn, s, after_s=300, me="node2", now=secs(1200)) == []
    got = q.silent_workers(conn, s, after_s=300, me="node2", now=secs(1301))
    assert [w["name"] for w in got] == ["node2-b"]
    assert q.silent_workers(conn, s, after_s=300, me="node2", now=secs(1400)) == [], "alarmed once"
    q.heartbeat(conn, s, "node2", now=secs(1400))
    assert q.silent_workers(conn, s, after_s=300, me="node2-b", now=secs(1401)) == [], "never for myself, and node2 is fresh"
    q.heartbeat(conn, s, "node2-b", now=secs(1500))
    w = {x["name"]: x for x in q.workers(conn, s)}["node2-b"]
    assert w["state"] == "up" and w["alarmed_at"] is None


def test_a_timetable_slot_is_queued_once_whoever_notices(conn, s, tmp_path):
    """Two workers see the same due slot: one row. The next slot is a new
    row; a slot is skipped while the earlier instance is still in the
    queue, so a stuck job does not pile up behind itself."""
    jobs = fx.JOBS + '\n[jobs.tick]\nneeds = "processor"\nmemory_gb = 0.1\ndeadline_s = 60\nquery_timeout_s = 10\n' \
                     'priority = 50\ncommand = ["true"]\nevery_s = 600\n'
    j, _ = fx.write(tmp_path, jobs=jobs)
    cat = reg.load(j)
    assert q.slot_for(cat["tick"], secs(50)) == secs(0)
    assert q.enqueue_due(conn, s, cat, now=secs(50), created_by="node2") == [], "new to the clock: its next slot"
    assert q.slot_for(cat["tick"], secs(650)) == secs(600)
    first = q.enqueue_due(conn, s, cat, now=secs(650), created_by="node2")
    again = q.enqueue_due(conn, s, cat, now=secs(651), created_by="node2-b")
    assert len(first) == 1 and again == []
    assert q.enqueue_due(conn, s, cat, now=secs(1250), created_by="node2") == [], "the earlier instance is still queued"
    c = q.claim(conn, s, "node2", ["tick"], lease_s=60, now=secs(1250))
    assert c["timetable_slot"] == secs(600) and c["cls"] == "whenever"
    q.complete(conn, s, c["id"], c["token"], outcome="ok", now=secs(1260))
    nxt = q.enqueue_due(conn, s, cat, now=secs(1261), created_by="node2-b")
    assert len(nxt) == 1
    slot = conn.execute(f"SELECT timetable_slot FROM {s}.queue WHERE id = %s", (nxt[0],)).fetchone()[0]
    assert slot == secs(1200)
    row = conn.execute(f"SELECT last_slot, last_done, clock FROM {s}.timetable WHERE job = 'tick'").fetchone()
    assert row[0] == secs(1200) and row[1] == secs(1260) and row[2] == "every 600s"


def test_a_daily_slot_is_today_once_the_clock_has_passed_it(tmp_path):
    jobs = fx.JOBS + '\n[jobs.daily]\nneeds = "processor"\nmemory_gb = 0.1\ndeadline_s = 60\nquery_timeout_s = 10\n' \
                     'priority = 51\ncommand = ["true"]\nat_utc = "03:30"\n'
    j, _ = fx.write(tmp_path, jobs=jobs)
    jt = reg.load(j)["daily"]
    day = dt.datetime(2026, 10, 18, tzinfo=dt.timezone.utc)
    assert q.slot_for(jt, day.replace(hour=3, minute=29)) == day.replace(hour=3, minute=30) - dt.timedelta(days=1)
    assert q.slot_for(jt, day.replace(hour=3, minute=30)) == day.replace(hour=3, minute=30)
    assert q.slot_for(jt, day.replace(hour=23)) == day.replace(hour=3, minute=30)


def test_a_standing_service_is_topped_up_to_its_wanted_count(conn, s, tmp_path):
    jobs = fx.JOBS + '\n[jobs.app]\nneeds = "processor"\nmemory_gb = 0.1\ndeadline_s = 86400\nquery_timeout_s = 10\n' \
                     'priority = 52\ncommand = ["true"]\nwanted = 2\n'
    j, _ = fx.write(tmp_path, jobs=jobs)
    cat = reg.load(j)
    assert len(q.enqueue_standing(conn, s, cat, now=secs(0))) == 2
    assert q.enqueue_standing(conn, s, cat, now=secs(1)) == []
    c = q.claim(conn, s, "node2", ["app"], lease_s=60, now=secs(2))
    assert c["standing"]
    assert q.enqueue_standing(conn, s, cat, now=secs(3)) == [], "a leased copy counts"
    q.complete(conn, s, c["id"], c["token"], outcome="failed", detail="died", now=secs(4))
    assert len(q.enqueue_standing(conn, s, cat, now=secs(5))) == 1, "a dead copy is replaced"


def test_demands_count_pieces_left_and_the_most_urgent_class(conn, s, cat):
    q.enqueue(conn, s, "doc", pieces=["a", "b", "c", "d"], registry=cat, now=secs(0))
    q.enqueue(conn, s, "doc", cls="due", due_at=secs(900), not_before=secs(50), registry=cat, now=secs(1))
    q.enqueue(conn, s, "cpu", registry=cat, now=secs(2))
    c = q.claim(conn, s, "w", ["doc"], lease_s=600, now=secs(3))        # the four-piece one; the due one is held back
    assert c["pieces_total"] == 4
    p = q.next_piece(conn, s, c["id"], c["token"], "w", now=secs(4))
    q.finish_piece(conn, s, c["id"], c["token"], p["piece"], ok=True, seconds=2.0, now=secs(6))
    d = q.demands(conn, s, cat, now=secs(100))
    assert d["doc"].depth == 3 + 1 and d["doc"].cls == "due" and d["doc"].due_at == secs(900).timestamp()
    assert d["doc"].waiting_since == secs(1).timestamp()
    assert d["cpu"].depth == 1 and d["cpu"].item_seconds is None
    q.run_begin(conn, s, "r1", job="cpu", worker="w", box="node2", declared_mb=2048, now=secs(20))
    q.run_end(conn, s, "r1", outcome="ok", exit_code=0, peak_mb=3000, now=secs(80))
    d = q.demands(conn, s, cat, now=secs(100))
    assert d["cpu"].item_seconds == 60.0
    assert q.over_declared(conn, s) == [{"run_id": "r1", "job": "cpu", "peak_mb": 3000, "declared_mb": 2048}]


def test_swaps_are_recorded_and_load_times_measured(conn, s):
    q.upsert_card(conn, s, "node2", 0, reserved=True, reserved_why="carve-out")
    q.upsert_card(conn, s, "node2", 1, memory_total_gb=31.9)
    for n in (80.0, 100.0):
        q.record_swap(conn, s, "node2", 1, "load", "test", to_profile="text-reader", load_seconds=n, ok=True, by_worker="w")
    q.record_swap(conn, s, "node2", 1, "load", "test", to_profile="text-reader", load_seconds=999.0, ok=False)
    assert q.measured_load_seconds(conn, s) == {"text-reader": 90.0}
    q.upsert_card(conn, s, "node2", 1, profile="text-reader", port=8111, holder="doc")
    cs = {c["card"]: c for c in q.cards(conn, s, "node2")}
    assert cs[0]["reserved"] and cs[1]["profile"] == "text-reader" and cs[1]["holder"] == "doc"
    st = q.status(conn, s)
    assert st["cards"][0]["reserved"] and len(st["swaps"]) == 3


def test_a_twice_daily_slot_is_the_latest_time_passed_or_yesterdays_last(tmp_path):
    jobs = fx.JOBS + '\n[jobs.twice]\nneeds = "processor"\nmemory_gb = 0.1\ndeadline_s = 60\nquery_timeout_s = 10\n' \
                     'priority = 52\ncommand = ["true"]\nat_utc = ["20:00", "08:00"]\n'
    j, _ = fx.write(tmp_path, jobs=jobs)
    jt = reg.load(j)["twice"]
    day = dt.datetime(2026, 10, 18, tzinfo=dt.timezone.utc)
    assert q.slot_for(jt, day.replace(hour=7, minute=59)) == day.replace(hour=20) - dt.timedelta(days=1)
    assert q.slot_for(jt, day.replace(hour=8)) == day.replace(hour=8)
    assert q.slot_for(jt, day.replace(hour=19, minute=59)) == day.replace(hour=8)
    assert q.slot_for(jt, day.replace(hour=20)) == day.replace(hour=20)
    assert q.slot_for(jt, day.replace(hour=23, minute=59)) == day.replace(hour=20)


def test_a_handover_marks_the_timers_slot_served_so_the_queue_runs_the_next_one(conn, s, tmp_path):
    """Step 2.12 at the switch: the timer served today's slot; the queue
    must not run it again, and must run tomorrow's."""
    jobs = fx.JOBS + '\n[jobs.daily]\nneeds = "processor"\nmemory_gb = 0.1\ndeadline_s = 60\nquery_timeout_s = 10\n' \
                     'priority = 51\ncommand = ["true"]\nat_utc = "03:30"\n'
    j, _ = fx.write(tmp_path, jobs=jobs)
    cat = reg.load(j)
    day = dt.datetime(2026, 10, 18, tzinfo=dt.timezone.utc)
    slot = q.handover(conn, s, "daily", registry=cat, now=day.replace(hour=9), by="installer: x.timer superseded")
    assert slot == day.replace(hour=3, minute=30)
    assert q.enqueue_due(conn, s, cat, now=day.replace(hour=9, minute=1), created_by="node2") == [], "the timer served today's"
    assert q.enqueue_due(conn, s, cat, now=day.replace(hour=23), created_by="node2") == []
    nxt = q.enqueue_due(conn, s, cat, now=(day + dt.timedelta(days=1)).replace(hour=3, minute=30), created_by="node2")
    assert len(nxt) == 1, "tomorrow's slot is the queue's"
    assert q.handover(conn, s, "daily", registry=cat, now=day.replace(hour=9)) == day.replace(hour=3, minute=30)
    row = conn.execute(f"SELECT last_slot FROM {s}.timetable WHERE job = 'daily'").fetchone()
    assert row[0] == (day + dt.timedelta(days=1)).replace(hour=3, minute=30), "a handover never moves the clock back"
    assert q.handover(conn, s, "doc", registry=cat, now=day) is None, "a job with no timetable has no clock to hand over"


DAILY = ('[jobs.daily]\nneeds = "processor"\nmemory_gb = 0.1\ndeadline_s = 60\nquery_timeout_s = 10\n'
         'priority = 50\ncommand = ["true"]\n')


def daily(tmp_path, at, name="jobs.toml", enabled=True):
    sub = tmp_path / name.replace(".", "_")
    sub.mkdir(exist_ok=True)
    j, _ = fx.write(sub, jobs=fx.JOBS + "\n" + DAILY + f"at_utc = {at}\n" + ("" if enabled else "enabled = false\n"))
    return reg.load(j)


def test_a_job_new_to_the_catalogue_takes_its_next_slot_not_yesterdays(conn, s, tmp_path):
    """Card the-scheduler-s-worker-runs-the-main-checkout-…, finding 1: a daily
    job appearing at 22:30, before nothing of today's 03:30 is owed, used to be
    owed yesterday's 03:30 and ran at once (procurement-1, 22 October). Now
    the slot due when it appears is marked served and the first run is the
    next 03:30; nothing runs between."""
    cat = daily(tmp_path, '"03:30"')
    day = dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc)
    lines = []
    assert q.enqueue_due(conn, s, cat, now=day.replace(hour=2), created_by="node2", log=lines.append) == []
    assert len(lines) == 1 and "daily new to the clock" in lines[0] and "first run 2026-10-22 03:30" in lines[0], lines
    row = conn.execute(f"SELECT last_slot, clock FROM {s}.timetable WHERE job = 'daily'").fetchone()
    assert row == (day.replace(hour=3, minute=30) - dt.timedelta(days=1), "at 03:30")
    assert q.enqueue_due(conn, s, cat, now=day.replace(hour=3, minute=29), created_by="node2-b", log=lines.append) == []
    assert len(lines) == 1, "marked once, by whichever worker noticed first"
    first = q.enqueue_due(conn, s, cat, now=day.replace(hour=3, minute=31), created_by="node2")
    assert len(first) == 1
    assert conn.execute(f"SELECT timetable_slot FROM {s}.queue WHERE id = %s", (first[0],)).fetchone()[0] == \
        day.replace(hour=3, minute=30)


def test_a_job_appearing_after_todays_time_waits_for_tomorrows(conn, s, tmp_path):
    cat = daily(tmp_path, '"03:30"')
    day = dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc)
    assert q.enqueue_due(conn, s, cat, now=day.replace(hour=22, minute=30), created_by="node2") == []
    assert q.enqueue_due(conn, s, cat, now=day.replace(hour=23, minute=59), created_by="node2") == []
    assert len(q.enqueue_due(conn, s, cat, now=(day + dt.timedelta(days=1)).replace(hour=3, minute=30),
                             created_by="node2")) == 1


def test_a_job_whose_timetable_changed_takes_its_next_slot(conn, s, tmp_path):
    """A daily job moved from 03:30 to 20:00, read at 21:00: today's 20:00 was
    never served, but it is not owed; the first run under the new time is
    tomorrow's 20:00. Reordering the same times is not a change."""
    day = dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc)
    old = daily(tmp_path, '"03:30"', "old.toml")
    q.enqueue_due(conn, s, old, now=day.replace(hour=2), created_by="node2")
    qid = q.enqueue_due(conn, s, old, now=day.replace(hour=3, minute=30), created_by="node2")[0]
    c = q.claim(conn, s, "node2", ["daily"], lease_s=60, now=day.replace(hour=3, minute=31))
    assert c["id"] == qid
    q.complete(conn, s, qid, c["token"], outcome="ok", now=day.replace(hour=3, minute=32))
    new = daily(tmp_path, '"20:00"', "new.toml")
    lines = []
    assert q.enqueue_due(conn, s, new, now=day.replace(hour=21), created_by="node2", log=lines.append) == []
    assert len(lines) == 1 and "timetable changed from 'at 03:30'" in lines[0], lines
    assert q.enqueue_due(conn, s, new, now=day.replace(hour=23), created_by="node2") == []
    assert len(q.enqueue_due(conn, s, new, now=(day + dt.timedelta(days=1)).replace(hour=20), created_by="node2")) == 1
    two = daily(tmp_path, '["20:00", "08:00"]', "two.toml")
    q.enqueue_due(conn, s, two, now=(day + dt.timedelta(days=1)).replace(hour=21), created_by="node2")
    same = daily(tmp_path, '["08:00", "20:00"]', "same.toml")
    lines = []
    q.enqueue_due(conn, s, same, now=(day + dt.timedelta(days=1)).replace(hour=21), created_by="node2", log=lines.append)
    assert lines == [], "the same times in another order are the same timetable"


def test_a_job_enabled_after_entering_disabled_takes_its_next_slot(conn, s, tmp_path):
    """The local-elections jobs entered disabled and were enabled after the
    adopt run: enabling is when the clock first sees them, so they too wait
    for the next slot."""
    day = dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc)
    off = daily(tmp_path, '"03:30"', "off.toml", enabled=False)
    assert q.enqueue_due(conn, s, off, now=day.replace(hour=2), created_by="node2") == []
    assert conn.execute(f"SELECT count(*) FROM {s}.timetable WHERE job = 'daily'").fetchone()[0] == 0
    on = daily(tmp_path, '"03:30"', "on.toml")
    assert q.enqueue_due(conn, s, on, now=day.replace(hour=9), created_by="node2") == []
    assert len(q.enqueue_due(conn, s, on, now=(day + dt.timedelta(days=1)).replace(hour=3, minute=30),
                             created_by="node2")) == 1


def test_a_row_from_before_the_clock_was_recorded_is_served_as_before(conn, s, tmp_path):
    """The deploy: the live rows have no `clock`. Each adopts its timetable
    and a slot it is owed still runs; none is skipped by the upgrade."""
    cat = daily(tmp_path, '"03:30"')
    day = dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc)
    conn.execute(f"INSERT INTO {s}.timetable (job, last_slot, last_by) VALUES ('daily', %s, 'node2')",
                 (day.replace(hour=3, minute=30) - dt.timedelta(days=1),))
    assert len(q.enqueue_due(conn, s, cat, now=day.replace(hour=9), created_by="node2")) == 1
    assert conn.execute(f"SELECT clock FROM {s}.timetable WHERE job = 'daily'").fetchone()[0] == "at 03:30"


def test_a_job_with_no_timetable_is_untouched_by_the_clock(conn, s, cat):
    assert q.enqueue_due(conn, s, cat, now=T0, created_by="node2") == []
    assert conn.execute(f"SELECT count(*) FROM {s}.timetable").fetchone()[0] == 0


def test_pieces_from_a_command_then_rows_and_the_status_fields_against_the_tables(conn, s, cat, tmp_path):
    """31 October: a pieced row queued with no pieces (its type names a
    pieces_command) takes them at the claim under the fence; a finished
    row's `then` queues one row each, one in flight, and writes the lines
    into its detail; `status` reads the source, the in-flight figure, the
    running pieces and the then rows."""
    import dataclasses
    cat["cpu"] = dataclasses.replace(cat["cpu"], then=("doc", "emb"))
    with pytest.raises(ValueError, match="names no pieces_command"):
        q.enqueue(conn, s, "doc", registry={**cat, "doc": dataclasses.replace(cat["doc"], pieces_command=())}, now=secs(0))
    load = q.enqueue(conn, s, "cpu", registry=cat, now=secs(0))
    c = q.claim(conn, s, "w1", ALL, lease_s=60, now=secs(1))
    assert c["pieces_source"] is None
    assert q.complete(conn, s, load, c["token"], outcome="ok", detail="done", now=secs(2))
    doc, emb = load + 1, load + 2
    assert q.then_rows(conn, s, load, cat["cpu"], registry=cat, now=secs(3)) == [f"then: doc queued as row {doc}",
                                                                                f"then: emb queued as row {emb}"]
    row = conn.execute(f"SELECT detail, state FROM {s}.queue WHERE id = %s", (load,)).fetchone()
    assert row == (f"done | then: doc queued as row {doc} | then: emb queued as row {emb}", "done")
    new = conn.execute(f"SELECT job, cls, pieces_total, pieces_source, then_of, created_by FROM {s}.queue WHERE id = %s", (doc,)).fetchone()
    assert new == ("doc", "whenever", 0, "command", load, f"then of row {load}")
    # a second finish while both are still queued: one in flight each, nothing new
    load2 = q.enqueue(conn, s, "cpu", registry=cat, now=secs(4))
    c2 = q.claim(conn, s, "w1", ["cpu"], lease_s=60, now=secs(5))
    q.complete(conn, s, load2, c2["token"], outcome="ok", now=secs(6))
    assert q.then_rows(conn, s, load2, cat["cpu"], registry=cat, now=secs(7)) == [f"then: doc already queued as row {doc}",
                                                                                 f"then: emb already queued as row {emb}"]
    assert conn.execute(f"SELECT count(*) FROM {s}.queue").fetchone()[0] == 4
    # the reader is claimed with no pieces and takes them from its command's lines, under the fence
    cd = q.claim(conn, s, "w1", ["doc"], lease_s=60, now=secs(8))
    assert cd["id"] == doc and cd["pieces_total"] == 0 and cd["pieces_source"] == "command"
    assert q.add_pieces(conn, s, doc, uuid.uuid4(), ["x"], now=secs(9)) == -1, "not this worker's lease"
    assert q.add_pieces(conn, s, doc, cd["token"], ["k1", "k2", "k3"], now=secs(9)) == 3
    assert q.add_pieces(conn, s, doc, cd["token"], ["again"], now=secs(9)) == 0, "a row with pieces keeps them"
    assert q.pieces_left(conn, s, doc) == {"todo": 3, "running": 0, "done": 0, "failed": 0}
    assert conn.execute(f"SELECT pieces_total, pieces_source FROM {s}.queue WHERE id = %s", (doc,)).fetchone() == (3, "command")
    q.set_in_flight(conn, s, doc, 2)
    q.next_piece(conn, s, doc, cd["token"], "w1", now=secs(10))
    q.next_piece(conn, s, doc, cd["token"], "w1", now=secs(10))
    assert [p["key"] for p in q.pieces_running(conn, s, doc)] == ["k1", "k2"]
    st = q.status(conn, s)
    by = {r["id"]: r for r in st["recent"]}
    assert (by[doc]["pieces_source"], by[doc]["in_flight"], by[doc]["pieces_running"], by[doc]["then_of"]) == ("command", 2, 2, load)
    assert by[load]["then_rows"] == [doc, emb] and by[emb]["then_rows"] == [] and by[emb]["pieces_source"] is None
    # a then naming a job the catalogue lacks is a line, not an exception
    gone = dataclasses.replace(cat["cpu"], then=("nowhere",))
    assert q.then_rows(conn, s, load2, gone, registry=cat, now=secs(11)) == ["then: nowhere is not in the catalogue; not queued"]
