"""Ruling 121: on node2 Flash-Next, served by Radiance, replaces Qwen3.6 as
the text-reader and review model. The server is a standing unit
(`qv4-radiance`) holding both cards as ONE profile, `flash-next`; the
text reader and review are views on it that differ only in what each
request says (thinking off for the reader, on with a budget for review).

The card manager never starts or stops a standing server: it reads back
the model the unit's port serves, marks both cards as holding the profile
(or as held and not answering), records the standing load in the swap
ledger, and the planner treats those cards as untouchable. A job on a view
is eligible on a card holding the server it is a view of."""
from __future__ import annotations

import json
import pathlib
import shlex
import threading

import pytest

from support.scheduler import cards, policy, probe
from support.scheduler import registry as reg
from support.scheduler import worker as wk
from support.scheduler.tests.test_cards import FakeConn

UNIT = pathlib.Path(__file__).resolve().parents[1] / "units" / "qv4-radiance.service"

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
request = {chat_template_kwargs = {enable_thinking = false}}

[profiles.review]
on = "flash-next"
model = "qwen4exp"
slots = 16
context = 16384
temperature = 0.2
max_tokens = 6144
request = {chat_template_kwargs = {enable_thinking = true}, thinking_token_budget = 2048}

[profiles.embedding]
model = "bge"
weights = ["b.gguf"]
slots = 8
context = 8192
temperature = 0.0
max_tokens = 0
memory_gb = 0.7
measured_geometry = "8192x8"
embedding = true
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

[jobs.qv4-emb]
needs = "model-profile"
profile = "embedding"
memory_gb = 1.0
deadline_s = 120
query_timeout_s = 30
priority = 3
command = ["true"]
"""


@pytest.fixture
def cat(tmp_path):
    (tmp_path / "jobs.toml").write_text(JOBS)
    (tmp_path / "profiles.toml").write_text(PROFILES)
    return tmp_path / "jobs.toml", tmp_path / "profiles.toml"


# ── the shipped profiles ─────────────────────────────────────────────────────

def test_the_shipped_flash_next_profile_is_the_standing_radiance_server_on_both_cards():
    p = reg.profiles()["flash-next"]
    assert (p.model, p.binary, p.unit, p.port, p.cards) == ("qwen4exp", "radiance", "qv4-radiance.service", 8060, 2)
    assert p.weights == ("radiance/qwen3.8-next-flash-fp8-iq4r-moe.rad",)
    assert p.geometry == "16384x16" and p.measured_geometry == p.geometry
    assert p.memory_gb and p.host_memory_gb and p.load_seconds, "memory and load time are measured, not left empty"


def test_the_reader_and_review_are_views_on_it_and_qwen36_has_left():
    profs = reg.profiles()
    tr, rv = profs["text-reader"], profs["review"]
    assert tr.on == rv.on == "flash-next" and tr.model == rv.model == "qwen4exp"
    assert tr.request_fields["chat_template_kwargs"] == {"enable_thinking": False}
    assert rv.request_fields["chat_template_kwargs"] == {"enable_thinking": True}
    assert rv.request_fields["thinking_token_budget"] > 0
    assert not any("qwen3.6" in p.model or any("Qwen3.6" in w for w in p.weights) for p in profs.values())
    assert reg.problems() == []


def test_the_unit_and_the_profile_agree():
    """One fact, two files: the unit's served name, slots, context bound and
    port are the profile's, or the read-back refuses every load."""
    p = reg.profiles()["flash-next"]
    text = UNIT.read_text(encoding="utf-8")
    body = text.split("ExecStart=", 1)[1].split("\nExecStop=", 1)[0]
    argv = shlex.split(" ".join(l.rstrip("\\").strip() for l in body.splitlines() if not l.lstrip().startswith("#")))
    flag = lambda n: argv[argv.index(n) + 1]  # noqa: E731
    assert flag("--served-model-name") == p.model
    assert int(flag("--max-num-seqs")) == p.slots and int(flag("--max-model-len")) == p.context
    assert flag("-p") == f"127.0.0.1:{p.port}:{p.port}"
    assert p.unit == UNIT.name
    assert flag("-v").split(":")[0].endswith(p.weights[0])


def test_no_card_on_node2_is_reserved_for_the_frozen_chat_model_any_more():
    assert not any(r.key == "node2:0" and "agent-llm" in r.holder for r in reg.reservations())


# ── the registry's rules for views and standing servers ──────────────────────

