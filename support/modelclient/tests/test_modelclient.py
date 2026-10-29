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


@pytest.mark.parametrize("url", [
    "http://localhost:x@evil/v1/chat", "http://127.0.0.1:x@evil.example/v1", "http://10.0.0.2:x@203.0.113.9/v1",
    "http://evil.example/localhost", "http://localhost.evil.example/v1", "ftp://localhost/v1", "http://[::1]:x@evil/v1",
])
def test_the_host_is_parsed_never_pattern_matched(url):
    assert mc.endpoint_refusal(url)


@pytest.mark.parametrize("url", [
    "http://localhost:11434/v1/chat", "http://127.0.0.1:8000/v1", "http://[::1]:8000/v1", "https://10.0.0.1:8000/v1",
    "http://10.0.0.2/v1", "http://10.0.0.10:8090/v1/chat/completions",
])
def test_loopback_and_the_twin_lan_forms_pass(url):
    assert mc.endpoint_refusal(url) == ""


EURL = "http://127.0.0.1:8111/v1/embeddings"
TEXTS = ["the secret first text", "the secret second text"]


def vectors(n=2):
    """An embeddings answer the way llama-server gives it: `model` is the
    REQUEST'S model echoed back, whatever is loaded."""
    def post(url, body, timeout):
        assert body["input"] == TEXTS[:n]
        return {"model": body["model"], "data": [{"index": i, "embedding": [float(i), 1.0]} for i in reversed(range(n))],
                "usage": {"prompt_tokens": 9}}
    return post


def holds(model="bge-m3-q8"):
    def get(url, timeout):
        assert url == "http://127.0.0.1:8111/v1/models", url
        return {"data": [{"id": model, "object": "model"}]}
    return get


def test_an_embedding_call_returns_vectors_in_order_and_is_recorded_without_the_texts(tmp_path):
    ledger = str(tmp_path / "calls.jsonl")
    out = mc.embed(EURL, lane="search", model="bge-m3-q8", texts=TEXTS, post=vectors(), get=holds(), ledger=ledger)
    assert out == [[0.0, 1.0], [1.0, 1.0]], "in the texts' order, whatever order the server answers in"
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["ok"] and rec["kind"] == "embed" and rec["n"] == 2 and rec["dims"] == 2 and rec["served_model"] == "bge-m3-q8"
    assert "secret" not in open(ledger).read()
    assert mc.embed(EURL, lane="search", model="bge-m3-q8", texts=[], post=vectors(), get=holds(), ledger=ledger) == []


def test_the_served_model_is_read_back_not_taken_from_the_answer(tmp_path):
    """llama-server echoes the request's model in an embeddings answer, so a
    card holding the wrong model would pass a check on the answer. The
    model list is what the card holds."""
    ledger = str(tmp_path / "calls.jsonl")
    with pytest.raises(mc.WrongModel) as e:
        mc.embed(EURL, lane="search", model="bge-m3-q8", texts=TEXTS, post=vectors(), get=holds("nomic-embed"), ledger=ledger)
    assert e.value.served == "nomic-embed"
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["model_mismatch"] is True and rec["ok"] is False and rec["answer_model"] == "bge-m3-q8"
    assert mc.served_model(EURL, get=holds("x")) == "x"
    assert mc.served_model(EURL, get=lambda u, t: {"data": []}) is None


def test_a_cloud_address_is_never_reached_and_a_call_names_its_model(tmp_path):
    ledger = str(tmp_path / "calls.jsonl")
    sent = []
    with pytest.raises(mc.Refused):
        mc.embed("https://api.example.com/v1/embeddings", lane="search", model="m", texts=TEXTS,
                 post=lambda *a: sent.append(1), get=lambda *a: sent.append(1), ledger=ledger)
    assert sent == []
    with pytest.raises(mc.Refused):
        mc.embed(EURL, lane="search", model="", texts=TEXTS, post=vectors(), get=holds(), ledger=ledger)


def test_a_short_answer_is_an_error_not_a_silent_gap(tmp_path):
    ledger = str(tmp_path / "calls.jsonl")

    def one_short(url, body, timeout):
        return {"model": "bge-m3-q8", "data": [{"index": 0, "embedding": [1.0]}]}
    with pytest.raises(RuntimeError, match="1 vectors for 2 texts"):
        mc.embed(EURL, lane="search", model="bge-m3-q8", texts=TEXTS, post=one_short, get=holds(), ledger=ledger)
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["ok"] is False


def test_a_chat_call_reads_the_served_model_back_before_sending(tmp_path):
    """Ruling 121: Radiance echoes the requested name in its answer, so the
    answer alone would let a call for Qwen3.6 through to Flash-Next."""
    ledger = str(tmp_path / "calls.jsonl")
    sent = []
    echo = lambda url, body, timeout: sent.append(body) or {"model": body["model"], "choices": [], "usage": {}}  # noqa: E731
    holds = lambda name: (lambda url, timeout: {"data": [{"id": name}]})  # noqa: E731
    with pytest.raises(mc.WrongModel):
        mc.chat(URL, lane="any", model="qwen3.6-35b-a3b-q4km", messages=MSGS, post=echo, get=holds("qwen4exp"), ledger=ledger)
    assert sent == [], "nothing is sent to a server holding another model"
    out = mc.chat(URL, lane="any", model="qwen4exp", messages=MSGS, post=echo, get=holds("qwen4exp"), ledger=ledger)
    assert out["model"] == "qwen4exp" and len(sent) == 1
    lines = [json.loads(l) for l in open(ledger)]
    assert lines[0]["ok"] is False and lines[0]["model_mismatch"] and lines[1]["read_back"] == "qwen4exp"


def test_radiance_s_answer_shape_is_accepted(tmp_path):
    """The answer Radiance 1.13 gives (system_fingerprint, timings, reasoning
    token details) passes as an OpenAI-style chat answer."""
    ledger = str(tmp_path / "calls.jsonl")
    answer_ = {"id": "chatcmpl-0ea8", "object": "chat.completion", "created": 1793257205, "model": "qwen4exp",
               "system_fingerprint": "radiance-1.13.0",
               "choices": [{"index": 0, "message": {"role": "assistant", "content": "OK"}, "logprobs": None,
                            "finish_reason": "stop"}],
               "usage": {"prompt_tokens": 15, "completion_tokens": 2, "total_tokens": 17,
                         "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 0}},
               "timings": {"prompt_n": 15, "prompt_ms": 67.8}}
    out = mc.chat(URL, lane="board", model="qwen4exp", messages=MSGS, post=lambda *a: answer_,
                  get=lambda url, timeout: {"object": "list", "data": [{"id": "qwen4exp", "owned_by": "radiance"}]},
                  ledger=ledger)
    assert out["choices"][0]["message"]["content"] == "OK"
    line = json.loads(open(ledger).read().splitlines()[-1])
    assert line["ok"] and line["prompt_tokens"] == 15 and line["completion_tokens"] == 2
