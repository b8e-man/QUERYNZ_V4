"""C260: the gate that authorises the merge drain, and what it cannot see.

THE CARD'S PREMISE IS DEAD, AND THAT IS THE FIRST FINDING. The row says
*"era_env lacks LLM_API_URL — merge drain skipped in resolve"*. Measured
2026-10-06: audit A30 (commit 3256763f) changed both `merge_refuter.
endpoint_refusal` and `crawler._re_read` to judge the RESOLVED endpoint
(`query.agent.API`, loopback since 211d32e) instead of the raw env, so an
unset `LLM_API_URL` no longer refuses. The resolved default is
`http://127.0.0.1:8090/v1/chat/completions`, which is what
`querynz-crawler.service` and `querynz-sweep.service` pin, and the gateway
there answers `/gw/status` with two live 35B backends. `era_env` still does
not carry the var and no longer needs to.

WHAT IS ACTUALLY WRONG IS THE OTHER GATE — the one the card never named.
`refuter_measured()` reads a gate artifact, and the drain runs on its word:

  1. `GATE_GLOB` was RELATIVE (`var/audits/b4b-refuter-gate-*.json`), so the
     gate's answer depended on the caller's working directory. Measured from
     the repo it returns `(True, '…042025Z.json catch=0.846 …')`; measured
     from `/tmp` it returns `(False, 'no full refuter gate run recorded')` and
     the drain skips, politely, forever. It works today only because both
     units happen to set `WorkingDirectory` to the repo — correctness resting
     on a coincidence of configuration, which is the DSN-gate family.

  2. The artifact is from **2026-08-22 and nothing says so**. It authorises
     the drain with no bound, and `merge_refuter.py` has been committed to
     three times since. Those three turned out to be endpoint plumbing only —
     the prompt, the verdict vocabulary and the refutation logic are
     unchanged, so the old measurement does still measure what runs — but
     NOTHING CHECKED THAT, and the log line reads
     `merge drain (refuter-gated by b4b-refuter-gate-2026-08-22T042025Z.json…)`
     whether the gap is one day or one year. Making the age visible is this
     card; refusing on a changed refuter needs a fresh ~50-minute gate run
     against the frozen labelled set and is C513.
"""
import datetime as _dt
import importlib
import json
import os
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "data-layer" / "healer"))


@pytest.fixture
def crawler():
    """Imported fresh, because GATE_GLOB is bound at import time."""
    import healer.crawler as c
    return importlib.reload(c)


def test_the_gate_glob_is_anchored_to_the_REPO_not_the_caller(crawler):
    """A gate whose answer depends on `os.getcwd()` is not a gate. The
    default must name one place on disk however the process was started."""
    assert os.path.isabs(crawler.GATE_GLOB), (
        f"GATE_GLOB is relative ({crawler.GATE_GLOB!r}) — read from any other "
        f"working directory it finds no artifact and the drain skips silently")
    assert str(REPO) in crawler.GATE_GLOB


def test_the_answer_is_the_SAME_from_any_working_directory(crawler, tmp_path):
    """The defect, reproduced as the user would hit it: one call from the
    repo, one from elsewhere, and before the fix they disagree."""
    here = os.getcwd()
    try:
        os.chdir(REPO)
        from_repo = crawler.refuter_measured()
        os.chdir(tmp_path)
        from_elsewhere = crawler.refuter_measured()
    finally:
        os.chdir(here)
    assert from_repo == from_elsewhere, (
        f"the gate answers {from_repo[0]} from the repo and "
        f"{from_elsewhere[0]} from {tmp_path} — the drain's authorisation "
        f"depends on who started the process")


def test_an_authorising_artifact_states_its_AGE(crawler, tmp_path, monkeypatch):
    """The reason string is what the era record and the journal carry, so the
    age has to be IN it. A 45-day-old authorisation that reads identically to
    a fresh one is an instrument that cannot be doubted."""
    # UTC on BOTH sides. The artifact stamps carry `Z` and the gate reckons
    # the age in UTC; building this fixture from the LOCAL date would make the
    # test read 44d between 00:00 and 12:59 NZDT — flaky exactly overnight,
    # which is when this estate works.
    old = (_dt.datetime.now(_dt.UTC) - _dt.timedelta(days=45)).strftime("%Y-%m-%dT%H%M%SZ")
    art = tmp_path / f"b4b-refuter-gate-{old}.json"
    monkeypatch.setenv("B4B_GATE_GLOB", str(tmp_path / "b4b-refuter-gate-*.json"))
    import healer.crawler as c
    c = importlib.reload(c)
    # C513: an artifact authorises only the refuter it measured, so the fixture carries
    # the live fingerprint. The AGE is still what this test is about.
    art.write_text(json.dumps({"passed": True,
                               "rates": {"catch": 0.9, "false_refute": 0.05},
                               "judgment_fingerprint": c._judgment_fingerprint()}))
    ok, why = c.refuter_measured()
    assert ok, why
    assert "45d old" in why, (
        f"the authorisation reads {why!r} — a reader cannot tell a measurement "
        f"taken today from one taken six weeks ago")


def test_a_FRESH_artifact_says_so_too(crawler, tmp_path, monkeypatch):
    """Not only the old ones: the age is always stated, so its absence is
    never what distinguishes a good run."""
    now = _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H%M%SZ")
    art = tmp_path / f"b4b-refuter-gate-{now}.json"
    monkeypatch.setenv("B4B_GATE_GLOB", str(tmp_path / "b4b-refuter-gate-*.json"))
    import healer.crawler as c
    c = importlib.reload(c)
    art.write_text(json.dumps({"passed": True,
                               "rates": {"catch": 0.9, "false_refute": 0.05},
                               "judgment_fingerprint": c._judgment_fingerprint()}))
    ok, why = c.refuter_measured()
    assert ok and "0d old" in why, why


def test_the_env_override_still_wins(tmp_path, monkeypatch):
    """The seam the tests themselves ride on. Anchoring the DEFAULT must not
    take the override away — `ops/b4b_refuter_gate.py` and every test here
    point the gate at a fixture directory."""
    monkeypatch.setenv("B4B_GATE_GLOB", str(tmp_path / "x-*.json"))
    import healer.crawler as c
    c = importlib.reload(c)
    assert c.GATE_GLOB == str(tmp_path / "x-*.json")


def test_a_smoke_run_still_never_authorises(crawler, tmp_path, monkeypatch):
    """Unchanged behaviour, pinned because this card edits the function that
    enforces it: an artifact carrying `limit` or `only` is a smoke run and
    must not count however new it is."""
    now = _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H%M%SZ")
    (tmp_path / f"b4b-refuter-gate-{now}.json").write_text(
        json.dumps({"passed": True, "limit": 2, "rates": {}}))
    monkeypatch.setenv("B4B_GATE_GLOB", str(tmp_path / "b4b-refuter-gate-*.json"))
    import healer.crawler as c
    c = importlib.reload(c)
    ok, why = c.refuter_measured()
    assert not ok and "no full refuter gate run recorded" in why
