"""The catalogue's checks, each one a shape that has cost something
(carried from ops/fleet/tests/test_jobs.py, on TOML and profiles).

The headroom rule is the important one. The old `ec_pageread` job asked for
up to 16,000 OUTPUT tokens; the 8-slot server gave each request 16,384
tokens TOTAL; 409 of its calls went there, leaving ~384 tokens for the page
it was reading. This is the rule that makes it un-writable."""
from __future__ import annotations

import pathlib

from support.scheduler import registry as reg
from support.scheduler.tests import fixtures as fx

BASE_JOBS = """
version = 1
[queueing]
slice_seconds = 3600
"""

JOB = """
[jobs.{name}]
needs = "{needs}"
profile = "{profile}"
memory_gb = {mem}
deadline_s = {deadline}
query_timeout_s = {qt}
priority = {prio}
command = ["true"]
{extra}
"""

PROFILE = """
[profiles.{name}]
model = "{model}"
weights = ["w.gguf"]
slots = {np}
context = {ctx}
temperature = 0.0
max_tokens = {out}
{mem}
{geom}
"""


def job(name="qv4-a", needs="model-profile", profile="p", mem=1.0, deadline=300, qt=60, prio=1, extra=""):
    return JOB.format(name=name, needs=needs, profile=profile if needs == "model-profile" else "", mem=mem,
                      deadline=deadline, qt=qt, prio=prio, extra=extra)


def profile(name="p", model="M", np=1, ctx=16384, out=2000, mem="memory_gb = 24.0", geom=None):
    return PROFILE.format(name=name, model=model, np=np, ctx=ctx, out=out, mem=mem,
                          geom=geom if geom is not None else f'measured_geometry = "{ctx}x{np}"')


def files(tmp_path: pathlib.Path, jobs: str = "", profiles: str = ""):
    j = tmp_path / "j.toml"
    p = tmp_path / "p.toml"
    j.write_text(BASE_JOBS + jobs)
    p.write_text(profiles)
    return j, p


# ── context arithmetic: the ec_pageread defect as a rule ─────────────────────

def test_context_is_per_request_and_the_server_flag_is_derived(tmp_path):
    """`-c` is the TOTAL across slots. A server at -c 131072 -np 8 gives one
    request 16,384 tokens. The profile declares the per-request figure and
    derives the flag, so nobody does that arithmetic by hand again."""
    _, p = files(tmp_path, profiles=profile(ctx=16384, np=8))
    pr = reg.profiles(p)["p"]
    assert pr.total_context == 131072
    assert pr.serve_flags() == ["-c", "131072", "-np", "8"]


def test_an_output_budget_that_swallows_its_context_is_refused(tmp_path):
    """16,000 output tokens in a 16,384-token slot leaves 384 for the page."""
    j, p = files(tmp_path, job(), profile(ctx=16384, out=16000))
    probs = reg.problems(j, p)
    assert any("leaves 384 tokens for the prompt" in x for x in probs), probs


def test_a_generous_context_for_the_same_budget_passes(tmp_path):
    j, p = files(tmp_path, job(), profile(ctx=50000, out=16000, np=2, mem="memory_gb = 25.2"))
    assert reg.problems(j, p) == []
    assert reg.profiles(p)["p"].headroom == 34000


# ── the job contract rides the catalogue ─────────────────────────────────────

def test_a_job_without_the_prefix_is_refused(tmp_path):
    j, p = files(tmp_path, job(name="a"), profile())
    assert any("qv4- prefix" in x for x in reg.problems(j, p))


def test_a_query_time_limit_over_the_deadline_is_refused(tmp_path):
    j, p = files(tmp_path, job(deadline=300, qt=300), profile())
    assert any("query time limit sits under the deadline" in x for x in reg.problems(j, p))


def test_a_deadline_at_or_over_the_interval_is_refused(tmp_path):
    j, p = files(tmp_path, job(deadline=3600, qt=60, extra="every_s = 3600"), profile())
    assert any("shorter than the interval" in x for x in reg.problems(j, p))


def test_a_job_naming_an_unknown_profile_is_refused(tmp_path):
    j, p = files(tmp_path, job(profile="ghost"), profile())
    assert any("names profile 'ghost'" in x for x in reg.problems(j, p))


