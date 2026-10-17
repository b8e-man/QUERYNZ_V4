"""The fast tier's rule, at the repository root (plan 1b.7; core: "Two tiers
of checks"): a test that takes more than five seconds, or needs a graphics
card, the network or a full table, is marked `slow`, and the fast tier
fails on any unmarked test that does. With `QV4_FAST=1` (set by bin/fast)
an unmarked test whose call phase runs past the limit is reported as a
failure naming the limit; without it, durations are only recorded, so a
plain `pytest` run stays green while someone is still writing the test.

Also puts the repository root on the import path for every test (pytest.ini
does the same with `pythonpath`; this is for a copy run elsewhere)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FAST_LIMIT_S = 5.0


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call" or not os.environ.get("QV4_FAST"):
        return
    if rep.duration > FAST_LIMIT_S and item.get_closest_marker("slow") is None and rep.passed:
        rep.outcome = "failed"
        rep.longrepr = (f"{item.nodeid} took {rep.duration:.1f} s and is not marked slow: the fast tier allows "
                        f"{FAST_LIMIT_S:.0f} s. Mark it @pytest.mark.slow (it then runs in the full tier) or make it quick.")
