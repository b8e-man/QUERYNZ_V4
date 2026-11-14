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
def lanes(monkeypatch, tmp_path):
    monkeypatch.setattr(sl, "LANES", LANES)
    monkeypatch.setattr(sl, "ASKS_DIR", str(tmp_path / "no-asks"))   # never the live handover/asks/ (11 November 2026)


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
    f["mcp_run"] = {"job": sl.MCP_PULL, "ok": False, "detail": "othercorp: FAILED HTTP 500"}   # never reached it
    assert light(f, "m") == "green"            # its budget spent before the corpus: not red for that (ruling 159)
    f["mcp_run"]["detail"] = "othercorp: 1→2 of 2; mcorp: FAILED McpError: HTTP 502"
    assert light(f, "m") == "red" and "failed on the mcorp corpus" in lights(f)["m"]["reason"]
    f["mcp_run"] = {"job": sl.MCP_PULL, "ok": False, "detail": "`corpora` failed: McpError: refused"}
    assert light(f, "m") == "red"
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


# ── the provider's freshness (ruling 159) ──

def fresh_facts(registry, days_old, cadence=7, paused_until=None, lane="mcorp-lane", read=True):
    """Lane m reads mcorp; the provider's newest arrival `days_old` days before NOW."""
    f = good_facts(registry)
    f["cadence"] = {"mcorp": {"days": cadence, "basis": "measured", "reason": "r", "paused_until": paused_until}}
    f["freshness"] = {"mcorp": {"at": ago(1), "corpus": "mcorp", "records": 10, "ingest_cursor": 10,
                                "newest_arrival": NOW - dt.timedelta(days=days_old), "arrivals_last_24h": 0,
                                "date_to": None, "pipeline_lane": lane, "pipeline_status": "active" if lane else None,
                                "pipeline_read": read, "grew_at": None}}
    return f


def test_a_copy_past_its_cadence_is_orange_and_past_three_times_red(registry):
    f = fresh_facts(registry, 6.5)
    assert light(f, "m") == "green" and lights(f)["m"]["fresh"].startswith("provider's copy: newest 29 Oct 00:00;")
    f = fresh_facts(registry, 7.5)
    m = lights(f)["m"]
    assert m["light"] == "orange", m
    assert m["reason"] == "the provider's copy of mcorp has had nothing new since 28 Oct 00:00; its source publishes about weekly"
    f = fresh_facts(registry, 20.5)
    assert light(f, "m") == "orange"
    f = fresh_facts(registry, 21.5)
    m = lights(f)["m"]
    assert m["light"] == "red" and m["reason"].endswith("(22 days, over three times that)"), m
    assert "fresh" not in lights(f)["x"]                                    # a lane the MCP does not feed


def test_freshness_is_the_provider_s_newest_arrival_not_our_pull(registry):
    """A pull that ran out of budget before the corpus (the estate-* corpora come last) is not red, and a pull that
    took everything does not make a stale copy fresh."""
    f = fresh_facts(registry, 1)
    f["mcp_run"] = {"job": sl.MCP_PULL, "ok": False, "ended": ago(1).isoformat(), "detail": "othercorp: 0→5 of 9 (budget)"}
    assert light(f, "m") == "green"
    f = fresh_facts(registry, 30)
    f["last_done"][sl.MCP_PULL] = f["last_finished"][sl.MCP_PULL] = done(0.5)
    assert light(f, "m") == "red"                                           # our pull an hour ago changes nothing


