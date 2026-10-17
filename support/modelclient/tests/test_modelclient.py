"""Every call names its model, goes only to a local address, refuses an
answer from a different model, and is recorded without its prompt."""
import json

import pytest

import support.modelclient as mc

URL = "http://127.0.0.1:8090/v1/chat/completions"
MSGS = [{"role": "user", "content": "the secret prompt text"}]


def answer(model="qwen3.6-35b-a3b-q4km"):
    def post(url, body, timeout):
        return {"model": model, "choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 5, "completion_tokens": 1}}
    return post


def test_a_good_call_is_recorded_without_the_prompt(tmp_path):
    ledger = str(tmp_path / "calls.jsonl")
    out = mc.chat(URL, lane="party_returns", model="qwen3.6-35b-a3b-q4km", messages=MSGS, post=answer(), ledger=ledger)
    assert out["choices"][0]["message"]["content"] == "ok"
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["ok"] and rec["served_model"] == "qwen3.6-35b-a3b-q4km" and rec["prompt_tokens"] == 5
    assert "secret prompt" not in open(ledger).read()


def test_a_cloud_address_is_refused_before_any_bytes_leave(tmp_path):
    ledger = str(tmp_path / "calls.jsonl")
    sent = []
    with pytest.raises(mc.Refused):
        mc.chat("https://api.example.com/v1/chat/completions", lane="x", model="m", messages=MSGS,
                post=lambda *a: sent.append(1), ledger=ledger)
    assert sent == []
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["ok"] is False and "hard limit 10" in rec["refused"]
    for host in ("http://10.0.0.10:8090/x", "http://node1:8001/x", "http://localhost:8020/x"):
        assert mc.endpoint_refusal(host) == ""


def test_the_wrong_model_is_refused_for_every_lane(tmp_path):
    ledger = str(tmp_path / "calls.jsonl")
    with pytest.raises(mc.WrongModel) as e:
        mc.chat(URL, lane="any-lane", model="qwen3.6-35b-a3b-q4km", messages=MSGS, post=answer("qwen3.8-27b"), ledger=ledger)
    assert e.value.served == "qwen3.8-27b"
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["model_mismatch"] is True and rec["ok"] is False


def test_a_call_names_its_model_and_an_error_is_recorded(tmp_path):
    ledger = str(tmp_path / "calls.jsonl")
    with pytest.raises(mc.Refused):
        mc.chat(URL, lane="x", model="", messages=MSGS, post=answer(), ledger=ledger)

    def down(url, body, timeout):
        raise ConnectionError("down")
    with pytest.raises(ConnectionError):
        mc.chat(URL, lane="x", model="m", messages=MSGS, post=down, ledger=ledger)
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["error"].startswith("ConnectionError")