def test_a_processor_job_names_no_profile_and_needs_none(tmp_path):
    j, p = files(tmp_path, job(needs="processor"), profile())
    assert reg.problems(j, p) == []
    assert reg.load(j)["qv4-a"].profile is None


def test_a_timetable_is_one_thing_and_a_standing_service_has_none(tmp_path):
    j, p = files(tmp_path, job(extra='every_s = 600\nat_utc = "03:00"'), profile())
    assert any("every_s or at_utc, not both" in x for x in reg.problems(j, p))
    j, p = files(tmp_path, job(deadline=100, extra='wanted = 1\nevery_s = 600'), profile())
    assert any("standing service has no timetable" in x for x in reg.problems(j, p))
    j, p = files(tmp_path, job(extra='at_utc = "25:00"'), profile())
    assert any("is not HH:MM" in x for x in reg.problems(j, p))


def test_a_class_outside_the_three_is_refused(tmp_path):
    j, p = files(tmp_path, job(extra='class = "urgent"'), profile())
    assert any("class 'urgent'" in x for x in reg.problems(j, p))


# ── the scheduler's preconditions ────────────────────────────────────────────

def test_duplicate_priorities_are_refused(tmp_path):
    """Round-robin orders each round by priority; a tie it cannot break makes
    the order depend on dict insertion, which is not a policy."""
    j, p = files(tmp_path, job(prio=1) + job(name="qv4-b", prio=1), profile())
    assert any("priorities are not unique" in x for x in reg.problems(j, p))


def test_a_profile_with_no_model_is_refused(tmp_path):
    j, p = files(tmp_path, job(), profile(model=""))
    assert any("names no model" in x for x in reg.problems(j, p))


# ── measurement provenance ───────────────────────────────────────────────────

def test_a_profile_naming_a_server_the_probe_does_not_know_is_refused(tmp_path):
    """A `binary` the probe never looks for would make the profile loadable
    nowhere, silently (the TeleOCR shape, card
    teleocr-needs-a-patched-server-the-scheduler-cannot-choose)."""
    j, p = files(tmp_path, job(), profile() + 'binary = "qv4-llama-server-ghost"\n')
    assert any("binary 'qv4-llama-server-ghost' is not a program the probe looks for" in x for x in reg.problems(j, p))
    j, p = files(tmp_path, job(), profile() + 'binary = "qv4-llama-server-teleocr"\n')
    assert reg.problems(j, p) == [] and reg.profiles(p)["p"].binary == "qv4-llama-server-teleocr"
    assert reg.profiles(fx.write(tmp_path)[1])["bge"].binary is None


def test_a_memory_figure_measured_at_another_geometry_is_a_warning(tmp_path):
    """A footprint measured at 2x50k says nothing about 6x32k — the KV cache
    is most of the difference. Carried across a geometry change it is not
    evidence, so the registry says so instead of implying otherwise. And it
    is a WARNING, not a failure: a gate that fails on work not yet done gets
    switched off, and then it stops catching what is truly wrong."""
    j, p = files(tmp_path, job(), profile(ctx=32768, np=6, geom='measured_geometry = "50000x2"'))
    warns = reg.warnings(j, p)
    assert any("was measured at 50000x2" in w for w in warns), warns
    assert reg.problems(j, p) == []


def test_a_profile_with_no_measured_memory_is_a_warning(tmp_path):
    j, p = files(tmp_path, job(), profile(mem="", geom=""))
    assert any("no measured memory_gb" in w for w in reg.warnings(j, p))
    assert reg.problems(j, p) == []


def test_an_unmeasured_load_time_is_a_warning_not_a_problem(tmp_path):
    j, p = files(tmp_path, job(), profile())
    assert any("load time not yet measured" in w for w in reg.warnings(j, p))
    assert reg.problems(j, p) == []


# ── switching cost, which the queueing rules turn on ─────────────────────────