def test_a_declared_pause_and_a_closed_corpus_are_not_judged(registry):
    soon = (NOW + dt.timedelta(days=3)).date()
    f = fresh_facts(registry, 60, paused_until=soon)
    assert light(f, "m") == "green" and "not judged until 6 Nov" in lights(f)["m"]["fresh"]
    gone = (NOW - dt.timedelta(days=9)).date()                             # the pause ended nine days ago
    f = fresh_facts(registry, 60, paused_until=gone)
    m = lights(f)["m"]
    assert m["light"] == "orange", m                                       # 9 days since the pause, not 60
    f = fresh_facts(registry, 60, cadence=0)
    assert light(f, "m") == "green" and "fresh" not in lights(f)["m"]
    f = fresh_facts(registry, 60)
    f["cadence"] = {}                                                       # no line: not judged, and the cadence test
    assert light(f, "m") == "green"                                         # below holds every real corpus to a line


def test_no_freshness_measure_yet_says_so(registry):
    f = good_facts(registry)
    f["cadence"] = {"mcorp": {"days": 7, "basis": "default", "reason": "r", "paused_until": None}}
    m = lights(f)["m"]
    assert m["light"] == "green" and m["fresh"] == "provider's copy: no freshness measure yet"


def test_the_provider_list(registry):
    f = fresh_facts(registry, 30, lane=None)
    f["freshness"]["other"] = {**f["freshness"]["mcorp"], "corpus": "other", "pipeline_lane": "other-capture",
                               "pipeline_status": "blocked", "newest_arrival": NOW - dt.timedelta(days=9.5)}
    f["freshness"]["fine"] = {**f["freshness"]["mcorp"], "corpus": "fine", "newest_arrival": NOW - dt.timedelta(days=1),
                              "pipeline_lane": "fine-capture", "pipeline_status": "active"}
    f["freshness"]["unread"] = {**f["freshness"]["mcorp"], "corpus": "unread", "pipeline_lane": None,
                                "pipeline_read": False, "newest_arrival": NOW - dt.timedelta(days=7.4)}
    for k in ("other", "fine", "unread"):
        f["cadence"][k] = {"days": 7, "basis": "measured", "reason": "r", "paused_until": None}
    text = sl.provider_list(f, NOW)
    lines = text.splitlines()
    assert lines[0] == "# The ingest MCP's stale copies, 4 November 2026 12:00 NZ time"
    rows = [l for l in lines if l.startswith("| ") and not l.startswith("| Corpus") and not l.startswith("| ---")]
    assert rows == ["| mcorp | 5 Oct 12:00 | about weekly (every 7 days) | 23 | no lane in pipeline.yaml |",
                    "| other | 26 Oct 00:00 | about weekly (every 7 days) | 2 | other-capture (blocked) |",
                    "| unread | 28 Oct 02:24 | about weekly (every 7 days) | under 1 | not known (`pipeline` did not answer) |"]
    f["freshness"] = {"fine": f["freshness"]["fine"]}
    assert "Nothing is stale" in sl.provider_list(f, NOW)
    f["freshness"] = {}
    assert "No reading of `corpora` is held yet" in sl.provider_list(f, NOW)
    many = fresh_facts(registry, 30)
    for i in range(sl.PAGE_ROWS + 5):
        many["freshness"][f"c{i:02}"] = {**many["freshness"]["mcorp"], "corpus": f"c{i:02}"}
        many["cadence"][f"c{i:02}"] = many["cadence"]["mcorp"]
    text = sl.provider_list(many, NOW)
    assert sum(1 for l in text.splitlines() if l.startswith("| c")) == sl.PAGE_ROWS and "And 6 more." in text


