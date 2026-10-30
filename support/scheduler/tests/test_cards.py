"""The card manager acts on the planner's decisions reversibly and never on
a reserved card: a load starts the estate's own server with the profile's
derived geometry, reads back the model it serves and refuses a wrong one, a
busy port is refused, a swap is in the ledger before and after, and a
worker's stop unloads what it loaded. Everything injected; no card here."""
from __future__ import annotations

import dataclasses
import os
import subprocess

import pytest

from support.scheduler import cards, policy
from support.scheduler import registry as reg
from support.scheduler.tests import fixtures as fx


class FakeProc:
    def __init__(self, argv, **kw):
        self.argv, self.kw, self.returncode, self.pid = argv, kw, None, 4242
        self.signals = []

    def poll(self):
        return self.returncode

    def send_signal(self, s):
        self.signals.append(s)
        self.returncode = -int(s)

    def wait(self, timeout=None):
        if self.returncode is None:
            raise subprocess.TimeoutExpired("x", timeout)
        return self.returncode


class FakeConn:
    """Enough of psycopg for queue.upsert_card / record_swap / cards."""
    def __init__(self):
        self.sql = []
        self.rows = {}

    def transaction(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        self.sql.append((sql, params))
        return self

    def fetchone(self):
        return (1,)

    def fetchall(self):
        return self.rows.get("all", [])


class FakeWorker:
    def __init__(self, tmp_path, profiles, registry, rules):
        self.conn, self.schema, self.box, self.name = FakeConn(), "s", "n", "w"
        self.profiles, self.registry, self.rules = profiles, registry, rules
        self.profile = {"programs": {"qv4-llama-server": str(tmp_path / "llama-server"), "llama-server": None},
                        "cards": [{"index": 9, "memory_total_gb": 31.9, "memory_used_gb": 26.0}, {"index": 1, "memory_total_gb": 31.9, "memory_used_gb": 1.8}]}
        self.running = {}
        import threading
        self.lock = threading.Lock()
        self.logs = []
        self.log = self.logs.append


@pytest.fixture
def kit(tmp_path, monkeypatch):
    registry, profiles, rules = fx.catalogue(tmp_path)
    (tmp_path / "llama-server").write_text("#!/bin/sh\n")
    for w in ("m.gguf", "b.gguf"):
        (tmp_path / w).write_text("weights")
    monkeypatch.setattr(cards, "LOGS", str(tmp_path / "logs"))
    monkeypatch.setattr(cards.runs, "LEDGER", tmp_path / "runs.jsonl")
    answers = {"served": None, "healthy": False}
    procs = []

    def popen(argv, **kw):
        p = FakeProc(argv, **kw)
        procs.append(p)
        answers.update(served=answers.get("will_serve"), healthy=True)
        return p

    def ask(port):
        return {"port": port, "served": answers["served"], "free": 2, "total": 2, "healthy": answers["healthy"]}

    m = cards.Manager(popen=popen, ask=ask, models_dir=str(tmp_path), reservations=[reg.Reservation("n", 9, "the-carve-out", "test")])
    w = FakeWorker(tmp_path, profiles, registry, rules)
    m.start(w)
    return m, w, answers, procs


def swaps(w):
    return [(p[3], p[4], p[5], p[11]) for s, p in w.conn.sql if "INSERT INTO s.swaps" in s]   # action, from, to, ok


def test_the_server_command_derives_its_geometry_from_the_profile(tmp_path):
    _, profiles, _ = fx.catalogue(tmp_path)
    argv = cards.server_argv("/bin/llama-server", profiles["qwen-50k"], 1, 8111, "/m")
    assert argv[:3] == ["/bin/llama-server", "-m", "/m/m.gguf"]
    assert "-c" in argv and argv[argv.index("-c") + 1] == "100000" and argv[argv.index("-np") + 1] == "2"
    assert "--alias" in argv and argv[argv.index("--alias") + 1] == "M" and "--port" in argv


def test_a_load_starts_the_server_on_its_card_reads_the_model_back_and_ledgers_it(kit):
    m, w, answers, procs = kit
    answers["will_serve"] = "M"
    d = policy.Decision("n:1", policy.LOAD, "doc", "doc takes this card", "qwen-50k")
    assert m.load(w, 1, d, 0.0) is True
    p, = procs
    assert p.kw["env"]["HIP_VISIBLE_DEVICES"] == "1" and "ROCR_VISIBLE_DEVICES" not in p.kw["env"]
    assert p.kw["env"]["LD_LIBRARY_PATH"].split(":")[0] == os.path.dirname(w.profile["programs"]["qv4-llama-server"])
    assert 1 in m.servers and m.servers[1].prof.name == "qwen-50k"
    assert swaps(w)[-1] == ("load", None, "qwen-50k", True)
    assert any("INSERT INTO s.cards" in s and "profile" in s for s, _ in w.conn.sql)


def test_a_card_answering_with_the_wrong_model_is_not_ready(kit):
    """The 13.8%: the server is started, says it serves another model, and
    is stopped; the swap is in the ledger as failed with what it answered."""
    m, w, answers, procs = kit
    answers["will_serve"] = "OTHER"
    d = policy.Decision("n:1", policy.LOAD, "doc", "test", "qwen-50k")
    assert m.load(w, 1, d, 0.0) is False
    assert procs[0].signals, "the wrong server was stopped"
    action, _, to, ok = swaps(w)[-1]
    assert (action, to, ok) == ("failed", "qwen-50k", False) and 1 not in m.servers


def test_a_busy_port_is_refused_before_anything_starts(kit):
    m, w, answers, procs = kit
    answers.update(served="STRAY", healthy=True)
    d = policy.Decision("n:1", policy.LOAD, "doc", "test", "qwen-50k")
    assert m.load(w, 1, d, 0.0) is False and procs == []
    assert swaps(w)[-1][0] == "failed" and "stray" in w.logs[-1]


def test_a_second_load_unloads_the_first_and_measures_the_swap(kit):
    m, w, answers, procs = kit
    answers["will_serve"] = "M"
    m.load(w, 1, policy.Decision("n:1", policy.LOAD, "doc", "first", "qwen-50k"), 0.0)
    first = procs[0]
    answers["will_serve"] = "B"
    first.returncode = 0              # it stops when told
    answers.update(healthy=False)
    assert m.load(w, 1, policy.Decision("n:1", policy.LOAD, "emb", "second", "bge"), 10.0) is True
    assert first.signals, "the first server was told to stop"
    acts = [s[0] for s in swaps(w)]
    assert acts[-2:] == ["unload", "load"] and swaps(w)[-1][1:3] == ("qwen-50k", "bge")
    assert m.servers[1].prof.name == "bge"


def test_bookkeeping_decisions_change_the_card_row_not_the_server(kit):
    m, w, answers, procs = kit
    for action in (policy.DRAIN, policy.RELEASE, policy.HANDOVER):
        m.apply(w, policy.Decision("n:1", action, "doc", "why", "qwen-50k"), 5.0)
    assert procs == [] and [s[0] for s in swaps(w)] == ["drain", "release", "handover"]
    assert m.holder_since.get(1) == 5.0


def test_a_reserved_card_is_registered_reserved_and_a_keep_does_nothing(kit):
    m, w, answers, procs = kit
    reserved = [p for s, p in w.conn.sql if "INSERT INTO s.cards" in s and p[1] == 9 and True in p]
    assert reserved, "card 9 (the fixture's reservation) is written reserved"
    n = len(w.conn.sql)
    m.apply(w, policy.Decision("n:9", policy.KEEP, None, "reserved", None), 0.0)
    assert len(w.conn.sql) == n


def test_stop_all_unloads_every_server_this_worker_started(kit):
    m, w, answers, procs = kit
    answers["will_serve"] = "M"
    m.load(w, 1, policy.Decision("n:1", policy.LOAD, "doc", "x", "qwen-50k"), 0.0)
    procs[0].returncode = 0
    m.stop_all(w)
    assert m.servers == {} and swaps(w)[-1][0] == "unload"


def test_a_server_that_died_leaves_the_card_cold_and_a_ledger_line(kit):
    m, w, answers, procs = kit
    answers["will_serve"] = "M"
    m.load(w, 1, policy.Decision("n:1", policy.LOAD, "doc", "x", "qwen-50k"), 0.0)
    procs[0].returncode = 1
    m._reap_dead_servers(w)
    assert m.servers == {} and swaps(w)[-1][0] == "died"


def test_a_running_job_keeps_its_card_in_flight(kit):
    """A job this worker runs against the card's profile counts as in
    flight, so the planner drains rather than swaps under it."""
    m, w, answers, procs = kit

    class R:
        jt = w.registry["doc"]

    w.running[1] = R()
    m.servers[1] = cards.Server(FakeProc([]), w.profiles["qwen-50k"], 1, 8111, 0.0)
    w.conn.fetchall = lambda: [("n", 1, False, None, 31.9, 1.8, None, "qwen-50k", 8111, 1, None, "doc", None, False, 2, 0, "w", None),
                               ("n", 9, True, "carve-out", 31.9, 26.0, None, None, None, None, None, None, None, False, None, None, "w", None)]
    held = {h.card: h for h in m.held(w, 100.0)}
    assert held["n:1"].in_flight == 1 and held["n:1"].loaded == "qwen-50k" and held["n:1"].job_type == "doc"
    assert held["n:9"].reserved


def test_a_card_another_live_worker_manages_is_left_alone(kit, monkeypatch):
    """Two workers on one box: the second neither registers nor plans the
    first's card; it still runs jobs on the profile the row shows."""
    m, w, answers, procs = kit
    monkeypatch.setattr(cards.q, "workers", lambda conn, schema: [{"name": "other", "state": "up", "last_seen": cards.q.utcnow()}])
    monkeypatch.setattr(cards.q, "cards", lambda conn, schema, box=None: [
        {"box": "n", "card": 1, "reserved": False, "worker": "other", "profile": "qwen-50k", "port": 8111, "holder": "doc",
         "draining": False, "memory_total_gb": 31.9, "memory_used_gb": 25.0}])
    w.alarm_after_s = 300
    n = len(w.conn.sql)
    m.register_cards(w)
    written = [p[1] for s_, p in w.conn.sql[n:] if "INSERT INTO s.cards" in s_]
    assert 1 not in written and "managed by other" in " ".join(w.logs)
    assert [h.card for h in m.held(w, 0.0)] == [], "nothing of the other worker's is planned"


def test_a_profile_whose_load_failed_here_is_not_tried_again_until_the_programs_change(kit):
    """Card the-card-manager-loads-a-profile-for-a-job-no-box-can-claim: the
    unpatched server was started for TeleOCR three times in a day. After a
    failed load the job types on that profile leave the planner's eligible
    set, and come back when the probe's programs change (a program installed
    or removed), not before."""
    m, w, answers, procs = kit
    assert {"doc", "rev", "reason", "emb"} <= m.claimable(w)
    answers["will_serve"] = "OTHER"
    assert m.load(w, 1, policy.Decision("n:1", policy.LOAD, "doc", "test", "qwen-50k"), 0.0) is False
    assert m.failed_loads == {"qwen-50k": m._programs_key(w)}
    assert m.claimable(w) == {"rev", "emb", "cpu"}, "doc and reason both name the failed profile"
    w.profile["programs"]["qv4-llama-server-built"] = "/elsewhere/llama-server"
    assert {"doc", "reason"} <= m.claimable(w), "the probe changed: tried again"


def test_a_stray_on_the_port_is_not_held_against_the_profile(kit):
    m, w, answers, procs = kit
    answers.update(served="STRAY", healthy=True)
    assert m.load(w, 1, policy.Decision("n:1", policy.LOAD, "doc", "test", "qwen-50k"), 0.0) is False
    assert m.failed_loads == {} and "doc" in m.claimable(w)


def test_a_job_whose_program_this_box_lacks_is_not_claimable_here(kit):
    m, w, answers, procs = kit
    w.registry["doc"] = dataclasses.replace(w.registry["doc"], requires=("ghost-program",))
    assert "doc" not in m.claimable(w) and "reason" in m.claimable(w)


def test_what_can_be_checked_without_the_card_is_checked_before_the_resident_profile_goes(kit):
    """Three times on 19 October a working page-reader was unloaded for a load
    whose weights or server could have been checked first."""
    m, w, answers, procs = kit
    answers["will_serve"] = "M"
    m.load(w, 1, policy.Decision("n:1", policy.LOAD, "doc", "first", "qwen-50k"), 0.0)
    os.remove(os.path.join(m.models_dir, "b.gguf"))
    assert m.load(w, 1, policy.Decision("n:1", policy.LOAD, "emb", "second", "bge"), 10.0) is False
    assert m.servers[1].prof.name == "qwen-50k" and not procs[0].signals, "the resident profile was kept"
    assert swaps(w)[-1][0] == "failed" and "weights missing" in w.logs[-1]


def test_a_profile_naming_its_own_server_loads_with_it_and_never_with_another(kit, tmp_path):
    """Card teleocr-needs-a-patched-server-the-scheduler-cannot-choose: the
    conversion loads only on the patched build. A profile with `binary` gets
    that program; where the box lacks it the load is refused (no fall back to
    the [server] setting) and the planner never sees the job's demand here."""
    m, w, answers, procs = kit
    teleocr = dataclasses.replace(w.profiles["bge"], name="tele", binary="qv4-llama-server-teleocr")
    w.profiles["tele"] = teleocr
    w.registry["ocr"] = dataclasses.replace(w.registry["emb"], needs=dataclasses.replace(w.registry["emb"].needs, name="ocr", model_profile="tele"))
    programs = w.profile["programs"]
    assert cards.server_binary(programs, "copy", teleocr) is None and "ocr" not in m.claimable(w)
    answers["will_serve"] = "B"
    assert m.load(w, 1, policy.Decision("n:1", policy.LOAD, "ocr", "test", "tele"), 0.0) is False and procs == []
    assert "'qv4-llama-server-teleocr'" in w.logs[-1] and swaps(w)[-1][0] == "failed"
    patched = tmp_path / "built-teleocr" / "llama-server"
    patched.parent.mkdir()
    patched.write_text("#!/bin/sh\n")
    programs["qv4-llama-server-teleocr"] = str(patched)
    assert cards.server_binary(programs, "copy", teleocr) == str(patched) and "ocr" in m.claimable(w), "the probe changed"
    assert m.load(w, 1, policy.Decision("n:1", policy.LOAD, "ocr", "test", "tele"), 0.0) is True
    assert procs[0].argv[0] == str(patched) and procs[0].kw["env"]["LD_LIBRARY_PATH"].split(":")[0] == str(patched.parent)
    assert cards.server_binary(programs, "copy", w.profiles["bge"]) == programs["qv4-llama-server"], "a profile without one keeps the setting"


# ── a device that is not a card (card the-probe-lists-the-processor-s-own-graphics-as-a-card) ─────────────

def _upserts(w, since=0):
    """card → the fields of each `cards` upsert after `since`, in order."""
    out = []
    for s, p in w.conn.sql[since:]:
        if "INSERT INTO s.cards" in s:
            cols = s[s.index("(") + 1:s.index(")")].split(", ")
            out.append(dict(zip(cols, p)))
    return out


def _row(card, **more):
    base = {"box": "n", "card": card, "reserved": False, "reserved_why": None, "worker": "w", "profile": None, "port": None,
            "holder": None, "draining": False, "memory_total_gb": 31.9, "memory_used_gb": 1.8, "product": "AMD Radeon AI PRO R9700"}
    return {**base, **more}


def test_the_processors_graphics_in_the_probe_listing_is_not_registered(kit):
    """30 October 13:49: rocm-smi listed the processor's own graphics (index 2, 2.0 GB) for one tick; the row
    was written, the planner saw a cold card, and the page reader ran on the processor."""
    from support.scheduler import probe
    from support.scheduler.tests.test_probe import RYZEN
    m, w, answers, procs = kit
    w.profile["cards"] = probe.cards(RYZEN)
    n = len(w.conn.sql)
    m.register_cards(w)
    assert sorted(u["card"] for u in _upserts(w, n)) == [0, 1]


def test_a_row_whose_card_the_probe_no_longer_lists_is_reserved_and_never_planned(kit, monkeypatch):
    """The stale row (node2, 2), reserved by the integrator's hand, takes this reservation on the first tick;
    `held` shows it reserved, so the planner never loads there."""
    m, w, answers, procs = kit
    w.alarm_after_s = 300
    rows = [_row(0), _row(1), _row(2, reserved=True, reserved_why="reserved by hand: the processor's graphics, see the card",
                                 product="AMD Ryzen 9 9950X 16-Core Processor", memory_total_gb=2.0, memory_used_gb=0.1)]
    monkeypatch.setattr(cards.q, "workers", lambda conn, schema: [])
    monkeypatch.setattr(cards.q, "cards", lambda conn, schema, box=None: rows)
    w.profile["cards"] = [{"index": 0, "memory_total_gb": 31.9, "memory_used_gb": 26.0, "product": "AMD Radeon AI PRO R9700"},
                          {"index": 1, "memory_total_gb": 31.9, "memory_used_gb": 1.8, "product": "AMD Radeon AI PRO R9700"}]
    n = len(w.conn.sql)
    m.register_cards(w)
    stale = [u for u in _upserts(w, n) if u["card"] == 2]
    assert stale and stale[-1]["reserved"] is True and stale[-1]["reserved_why"] == cards.STALE_WHY
    assert "card 2: not listed by the probe" in " ".join(w.logs)
    rows[2].update(reserved=True, reserved_why=cards.STALE_WHY)
    held = {h.card: h for h in m.held(w, 0.0)}
    assert held["n:2"].reserved and not held["n:0"].reserved
    # said once: a second tick with the same listing writes nothing for the stale row
    n = len(w.conn.sql)
    m.reconcile_listing(w)
    assert not [u for u in _upserts(w, n) if u["card"] == 2]
    # a failed probe is not data: it marks nothing stale
    rows[2].update(reserved=False, reserved_why=None)
    w.profile["cards"] = None
    n = len(w.conn.sql)
    m.reconcile_listing(w)
    assert not _upserts(w, n)


def test_a_stale_reservation_clears_when_the_probe_lists_the_card_again(kit, monkeypatch):
    m, w, answers, procs = kit
    w.alarm_after_s = 300
    rows = [_row(0), _row(1, reserved=True, reserved_why=cards.STALE_WHY),
            _row(5, reserved=True, reserved_why="held for the frozen product's OCR server")]
    monkeypatch.setattr(cards.q, "workers", lambda conn, schema: [])
    monkeypatch.setattr(cards.q, "cards", lambda conn, schema, box=None: rows)
    w.profile["cards"] = [{"index": 0, "memory_total_gb": 31.9, "memory_used_gb": 26.0, "product": "AMD Radeon AI PRO R9700"},
                          {"index": 1, "memory_total_gb": 31.9, "memory_used_gb": 1.8, "product": "AMD Radeon AI PRO R9700"},
                          {"index": 5, "memory_total_gb": 31.9, "memory_used_gb": 1.8, "product": "AMD Radeon AI PRO R9700"}]
    n = len(w.conn.sql)
    m.register_cards(w)
    cleared = [u for u in _upserts(w, n) if u["card"] == 1 and "reserved" in u]
    assert cleared and cleared[-1]["reserved"] is False and cleared[-1]["reserved_why"] is None
    assert not [u for u in _upserts(w, n) if u["card"] == 5 and "reserved" in u], "a reservation that is not this one stands"
