"""The source lights on invented queue rows, refusals, run records and gaps:
each light's rules, the stale file on the board's side, and mutants (each
red, orange and green rule removed in turn is caught by these scenarios)."""
import datetime as dt
import json

import pytest

from checks import source_lights as sl
from support.scheduler import registry as reg

UTC = dt.timezone.utc
REAL_LANES = dict(sl.LANES)
NOW = dt.datetime(2026, 11, 3, 23, 0, tzinfo=UTC)      # 4 November 12:00 NZDT

JOBS = """
[jobs.qv4-x-capture]
needs = "processor"
memory_gb = 0.2
deadline_s = 3600
class = "due"
priority = 1
command = ["true"]
at_utc = "10:00"
then = ["qv4-x-load"]

[jobs.qv4-x-load]
needs = "processor"
memory_gb = 0.2
deadline_s = 600
class = "due"
priority = 2
command = ["true"]

[jobs.qv4-x-read]
needs = "processor"
memory_gb = 0.2
class = "whenever"
priority = 3
pieces = true
command = ["true"]

[jobs.qv4-mcp-pull]
needs = "processor"
memory_gb = 0.2
deadline_s = 3600
class = "due"
priority = 4
command = ["true"]
every_s = 21600

[jobs.qv4-y-load]
needs = "processor"
memory_gb = 0.2
class = "whenever"
priority = 5
command = ["true"]

[jobs.qv4-z-watch]
needs = "processor"
memory_gb = 0.2
class = "due"
priority = 6
command = ["true"]
at_utc = "09:00"
enabled = false

[jobs.qv4-w-capture]
needs = "processor"
memory_gb = 0.2
deadline_s = 3600
class = "due"
priority = 7
command = ["true"]
at_utc = "09:00"
enabled = false

[jobs.qv4-w-load]
needs = "processor"
memory_gb = 0.2
deadline_s = 600
class = "due"
priority = 8
command = ["true"]
at_utc = "17:00"
"""

LANES = {
    "x": sl.Lane(update=("qv4-x-capture", "qv4-x-load"), read=("qv4-x-read",), hosts=("www.x.govt.nz",),
                 waiting=(("x_documents", "true"),), coverage="local_elections"),
    "m": sl.Lane(update=(sl.MCP_PULL,), corpora=("mcorp",)),
    "y": sl.Lane(update=("qv4-y-load",)),
    "z": sl.Lane(update=("qv4-z-watch",)),
    "g": sl.Lane(note="loaded by the merge gate's staging step"),
}
REGS = [(r, r, True) for r in LANES] + [("unknown", "unknown", False)]


@pytest.fixture(autouse=True)
def lanes(monkeypatch):
    monkeypatch.setattr(sl, "LANES", LANES)


@pytest.fixture
def registry(tmp_path):
    p = tmp_path / "jobs.toml"
    p.write_text(JOBS)
    return reg.load(p)


def ago(hours):
    return NOW - dt.timedelta(hours=hours)


def done(hours, state="done"):
    return {"state": state, "finished_at": ago(hours)}


def good_facts(registry):
    """Every lane working, nothing outstanding."""
    f = sl.empty_facts(registry)
    for j in ("qv4-x-capture", "qv4-x-load", "qv4-x-read", sl.MCP_PULL, "qv4-y-load"):
        f["last_done"][j] = done(2)
        f["last_finished"][j] = done(2)
    f["mcp_run"] = {"job": sl.MCP_PULL, "ok": True, "ended": ago(2).isoformat(), "mcorp_to": 10, "mcorp_caught": 0,
                    "mcorp_drift": 0}
    return f


def lights(facts):
    out = sl.compute(facts, now=NOW, regs=REGS)
    return {x["register"]: x for x in out["lights"]}


def light(facts, register):
    return lights(facts)[register]["light"]


# ── green and grey ──

def test_everything_working_is_green(registry):
    L = lights(good_facts(registry))
    assert L["x"]["light"] == "green" and L["x"]["reason"].startswith("up to date: last good update 4 Nov")
    assert L["m"]["light"] == "green"


