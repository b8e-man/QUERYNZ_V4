"""Ruling 129: the standing server's night window. Between 22:00 and 05:45
NZDT, when page-reader work is queued and no text-reader or review piece is
running or leased, the card manager stops `qv4-radiance`, holds one card for
the frozen product's OCR server, and leaves the other cold for the planner
to load the page reader on; when the page queue is empty, a text piece is
due, or the window closes, the page reader drains, the unit is started again
and the cards are marked standing. Outside the window nothing is touched.

Everything is faked: systemctl, the card memory, the ports, the clock. No
model is called and no second passes."""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
import pathlib
import threading

import pytest

from support.scheduler import cards, night, policy
from support.scheduler import registry as reg
from support.scheduler.tests.test_cards import FakeConn, FakeProc

UTC = dt.timezone.utc
NZDT = dt.timezone(dt.timedelta(hours=13))

PROFILES = """
[profiles.flash-next]
model = "qwen4exp"
binary = "radiance"
unit = "qv4-radiance.service"
port = 8060
cards = 2
weights = ["radiance/flash.rad"]
slots = 16
context = 16384
temperature = 0.0
max_tokens = 8192
memory_gb = 26.1
measured_geometry = "16384x16"
load_seconds = 21.6

[profiles.text-reader]
on = "flash-next"
model = "qwen4exp"
slots = 16
context = 16384
temperature = 0.0
max_tokens = 8192

[profiles.review]
on = "flash-next"
model = "qwen4exp"
slots = 16
context = 16384
temperature = 0.2
max_tokens = 6144

[profiles.page-reader]
model = "glm-ocr"
weights = ["glm.gguf", "mmproj.gguf"]
slots = 1
context = 32768
temperature = 0.0
max_tokens = 8000
memory_gb = 4.8
measured_geometry = "32768x1"
load_seconds = 30.0
"""

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

[night_window]
start_local = "22:00"
end_local = "05:45"
timezone = "Pacific/Auckland"
standing = "flash-next"
profile = "page-reader"
card = 1

[jobs.qv4-read]
needs = "model-profile"
profile = "text-reader"
memory_gb = 1.0
deadline_s = 900
query_timeout_s = 300
priority = 1
command = ["true"]
can_share = true

[jobs.qv4-judge]
needs = "model-profile"
profile = "review"
memory_gb = 1.0
deadline_s = 900
query_timeout_s = 300
priority = 2
command = ["true"]
can_share = true

[jobs.qv4-pages]
needs = "model-profile"
profile = "page-reader"
memory_gb = 1.5
deadline_s = 1800
query_timeout_s = 300
priority = 23
command = ["true"]
pieces = true
"""

CARD_KEYS = ("box", "card", "reserved", "reserved_why", "memory_total_gb", "memory_used_gb", "product", "profile", "port",
             "pid", "server_started_at", "holder", "holder_since", "draining", "slots", "slots_busy", "worker", "updated_at")


def nz(day: int, hh: int, mm: int = 0, month: int = 10) -> dt.datetime:
    """A moment on the NZDT clock, as the UTC moment the scheduler holds."""
    return dt.datetime(2026, month, day, hh, mm, tzinfo=NZDT).astimezone(UTC)


class NightConn(FakeConn):
    """The cards table kept from the manager's own upserts, so `held()` sees
    what the manager marked; the queue's rows set by the test."""
    def __init__(self):
        super().__init__()
        self.table: dict[int, dict] = {}
        self.queue_rows: list[tuple] = []
        self._last = ""

    def execute(self, sql, params=()):
        self._last = sql
        self.sql.append((sql, params))
        if sql.startswith("INSERT INTO s.cards"):
            cols = sql.split("(", 1)[1].split(")", 1)[0].split(", ")
            row = self.table.setdefault(params[1], {k: None for k in CARD_KEYS})
            row.update(dict(zip(cols, params)))
            row["reserved"] = bool(row["reserved"])
            row["draining"] = bool(row["draining"])
        return self

    def fetchall(self):
        if "FROM s.cards" in self._last:
            return [tuple(r[k] for k in CARD_KEYS) for _, r in sorted(self.table.items())]
        if "FROM s.queue" in self._last:
            return list(self.queue_rows)
        return []