def test_a_view_must_name_a_standing_server_with_its_model(cat):
    jp, pp = cat
    assert reg.problems(jp, pp) == []
    bad = PROFILES.replace('[profiles.review]\non = "flash-next"\nmodel = "qwen4exp"', '[profiles.review]\non = "embedding"\nmodel = "bge"')
    pp.write_text(bad)
    assert any("review" in p and "standing" in p for p in reg.problems(jp, pp))
    pp.write_text(PROFILES.replace('[profiles.review]\non = "flash-next"\nmodel = "qwen4exp"', '[profiles.review]\non = "flash-next"\nmodel = "other"'))
    assert any("review" in p and "qwen4exp" in p for p in reg.problems(jp, pp))


def test_a_standing_server_names_its_port_and_a_qv4_unit(cat):
    jp, pp = cat
    pp.write_text(PROFILES.replace('unit = "qv4-radiance.service"', 'unit = "radiance.service"'))
    assert any("qv4-" in p for p in reg.problems(jp, pp))
    pp.write_text(PROFILES.replace("port = 8060\n", ""))
    assert any("port" in p for p in reg.problems(jp, pp))


def test_a_view_is_not_warned_for_memory_its_server_measured(cat):
    jp, pp = cat
    w = reg.warnings(jp, pp)
    assert not any(x.startswith(("profile text-reader", "profile review")) for x in w)


def test_the_server_of_a_view_is_the_standing_profile(cat):
    _, pp = cat
    profs = reg.profiles(pp)
    assert reg.server_of(profs, "text-reader").name == "flash-next"
    assert reg.server_of(profs, "flash-next").name == "flash-next"
    assert reg.server_of(profs, "embedding").name == "embedding"


def test_the_probe_finds_radiance_by_its_installed_unit(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "RADIANCE_UNIT", str(tmp_path / "qv4-radiance.service"))
    which = lambda n: "/usr/bin/podman" if n == "podman" else None  # noqa: E731
    assert probe.programs(("radiance",), which=which) == {"radiance": None}
    (tmp_path / "qv4-radiance.service").write_text("[Service]\n")
    assert probe.programs(("radiance",), which=which) == {"radiance": str(tmp_path / "qv4-radiance.service")}
    assert probe.programs(("radiance",), which=lambda n: None) == {"radiance": None}, "no podman, no server"


# ── the card manager ─────────────────────────────────────────────────────────

class W:
    def __init__(self, jp, pp):
        self.conn, self.schema, self.box, self.name = FakeConn(), "s", "node2", "node2"
        self.registry, self.profiles, self.rules = reg.load(jp), reg.profiles(pp), reg.queueing(jp)
        self.profile = {"programs": {"radiance": "/u/qv4-radiance.service", "qv4-llama-server": "/x/llama-server"},
                        "cards": [{"index": 0, "memory_total_gb": 31.9, "memory_used_gb": 29.3},
                                  {"index": 1, "memory_total_gb": 31.9, "memory_used_gb": 27.9}]}
        self.running, self.lock, self.logs = {}, threading.Lock(), []
        self.log = self.logs.append
        self.alarm_after_s = 300


def upserts(w):
    out = {}
    for sql, params in w.conn.sql:
        if "INTO s.cards" in sql:
            cols = sql.split("(", 1)[1].split(")", 1)[0].split(", ")
            out.setdefault(params[1], {}).update(dict(zip(cols, params)))
    return out


def swaps(w):
    return [p for s, p in w.conn.sql if "INSERT INTO s.swaps" in s]


@pytest.fixture
def mgr(cat):
    jp, pp = cat
    answers = {"served": "qwen4exp", "healthy": True}
    started = []

    def ask(port):
        if port != 8060:
            return {"port": port, "served": None, "free": -1, "total": 0, "healthy": False}
        return {"port": port, "served": answers["served"], "free": -1, "total": 0, "healthy": answers["healthy"]}

    m = cards.Manager(popen=lambda argv, **kw: started.append(argv), ask=ask, models_dir="/m", reservations=[],
                      active_seconds=lambda unit: 21.6)
    w = W(jp, pp)
    return m, w, answers, started


