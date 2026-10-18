"""The run ledger must be able to say a job DIED, not just that it erred
(carried from ops/fleet/tests/test_runs.py; peak memory added).

Two append-only rows per run, so a start with no end survives as evidence
of a crash. A ledger that mutated a row in place would have lost exactly
the case worth finding."""
from __future__ import annotations

import pathlib

import pytest

from support.scheduler import runs


@pytest.fixture
def led(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "job-runs.jsonl"


def test_a_completed_run_reads_back_whole(led):
    rid = runs.begin("qv4-reread", "party_returns", card="node2:1", requested_model="qwen3.6-35b-a3b-q4km",
                     args={"limit": 9}, queue_id=7, box="node2", ledger=led)
    runs.finish(rid, outcome=runs.OK, n_in=9, n_out=7, served_model="qwen3.6-35b-a3b-q4km", peak_mb=900,
                declared_mb=1536, ledger=led)
    r, = runs.runs(led)
    assert (r.job_type, r.lane, r.card, r.queue_id, r.box) == ("qv4-reread", "party_returns", "node2:1", 7, "node2")
    assert (r.outcome, r.n_in, r.n_out, r.peak_mb) == (runs.OK, 9, 7, 900)
    assert r.unfinished is False and r.model_is_known and not r.over_declared


def test_a_run_that_never_ended_is_visible_as_unfinished(led):
    """THE POINT OF TWO ROWS. A job killed mid-run, an OOM, a reboot: with
    one mutable row per run this is indistinguishable from a run that never
    started."""
    runs.begin("qv4-x", ledger=led)
    assert [r.unfinished for r in runs.runs(led)] == [True]
    assert len(runs.unfinished(led)) == 1


def test_the_ledger_is_append_only_so_a_finish_adds_rather_than_rewrites(led):
    rid = runs.begin("qv4-x", ledger=led)
    runs.finish(rid, outcome=runs.OK, ledger=led)
    assert [r["kind"] for r in runs.rows(led)] == ["start", "end"]


def test_errors_have_a_denominator(led):
    for i in range(4):
        rid = runs.begin("qv4-x", ledger=led)
        runs.finish(rid, outcome=runs.OK if i else runs.FAILED, error=None if i else "ConnectError", ledger=led)
    s = runs.summary(led)["qv4-x"]
    assert (s["runs"], s["ok"], s["failed"]) == (4, 3, 1)
    assert [r.error for r in runs.failures(led)] == ["ConnectError"]


def test_a_run_whose_model_is_unknown_is_counted_as_such(led):
    rid = runs.begin("qv4-x", ledger=led)
    runs.finish(rid, outcome=runs.OK, ledger=led)          # no served_model
    assert runs.summary(led)["qv4-x"]["model_unknown"] == 1
    assert runs.runs(led)[0].model_is_known is False


def test_a_peak_above_the_declared_memory_is_flagged(led):
    """Step 2.6: the run record keeps the peak, and a job whose peak passes
    its declared cost is flagged so the figure is corrected."""
    rid = runs.begin("qv4-x", ledger=led)
    runs.finish(rid, outcome=runs.OK, peak_mb=2100, declared_mb=1536, ledger=led)
    r, = runs.over_declared(led)
    assert r.run_id == rid
    s = runs.summary(led)["qv4-x"]
    assert s["over_declared"] == 1 and s["peak_mb"] == 2100


def test_a_placement_decision_records_its_reason_verbatim(led):
    runs.placement("node2:1", "load", "qv4-reread", "qv4-reread (priority 20) takes this card, 40 queued, load",
                   profile="text-reader", ledger=led)
    row, = [r for r in runs.rows(led) if r["kind"] == "placement"]
    assert row["card"] == "node2:1" and row["action"] == "load" and row["profile"] == "text-reader"
    assert "40 queued" in row["why"]


def test_a_torn_line_does_not_lose_the_rest_of_the_history(led):
    rid = runs.begin("qv4-x", ledger=led)
    with led.open("a") as f:
        f.write('{"kind": "end", "run_id": "tr\n')     # a half-written line
    runs.finish(rid, outcome=runs.OK, ledger=led)
    assert [r.outcome for r in runs.runs(led)] == [runs.OK]


def test_an_unwritable_ledger_does_not_take_the_job_down(tmp_path):
    blocked = tmp_path / "nope"
    blocked.write_text("i am a file, not a directory")
    rid = runs.begin("qv4-x", ledger=blocked / "runs.jsonl")
    runs.finish(rid, outcome=runs.OK, ledger=blocked / "runs.jsonl")
    assert isinstance(rid, str) and len(rid) == 16


def test_runs_are_separated_by_job_type(led):
    runs.finish(runs.begin("qv4-a", "x", ledger=led), outcome=runs.OK, ledger=led)
    runs.finish(runs.begin("qv4-b", "y", ledger=led), outcome=runs.OK, ledger=led)
    assert [r.lane for r in runs.for_job("qv4-b", led)] == ["y"]
    assert set(runs.summary(led)) == {"qv4-a", "qv4-b"}


def test_a_second_end_row_is_the_last_word(led):
    rid = runs.begin("qv4-x", ledger=led)
    runs.finish(rid, outcome=runs.FAILED, error="timeout", ledger=led)
    runs.finish(rid, outcome=runs.OK, ledger=led)
    assert runs.runs(led)[0].outcome == runs.OK
    assert len(runs.rows(led)) == 3


def test_an_absent_ledger_reads_as_no_history_not_an_error(led):
    assert runs.runs(led) == [] and runs.summary(led) == {}


def test_the_environment_can_redirect_the_ledger(tmp_path, monkeypatch):
    p = tmp_path / "elsewhere.jsonl"
    monkeypatch.setenv(runs.ENV, str(p))
    runs.begin("qv4-x")
    assert p.exists() and len(runs.runs()) == 1


def test_an_unfinished_run_is_not_counted_as_a_success(led):
    runs.begin("qv4-x", ledger=led)                 # dies
    runs.finish(runs.begin("qv4-x", ledger=led), outcome=runs.OK, ledger=led)
    s = runs.summary(led)["qv4-x"]
    assert (s["runs"], s["ok"], s["unfinished"]) == (2, 1, 1)