class W:
    def __init__(self, jp, pp):
        self.conn, self.schema, self.box, self.name = NightConn(), "s", "node2", "node2"
        self.registry, self.profiles, self.rules = reg.load(jp), reg.profiles(pp), reg.queueing(jp)
        self.profile = {"programs": {"radiance": "/u/qv4-radiance.service", "qv4-llama-server-built": "/x/llama-server"},
                        "cards": [{"index": 0, "memory_total_gb": 31.9, "memory_used_gb": 29.3},
                                  {"index": 1, "memory_total_gb": 31.9, "memory_used_gb": 27.9}]}
        self.running, self.lock, self.logs, self.alarms = {}, threading.Lock(), [], []
        self.log = self.logs.append
        self.alarm = lambda title, body: self.alarms.append((title, body))
        self.alarm_after_s = 300

    def queue(self, *rows):
        """(job, state, cls, created_at, due_at, pieces left)."""
        self.conn.queue_rows = [(j, st, cls, created, due, left) for j, st, cls, created, due, left in rows]

    def run(self, job):
        class R:
            jt = self.registry[job]
        self.running[len(self.running) + 1] = R()


class Box:
    """The box as the fakes see it: the unit up or down, the page reader up
    or down, the card memory following both, a clock that moves only when
    read, and every systemctl call recorded."""
    def __init__(self):
        self.unit_up, self.page_up, self.fail_start, self.stop_rc = True, False, False, 0
        self.calls: list[tuple[str, str]] = []
        self.t = 1000.0

    def clock(self):
        self.t += 0.5
        return self.t

    def sleep(self, s):
        self.t += s

    def ask(self, port):
        if port == 8060:
            return {"port": port, "served": "qwen4exp" if self.unit_up else None, "free": -1, "total": 0, "healthy": self.unit_up}
        if port == 8111:
            return {"port": port, "served": "glm-ocr" if self.page_up else None, "free": 1, "total": 1, "healthy": self.page_up}
        return {"port": port, "served": None, "free": -1, "total": 0, "healthy": False}

    def systemctl(self, verb, unit):
        self.calls.append((verb, unit))
        if verb == "stop":
            if self.stop_rc:
                return self.stop_rc
            self.unit_up = False
        if verb == "start" and not self.fail_start:
            self.unit_up = True
        return 0

    def read_cards(self):
        base0, base1 = 3.2, 1.8                              # the frozen OCR server's share and the driver
        if self.unit_up:
            base0, base1 = base0 + 26.1, base1 + 26.1
        if self.page_up:
            base1 += 4.8
        return [{"index": 0, "product": "x", "memory_total_gb": 31.9, "memory_used_gb": round(base0, 1)},
                {"index": 1, "product": "x", "memory_total_gb": 31.9, "memory_used_gb": round(base1, 1)}]

    def popen(self, argv, **kw):
        p = FakeProc(argv, **kw)
        self.page_up = True
        self.procs.append(p)
        return p


@pytest.fixture
def kit(tmp_path, monkeypatch):
    (tmp_path / "jobs.toml").write_text(JOBS)
    (tmp_path / "profiles.toml").write_text(PROFILES)
    for wgt in ("glm.gguf", "mmproj.gguf"):
        (tmp_path / wgt).write_text("weights")
    monkeypatch.setattr(cards, "LOGS", str(tmp_path / "logs"))
    monkeypatch.setattr(cards.runs, "LEDGER", tmp_path / "runs.jsonl")
    box = Box()
    box.procs = []
    w = W(tmp_path / "jobs.toml", tmp_path / "profiles.toml")
    m = cards.Manager(popen=box.popen, ask=box.ask, models_dir=str(tmp_path), reservations=[], active_seconds=lambda u: 21.6,
                      window=reg.night_window(tmp_path / "jobs.toml"), systemctl=box.systemctl, read_cards=box.read_cards,
                      clock=box.clock, sleep=box.sleep, mark=str(tmp_path / "night.json"), inbox=str(tmp_path / "inbox"))
    m.start(w)
    return m, w, box


