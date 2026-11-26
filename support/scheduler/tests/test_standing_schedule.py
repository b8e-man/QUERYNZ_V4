"""The standing schedule (Arthur, 26 November 2026: "the answer is always a scheduled configuration change based on
document profiles"): a box stands one standing server at a time, the one jobs.toml [standing] names for the hour; at
an edge the card manager drains the outgoing server's views, stops its unit until the cards release it, starts the due
one and reads its model back, each a swap-ledger line."""
from __future__ import annotations

import datetime as dt
import threading

import pytest

from support.scheduler import cards, night
from support.scheduler import registry as reg
from support.scheduler.tests.test_cards import FakeConn

UTC = dt.timezone.utc


def nz(h, m=0):
    """A moment at NZDT (UTC+13) hour h on 26-27 November 2026, as UTC."""
    return dt.datetime(2026, 11, 26, h, m, tzinfo=dt.timezone(dt.timedelta(hours=13))).astimezone(UTC)


SCHEDULE = night.Schedule(default="dense", shifts=(night.Shift(box="node2", start="22:00", end="05:45", profile="flash"),))


def test_the_shipped_schedule_is_the_27b_by_day_and_flash_next_on_node2_by_night():
    s = reg.shipped_standing_schedule()
    assert s.default == "qwen38-27b"
    assert [(x.box, x.start, x.end, x.profile) for x in s.shifts] == [("node2", "22:00", "05:45", "flash-next")]
    assert s.due("node2", nz(23)) == s.due("node2", nz(3)) == "flash-next"
    assert s.due("node2", nz(12)) == s.due("node2", nz(5, 45)) == "qwen38-27b"
    assert s.due("node1", nz(23)) == "qwen38-27b", "node1 stands the 27B at every hour"


def test_the_check_refuses_a_schedule_naming_no_standing_server(tmp_path):
    import pathlib
    here = pathlib.Path(reg.__file__).resolve().parent
    jobs = (here / "jobs.toml").read_text(encoding="utf-8")
    jp = tmp_path / "jobs.toml"
    real = reg.shipped_standing_schedule
    jp.write_text(jobs.replace('profile = "flash-next"\n\n# Step 2.9', 'profile = "text-reader"\n\n# Step 2.9'))
    assert any("standing: 'text-reader' is not a standing server" in p for p in
               _problems_with(real, jp, here / "profiles.toml"))
    jp.write_text(jobs.replace('start_local = "22:00"\nend_local = "05:45"\nprofile = "flash-next"',
                               'start_local = "22h"\nend_local = "05:45"\nprofile = "flash-next"'))
    assert any("standing: the shift for node2" in p for p in _problems_with(real, jp, here / "profiles.toml"))


def _problems_with(real, jp, pp):
    saved = reg.standing_schedule
    reg.standing_schedule = real
    try:
        return reg.problems(jp, pp)
    finally:
        reg.standing_schedule = saved


# ── the swap ─────────────────────────────────────────────────────────────────

class P:
    def __init__(self, name, model, unit, cards=2, memory_gb=27.0):
        self.name, self.model, self.unit, self.port, self.cards = name, model, unit, 8060, cards
        self.binary, self.standing, self.on, self.memory_gb, self.slots = "radiance", True, None, memory_gb, 16


class V:
    def __init__(self, name, on):
        self.name, self.on, self.standing, self.binary = name, on, False, None


class J:
    def __init__(self, name, profile):
        self.name, self.profile = name, profile


class R:
    def __init__(self, jt):
        self.jt = jt


class W:
    def __init__(self):
        self.conn, self.schema, self.box, self.name = FakeConn(), "s", "node2", "node2"
        self.profiles = {"dense": P("dense", "qwen38-27b", "qv4-radiance.service"),
                         "flash": P("flash", "qwen4exp", "qv4-radiance-flash.service"),
                         "news": V("news", "dense"), "text": V("text", "flash")}
        self.registry = {"qv4-news-read": J("qv4-news-read", "news"), "qv4-hansard-read": J("qv4-hansard-read", "text")}
        self.profile = {"programs": {"radiance": "/u/qv4-radiance.service"},
                        "cards": [{"index": 0, "memory_total_gb": 31.9, "memory_used_gb": 31.0},
                                  {"index": 1, "memory_total_gb": 31.9, "memory_used_gb": 31.0}]}
        self.running, self.lock, self.logs = {}, threading.Lock(), []
        self.log = self.logs.append