def test_no_update_job_is_grey(registry):
    L = lights(good_facts(registry))
    assert L["g"] == {**L["g"], "light": "grey", "reason": "no update job: loaded by the merge gate's staging step"}
    assert L["y"]["light"] == "grey" and "on demand" in L["y"]["reason"]          # no clock of its own and none before it
    assert L["z"]["light"] == "grey" and "qv4-z-watch switched off" in L["z"]["reason"]
    assert L["unknown"]["light"] == "grey"


# ── red ──

def test_a_failed_last_run_is_red(registry):
    f = good_facts(registry)
    f["last_finished"]["qv4-x-load"] = done(1, "failed")
    assert light(f, "x") == "red"
    assert lights(f)["x"]["reason"].startswith("qv4-x-load's last run failed at 4 Nov")


def test_a_failed_reader_is_red(registry):
    f = good_facts(registry)
    f["last_finished"]["qv4-x-read"] = done(1, "failed")
    assert light(f, "x") == "red"


def test_a_failed_on_demand_load_is_red(registry):
    f = good_facts(registry)
    f["last_finished"]["qv4-y-load"] = done(1, "failed")
    assert light(f, "y") == "red"


def test_no_good_run_inside_the_cadence_is_red(registry):
    f = good_facts(registry)
    f["last_done"]["qv4-x-capture"] = done(24 + 1 + 6 + 1)             # a day, its deadline (an hour), the grace, and more
    f["last_finished"]["qv4-x-capture"] = done(24 + 1 + 6 + 1)
    assert light(f, "x") == "red"
    assert "qv4-x-capture has not run well since" in lights(f)["x"]["reason"]
    f["last_done"]["qv4-x-capture"] = done(24 + 1 + 6 - 1)             # inside it
    f["last_finished"]["qv4-x-capture"] = done(24 + 1 + 6 - 1)
    f["last_done"]["qv4-x-load"] = f["last_finished"]["qv4-x-load"] = done(24 + 1 + 6 - 2)
    assert light(f, "x") == "green"


def test_a_job_new_to_its_clock_is_judged_from_its_slot(registry):
    f = good_facts(registry)
    del f["last_done"]["qv4-x-capture"], f["last_finished"]["qv4-x-capture"]
    f["timetable"]["qv4-x-capture"] = {"last_slot": ago(10), "last_by": "node2: new to the clock"}
    assert light(f, "x") == "green"
    f["timetable"]["qv4-x-capture"] = {"last_slot": ago(10), "last_by": "timetable"}
    assert light(f, "x") == "red"
    assert "no good run" in lights(f)["x"]["reason"]


def test_a_chained_job_that_did_not_follow_its_parent_is_red(registry):
    f = good_facts(registry)
    f["last_done"]["qv4-x-capture"] = f["last_finished"]["qv4-x-capture"] = done(8)
    f["last_done"]["qv4-x-load"] = f["last_finished"]["qv4-x-load"] = done(20)       # before the capture finished
    assert light(f, "x") == "red"
    assert "qv4-x-load has not run since the job before it finished" in lights(f)["x"]["reason"]
    f["open"] = [{"job": "qv4-x-load", "state": "queued", "pieces_done": 0, "pieces_total": 0}]
    assert light(f, "x") == "green"                                    # it is queued: not late


def test_the_mcp_pull_is_judged_per_corpus(registry):
    f = good_facts(registry)
    f["last_finished"][sl.MCP_PULL] = done(1, "failed")               # failed on another corpus's new fields
    f["mcp_run"] = {**f["mcp_run"], "ok": False, "othercorp_drift": 7}
    assert light(f, "m") == "green"
    f["mcp_run"]["mcorp_drift"] = 3
    assert light(f, "m") == "red" and "3 new field(s) in the mcorp corpus" in lights(f)["m"]["reason"]
    f["mcp_run"]["mcorp_drift"] = 0
    f["mcp_run"]["mcorp_caught"] = 2
    assert light(f, "m") == "red"
    f["mcp_run"] = {"job": sl.MCP_PULL, "ok": False}                 # stopped before the corpus
    assert light(f, "m") == "red" and "failed before it reached the mcorp corpus" in lights(f)["m"]["reason"]
    f["mcp_run"] = None                                               # no run record at all: the queue row says
    assert light(f, "m") == "red"


