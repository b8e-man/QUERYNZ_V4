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

from support.scheduler import cards, runs


@pytest.fixture(autouse=True, scope="session")
def _never_the_real_ledger(tmp_path_factory) -> None:
    runs.LEDGER = tmp_path_factory.mktemp("scheduler-runs") / "job-runs.jsonl"


@pytest.fixture(autouse=True)
def _never_the_live_folder(tmp_path, monkeypatch) -> None:
    """Every card manager a test builds keeps its markers, its word, its
    server logs and its inbox notes in the test's own folder, whether or
    not the test passes `mark=`. 30 October: a Manager built without it
    read the box's real night marker while a window was open, and the fast
    tier went red on the fake worker (card the-schedulers-tests-read-the-
    live-night-marker). A test that means to read the live folder says so
    by setting the path itself."""
    monkeypatch.setattr(cards, "NIGHT_MARK", str(tmp_path / "live-never" / "night-window.json"))
    monkeypatch.setattr(cards, "NIGHT_WORD", str(tmp_path / "live-never" / "night-word.json"))
    monkeypatch.setattr(cards, "INBOX_CARDS", str(tmp_path / "live-never" / "inbox"))
    monkeypatch.setattr(cards, "LOGS", str(tmp_path / "live-never" / "servers"))
