"""C513: the merge drain's authorisation did not expire.

`refuter_measured()` lets the drain run while the newest FULL gate artifact says
`passed`. On 2026-10-06 that artifact was **45 days old** and
`research/merge_refuter.py` had three commits since. All three turned out to be endpoint
plumbing, so the judgment the gate measured was in fact unchanged — **but nothing
checked, and the next three may not be.** C260 made the age visible; this makes the
mismatch refuse.

A MEASUREMENT AUTHORISES THE THING IT MEASURED, not the file that has replaced it. So
the artifact now records `judgment_fingerprint` — a hash of the system prompt, the
verdict vocabulary, the round budget and the SOURCE of the refute path (`refute`,
`_tools`, `_finalize_for`) — and a mismatch makes the drain fail CLOSED.

WHAT IS DELIBERATELY NOT IN THE HASH: the model name and the endpoint. Both are already
recorded in the artifact and both are operational rather than judgment — moving a backend
from 8001 to 8020 must not cost a fifty-minute re-run. What IS in it is conservative to
the point of catching a comment edit inside `refute`, because a false re-run costs 50
minutes and a false authorisation drains merges on a judgment nobody measured.
"""
import importlib
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
for p in ("data-layer/healer", "data-layer/research", "data-layer/query"):
    sys.path.insert(0, str(REPO / p))


@pytest.fixture
def crawler(monkeypatch, tmp_path):
    monkeypatch.setenv("B4B_GATE_GLOB", str(tmp_path / "b4b-refuter-gate-*.json"))
    import healer.crawler as c
    return importlib.reload(c)


def _refuter():
    try:
        from research import merge_refuter
    except Exception as exc:                                  # noqa: BLE001
        pytest.skip(f"research.merge_refuter not importable here: {type(exc).__name__}")
    return merge_refuter


# ── the fingerprint covers what decides a verdict ───────────────────────────
def test_the_fingerprint_is_STABLE_across_calls():
    m = _refuter()
    assert m.judgment_fingerprint() == m.judgment_fingerprint()
    assert len(m.judgment_fingerprint()) == 16


def test_it_is_EXACTLY_the_prompt_vocabulary_budget_and_refute_path():
    """Asserted by RECOMPUTING it, so this test says what goes in rather than only
    that something does. A test that merely checks "it changed" cannot tell you that
    the round budget was left out."""
    import hashlib
    import inspect
    m = _refuter()
    h = hashlib.sha256()
    h.update(m.SYSTEM.encode())
    h.update(repr(m.LABELS).encode())
    h.update(f"{m.ABSTAIN}|{m.MAX_ROUNDS}".encode())
    for fn in (m.refute, m._tools, m._finalize_for):
        h.update(inspect.getsource(fn).encode())
    assert m.judgment_fingerprint() == h.hexdigest()[:16]


@pytest.mark.parametrize("attr,value", [
    ("SYSTEM", "You are no longer an adversary."),
    ("LABELS", ("refuted", "not-refuted")),
    ("ABSTAIN", "unsure"),
    ("MAX_ROUNDS", 3),
])
def test_CHANGING_A_JUDGMENT_SOURCE_changes_the_fingerprint(monkeypatch, attr, value):
    m = _refuter()
    before = m.judgment_fingerprint()
    monkeypatch.setattr(m, attr, value)
    assert m.judgment_fingerprint() != before, (
        f"{attr} is not in the fingerprint — a refuter that judges differently would "
        f"keep a 45-day-old authorisation")


def test_the_MODEL_and_ENDPOINT_are_NOT_in_it(monkeypatch):
    """Operational, not judgment, and both already recorded in the artifact. A
    fingerprint that moved when a backend moved would make the gate a nuisance, and a
    gate that is a nuisance gets bypassed."""
    m = _refuter()
    before = m.judgment_fingerprint()
    monkeypatch.setenv("AGENT_MODEL", "some-other-model")
    monkeypatch.setenv("LLM_API_URL", "http://127.0.0.1:8001/v1/chat/completions")
    assert m.judgment_fingerprint() == before


def test_the_docstring_states_what_is_LEFT_OUT_and_why():
    m = _refuter()
    doc = m.judgment_fingerprint.__doc__
    assert "model name" in doc and "endpoint" in doc


# ── the gate fails CLOSED ───────────────────────────────────────────────────
def _artifact(dirpath, stamp, **kw):
    doc = {"limit": 0, "only": None, "passed": True,
           "rates": {"catch": 0.9, "false_refute": 0.05}}
    doc.update(kw)
    (dirpath / f"b4b-refuter-gate-{stamp}.json").write_text(json.dumps(doc))


def test_an_artifact_with_NO_fingerprint_is_REFUSED(crawler, tmp_path):
    """Every artifact written before this card. #ffe697: a gate whose subject is
    absent must not pass politely — the authorisation is withdrawn until one full run
    re-establishes it, which is the cost the card budgeted."""
    _artifact(tmp_path, "2026-08-22T042025Z")
    ok, why = crawler.refuter_measured()
    assert ok is False
    assert "no fingerprint" in why and "written before C513" in why
    assert "re-authorise" in why, "the refusal must say what clears it"