def test_a_held_host_is_red(registry):
    f = good_facts(registry)
    f["refusals"] = {"x.govt.nz": {"host": "x.govt.nz", "state": "held", "why": "every PDF reset", "at": "2026-11-04T00:24:31+13:00"}}
    L = lights(f)
    assert L["x"]["light"] == "red"
    assert L["x"]["reason"] == "the fetch gate holds x.govt.nz since 4 Nov 00:24: every PDF reset"
    f["refusals"] = {"forms.x.govt.nz": {"host": "forms.x.govt.nz", "state": "held", "why": "w", "at": "2026-11-04T00:24:31+13:00"}}
    assert light(f, "x") == "green"                                    # a sibling host is not the one it asks


def test_a_held_host_from_a_legal_position(registry):
    f = good_facts(registry)
    LANES2 = {**LANES, "x": sl.Lane(update=LANES["x"].update, positions=("tenancy",))}
    f["positions"] = {"tenancy": ("forms.justice.govt.nz",)}
    f["refusals"] = {"forms.justice.govt.nz": {"host": "forms.justice.govt.nz", "state": "held", "why": "reset", "at": None}}
    sl.LANES = LANES2
    assert light(f, "x") == "red"


def test_a_held_host_among_many_a_position_names_is_orange_not_red(registry):
    """5 November 2026: the gate held three councils' sites on local_elections' 403s; every lane whose position names
    a council's site went red, though each of those lanes still asks the other councils (one of the disabled)."""
    f = good_facts(registry)
    sl.LANES = {**LANES, "x": sl.Lane(update=LANES["x"].update, positions=("councils",))}
    f["positions"] = {"councils": ("dunedin.govt.nz", "gdc.govt.nz", "kaipara.govt.nz", "nelson.govt.nz")}
    f["refusals"] = {h: {"host": h, "state": "held", "why": "HTTP 403", "at": "2026-11-04T22:20:11+13:00"}
                     for h in ("www.dunedin.govt.nz", "www.gdc.govt.nz")}
    L = lights(f)
    assert L["x"]["light"] == "orange"
    assert L["x"]["reason"] == ("the fetch gate holds www.dunedin.govt.nz since 4 Nov 22:20: HTTP 403 "
                                "(one of the 4 hosts the lane reads; the rest are still asked) (and 1 more)")
    f["refusals"].update({h: {"host": h, "state": "held", "why": "HTTP 403", "at": None}
                          for h in ("www.kaipara.govt.nz", "www.nelson.govt.nz")})
    assert light(f, "x") == "red"                                       # every host it reads is held: stopped


def test_a_lane_that_asks_nothing_is_not_lit_by_a_hold(registry):
    f = good_facts(registry)
    sl.LANES = {**LANES, "z": sl.Lane(update=("qv4-z-watch",), hosts=("www.x.govt.nz",))}
    f["refusals"] = {"www.x.govt.nz": {"host": "www.x.govt.nz", "state": "held", "why": "HTTP 403", "at": None}}
    L = lights(f)
    assert L["z"]["light"] == "grey" and "switched off" in L["z"]["reason"]   # its only job is off: it asks nothing


def test_a_declared_gap_naming_the_held_host_says_the_gap(registry):
    f = good_facts(registry)
    f["refusals"] = {"x.govt.nz": {"host": "x.govt.nz", "state": "held", "why": "every PDF reset", "at": None}}
    f["gaps"] = [{"register": "x", "reason": "the host is held; 13,069 orders wait", "since": "2026-11-05",
                  "source": "s", "hosts": ("x.govt.nz",)}]
    L = lights(f)
    assert L["x"]["light"] == "orange" and L["x"]["reasons"] == ["the host is held; 13,069 orders wait (declared 2026-11-05)"]
    f["gaps"][0]["hosts"] = ()                                          # a gap that does not name the host: still red
    assert light(f, "x") == "red"


def test_wildcard_hosts():
    assert sl.host_matches("waitaki.infocouncil.biz", {"*.infocouncil.biz"})
    assert not sl.host_matches("infocouncil.biz.evil.nz", {"*.infocouncil.biz"})
    assert sl.host_matches("www.x.govt.nz", {"x.govt.nz"})


def test_red_outranks_orange(registry):
    f = good_facts(registry)
    f["gaps"] = [{"register": "x", "reason": "half the back catalogue", "since": "2026-11-04", "source": "s"}]
    f["last_finished"]["qv4-x-load"] = done(1, "failed")
    assert light(f, "x") == "red"


