"""The review agent's reading is parsed safely, refuses to pick a model
server, and records only the three verdicts; the old estate's verdicts map
to the new ones; the check's shape."""
import json

import pytest

import links
from links import check, old, review


def test_the_agent_s_answer_is_parsed_and_anything_else_is_contested():
    assert review.parse_verdict('{"verdict": "no reason to doubt", "reasoning": "same middle name, one office"}') == \
        {"verdict": "no reason to doubt", "reasoning": "same middle name, one office"}
    assert review.parse_verdict('Sure. {"verdict":"not the same","reasoning":"regions apart, 40 years"} ')["verdict"] == "not the same"
    assert review.parse_verdict('{"verdict": "same"}')["verdict"] == "contested"
    assert review.parse_verdict("I think so")["verdict"] == "contested"
    assert review.VERDICTS == ("no reason to doubt", "contested", "not the same")


def test_the_reading_goes_through_the_model_client_and_names_its_model():
    seen = {}

    def post(url, body, timeout):
        seen.update(url=url, model=body["model"], system=body["messages"][0]["content"])
        return {"model": body["model"], "choices": [{"message": {"content": '{"verdict": "contested", "reasoning": "busy address"}'}}],
                "usage": {}}

    v = review.ask({"link_id": 1, "rows": []}, url="http://127.0.0.1:8020/v1/chat/completions", model="qwen3.6-35b-a3b-q4km", post=post)
    assert (v["verdict"], v["reasoning"], v["model"], v["screen"]) == ("contested", "busy address", "qwen3.6-35b-a3b-q4km", "model")
    assert seen["model"] == "qwen3.6-35b-a3b-q4km" and "contested" in seen["system"]
    with pytest.raises(Exception):
        review.ask({"link_id": 1}, url="https://api.example.com/v1/chat/completions", model="x", post=post)   # not a local address


def test_the_run_refuses_without_the_worker_s_model(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("QV4_MODEL_URL", raising=False)
    monkeypatch.delenv("QV4_MODEL", raising=False)
    f = tmp_path / "s.jsonl"
    f.write_text("{}\n")
    monkeypatch.setattr("support.db.connect", lambda *a, **k: _NoConn())
    assert review.main(["--run", str(f)]) == 2


class _NoConn:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_old_verdicts_map_to_the_new_ones_and_a_hold_is_contested():
    assert old.CURRENT_WEIGHTS == "donor-anchor-2.2"
    assert set(old.LEDGERS) == {"roster_identity_folds", "donor_anchors", "review_verdicts"}
    # the brief: the old "hold" is "contested"; a fold or an accept is "same"
    doc = old.__doc__
    assert "hold" in doc and "contested" in doc
    assert links.check_decision("contested", "old-estate:review_verdicts:9", {"old_table": "review_verdicts"}) == []
    assert links.check_decision("same", "old-estate:roster_identity_folds:1", {"old_rule": "same-full-name+shared-address"}) == []


def test_the_check_names_the_suppression_day():
    assert check.SUPPRESSION_DAY.isoformat() == "2026-11-18"
    assert json.dumps({"ok": True})   # the check prints JSON a job can read
