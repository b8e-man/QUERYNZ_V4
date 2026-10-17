"""Ruling 31 (2026-08-22) stopped the unattended merge drain; B4b restarts
it BEHIND the adversarial refuter. This test asserted absence; it now
asserts the GATED FORM (plan B4b §5 d), statically:

  - run() calls merge_duplicates with the per-run cap, and the cap is ≤40
  - merge_duplicates calls the refuter (_refute) BEFORE the merge gate
    (merge_entities), so no pair can reach the gate unrefuted
  - a refuted verdict never reaches merge_entities (the keeper is dropped)

Static by design — run() needs a live graph, and the property is about
what the code does, not the data. Rewritten failing-first against the
ruling-31 code (no drain in run, no refuter in merge_duplicates)."""
import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "healer" / "crawler.py"


def _fn(tree, name):
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(fns) == 1, f"{name} not found once"
    return fns[0]


def _calls(fn):
    out = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            out.append((f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""), node))
    return out


def test_run_drains_merges_behind_the_refuter_with_a_cap():
    tree = ast.parse(SRC.read_text())
    run = _fn(tree, "run")
    drains = [n for name, n in _calls(run) if name == "merge_duplicates"]
    assert len(drains) == 1, "run() must drain merges exactly once per cycle (B4b restart)"
    kw = {k.arg: k.value for k in drains[0].keywords}
    assert "cap" in kw and isinstance(kw["cap"], ast.Name) and kw["cap"].id == "MERGE_CAP"
    cap = next(n for n in tree.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "MERGE_CAP" for t in n.targets))
    assert cap.value.value <= 40, "per-run merge cap above 40 re-opens ruling 31's concern"


def test_merge_duplicates_refutes_before_the_gate():
    tree = ast.parse(SRC.read_text())
    md = _fn(tree, "merge_duplicates")
    calls = _calls(md)
    names = [name for name, _ in calls]
    assert "_refute" in names, "merge_duplicates never calls the refuter"
    assert "merge_entities" in names
    first_refute = min(n.lineno for name, n in calls if name == "_refute")
    first_gate = min(n.lineno for name, n in calls if name == "merge_entities")
    assert first_refute < first_gate, "the refuter must run before the merge gate"
    src = SRC.read_text()
    assert 'verdict["verdict"] == "refuted"' in src and "keeper = None" in src


def test_refuter_is_the_research_configuration_not_a_local_web_client():
    src = SRC.read_text()
    assert "from research.merge_refuter import" in src
    for tok in ("webtools", "urllib.request", "httpx", "requests."):
        assert tok not in src, f"crawler reaches the web directly via {tok}"


def test_run_consults_the_gate_artifact_before_draining(tmp_path, monkeypatch):
    """Measured before trusted: no full gate artifact, or a failed one, and
    run() must not drain. Static half: run() calls refuter_measured() before
    merge_duplicates. Dynamic half: the helper reads the newest FULL artifact."""
    import json
    tree = ast.parse(SRC.read_text())
    run = _fn(tree, "run")
    calls = _calls(run)
    assert min(n.lineno for name, n in calls if name == "refuter_measured") < \
           min(n.lineno for name, n in calls if name == "merge_duplicates")
    from healer import crawler
    monkeypatch.setattr(crawler, "GATE_GLOB", str(tmp_path / "b4b-refuter-gate-*.json"))
    assert crawler.refuter_measured() == (False, "no full refuter gate run recorded")
    (tmp_path / "b4b-refuter-gate-2026-08-22T010000Z.json").write_text(json.dumps(
        {"limit": 2, "only": "same", "passed": False, "rates": {}}))
    assert crawler.refuter_measured()[0] is False          # a smoke run never counts
    (tmp_path / "b4b-refuter-gate-2026-08-22T020000Z.json").write_text(json.dumps(
        {"limit": 0, "only": None, "passed": False, "rates": {"catch": 0.5, "false_refute": 0.0}}))
    ok, why = crawler.refuter_measured()
    assert ok is False and "FAILED" in why
    # C513: a PASSING artifact must also have measured the refuter that would run, so
    # the fixture carries the live fingerprint. Written as a call rather than a literal
    # because the literal would have to be edited every time the prompt changes — and
    # a test that needs editing to keep passing is a test that gets loosened.
    (tmp_path / "b4b-refuter-gate-2026-08-22T030000Z.json").write_text(json.dumps(
        {"limit": 0, "only": None, "passed": True, "rates": {"catch": 1.0, "false_refute": 0.0},
         "judgment_fingerprint": crawler._judgment_fingerprint()}))
    ok, why = crawler.refuter_measured()
    assert ok is True and "030000Z" in why
    # and the SAME artifact without it is refused — the drain fails closed
    (tmp_path / "b4b-refuter-gate-2026-08-22T040000Z.json").write_text(json.dumps(
        {"limit": 0, "only": None, "passed": True, "rates": {"catch": 1.0, "false_refute": 0.0}}))
    ok, why = crawler.refuter_measured()
    assert ok is False and "DIFFERENT refuter" in why