# ── orange ──

def test_pieces_to_go_is_orange(registry):
    f = good_facts(registry)
    f["open"] = [{"job": "qv4-x-read", "state": "leased", "pieces_done": 40, "pieces_total": 100}]
    assert light(f, "x") == "orange"
    assert lights(f)["x"]["reason"] == "qv4-x-read has 60 of 100 pieces to go"
    f["open"] = [{"job": "qv4-x-read", "state": "leased", "pieces_done": 100, "pieces_total": 100}]
    assert light(f, "x") == "green"


def test_documents_waiting_is_orange(registry):
    f = good_facts(registry)
    f["waiting"] = {"x": 4117}
    assert light(f, "x") == "orange" and lights(f)["x"]["reason"] == "4,117 document(s) waiting on a reader"


def test_a_short_count_is_orange(registry):
    f = good_facts(registry)
    f["coverage"] = {"x": (1854, 2183, 223)}
    assert light(f, "x") == "orange"
    assert lights(f)["x"]["reason"] == "1,854 of 2,183 return files held (223 failed)"
    f["coverage"] = {"x": (2183, 2183, 0)}
    assert light(f, "x") == "green"


def test_a_declared_gap_is_orange(registry):
    f = good_facts(registry)
    f["gaps"] = [{"register": "x", "reason": "half the back catalogue", "since": "2026-11-04", "source": "s"}]
    assert light(f, "x") == "orange"
    assert lights(f)["x"]["reason"] == "half the back catalogue (declared 2026-11-04)"


def test_a_switched_off_capture_beside_a_running_load_is_orange(registry):
    """9 November 2026 (3429166): the boxes stopped nine captures the ingest MCP gathers; each lane's load still ran
    on its clock over what the stopped capture had landed, and the light said green, "up to date"."""
    f = good_facts(registry)
    sl.LANES = {**LANES, "w": sl.Lane(update=("qv4-w-capture", "qv4-w-load"))}
    f["last_done"]["qv4-w-load"] = f["last_finished"]["qv4-w-load"] = done(2)
    f["last_done"]["qv4-w-capture"] = f["last_finished"]["qv4-w-capture"] = done(14)
    w = sl.compute(f, now=NOW, regs=[("w", "w", True)])["lights"][0]
    assert w["light"] == "orange"
    assert w["reason"] == "qv4-w-capture switched off in the catalogue, so the register holds what it last gathered (3 Nov 22:00)"
    sl.LANES = {**LANES, "w": sl.Lane(update=("qv4-w-load",))}           # a lane with no capture named: the load is all
    assert sl.compute(f, now=NOW, regs=[("w", "w", True)])["lights"][0]["light"] == "green"


def test_a_hold_lights_a_lane_only_while_a_job_that_asks_the_host_is_on(registry):
    f = good_facts(registry)
    f["last_done"]["qv4-w-load"] = f["last_finished"]["qv4-w-load"] = done(2)
    f["refusals"] = {"www.w.govt.nz": {"host": "www.w.govt.nz", "state": "held", "why": "HTTP 403", "at": None}}
    sl.LANES = {**LANES, "w": sl.Lane(update=("qv4-w-capture", "qv4-w-load"), hosts=("w.govt.nz",), asks=("qv4-w-capture",))}
    w = sl.compute(f, now=NOW, regs=[("w", "w", True)])["lights"][0]
    assert w["light"] == "orange" and not any("fetch gate" in r for r in w["reasons"])   # the capture is off: nothing asks
    sl.LANES = {**LANES, "w": sl.Lane(update=("qv4-w-capture", "qv4-w-load"), hosts=("w.govt.nz",), asks=("qv4-w-load",))}
    assert sl.compute(f, now=NOW, regs=[("w", "w", True)])["lights"][0]["light"] == "red"   # the asking job is on


def test_two_reasons_say_how_many_more(registry):
    f = good_facts(registry)
    f["waiting"] = {"x": 1}
    f["gaps"] = [{"register": "x", "reason": "r", "since": "d", "source": "s"}]
    x = lights(f)["x"]
    assert x["reason"].endswith("(and 1 more)") and len(x["reasons"]) == 2