def test_a_MISMATCHED_fingerprint_is_REFUSED(crawler, tmp_path):
    _artifact(tmp_path, "2026-10-08T000000Z", judgment_fingerprint="deadbeefdeadbeef")
    ok, why = crawler.refuter_measured()
    assert ok is False and "DIFFERENT refuter" in why and "deadbeefdeadbeef" in why


def test_a_MATCHING_fingerprint_AUTHORISES(crawler, tmp_path):
    _artifact(tmp_path, "2026-10-08T000000Z",
              judgment_fingerprint=crawler._judgment_fingerprint())
    ok, why = crawler.refuter_measured()
    assert ok is True, why
    assert "fp=" in why, "the authorising line must name the fingerprint it accepted"


def test_a_FAILED_artifact_is_still_refused_BEFORE_the_fingerprint_is_read(crawler, tmp_path):
    """Order matters for the message: a failed run's reason should be the rates, not a
    fingerprint lecture."""
    _artifact(tmp_path, "2026-10-08T000000Z", passed=False,
              rates={"catch": 0.5, "false_refute": 0.2})
    ok, why = crawler.refuter_measured()
    assert ok is False and "FAILED" in why and "DIFFERENT refuter" not in why


def test_an_UNLOADABLE_refuter_can_never_AUTHORISE(crawler, tmp_path, monkeypatch):
    """The healer must not depend on the query layer to answer a question about a file,
    so the import is lazy — and a lazy import that fails must not read as "matches"."""
    real = crawler._judgment_fingerprint

    def _boom():
        import builtins
        orig = builtins.__import__

        def _imp(name, *a, **k):
            if "merge_refuter" in name:
                raise ImportError("no query layer here")
            return orig(name, *a, **k)
        monkeypatch.setattr(builtins, "__import__", _imp)
        return real()

    fp = _boom()
    assert fp.startswith("unloadable:"), fp
    _artifact(tmp_path, "2026-10-08T000000Z", judgment_fingerprint=fp)
    monkeypatch.setattr(crawler, "_judgment_fingerprint", lambda: "unloadable:ImportError")
    ok, why = crawler.refuter_measured()
    assert ok is False, (
        "an artifact stamped with the UNLOADABLE sentinel matched the live sentinel and "
        "authorised the drain — the sentinel must not be able to agree with itself")
    assert "did not import" in why and "cannot be loaded" in why, (
        f"the refusal reads {why!r} — \"I could not look\" is a third state and must "
        f"not be reported as a fingerprint mismatch")


def test_the_gate_script_WRITES_the_fingerprint():
    src = (REPO / "ops" / "b4b_refuter_gate.py").read_text()
    assert '"judgment_fingerprint": merge_refuter.judgment_fingerprint()' in src
    assert "fails CLOSED" in src, "the script must say what the field is for"


# ── an abstain-on-error is not a cautious abstain ──────────────────────────
def _gate():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "b4b_gate", REPO / "ops" / "b4b_refuter_gate.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _doc(per_case):
    return {"per_case": per_case,
            "rates": {"catch": 1.0, "false_refute": 0.0},
            "thresholds": {"catch_min": 0.80, "false_refute_max": 0.10}}


def test_a_PERFECT_run_passes():
    g = _gate()
    ok, why = g.passes(_doc([{"verdict": "refuted", "errored": False}]))
    assert ok and why == "ok"


def test_a_RUN_THAT_NEVER_REACHED_A_VERDICT_cannot_pass():
    """With `LLM_API_KEY` unset the research lane raises `LocalProtocolError: Illegal
    header value b'Bearer '`; every case "abstained" after four retries at exactly
    75.0 s, and the rates would have read `catch 0.0 < 0.8` — a true statement about a
    lane that never ran. `refute()` already flags it in `meta["abstained_on_error"]` and
    this gate dropped the flag while recording `rounds` and `urls` from the same dict."""
    g = _gate()
    ok, why = g.passes(_doc([{"verdict": "abstain", "errored": True},
                             {"verdict": "refuted", "errored": False}]))
    assert not ok
    assert "never reached a verdict" in why and "measures nothing" in why


def test_a_CRASHED_case_counts_too():
    g = _gate()
    ok, why = g.passes(_doc([{"verdict": "error"}]))
    assert not ok and "1 case(s)" in why


def test_the_error_count_is_STORED_on_the_artifact():
    src = (REPO / "ops" / "b4b_refuter_gate.py").read_text()
    assert 'doc["errored_cases"]' in src, (
        "the count must be on the artifact, not only in the pass/fail reason — the "
        "board and the next reader see the artifact")
    assert '"errored": bool(meta.get("abstained_on_error"))' in src
