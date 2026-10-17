"""R3a on a scripted second endpoint (plan B4b §5 f): the fleet's own prompt
builder is what gets re-judged, agreement/dissent arithmetic is right on a
6-row fixture, the artifact is written, and nothing writes to the graph."""
import json
import pathlib

from healer import crawler, dense_validation

PKG = pathlib.Path(__file__).resolve().parents[1] / "healer"


class _Row(dict):
    pass


class _Conn:
    """mint_review rows for sample(); empty siblings/evidence for build_prompt."""
    ROWS = [
        _Row(entity_id=1, name="ACC", type="organisation", pattern="crawler-acronym-org",
             verdict="organisation", confidence=0.9, reasoning="an agency"),
        _Row(entity_id=2, name="OCR", type="organisation", pattern="crawler-acronym-org",
             verdict="concept", confidence=0.9, reasoning="the cash rate"),
        _Row(entity_id=3, name="GDP", type="organisation", pattern="crawler-acronym-org",
             verdict="concept", confidence=0.8, reasoning="a measure"),
        _Row(entity_id=4, name="Eric Hansen", type="organisation", pattern="crawler-type-multiplicity",
             verdict="mistyped-duplicate", confidence=0.95, reasoning="one man"),
        _Row(entity_id=5, name="Nelson", type="person", pattern="crawler-type-multiplicity",
             verdict="distinct-entities-ok", confidence=0.9, reasoning="city and people"),
        _Row(entity_id=6, name="Mana", type="person", pattern="crawler-type-multiplicity",
             verdict="abstain", confidence=0.3, reasoning="thin"),
    ]

    def __init__(self):
        self.writes = []

    def execute(self, sql, params=None):
        if any(w in sql for w in ("INSERT", "UPDATE", "DELETE")):
            self.writes.append(sql)
        rows = self.ROWS

        class _Cur:
            def fetchall(self_inner):
                if "FROM mint_review" in sql:
                    return [r for r in rows if r["pattern"] == params[0]]
                return []

            def fetchone(self_inner):
                return None
        return _Cur()


def test_rejudges_the_fleets_prompt_and_reports_dissent(tmp_path):
    g = _Conn()
    seen = []
    dense = {1: "organisation", 2: "organisation", 3: "concept", 4: "distinct-entities-ok",
             5: "distinct-entities-ok", 6: "mistyped-duplicate"}

    def judge(url, system, user, schema, model_name):
        seen.append((url, system, user, schema, model_name))
        eid = int(user.split("'")[1] == "ACC" and 1 or {"OCR": 2, "GDP": 3, "Eric Hansen": 4, "Nelson": 5, "Mana": 6}[user.split("'")[1]])
        return {"verdict": dense[eid], "confidence": 0.7, "reasoning": "second opinion", "model": model_name}

    doc, path = dense_validation.run(g, "http://127.0.0.1:8021/v1/chat/completions", "qwen3.8-27b",
                                     n=6, judge=judge, out_dir=str(tmp_path))
    assert doc["n"] == 6 and doc["errors"] == 0
    # 1 agree (ACC), 2 dissent (OCR), 3 agree (GDP), 4 dissent, 5 agree, 6 abstain-one-side
    assert doc["agreement"] == 3 / 6 and doc["dissent_rate"] == 2 / 6 and doc["abstain_one_side"] == 1
    assert {d["name"] for d in doc["dissent"]} == {"OCR", "Eric Hansen"}
    assert doc["per_pattern"]["crawler-acronym-org"]["agreement"] == 2 / 3
    assert all(s[0].startswith("http://127.0.0.1:8021") and s[4] == "qwen3.8-27b" for s in seen)
    # the fleet's own system prompts, not a re-worded one
    systems = {s[1] for s in seen}
    assert systems == {crawler.TYPE_SYSTEM, crawler.MULTI_SYSTEM}
    assert json.load(open(path))["model"] == "qwen3.8-27b"
    assert not g.writes, "R3a annotates; it never writes"


def test_errors_count_separately():
    rows = [{"entity_id": 1, "name": "x", "pattern": "crawler-acronym-org", "verdict": "organisation",
             "confidence": 0.9, "reasoning": "", "dense": {"verdict": "error", "confidence": None, "reasoning": "boom"}},
            {"entity_id": 2, "name": "y", "pattern": "crawler-acronym-org", "verdict": "organisation",
             "confidence": 0.9, "reasoning": "", "dense": {"verdict": "organisation", "confidence": 0.8, "reasoning": ""}}]
    rep = dense_validation.report(rows)
    assert rep["errors"] == 1 and rep["agreement"] == 1.0 and rep["dissent_rate"] == 0.0


def test_module_never_writes():
    src = (PKG / "dense_validation.py").read_text()
    for tok in ("INSERT INTO", "UPDATE ", "DELETE FROM", "remediate", "merge_entities"):
        assert tok not in src, tok


def test_partial_checkpoints_and_resume(tmp_path, monkeypatch):
    """Ledger 2026-08-24: run 1 died at 241/300 six hours in and left nothing.
    A partial lands every CHECKPOINT_EVERY verdicts; resume keeps its rows and
    judges only the remainder; success removes the partial."""
    monkeypatch.setattr(dense_validation, "CHECKPOINT_EVERY", 2)
    g = _Conn()
    calls = []

    def judge(url, system, user, schema, model_name):
        calls.append(1)
        return {"verdict": "organisation", "confidence": 0.5, "reasoning": "x", "model": "m"}

    doc, path = dense_validation.run(g, "http://x", None, n=6, judge=judge, out_dir=str(tmp_path))
    first_calls = len(calls)
    assert doc["n"] == first_calls and not list(tmp_path.glob("r3a-partial-*"))

    # a killed run: checkpoint fires, then we resume from the partial
    calls.clear()
    partial = tmp_path / "r3a-partial-x.json"
    rows = dense_validation.sample(g, n=6)
    judged = dense_validation.rejudge(g, rows[:2], "http://x", None, judge=judge)
    import json as _json
    partial.write_text(_json.dumps({"seed": 20260822, "requested": 6, "endpoint": "http://x", "rows": judged}))
    calls.clear()
    doc2, _ = dense_validation.run(g, "http://x", None, n=6, judge=judge, out_dir=str(tmp_path), resume=str(partial))
    assert doc2["n"] == first_calls and len(calls) == first_calls - 2
    # 2026-08-24 retro-audit card: success must remove the RESUME input too —
    # only this run's own partial was removed, so r3a-partial-*.json accumulated.
    assert not partial.exists(), "the resume input partial must be removed on success"
    assert not list(tmp_path.glob("r3a-partial-*"))
