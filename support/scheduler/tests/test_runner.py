"""The runner must never be the reason a job does not run, and must be the
reason a runaway one stops (carried in spirit from
ops/fleet/tests/test_runjob.py; the ceiling and the deadline are new)."""
from __future__ import annotations

import sys

import pytest

from support.scheduler import runner


def py(code: str) -> list[str]:
    return [sys.executable, "-c", code]


@pytest.mark.parametrize("code", [0, 1, 3, 127])
def test_the_childs_exit_code_passes_through_unchanged(code):
    r = runner.run(py(f"raise SystemExit({code})"), deadline_s=30, ceiling_mb=None)
    assert r.code == code
    assert r.outcome == ("ok" if code == 0 else "failed")
    assert r.error == (None if code == 0 else f"exit {code}")


def test_a_command_that_never_starts_still_leaves_a_result():
    r = runner.run(["/nonexistent/binary"], deadline_s=30, ceiling_mb=None)
    assert r.code is None and r.outcome == "failed" and "FileNotFoundError" in r.error


def test_a_job_past_its_memory_ceiling_is_stopped_and_its_peak_kept():
    """Step 2.6: a job that outgrows what it declared is stopped; the box is
    not. 300 MB against a 100 MB ceiling."""
    r = runner.run(py("x = bytearray(300 * 1024 * 1024); x[::4096] = b'1' * len(x[::4096]); import time; time.sleep(10)"),
                   deadline_s=30, ceiling_mb=100, grace_s=2)
    assert r.stopped_for == "memory" and r.outcome == "failed"
    assert r.peak_mb > 100 and "over its ceiling" in r.error
    assert r.seconds < 10


def test_a_job_past_its_deadline_is_stopped():
    r = runner.run(py("import time; time.sleep(30)"), deadline_s=1.0, ceiling_mb=None, grace_s=2)
    assert r.stopped_for == "deadline" and r.code == -15 and r.seconds < 5


def test_a_child_that_ignores_term_is_killed_after_the_grace():
    r = runner.run(py("import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"),
                   deadline_s=0.5, ceiling_mb=None, grace_s=0.5)
    assert r.stopped_for == "deadline" and r.code == -9


def test_a_lost_lease_stops_the_child():
    ticks = iter([True, True, False])
    r = runner.run(py("import time; time.sleep(30)"), deadline_s=30, ceiling_mb=None, tick=lambda: next(ticks, False),
                   grace_s=2)
    assert r.stopped_for == "lease" and r.seconds < 5


def test_the_query_time_limit_rides_in_pgoptions_and_the_env_is_passed():
    r = runner.run(py("import os, sys; sys.exit(0 if os.environ.get('PGOPTIONS') == '-c statement_timeout=60000' "
                      "and os.environ.get('QV4_RUN_ID') == 'r1' else 9)"),
                   deadline_s=30, ceiling_mb=None, query_timeout_s=60, env={"QV4_RUN_ID": "r1"})
    assert r.code == 0


def test_the_ceiling_is_the_declared_memory_plus_a_margin():
    assert runner.ceiling_for(1.5) == 1920
    assert runner.tree_mb(99999999) == 0