def test_a_standing_server_that_answers_marks_both_cards_and_records_the_load(mgr):
    m, w, answers, started = mgr
    m.start(w)
    rows = upserts(w)
    assert {c: (r["profile"], r["port"], r["reserved"]) for c, r in rows.items()} == {0: ("flash-next", 8060, False),
                                                                                      1: ("flash-next", 8060, False)}
    loads = [s for s in swaps(w) if s[3] == "load"]
    assert sorted(s[2] for s in loads) == [0, 1] and all(s[5] == "flash-next" and s[10] == "qwen4exp" for s in loads)
    assert started == [], "the worker never starts a standing server"
    n = len(swaps(w))
    m.mark_standing(w)
    assert len(swaps(w)) == n, "a server still answering is not recorded again"


def test_a_standing_server_not_answering_holds_its_cards_reserved_and_its_return_is_measured(mgr):
    m, w, answers, started = mgr
    answers.update(healthy=False, served=None)
    m.start(w)
    rows = upserts(w)
    assert all(r["reserved"] and r["profile"] is None and "qv4-radiance" in r["reserved_why"] for r in rows.values())
    assert not [s for s in swaps(w) if s[3] == "load"]
    answers.update(healthy=True, served="qwen4exp")
    m.mark_standing(w)
    loads = [s for s in swaps(w) if s[3] == "load"]
    assert len(loads) == 2 and all(s[9] == 21.6 for s in loads), "a return seen from down is a measured load"
    answers.update(healthy=True, served="something-else")
    m.mark_standing(w)
    assert upserts(w)[0]["reserved"] and upserts(w)[0]["profile"] is None, "the wrong model answering is not the profile"
    assert [s for s in swaps(w) if s[3] == "died"]


def test_the_planner_never_plans_a_standing_servers_cards(mgr, monkeypatch):
    m, w, answers, started = mgr
    m.start(w)
    table = [{"card": c, "worker": "node2", "reserved": False, "profile": "flash-next", "port": 8060, "holder": None,
              "draining": False} for c in (0, 1)]
    monkeypatch.setattr(cards.q, "cards", lambda conn, schema, box=None: table)
    held = m.held(w, 0.0)
    assert all(h.reserved for h in held)
    d, _ = policy.plan(now=0.0, held=held, queues={"qv4-emb": 50}, registry=w.registry, profiles=w.profiles, rules=w.rules)
    assert all(x.action == policy.KEEP for x in d), "embedding demand never unloads the standing server"


def test_a_load_of_a_standing_profile_or_a_view_is_never_acted_on(mgr):
    m, w, answers, started = mgr
    m.start(w)
    for prof in ("flash-next", "text-reader"):
        m.apply(w, policy.Decision("node2:2", policy.LOAD, "qv4-read", "rule 6", prof), 0.0)
    assert started == [], "no llama-server is started for a profile its own unit serves"


def test_claimable_takes_the_view_s_server_program(mgr):
    m, w, answers, started = mgr
    m.start(w)
    assert {"qv4-read", "qv4-judge"} <= m.claimable(w)
    w.profile["programs"]["radiance"] = None
    assert not ({"qv4-read", "qv4-judge"} & m.claimable(w)), "no radiance on this box: its views are not claimable"


# ── the worker ───────────────────────────────────────────────────────────────

def test_a_job_on_a_view_is_eligible_on_its_servers_card_and_gets_its_request(cat, monkeypatch):
    jp, pp = cat
    w = wk.Worker("node2", "node2", registry=reg.load(jp), profiles=reg.profiles(pp), rules=reg.queueing(jp),
                  connect=lambda: None, alarm=lambda *a: None, log=lambda m: None)
    w.profile = {"programs": {"radiance": "/u"}, "memory_total_gb": 125}
    table = [{"card": c, "reserved": False, "profile": "flash-next", "port": 8060, "draining": False} for c in (0, 1)]
    monkeypatch.setattr(w, "cards_here", lambda: table)
    monkeypatch.setattr(w, "available_gb", lambda: 50.0)
    assert set(w.eligible()) == {"qv4-read", "qv4-judge"}
    r = wk.Running({"id": 1, "args": {}}, w.registry["qv4-judge"])
    env = w._env(r, "run", None)
    assert env["QV4_MODEL_URL"] == "http://127.0.0.1:8060/v1/chat/completions" and env["QV4_MODEL"] == "qwen4exp"
    assert env["QV4_PROFILE"] == "review"
    req = json.loads(env["QV4_MODEL_REQUEST"])
    assert req["chat_template_kwargs"] == {"enable_thinking": True} and req["thinking_token_budget"] == 2048
    assert req["temperature"] == 0.2 and req["max_tokens"] == 6144