def swaps(w, action=None):
    out = [p for s, p in w.conn.sql if "INSERT INTO s.swaps" in s]
    return [p for p in out if p[3] == action] if action else out


def card(w, i):
    return w.conn.table[i]


def pages_queued(w, n=12):
    w.queue(("qv4-pages", "queued", "whenever", nz(30, 21, 0), None, n))


def opened(kit):
    """The window open at 22:00 with twelve pages queued: the unit stopped and the page reader loaded on card 1."""
    m, w, box = kit
    pages_queued(w)
    m.tick(w, nz(30, 22, 0))
    assert m.night_state == "page", w.logs
    return m, w, box


# ── the catalogue ────────────────────────────────────────────────────────────

def test_the_shipped_window_is_22_00_to_05_45_nzdt_for_the_page_reader_on_card_1():
    w = reg.night_window()
    # 30 October 2026: the start stands at 15:00 on Arthur's word for the page backlog; 22:00 again after (ruling 129)
    assert (w.start, w.end, w.timezone, w.standing, w.profile, w.card) == ("15:00", "05:45", "Pacific/Auckland", "flash-next",
                                                                            "page-reader", 1)
    assert reg.problems() == []
    assert reg.profiles()[w.profile].memory_gb == 4.8 and reg.profiles()[w.standing].load_seconds == 21.6


def test_the_window_opens_and_closes_by_the_local_clock_in_summer_and_winter():
    w = dataclasses.replace(reg.night_window(), start="22:00")     # the ruling's hours, whatever start the catalogue carries today
    assert not night.in_window(nz(30, 21, 59), w)
    assert night.in_window(nz(30, 22, 0), w)
    assert night.in_window(nz(31, 2, 0), w)
    assert night.in_window(nz(31, 5, 44), w)
    assert not night.in_window(nz(31, 5, 45), w)
    assert not night.in_window(nz(31, 12, 0), w)
    # July is NZST (UTC+12): 22:00 local is 10:00 UTC, and the window still opens at 22:00 on the wall clock
    july = dt.datetime(2026, 7, 15, 10, 0, tzinfo=UTC)
    assert night.in_window(july, w) and not night.in_window(july - dt.timedelta(minutes=1), w)
    assert night.closes_at(nz(30, 23, 0), w) == nz(31, 5, 45)
    assert night.opens_at(nz(30, 12, 0), w) == nz(30, 22, 0)


def test_the_check_refuses_a_window_that_cannot_work(tmp_path):
    jp, pp = tmp_path / "jobs.toml", tmp_path / "profiles.toml"
    pp.write_text(PROFILES)
    jp.write_text(JOBS)
    assert reg.problems(jp, pp) == []
    jp.write_text(JOBS.replace('start_local = "22:00"', 'start_local = "22h"'))
    assert any("start_local" in p for p in reg.problems(jp, pp))
    jp.write_text(JOBS.replace('timezone = "Pacific/Auckland"', 'timezone = "Pacific/Nowhere"'))
    assert any("timezone" in p for p in reg.problems(jp, pp))
    jp.write_text(JOBS.replace('standing = "flash-next"', 'standing = "page-reader"'))
    assert any("standing" in p for p in reg.problems(jp, pp))
    jp.write_text(JOBS.replace('profile = "page-reader"\ncard = 1', 'profile = "text-reader"\ncard = 1'))
    assert any("night_window: profile" in p for p in reg.problems(jp, pp))
    jp.write_text(JOBS.replace('end_local = "05:45"', 'end_local = "22:00"'))
    assert any("never opens" in p for p in reg.problems(jp, pp))
    jp.write_text(JOBS.split("[night_window]")[0] + "[jobs.qv4-read]" + JOBS.split("[jobs.qv4-read]")[1])
    assert reg.night_window(jp) is None and reg.problems(jp, pp) == []


# ── the window by the clock ──────────────────────────────────────────────────

