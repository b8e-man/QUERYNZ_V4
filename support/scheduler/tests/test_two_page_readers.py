"""Two cards holding one profile (the night window with a page reader on
card 1 and another beside the frozen OCR server on card 0, 30 October):
the worker sends each piece to the card with the fewest of its own jobs,
not to the first card holding the profile, and its cap for the job type is
per card. Fast: a fake cards table, no database, no card."""
from __future__ import annotations

from support.scheduler import registry as reg
from support.scheduler import worker as wk
from support.scheduler.tests.test_night_window import JOBS, PROFILES


def table(*cards):
    return [{"card": c, "reserved": False, "profile": "page-reader", "port": 8110 + c, "draining": False, "slots": 3}
            for c in cards]


def make(tmp_path, monkeypatch, cards, free_gb=50.0):
    (tmp_path / "jobs.toml").write_text(JOBS.replace("priority = 23\n", "priority = 23\nconcurrency = 3\n"))
    (tmp_path / "profiles.toml").write_text(PROFILES)
    w = wk.Worker("node2", "node2", registry=reg.load(tmp_path / "jobs.toml"), profiles=reg.profiles(tmp_path / "profiles.toml"),
                  rules=reg.queueing(tmp_path / "jobs.toml"), connect=lambda: None, alarm=lambda *a: None, log=lambda m: None)
    w.profile = {"programs": {"radiance": "/u", "qv4-llama-server-built": "/x"}, "memory_total_gb": 125}
    monkeypatch.setattr(w, "cards_here", lambda: cards)
    monkeypatch.setattr(w, "available_gb", lambda: free_gb)
    return w


def running(w, qid):
    r = wk.Running({"id": qid, "args": {}}, w.registry["qv4-pages"])
    w.running[qid] = r
    return r


def test_pieces_go_to_the_card_with_the_fewest_jobs_on_it_not_the_first(tmp_path, monkeypatch):
    w = make(tmp_path, monkeypatch, table(0, 1))
    a, b, c = running(w, 1), running(w, 2), running(w, 3)
    assert w.pick_card(a)["card"] == 0, "nothing runs: the lowest index"
    assert w.pick_card(b)["card"] == 1, "the second row goes to the other card"
    assert w.pick_card(c)["card"] == 0, "one each: the lowest index again"
    env = w._env(c, "run", {"piece": 7, "key": "k"})
    assert env["QV4_CARD"] == "0" and env["QV4_MODEL_PORT"] == "8110" and env["QV4_MODEL_URL"].startswith("http://127.0.0.1:8110/")
    # every piece picks again: when card 1 empties, the next piece goes there
    del w.running[2]
    assert w.pick_card(a)["card"] == 1, "card 0 holds c, card 1 nobody"
    assert a.card == 1 and c.card == 0
    # a row's own place is not counted against it
    w.running.clear()
    a = running(w, 1)
    a.card = 0
    assert w.pick_card(a)["card"] == 0


def test_a_draining_or_reserved_card_takes_no_piece(tmp_path, monkeypatch):
    cards = table(0, 1)
    cards[0]["draining"] = True
    w = make(tmp_path, monkeypatch, cards)
    r = running(w, 1)
    assert w.pick_card(r)["card"] == 1
    cards[1]["reserved"] = True
    assert w.pick_card(r) is None and r.card is None
    assert "QV4_MODEL_URL" not in w._env(r, "run", None)


def test_the_cap_for_a_profile_job_is_per_card_holding_the_profile(tmp_path, monkeypatch):
    w = make(tmp_path, monkeypatch, table(0, 1))
    for qid in range(1, 6):
        running(w, qid)
    assert "qv4-pages" in w.eligible(), "five rows run; two readers at three slots each take six"
    running(w, 6)
    assert "qv4-pages" not in w.eligible(), "six is the cap for two cards"
    w.running.clear()
    monkeypatch.setattr(w, "cards_here", lambda: table(1))
    for qid in range(1, 4):
        running(w, qid)
    assert "qv4-pages" not in w.eligible(), "three is the cap for one card"
    del w.running[3]
    assert "qv4-pages" in w.eligible()


def test_the_cap_still_bows_to_the_boxs_memory_and_the_workers_own_limit(tmp_path, monkeypatch):
    w = make(tmp_path, monkeypatch, table(0, 1), free_gb=3.0)     # two copies of 1.5 GB fit
    running(w, 1)
    running(w, 2)
    assert "qv4-pages" not in w.eligible()
    w = make(tmp_path, monkeypatch, table(0, 1))
    w.max_parallel = 4
    for qid in range(1, 5):
        running(w, qid)
    assert w.eligible() == []