def test_a_corpus_with_no_lane_and_nothing_new_is_listed_before_its_cadence(registry):
    """10 November 2026: thirteen estate-* corpora had no lane in the provider's pipeline and no arrival for one to
    eleven days; measured against their cadences only one was stale. No collector visible is listed now."""
    f = fresh_facts(registry, 3, lane=None)                                  # inside a weekly cadence, no lane
    f["freshness"]["busy"] = {**f["freshness"]["mcorp"], "corpus": "busy", "arrivals_last_24h": 40}
    f["freshness"]["laned"] = {**f["freshness"]["mcorp"], "corpus": "laned", "pipeline_lane": "laned-capture"}
    f["freshness"]["unread"] = {**f["freshness"]["mcorp"], "corpus": "unread", "pipeline_read": False}
    for k in ("busy", "laned", "unread"):
        f["cadence"][k] = f["cadence"]["mcorp"]
    assert [x["corpus"] for x in sl.stale_corpora(f, NOW)] == []
    assert [x["corpus"] for x in sl.no_collector(f, NOW)] == ["mcorp"]
    text = sl.provider_list(f, NOW)
    assert "No collector visible" in text and "| mcorp | 1 Nov 12:00 | about weekly |" in text
    feed = sl.provider_feed(f, NOW)
    assert [o["corpus"] for o in feed["no_collector"]] == ["mcorp"] and feed["stale"] == []
    f["cadence"]["mcorp"] = {**f["cadence"]["mcorp"], "days": 0}               # a closed corpus is never asked for
    assert sl.no_collector(f, NOW) == []


def test_the_provider_list_is_written_whole(tmp_path):
    p = tmp_path / "handover" / "mcp-stale.md"
    sl.write_provider_list("# x\n", str(p))
    assert p.read_text() == "# x\n" and not (tmp_path / "handover" / "mcp-stale.md.tmp").exists()


def test_a_bad_cadence_is_refused(tmp_path):
    p = tmp_path / "c.toml"
    for bad in ('corpus = "a"\ndays = 7\nbasis = "measured"\n',                                  # no reason
                'corpus = "a"\ndays = "weekly"\nbasis = "measured"\nreason = "r"\n',           # not a number
                'corpus = "a"\ndays = 7\nbasis = "guessed"\nreason = "r"\n',                   # not measured or default
                'corpus = "a"\ndays = 7\nbasis = "default"\nreason = "r"\n[[corpus]]\ncorpus = "a"\ndays = 1\n'
                'basis = "default"\nreason = "r"\n'):                                             # two lines
        p.write_text("[[corpus]]\n" + bad)
        with pytest.raises(ValueError):
            sl.cadences(str(p))
    p.write_text('[[corpus]]\ncorpus = "a"\ndays = 7\nbasis = "default"\nreason = "r"\npaused_until = "2026-12-01"\n')
    assert sl.cadences(str(p))["a"]["paused_until"] == dt.date(2026, 12, 1)


# ── mutants: each rule removed in turn is caught by the scenarios above ──

SCENARIOS = [test_everything_working_is_green, test_a_failed_last_run_is_red, test_a_failed_reader_is_red,
             test_a_failed_on_demand_load_is_red, test_no_good_run_inside_the_cadence_is_red,
             test_a_job_new_to_its_clock_is_judged_from_its_slot, test_a_chained_job_that_did_not_follow_its_parent_is_red,
             test_the_mcp_pull_is_judged_per_corpus, test_a_held_host_is_red,
             test_a_held_host_among_many_a_position_names_is_orange_not_red, test_pieces_to_go_is_orange,
             test_documents_waiting_is_orange, test_a_short_count_is_orange, test_a_declared_gap_is_orange,
             test_a_switched_off_capture_beside_a_running_load_is_orange,
             test_a_copy_past_its_cadence_is_orange_and_past_three_times_red]


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
    # from 10 November 2026 the capture reads the MCP's copy (--from-mcp) and asks the host nothing: the hold is not
    # its light. The boxes' own walk, were it switched back, is red on it again.
    import dataclasses
    assert "--from-mcp" in real["qv4-tenancy-tribunal-capture"].command
    assert sl.light_of("tenancy_tribunal", False, f, NOW)["light"] != "red"
    own = dataclasses.replace(real["qv4-tenancy-tribunal-capture"],
                              command=tuple(a for a in real["qv4-tenancy-tribunal-capture"].command if a != "--from-mcp"))
    f["registry"] = {**f["registry"], "qv4-tenancy-tribunal-capture": own}
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