@pytest.fixture
def kit():
    serving = {"unit": "qv4-radiance.service"}
    models = {"qv4-radiance.service": "qwen38-27b", "qv4-radiance-flash.service": "qwen4exp"}
    calls = []

    def ask(port):
        u = serving["unit"]
        return {"port": port, "served": models.get(u), "free": -1, "total": 0, "healthy": u is not None}

    def systemctl(verb, unit, timeout=None):
        calls.append((verb, unit))
        if verb == "stop" and serving["unit"] == unit:
            serving["unit"] = None
        elif verb in ("start", "restart"):
            serving["unit"] = unit
        return 0

    m = cards.Manager(ask=ask, models_dir="/m", reservations=[], window=None, schedule=SCHEDULE, systemctl=systemctl,
                      read_cards=lambda: None, clock=lambda: 0.0, sleep=lambda s: None, active_seconds=lambda u: 17.0)
    w = W()
    return m, w, serving, calls


def swaps(w):
    return [p for s, p in w.conn.sql if "INSERT INTO s.swaps" in s]


def test_a_worker_starting_stands_the_server_that_answers(kit):
    m, w, serving, calls = kit
    m.start(w)
    assert m.standing_now == "dense" and [p.name for p in m.standing_profiles(w)] == ["dense"]
    serving["unit"] = "qv4-radiance-flash.service"
    m2 = cards.Manager(ask=m.ask, models_dir="/m", reservations=[], window=None, schedule=SCHEDULE,
                       systemctl=m.systemctl, read_cards=lambda: None, clock=lambda: 0.0, sleep=lambda s: None)
    m2.log = w.log
    m2.standing_recover(w, nz(12))
    assert m2.standing_now == "flash", "what answers decides, not the clock: the shift tick swaps it back"


def test_by_day_nothing_moves(kit):
    m, w, serving, calls = kit
    m.start(w)
    m.shift_tick(w, nz(14), {})
    assert calls == [] and m.shift_state is None


def test_at_the_shift_the_views_drain_first_then_the_unit_is_swapped_and_recorded(kit):
    m, w, serving, calls = kit
    m.start(w)
    w.running = {1: R(w.registry["qv4-news-read"])}
    m.shift_tick(w, nz(22, 1), {})
    assert m.shift_state == "draining" and calls == [], "a news piece in flight here: nothing is stopped"
    drained = [p for s, p in w.conn.sql if "INTO s.cards" in s and "draining" in s]
    assert drained, "the outgoing server's cards drain, so the running row starts no new piece"
    m.mark_standing(w)
    assert m.shift_state == "draining", "mark_standing never undoes the drain"
    w.running = {}
    m.shift_tick(w, nz(22, 2), {})
    assert calls == [("stop", "qv4-radiance.service"), ("restart", "qv4-radiance-flash.service")]
    assert m.standing_now == "flash" and m.shift_state is None
    kinds = [(s[3], s[4], s[5]) for s in swaps(w)]
    assert ("stop", "dense", None) in kinds and ("load", "dense", "flash") in kinds
    assert [p.name for p in m.standing_profiles(w)] == ["flash"]
    m.shift_tick(w, nz(5, 45), {})
    assert calls[-2:] == [("stop", "qv4-radiance-flash.service"), ("restart", "qv4-radiance.service")]
    assert m.standing_now == "dense"


def test_another_view_running_does_not_hold_the_drain(kit):
    m, w, serving, calls = kit
    m.start(w)
    w.running = {1: R(w.registry["qv4-hansard-read"])}      # a view on the other server: not the outgoing one's
    m.shift_tick(w, nz(22, 1), {})
    assert m.standing_now == "flash"


def test_a_start_that_does_not_answer_is_retried_and_the_cards_stay_held(kit):
    m, w, serving, calls = kit
    m.start(w)
    real = m.systemctl

    def broken(verb, unit, timeout=None):
        if verb == "restart":
            calls.append((verb, unit))
            return 1
        return real(verb, unit)
    m.systemctl = broken
    m._wait_standing = lambda prof, timeout=0: None
    m.shift_tick(w, nz(22, 1), {})
    assert m.shift_state == "starting" and m.standing_now == "dense"
    assert any(s[3] == "load" and s[11] is False for s in swaps(w)), "the failed start is a swap-ledger line"
    m.shift_tick(w, nz(22, 2), {})
    assert sum(1 for c in calls if c[0] == "restart") == 1, "retried after two minutes, not every tick"