def test_the_same_profile_is_a_free_handover_and_other_settings_are_a_load(tmp_path):
    registry, profiles, _ = fx.catalogue(tmp_path)
    p50, p16, bge = profiles["qwen-50k"], profiles["qwen-16k"], profiles["bge"]
    assert reg.switch_cost(p50, p50) == "handover"
    assert reg.switch_cost(p50, p50, same_job=True) == "none"
    assert reg.switch_cost(p50, p16) == "load", "the same weights at other settings is a server restart: a load"
    assert reg.switch_cost(p50, bge) == "load"
    assert reg.switch_cost(None, p50) == "load", "a cold card"
    assert registry["doc"].profile == registry["reason"].profile == "qwen-50k"


# ── the real catalogue ───────────────────────────────────────────────────────

def test_the_shipped_catalogue_is_green():
    """Against the estate's own files: every job carries qv4-, names a real
    profile, keeps its query time limit under its deadline; the four
    profiles of step 2.15 are there, and no card is reserved: ruling 121 took
    the frozen chat model out of the carve-out and qv4-radiance holds both
    of node2's cards as a standing profile the planner never plans."""
    assert reg.problems() == []
    assert set(reg.profiles()) >= {"text-reader", "review", "embedding", "page-reader"}
    assert reg.reservations() == []
    jobs = reg.load()
    assert all(n.startswith("qv4-") for n in jobs)
    assert jobs["qv4-reread"].pieces and jobs["qv4-reread"].profile == "text-reader"
    assert jobs["qv4-scheduler-report"].every_s == 3600 and jobs["qv4-scheduler-report"].profile is None


def test_profile_weights_resolve_under_the_models_folder():
    pr = reg.profiles()["page-reader"]
    paths = pr.weight_paths("/m")
    assert paths == ["/m/vision-glm-ocr/GLM-OCR-Q8_0.gguf", "/m/vision-glm-ocr/mmproj-GLM-OCR-Q8_0.gguf"]


def test_a_daily_timetable_may_name_several_times_and_each_is_checked(tmp_path):
    j, p = files(tmp_path, job(needs="processor", extra='at_utc = ["20:00", "08:00"]\nnice = 10'), profile())
    jt = reg.load(j)["qv4-a"]
    assert jt.at_utc == ("20:00", "08:00") and jt.nice == 10
    assert not [x for x in reg.problems(j, p) if "qv4-a" in x]
    j, p = files(tmp_path, job(needs="processor", extra='at_utc = ["20:00", "20:00"]'), profile())
    assert any("names a time twice" in x for x in reg.problems(j, p))
    j, p = files(tmp_path, job(needs="processor", extra='at_utc = ["20:00", "24:00"]'), profile())
    assert any("is not HH:MM" in x for x in reg.problems(j, p))
    j, p = files(tmp_path, job(needs="processor", extra='nice = 30'), profile())
    assert any("nice is 0 to 19" in x for x in reg.problems(j, p))
    j, p = files(tmp_path, job(needs="processor"), profile())
    assert reg.load(j)["qv4-a"].at_utc == () and reg.load(j)["qv4-a"].nice == 0


def test_the_four_founding_jobs_are_on_the_queues_clock_in_utc():
    """Step 2.12: the founding timers' jobs, with the deadlines their units
    carried, a query limit under each, and their times in UTC (the units
    held NZDT: 07:30, 09:00/21:00, 04:30; the off-site dump's 03:05 became
    track B's copy at 21:00)."""
    cat = reg.load()
    want = {"qv4-checks-board": (("18:30",), 3600), "qv4-checks-heartbeat": (("20:00", "08:00"), 300),
            "qv4-full-tier": (("15:30",), 7200), "qv4-offsite-copy": (("08:00",), 16200)}
    for name, (times, deadline) in want.items():
        jt = cat[name]
        assert jt.at_utc == times and jt.needs.deadline_s == deadline and jt.cls == "due" and jt.enabled, name
        assert 0 < jt.needs.query_timeout_s < jt.needs.deadline_s, name
        assert jt.needs.needs == "processor" and not jt.every_s and not jt.wanted, name
    assert cat["qv4-offsite-copy"].requires == ("pg_dump", "gpg", "zstd"), "node1 once lacked a program and nobody knew"
    assert "qv4-offsite-dump" not in cat, "the step 1.8 dump was retired by track B (offsite-2b)"