# ── mutants: each rule removed in turn is caught by the scenarios above ──

SCENARIOS = [test_everything_working_is_green, test_a_failed_last_run_is_red, test_a_failed_reader_is_red,
             test_a_failed_on_demand_load_is_red, test_no_good_run_inside_the_cadence_is_red,
             test_a_job_new_to_its_clock_is_judged_from_its_slot, test_a_chained_job_that_did_not_follow_its_parent_is_red,
             test_the_mcp_pull_is_judged_per_corpus, test_a_held_host_is_red,
             test_a_held_host_among_many_a_position_names_is_orange_not_red, test_pieces_to_go_is_orange,
             test_documents_waiting_is_orange, test_a_short_count_is_orange, test_a_declared_gap_is_orange,
             test_a_switched_off_capture_beside_a_running_load_is_orange]


def caught(registry) -> bool:
    for s in SCENARIOS:
        sl.LANES = LANES
        try:
            s(registry)
        except AssertionError:
            return True
    return False


@pytest.mark.parametrize("which,rule", [("RED_RULES", r) for r in sl.RED_RULES] +
                         [("ORANGE_RULES", r) for r in sl.ORANGE_RULES] + [("GREEN_RULES", r) for r in sl.GREEN_RULES])
def test_each_rule_removed_is_caught(registry, monkeypatch, which, rule):
    assert not caught(registry), "the scenarios must pass on the real rules"
    monkeypatch.setattr(sl, which, [r for r in getattr(sl, which) if r is not rule])
    assert caught(registry), f"{rule.__name__} removed and no scenario noticed"


# ── the real catalogue, the real gaps file ──

def test_every_register_has_a_lane_and_every_lane_job_is_in_the_catalogue():
    real = reg.load()
    names = {r for r, _, _ in sl.registers()}
    assert names == set(REAL_LANES), names ^ set(REAL_LANES)
    for register, lane in REAL_LANES.items():
        assert register in names, f"{register} is not on the board"
        for j in lane.update + lane.read:
            assert j in real, f"{register}: {j} is not in jobs.toml"


def test_every_named_position_exists():
    held = sl.position_hosts()
    for register, lane in REAL_LANES.items():
        for p in lane.positions:
            assert p in held, f"{register}: no position {p} with a hosts line"


def test_the_gaps_file_reads_and_names_registers_on_the_board():
    names = {r for r, _, _ in sl.registers()}
    gs = sl.gaps()
    assert gs and all(g["register"] in names for g in gs)
    assert {"courts", "tenders", "parliament", "insolvency", "tenancy_tribunal"} <= {g["register"] for g in gs}


def test_a_gap_with_no_source_is_refused(tmp_path):
    p = tmp_path / "g.toml"
    p.write_text('[[gap]]\nregister = "x"\nreason = "r"\nsince = "2026-11-04"\n')
    with pytest.raises(ValueError):
        sl.gaps(str(p))


def test_the_tenancy_tribunal_held_host_is_red_on_the_real_lanes(monkeypatch):
    monkeypatch.setattr(sl, "LANES", REAL_LANES)
    real = reg.load()
    f = sl.empty_facts(real)
    f["positions"] = sl.position_hosts()
    for j in REAL_LANES["tenancy_tribunal"].update:
        f["last_done"][j] = f["last_finished"][j] = done(2)
    f["refusals"] = {"forms.justice.govt.nz": {"host": "forms.justice.govt.nz", "state": "held",
                                               "why": "the order PDFs reset every request", "at": "2026-11-04T00:24:31+13:00"}}
    x = sl.light_of("tenancy_tribunal", False, f, NOW)
    assert x["light"] == "red" and x["reason"].startswith("the fetch gate holds forms.justice.govt.nz")
    for other in ("contract_disclosures", "courts"):                   # justice.govt.nz's other hosts are not held
        assert not any("forms.justice.govt.nz" in r for r in sl.light_of(other, True, f, NOW)["reasons"])