def test_outside_the_window_the_standing_server_is_never_stopped_or_planned(kit):
    m, w, box = kit
    pages_queued(w, 50)
    for when in (nz(30, 21, 59), nz(30, 12, 0), nz(31, 5, 45), nz(31, 6, 15)):
        m.tick(w, when)
    assert box.calls == [] and box.procs == [] and m.night_state == "standing"
    assert card(w, 0)["profile"] == card(w, 1)["profile"] == "flash-next"
    assert not swaps(w, "stop") and not swaps(w, "failed")


def test_at_22_00_the_unit_is_stopped_and_the_page_reader_loads_on_card_1(kit):
    m, w, box = opened(kit)
    assert ("stop", "qv4-radiance.service") in box.calls and ("start", "qv4-radiance.service") not in box.calls
    stops = swaps(w, "stop")
    assert sorted(s[2] for s in stops) == [0, 1]
    assert all(s[4] == "flash-next" and s[11] is True and s[9] > 0 and "ruling 129" in s[7] and "12 page piece" in s[7] for s in stops)
    assert card(w, 0)["reserved"] and "OCR server" in card(w, 0)["reserved_why"] and card(w, 0)["profile"] is None
    assert card(w, 1)["profile"] == "page-reader" and card(w, 1)["port"] == 8111 and not card(w, 1)["reserved"]
    assert len(box.procs) == 1 and box.procs[0].kw["env"]["HIP_VISIBLE_DEVICES"] == "1"
    assert swaps(w, "load")[-1][5] == "page-reader" and swaps(w, "load")[-1][2] == 1
    mark = json.loads(pathlib.Path(m.mark).read_text())
    assert mark["unit"] == "qv4-radiance.service" and mark["page_card"] == 1 and mark["hold_cards"] == [0]
    # the next ticks inside the window change nothing: the read-back does not re-mark the cards it does not hold
    m.tick(w, nz(30, 23, 0))
    assert card(w, 1)["profile"] == "page-reader" and card(w, 0)["reserved"] and len(box.procs) == 1


def test_at_05_45_the_window_closes_with_pages_still_queued(kit):
    m, w, box = opened(kit)
    m.tick(w, nz(31, 5, 44))
    assert m.night_state == "page" and ("start", "qv4-radiance.service") not in box.calls
    m.tick(w, nz(31, 5, 45))
    assert m.night_state == "standing"
    assert box.calls[-2:] == [("reset-failed", "qv4-radiance.service"), ("start", "qv4-radiance.service")]
    assert box.procs[0].signals, "the page reader was unloaded before the unit started"
    assert swaps(w, "unload")[-1][4] == "page-reader"
    starts = swaps(w, "start")
    assert sorted(s[2] for s in starts) == [0, 1]
    assert all(s[5] == "flash-next" and s[10] == "qwen4exp" and s[11] is True and s[9] > 0 and "05:45" in s[7] for s in starts)
    assert card(w, 0)["profile"] == card(w, 1)["profile"] == "flash-next" and not card(w, 0)["reserved"]
    assert card(w, 0)["port"] == card(w, 1)["port"] == 8060
    assert not os.path.exists(m.mark) and m.servers == {}
    n = len(swaps(w))
    m.tick(w, nz(31, 5, 50))
    assert len(swaps(w)) == n, "standing as today: the read-back records nothing more"


def test_an_empty_page_queue_closes_the_window_early_and_no_new_stop_follows_for_a_rest(kit):
    m, w, box = opened(kit)
    w.queue()
    m.tick(w, nz(30, 23, 0))
    assert m.night_state == "standing" and "page queue is empty" in swaps(w, "start")[-1][7]
    pages_queued(w, 3)
    m.tick(w, nz(30, 23, 5))
    assert m.night_state == "standing" and len(swaps(w, "stop")) == 2, "a row back within the rest is not a new night"
    m.tick(w, nz(30, 23, 20))
    assert m.night_state == "page" and len(swaps(w, "stop")) == 4


# ── what blocks the stop ─────────────────────────────────────────────────────

