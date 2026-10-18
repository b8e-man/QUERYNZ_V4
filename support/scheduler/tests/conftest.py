"""Nothing in this package's tests may write the estate's real history.

Carried from the old fleet tests: `runs.py` honours an environment override
and every test passes an explicit `ledger=`. That was not enough: mutation
testing ran the suite against a deliberately broken module, and the mutant
that removed the environment override wrote test rows straight into the
real run history. So the guard is here, at the session level, where no
mutant inside the module can reach past it.
"""
from __future__ import annotations

import pytest

from support.scheduler import runs


@pytest.fixture(autouse=True, scope="session")
def _never_the_real_ledger(tmp_path_factory) -> None:
    runs.LEDGER = tmp_path_factory.mktemp("scheduler-runs") / "job-runs.jsonl"