def test_the_council_lanes_and_the_tenancy_tribunal_on_the_real_lanes_and_gaps(monkeypatch):
    """The four lights of 5 November 2026, from the real lanes, positions and gaps file: the three councils' holds thin
    local_elections and councillor_interests (orange), council_procurement asks nothing (grey), and the Tenancy
    Tribunal's hold is said by its declared gap once its capture stops asking (orange)."""
    monkeypatch.setattr(sl, "LANES", REAL_LANES)
    real = reg.load()
    f = sl.empty_facts(real)
    f["positions"], f["gaps"] = sl.position_hosts(), sl.gaps()
    for lane in REAL_LANES.values():
        for j in lane.update + lane.read:
            f["last_done"][j] = f["last_finished"][j] = done(2)
    f["refusals"] = {h: {"host": h, "state": "held", "why": "HTTP 403", "at": "2026-11-04T22:20:11+13:00"}
                     for h in ("www.dunedin.govt.nz", "www.gdc.govt.nz", "www.kaipara.govt.nz", "forms.justice.govt.nz")}
    L = {r: sl.light_of(r, True, f, NOW) for r in ("local_elections", "councillor_interests", "council_procurement",
                                                    "tenancy_tribunal")}
    assert {r: x["light"] for r, x in L.items()} == {"local_elections": "orange", "councillor_interests": "orange",
                                                     "council_procurement": "grey", "tenancy_tribunal": "orange"}
    assert all(r.endswith("(declared 2026-11-05)") for r in L["tenancy_tribunal"]["reasons"])   # the gap, not the gate's line


def test_a_gap_s_hosts_are_a_list(tmp_path):
    p = tmp_path / "g.toml"
    p.write_text('[[gap]]\nregister = "x"\nreason = "r"\nsince = "d"\nsource = "s"\nhosts = "a.govt.nz"\n')
    with pytest.raises(ValueError):
        sl.gaps(str(p))
    p.write_text('[[gap]]\nregister = "x"\nreason = "r"\nsince = "d"\nsource = "s"\nhosts = ["a.govt.nz"]\n')
    assert sl.gaps(str(p))[0]["hosts"] == ("a.govt.nz",)


def test_write_is_whole(tmp_path):
    p = tmp_path / "checks" / "source-lights.json"
    sl.write({"computed_at": NOW.isoformat(), "lights": []}, str(p))
    assert json.loads(p.read_text())["lights"] == []


def test_every_corpus_the_pull_takes_is_some_lane_s_light():
    """5 November 2026: parliament-papers and parliament-sc-evidence were pulled from 4 November (67a34b4) and read
    by the parliament lane, but no light named them, so a pull caught on them never turned a light red. Every
    parliament, Hansard and diaries corpus qv4-mcp-pull takes is in a lane's `corpora`."""
    import os
    import tomllib
    with open(os.path.join(sl.REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        cmd = tomllib.load(f)["jobs"][sl.MCP_PULL]["command"]
    pulled = {cmd[i + 1] for i, a in enumerate(cmd) if a == "--corpus" and cmd[i + 1].startswith("parliament-")}
    named = {c for lane in REAL_LANES.values() for c in lane.corpora}
    assert pulled - named == set()


def test_the_nine_stopped_sources_on_the_real_lanes(monkeypatch):
    """9 November 2026 (3429166, d1e125c): every lane whose capture the boxes stopped is orange on the real catalogue,
    never green, with every job that still runs well; FMA's capture runs again from the MCP's copy, so it stays green;
    and a council host the gate holds no longer lights the two council lanes, whose captures ask nothing now."""
    monkeypatch.setattr(sl, "LANES", REAL_LANES)
    real = reg.load()
    f = sl.empty_facts(real)
    f["positions"] = sl.position_hosts()
    for lane in REAL_LANES.values():
        for j in lane.update + lane.read:
            f["last_done"][j] = f["last_finished"][j] = done(2)
    f["refusals"] = {"www.fndc.govt.nz": {"host": "www.fndc.govt.nz", "state": "held", "why": "HTTP 403", "at": None}}
    stopped = ("commerce_commission", "worksafe", "building_practitioners", "council_minutes", "councillor_interests",
               "local_elections", "courts")
    for r in stopped:
        x = sl.light_of(r, True, f, NOW)
        assert x["light"] == "orange" and "switched off in the catalogue" in x["reason"], (r, x)
        assert not any("fndc" in w for w in x["reasons"]), (r, x)
    assert sl.light_of("fma", True, f, NOW)["light"] == "green"