def test_a_text_piece_in_flight_blocks_the_stop(kit):
    m, w, box = kit
    pages_queued(w)
    w.run("qv4-read")
    m.tick(w, nz(30, 22, 0))
    assert box.calls == [] and m.night_state == "standing"
    assert any("qv4-read is running here" in l and "stays up" in l for l in w.logs)
    w.running.clear()
    w.queue(("qv4-pages", "queued", "whenever", nz(30, 21, 0), None, 12),
            ("qv4-judge", "leased", "whenever", nz(30, 21, 30), None, 1))
    m.tick(w, nz(30, 22, 5))
    assert box.calls == [] and m.night_state == "standing", "a leased review row blocks it too"
    pages_queued(w)
    m.tick(w, nz(30, 22, 10))
    assert m.night_state == "page" and ("stop", "qv4-radiance.service") in box.calls


def test_a_due_text_piece_closes_the_window_and_the_page_reader_drains_first(kit):
    m, w, box = opened(kit)
    w.run("qv4-pages")
    w.queue(("qv4-pages", "leased", "whenever", nz(30, 21, 0), None, 9),
            ("qv4-read", "queued", "due", nz(30, 23, 0), nz(31, 0, 30), 1))
    m.tick(w, nz(30, 23, 10))
    assert m.night_state == "closing" and ("start", "qv4-radiance.service") not in box.calls
    assert card(w, 1)["draining"] is True and not box.procs[0].signals, "draining, not killing"
    assert any("qv4-read is due" in l for l in w.logs)
    m.tick(w, nz(30, 23, 11))
    assert card(w, 1)["draining"] is True and ("start", "qv4-radiance.service") not in box.calls
    w.running.clear()                       # the piece finished and the row went back
    m.tick(w, nz(30, 23, 12))
    assert m.night_state == "standing" and box.procs[0].signals and swaps(w, "start")
    assert "qv4-read is due" in swaps(w, "start")[-1][7]


def test_a_bulk_whenever_text_queue_does_not_close_the_window(kit):
    m, w, box = opened(kit)
    w.queue(("qv4-pages", "queued", "whenever", nz(30, 21, 0), None, 12),
            ("qv4-read", "queued", "whenever", nz(30, 23, 0), None, 400))
    m.tick(w, nz(30, 23, 10))
    assert m.night_state == "page" and ("start", "qv4-radiance.service") not in box.calls


# ── the frozen product's OCR server ──────────────────────────────────────────

def test_the_ocr_servers_card_is_never_taken(kit):
    m, w, box = kit
    pages_queued(w, 500)                    # bulk: rule 9 would take every free card it could see
    for minute in range(0, 60, 5):
        m.tick(w, nz(30, 22, minute))
    assert m.night_state == "page"
    assert all(p.kw["env"]["HIP_VISIBLE_DEVICES"] == "1" for p in box.procs) and len(box.procs) == 1
    assert card(w, 0)["reserved"] and card(w, 0)["profile"] is None and card(w, 0)["port"] is None
    held = {h.card: h for h in m.held(w, nz(30, 22, 30).timestamp())}
    assert held["node2:0"].reserved and not held["node2:1"].reserved
    assert not any("vision-ocr" in u or "8032" in u for _, u in box.calls)
    # the measured release: the cards' memory fell to the OCR server's share before anything was loaded
    assert all(s[9] >= 0 and "released qwen4exp" in s[12] for s in swaps(w, "stop"))


def test_a_stop_that_does_not_release_the_cards_is_a_failed_swap_and_the_unit_is_started_again(kit):
    m, w, box = kit
    box.stop_rc = 5
    pages_queued(w)
    m.tick(w, nz(30, 22, 0))
    assert m.night_state == "standing" and box.procs == []
    assert [s[12] for s in swaps(w, "failed")] == ["systemctl stop returned 5"] * 2
    assert ("start", "qv4-radiance.service") in box.calls
    assert card(w, 0)["profile"] == "flash-next", "the read-back marked the cards standing again"


# ── the restart ──────────────────────────────────────────────────────────────

