"""Ruling 115, the parts that need no database: the raised figure, the run
record of a re-run, and the lines the report and `memory` print."""
from __future__ import annotations

import datetime as dt
import pathlib

import pytest

from support.scheduler import queue as q
from support.scheduler import runner, runs
from support.scheduler.worker import memory_lines


@pytest.mark.parametrize("declared_gb, raised_gb", [
    (0.1, 0.5),     # ceiling 128 MB → 256 MB → the next 0.5 GB
    (0.3, 1.0),     # qv4-mcp-pull: ceiling 384 → 768 MB; it needed 615
    (0.5, 1.5),     # ceiling 640 → 1,280 MB → 1.5 GB
    (1.0, 2.5),     # qv4-beehive-load: ceiling 1,280 → 2,560 MB, exactly 2.5 GB; it needed 2,459
    (1.5, 4.0),     # ceiling 1,920 → 3,840 MB → 4.0 GB
])
def test_the_raise_is_twice_the_ceiling_crossed_rounded_up_to_half_a_gb(declared_gb, raised_gb):
    assert q.raised_figure_gb(runner.ceiling_for(declared_gb)) == raised_gb


def test_a_re_run_says_so_in_the_run_record_and_a_first_run_does_not(tmp_path: pathlib.Path):
    led = tmp_path / "job-runs.jsonl"
    first = runs.begin("qv4-x", queue_id=1, ledger=led)
    runs.finish(first, outcome=runs.FAILED, peak_mb=700, declared_mb=512, working_mb=512, note="memory", ledger=led)
    again = runs.begin("qv4-x", queue_id=2, ledger=led)
    runs.finish(again, outcome=runs.OK, peak_mb=700, declared_mb=512, working_mb=1536, rerun_of_raise=7, ledger=led)
    a, b = runs.runs(led)
    assert not a.rerun and a.rerun_of_raise is None
    assert b.rerun and b.rerun_of_raise == 7 and b.working_mb == 1536 and b.over_declared
    end = [r for r in runs.rows(led) if r["kind"] == "end"][1]
    assert end["rerun_of_raise"] == 7 and end["over_declared"] is True


def raise_row(**kw):
    d = {"id": 3, "at": dt.datetime(2026, 10, 28, 9, 0, tzinfo=dt.timezone.utc), "job": "qv4-beehive-load",
         "run_id": "abc", "queue_id": 41, "peak_mb": 1489, "ceiling_mb": 1280, "held_gb": 1.0, "raised_gb": 2.5,
         "budget_gb": 101.0, "applied": True, "requeued_id": 42, "note": "queued again as row 42 at 2.5 GB",
         "declared_gb": 1.0}
    d.update(kw)
    return d


def test_the_memory_lines_name_each_raise_and_what_to_fold():
    lines = memory_lines([raise_row(), raise_row(id=4, raised_gb=4.0, held_gb=2.5, ceiling_mb=3200, queue_id=42),
                          raise_row(id=5, job="qv4-y", applied=False, raised_gb=200.0)])
    assert lines[0] == "memory: 3 raise(s) not yet folded into jobs.toml"
    assert "raise 3 qv4-beehive-load: declared 1 GB, held 1 GB, peak 1489 MB over its ceiling of 1280 MB, raised to 2.5 GB" in lines[1]
    assert "(NOT applied)" in lines[3] and "(NOT applied)" not in lines[1]
    # the largest applied raise is what is folded; a raise not applied is never proposed
    assert lines[-1] == "  fold: [jobs.qv4-beehive-load] memory_gb = 4"
    assert not any("qv4-y] memory_gb" in x for x in lines)


def test_with_nothing_to_fold_memory_says_so():
    assert memory_lines([]) == ["memory: no raise waits to be folded into jobs.toml"]