def test_the_stopped_sources_read_the_mcp_copy_on_the_real_lanes(monkeypatch):
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
    # 10 November 2026: six read the MCP's copy (--from-mcp) and are on again; WorkSafe the seventh, 13 November
    for r in ("fma", "commerce_commission", "building_practitioners", "council_minutes", "councillor_interests",
              "local_elections", "worksafe"):
        x = sl.light_of(r, True, f, NOW)
        assert x["light"] == "green", (r, x)
        assert not any("fndc" in w for w in x["reasons"]), (r, x)



def test_every_corpus_a_lane_reads_or_the_pull_takes_has_a_cadence():
    """Ruling 159: a corpus with no cadence is never judged, so every corpus a lane reads and every corpus
    qv4-mcp-pull takes has its line in checks/mcp_cadence.toml, with a reason."""
    import os
    import tomllib
    cad = sl.cadences()
    with open(os.path.join(sl.REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        cmd = tomllib.load(f)["jobs"][sl.MCP_PULL]["command"]
    pulled = {cmd[i + 1] for i, a in enumerate(cmd) if a == "--corpus"}
    named = {c for lane in REAL_LANES.values() for c in lane.corpora}
    assert (pulled | named) - set(cad) == set()
    assert all(v["reason"] and v["basis"] in ("measured", "default") for v in cad.values())


def test_every_lane_reading_the_mcp_s_copy_names_its_corpus():
    """A capture or load run with --from-mcp reads its corpus only through the provider's copy, so its lane lists the
    corpus and its light shows the copy's freshness (10 November 2026: the six lanes of stream A3, FMA, the courts'
    two walks, the candidate returns)."""
    real = reg.load()
    for register, lane in REAL_LANES.items():
        mcp = [j for j in lane.update if j in real and "--from-mcp" in tuple(real[j].command or ())]
        if mcp:
            assert any(c.startswith("estate-") for c in lane.corpora), (register, mcp, lane.corpora)
    assert set(REAL_LANES["courts"].corpora) >= {"courts", "estate-courts-jdo", "estate-courts-era"}


def test_the_stale_copies_of_10_november_on_the_real_lanes(monkeypatch):
    """The MCP's `corpora` at 05:07 NZDT on 10 November 2026, judged on the real lanes and cadences: estate-courts
    (newest 30 Oct, weekly) is the one copy past its cadence; commerce commission, worksafe and councillors' interests
    (newest 8 Nov NZ time) are inside theirs, and go orange a week on if nothing arrives."""
    monkeypatch.setattr(sl, "LANES", REAL_LANES)
    real = reg.load()
    f = sl.empty_facts(real)
    f["cadence"] = sl.cadences()
    now = dt.datetime(2026, 11, 9, 16, 14, tzinfo=UTC)
    newest = {"estate-courts": "2026-10-30 03:38:35+13:00", "estate-commerce_commission": "2026-11-07 11:15:01+00:00",
              "estate-worksafe": "2026-11-07 12:02:47+00:00", "estate-councillor_interests": "2026-11-07 11:49:22+00:00",
              "estate-courts-jdo": "2026-11-10 00:41:34+13:00", "parliament-written-questions": "2026-10-23T13:33:24+00:00"}
    from support.mcpsource import freshness as F
    f["freshness"] = {c: {"at": now, "corpus": c, "newest_arrival": F.parse_time(t), "arrivals_last_24h": 0,
                          "pipeline_lane": None, "pipeline_status": None, "pipeline_read": True} for c, t in newest.items()}
    assert [x["corpus"] for x in sl.stale_corpora(f, now)] == []   # 11 November: the provider calls estate-courts a
    assert sl.copy_state("estate-courts", f, now)["state"] == "closed"  # closed copy; courtsofnz is live in `courts`
    later = now + dt.timedelta(days=7)
    assert {x["corpus"] for x in sl.stale_corpora(f, later)} >= {"estate-commerce_commission", "estate-worksafe"}
    for j in REAL_LANES["commerce_commission"].update:
        f["last_done"][j] = f["last_finished"][j] = {"state": "done", "finished_at": later - dt.timedelta(hours=2)}
    x = sl.light_of("commerce_commission", True, f, later)
    assert x["light"] == "orange" and x["reason"].startswith(
        "the provider's copy of estate-commerce_commission has had nothing new since 8 Nov 00:15"), x


# ── the provider's machine-readable list (Arthur, 10 November 2026) ──

def two_stale(registry):
    f = fresh_facts(registry, 30)                                           # mcorp: 23 days overdue, measured
    f["freshness"]["later"] = {**f["freshness"]["mcorp"], "corpus": "later", "pipeline_lane": None,
                               "newest_arrival": NOW - dt.timedelta(days=9.5), "records": 4, "arrivals_last_24h": 0}
    f["freshness"]["fine"] = {**f["freshness"]["mcorp"], "corpus": "fine", "newest_arrival": NOW - dt.timedelta(days=1)}
    f["cadence"]["later"] = {"days": 7, "basis": "default", "reason": "r", "paused_until": None}
    f["cadence"]["fine"] = f["cadence"]["mcorp"]
    return f


def test_the_feed_and_the_page_list_the_same_corpora(registry):
    f = two_stale(registry)
    feed = sl.provider_feed(f, NOW)
    page = sl.provider_list(f, NOW, feed=feed)
    on_page = [l.split(" | ")[0][2:] for l in page.splitlines() if l.startswith("| ") and not l.startswith(("| Corpus", "| ---"))]
    assert sorted(on_page) == [o["corpus"] for o in feed["stale"]] == ["later", "mcorp"]
    assert feed["schema_version"] == 1 and feed["measured_at"] == ago(1).isoformat() and feed["repaired"] == []
    m = feed["stale"][1]
    assert m == {"corpus": "mcorp", "newest_arrival": (NOW - dt.timedelta(days=30)).isoformat(), "records": 10,
                 "arrivals_last_24h": 0, "cadence_days": 7, "cadence_measured": True, "days_overdue": 23.0,
                 "pipeline_lane": "mcorp-lane", "asked": sl.ASKED,
                 "request_id": "mcorp@" + (NOW - dt.timedelta(days=30)).isoformat()}
    assert feed["stale"][0]["cadence_measured"] is False and feed["stale"][0]["pipeline_lane"] is None
    assert sl.provider_feed(f, NOW + dt.timedelta(hours=5))["stale"][1]["request_id"] == m["request_id"]   # stable


def test_a_repair_is_confirmed_only_by_fresh_arrivals(registry, tmp_path):
    f = two_stale(registry)
    page, json_path = tmp_path / "mcp-stale.md", tmp_path / "mcp-stale.json"
    _, feed = sl.provider_outputs(f, NOW, str(page), str(json_path), str(tmp_path / "none.md"))
    sl.write_provider_feed(feed, str(json_path))
    assert json.loads(json_path.read_text()) == feed
    later = NOW + dt.timedelta(hours=1)
    f["cadence"]["later"] = {**f["cadence"]["later"], "days": 31}           # no longer stale, but nothing arrived
    f["freshness"]["mcorp"] = {**f["freshness"]["mcorp"], "newest_arrival": later - dt.timedelta(minutes=5)}
    text, feed2 = sl.provider_outputs(f, later, str(page), str(json_path), str(tmp_path / "none.md"))
    assert feed2["stale"] == [] and [o["corpus"] for o in feed2["repaired"]] == ["mcorp"]
    r = feed2["repaired"][0]
    assert r["request_id"] == feed["stale"][1]["request_id"] and r["repaired_at"] == (later - dt.timedelta(minutes=5)).isoformat()
    assert "Repaired (new records have arrived since it was listed): mcorp (" in text
    sl.write_provider_feed(feed2, str(json_path))                           # the next run keeps it, a week at most
    assert [o["corpus"] for o in sl.provider_outputs(f, later + dt.timedelta(days=6), str(page), str(json_path),
                                                     str(tmp_path / "none.md"))[1]["repaired"]] == ["mcorp"]
    f["freshness"]["mcorp"] = {**f["freshness"]["mcorp"], "newest_arrival": later + dt.timedelta(days=7.9)}   # still fresh
    assert sl.provider_outputs(f, later + dt.timedelta(days=8), str(page), str(json_path),
                               str(tmp_path / "none.md"))[1]["repaired"] == []


CLOSING = "## For the provider: closing the loop\n\nCall the tool `x`. Keep *this* verbatim.\n\n- one\n- two\n"


def test_the_closing_section_is_carried_through_verbatim(registry, tmp_path):
    f = two_stale(registry)
    page = tmp_path / "mcp-stale.md"
    page.write_text("# A hand-made list\n\n| old | table |\n\n" + CLOSING)
    text, _ = sl.provider_outputs(f, NOW, str(page), str(tmp_path / "x.json"), str(tmp_path / "none.md"))
    assert text.endswith("\n" + CLOSING) and "hand-made" not in text
    page.write_text(text)                                                   # and again from our own page
    again, _ = sl.provider_outputs(f, NOW, str(page), str(tmp_path / "x.json"), str(tmp_path / "none.md"))
    assert again == text and again.count(sl.CLOSING_TITLE) == 1
    tpl = tmp_path / "mcp-stale.closing.md"
    tpl.write_text("## For the provider: closing the loop\n\nThe template wins.\n")
    assert sl.provider_outputs(f, NOW, str(page), str(tmp_path / "x.json"), str(tpl))[0].endswith("The template wins.\n")
    page.write_text("# no section\n")
    assert sl.provider_outputs(f, NOW, str(page), str(tmp_path / "x.json"), str(tmp_path / "none.md"))[0].rstrip().endswith(
        f"What is asked, for each: {sl.ASKED}.")


def test_a_lane_s_request_reaches_the_provider_page_and_feed(tmp_path):
    """Ruling 165: a lane's file under handover/asks/ is carried to the provider whole; a file that does not read, or
    asks for nothing, is skipped."""
    import datetime as dt
    import json
    from checks import source_lights as S
    (tmp_path / "tenancy_tribunal.json").write_text(json.dumps({
        "corpus": "estate-tenancy_tribunal", "source": "Tenancy Tribunal orders", "listed": 33847, "missing": 2,
        "earliest_take_down": "2028-06-23", "by_take_down_month": [{"month": "2028-06", "orders": 2}],
        "orders": [{"order_id": "1", "take_down": "2028-06-23"}, {"order_id": "2", "take_down": "2028-06-30"}],
        "asked": "gather these orders", "request_id": "estate-tenancy_tribunal@short-2-2028-06-23"}), encoding="utf-8")
    (tmp_path / "broken.json").write_text("{", encoding="utf-8")
    (tmp_path / "none.json").write_text(json.dumps({"corpus": "x", "missing": 0}), encoding="utf-8")
    (tmp_path / "tenders.json").write_text(json.dumps({                    # 11 November: a second lane, its own ask
        "corpus": "estate-tenders", "listed": 9, "missing": 9, "earliest_take_down": None,
        "asked": "gather the GETS award-notice files", "request_id": "estate-tenders@files-9-held-2026-08-14"}),
        encoding="utf-8")
    (tmp_path / "old-collectors.json").write_text(json.dumps({"asks": [                # one file, several requests
        {"corpus": "estate-coronial", "missing": 1, "asked": "a collector"}, {"corpus": "estate-nothing", "missing": 0},
        "not a request"]}), encoding="utf-8")
    now = dt.datetime(2026, 11, 10, tzinfo=dt.timezone.utc)
    feed = S.provider_feed({"freshness": {}}, now, None, asks_dir=str(tmp_path))
    assert [o["corpus"] for o in feed["short_of_source"]] == ["estate-coronial", "estate-tenancy_tribunal", "estate-tenders"]
    assert feed["short_of_source"][1]["orders"][1]["order_id"] == "2"
    page = S.provider_list({"freshness": {}}, now, "", feed)
    assert "Short of the source's own list" in page and "| estate-tenancy_tribunal | 33,847 | 2 | 2028-06-23 |" in page
    assert "| estate-tenders | 9 | 9 | ? |" in page
    assert "What is asked for estate-tenancy_tribunal: gather these orders." in page      # each lane's own words
    assert "What is asked for estate-tenders: gather the GETS award-notice files." in page


def test_a_host_the_mcp_collects_for_a_lane_never_lights_it():
    # 14 November 2026: charities stayed red on the www.charities.govt.nz hold after its six pages went to the MCP
    from checks import source_lights as SL
    lane = SL.Lane(hosts=("www.odata.charities.govt.nz",), positions=("p",), mcp_hosts=("www.charities.govt.nz",))
    assert SL.lane_hosts(lane, {"p": ("www.charities.govt.nz", "www.odata.charities.govt.nz")}) == {"odata.charities.govt.nz"}


# ── every source, a link and one line (Arthur, 14 November 2026) ──

class _Pull:
    command = ["python", "-m", "support.mcpsource", "--corpus", "estate-x", "--corpus", "unread-y"]


def _src_facts(**kw):
    f = sl.empty_facts(registry={sl.MCP_PULL: _Pull()})
    f.update(kw)
    return f


LN = {"registers": {"x": "https://x.govt.nz"}, "corpora": {"held-z": "https://z.govt.nz"},
      "requests": [{"id": "r1", "title": "White Pages whole", "corpus": "estate-w", "asked": dt.date(2026, 11, 1),
                    "due": dt.date(2026, 11, 2), "url": "https://w.co.nz"},
                   {"id": "r2", "title": "later", "corpus": "estate-v", "asked": dt.date(2026, 11, 1),
                    "due": dt.date(2026, 11, 20), "url": "https://v.co.nz"},
                   {"id": "r3", "title": "grown", "corpus": "estate-x", "asked": dt.date(2026, 11, 1),
                    "until_records": 10, "url": "https://x.govt.nz"}]}


def test_every_source_has_a_link_and_one_line_starting_with_its_light(monkeypatch):
    monkeypatch.setattr(sl, "LANES", {"x": sl.Lane(update=("qv4-x-capture",), corpora=("estate-x",))})
    fresh = {"estate-x": {"records": 50, "newest_arrival": NOW - dt.timedelta(hours=2)},
             "unread-y": {"records": 5, "newest_arrival": NOW},
             "held-z": {"records": 7, "newest_arrival": NOW}}
    facts = _src_facts(freshness=fresh, cadence={"estate-x": {"days": 1, "basis": "m", "reason": "", "paused_until": None}},
                       news=[{"host": "odt.co.nz", "articles": 9, "earliest": "2008-01-01", "newest": "2026-11-02"},
                             {"host": "old.co.nz", "articles": 3, "earliest": "2001-01-01", "newest": "2026-10-01"}])
    lights = [{"register": "x", "light": "green", "reason": "up to date: last good update 3 Nov"}]
    rows = {(r["kind"], r["name"]): r for r in sl.sources(lights, facts, NOW, {"x": "The X register"}, LN)}
    assert all(r["line"].split(":")[0] == sl.WORDS[r["light"]] and "\n" not in r["line"] for r in rows.values())
    assert rows["register", "x"]["url"] == "https://x.govt.nz" and rows["register", "x"]["label"] == "The X register"
    assert rows["copy", "estate-x"]["light"] == "green" and rows["copy", "estate-x"]["url"] == "https://x.govt.nz"
    assert rows["copy", "unread-y"]["light"] == "orange" and "no register reads it" in rows["copy", "unread-y"]["line"]
    assert rows["copy", "held-z"]["light"] == "grey" and "does not copy it" in rows["copy", "held-z"]["line"]
    assert rows["news", "odt.co.nz"]["light"] == "green" and rows["news", "odt.co.nz"]["url"] == "https://odt.co.nz"
    assert rows["news", "old.co.nz"]["light"] == "orange"
    assert rows["request", "r1"]["light"] == "red" and "nothing has landed" in rows["request", "r1"]["line"]
    assert rows["request", "r2"]["light"] == "orange" and "20 Nov" in rows["request", "r2"]["line"]
    assert ("request", "r3") not in rows          # its corpus holds more than the request's mark: the copy row speaks


def test_a_request_whose_corpus_has_not_grown_past_its_mark_still_stands(monkeypatch):
    monkeypatch.setattr(sl, "LANES", {})
    facts = _src_facts(freshness={"estate-x": {"records": 10, "newest_arrival": NOW}})
    names = [r["name"] for r in sl.sources([], facts, NOW, {}, LN) if r["kind"] == "request"]
    assert names == ["r1", "r2", "r3"]


def test_the_links_file_reads_and_names_every_register_of_the_catalogue():
    ln = sl.links()
    missing = [r for r, _, _ in sl.registers() if r not in ln["registers"]]
    assert not missing, f"checks/source_links.toml names no link for {missing}"
    assert all(u.startswith(("https://", "/")) for u in list(ln["registers"].values()) + list(ln["corpora"].values()))
    for r in ln["requests"]:
        assert r["id"] and r["title"] and isinstance(r["asked"], dt.date)


def test_compute_writes_the_sources_beside_the_lights(monkeypatch):
    monkeypatch.setattr(sl, "LANES", {})
    out = sl.compute(_src_facts(), NOW, regs=[("x", "X", True)])
    assert [r["name"] for r in out["sources"] if r["kind"] == "register"] == ["x"]


def test_a_news_site_gathered_another_way_is_left_off_and_a_standing_request_stays_while_copies_arrive(monkeypatch):
    # Arthur, 14 November 2026: "remove the ones that we ARe gathering through other means"
    monkeypatch.setattr(sl, "LANES", {})
    ln = {**LN, "other_means": ["gazette.govt.nz", "*.infocouncil.biz", "infocouncil.*"],
          "requests": [{"id": "m", "title": "media", "corpus": "estate-news", "asked": dt.date(2026, 11, 1),
                        "due": dt.date(2026, 11, 2), "standing": True}]}
    news = [{"host": h, "articles": 1, "newest": "2026-11-01"} for h in
            ("www.gazette.govt.nz", "christchurch.infocouncil.biz", "infocouncil.dunedin.govt.nz", "odt.co.nz", "notgazette.govt.nz")]
    facts = _src_facts(news=news, freshness={"estate-news": {"records": 5418, "newest_arrival": NOW}})
    rows = sl.sources([], facts, NOW, {}, ln)
    assert sorted(r["name"] for r in rows if r["kind"] == "news") == ["notgazette.govt.nz", "odt.co.nz"]
    req = [r for r in rows if r["kind"] == "request"]
    assert len(req) == 1 and req[0]["light"] == "orange" and "5,418 records" in req[0]["line"]


def test_a_copy_held_another_way_is_grey_with_its_reason_not_orange(monkeypatch):
    monkeypatch.setattr(sl, "LANES", {})
    ln = {**LN, "covered": {"unread-y": "every file held by the courts lane"}}
    facts = _src_facts(freshness={"unread-y": {"records": 5, "newest_arrival": NOW}})
    row = next(r for r in sl.sources([], facts, NOW, {}, ln) if r["name"] == "unread-y")
    assert row["light"] == "grey" and row["line"].endswith("every file held by the courts lane")