def test_a_start_that_fails_is_alarmed_noted_and_retried_each_tick(kit):
    m, w, box = opened(kit)
    box.fail_start = True
    w.queue()
    m.tick(w, nz(30, 23, 0))
    assert m.night_state == "restarting"
    fails = swaps(w, "failed")
    assert len(fails) == 2 and all(s[5] == "flash-next" and s[9] >= cards.START_TIMEOUT_S and "not answering" in s[12] for s in fails)
    assert card(w, 0)["reserved"] and "did not start again" in card(w, 0)["reserved_why"]
    assert len(w.alarms) == 1 and "did not start" in w.alarms[0][0]
    notes = list(pathlib.Path(m.inbox).iterdir())
    assert len(notes) == 1 and "qv4-radiance" in notes[0].name
    text = notes[0].read_text()
    assert text.count("# qv4-radiance.service did not start") == 1 and "systemctl --user status qv4-radiance.service" in text
    starts_before = box.calls.count(("start", "qv4-radiance.service"))
    m.tick(w, nz(30, 23, 6))
    assert box.calls.count(("start", "qv4-radiance.service")) == starts_before + 1, "tried again"
    assert len(w.alarms) == 1 and notes[0].read_text().count("# qv4-radiance.service") == 1, "one alarm, one note per episode"
    assert len(swaps(w, "failed")) == 4
    box.fail_start = False
    m.tick(w, nz(30, 23, 12))
    assert m.night_state == "standing" and len(swaps(w, "start")) == 2
    assert card(w, 0)["profile"] == card(w, 1)["profile"] == "flash-next" and not card(w, 0)["reserved"]
    assert not os.path.exists(m.mark)


def test_a_unit_that_comes_back_on_its_own_ends_the_episode(kit):
    m, w, box = opened(kit)
    box.fail_start = True
    w.queue()
    m.tick(w, nz(30, 23, 0))
    assert m.night_state == "restarting"
    box.unit_up = True                      # systemd's own Restart=, or Arthur
    m.tick(w, nz(30, 23, 6))
    assert m.night_state == "standing" and card(w, 1)["profile"] == "flash-next" and not card(w, 0)["reserved"]
    last = swaps(w)[-1]
    assert last[3] == "start" and last[5] == "flash-next" and last[10] == "qwen4exp" and last[11] is True
    assert len(w.alarms) == 1 and not os.path.exists(m.mark)


def test_a_worker_restarted_mid_window_starts_the_unit_again(kit, tmp_path):
    m, w, box = opened(kit)
    assert os.path.exists(m.mark)
    w2 = W(tmp_path / "jobs.toml", tmp_path / "profiles.toml")
    box.page_up = False                     # the old worker's child went with it
    m2 = cards.Manager(popen=box.popen, ask=box.ask, models_dir=str(tmp_path), reservations=[], active_seconds=lambda u: 21.6,
                       window=m.window, systemctl=box.systemctl, read_cards=box.read_cards, clock=box.clock, sleep=box.sleep,
                       mark=m.mark, inbox=m.inbox)
    m2.start(w2)
    assert m2.night_state == "closing" and "restarted" in m2.night_reason
    pages_queued(w2)
    m2.tick(w2, nz(30, 23, 30))
    assert m2.night_state == "standing" and ("start", "qv4-radiance.service") in box.calls
    assert not os.path.exists(m.mark) and "restarted" in swaps(w2, "start")[-1][7]


def test_a_load_of_the_standing_profile_is_still_never_acted_on_and_its_cards_never_planned(kit):
    m, w, box = kit
    m.tick(w, nz(30, 12, 0))
    held = m.held(w, nz(30, 12, 0).timestamp())
    assert all(h.reserved for h in held)
    d, _ = policy.plan(now=0.0, held=held, queues={"qv4-pages": 50}, registry=w.registry, profiles=w.profiles, rules=w.rules)
    assert all(x.action == policy.KEEP for x in d)
    m.apply(w, policy.Decision("node2:1", policy.LOAD, "qv4-read", "rule 6", "flash-next"), 0.0)
    assert box.procs == []
