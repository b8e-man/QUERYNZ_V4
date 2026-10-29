"""The bench rehearsal sends `streams` page-sized requests at once through
the model client with the profile's own request settings, each prompt
unique from its first line and about the size asked, and reports counts
and seconds only; a wrong model stops it. No card, no network here."""
from __future__ import annotations

import json
import threading
import time

import pytest

from support import modelclient as mc
from support.scheduler import __main__ as cli
from support.scheduler import bench


def fake_chat(served="qwen4exp", delay=0.2):
    seen, lock, live = [], threading.Lock(), {"now": 0, "max": 0}

    def chat(url, *, lane, model, messages, extra=None, timeout=None):
        with lock:
            seen.append({"url": url, "lane": lane, "model": model, "prompt": messages[0]["content"], "extra": extra})
            live["now"] += 1
            live["max"] = max(live["max"], live["now"])
        time.sleep(delay)
        with lock:
            live["now"] -= 1
        if served != model:
            raise mc.WrongModel(model, served, lane)
        n = int(len(messages[0]["content"]) / bench.CHARS_A_TOKEN)
        return {"model": served, "choices": [{"message": {"content": "17"}}],
                "usage": {"prompt_tokens": n, "completion_tokens": 3}}
    return chat, seen, live


def test_eight_unique_page_sized_prompts_go_at_once_with_the_profiles_request():
    chat, seen, live = fake_chat()
    req = {"chat_template_kwargs": {"enable_thinking": False}, "temperature": 0.0, "max_tokens": 8192}
    out = bench.run("http://127.0.0.1:8060/v1/chat/completions", "qwen4exp", req, streams=8, prompt_tokens=4000, chat=chat)
    assert len(seen) == 8 and live["max"] == 8, "the eight streams are in flight together"
    firsts = {s["prompt"].splitlines()[0] for s in seen}
    assert len(firsts) == 8, "each stream's prompt differs from its first line (no prefix-cache fiction)"
    assert all(3900 <= len(s["prompt"]) / bench.CHARS_A_TOKEN <= 4200 for s in seen)
    assert all(s["extra"]["chat_template_kwargs"] == {"enable_thinking": False} and s["extra"]["max_tokens"] == 128
               for s in seen), "the profile's request rides on every call; the answer is short"
    assert all(s["lane"] == bench.LANE and s["model"] == "qwen4exp" for s in seen)
    assert out["streams"] == 8 and out["answered"] == 8 and out["prompt_tokens_a_second"] > 0 and out["size_ok"]
    assert "prompt" not in json.dumps(out).replace("prompt_tokens", ""), "counts and seconds only, never the text"


def test_a_wrong_model_stops_the_bench():
    chat, _, _ = fake_chat(served="qwen3.6-35b-a3b-q4km", delay=0)
    with pytest.raises(mc.WrongModel):
        bench.run("http://127.0.0.1:8060/v1/chat/completions", "qwen4exp", {}, streams=2, prompt_tokens=100, chat=chat)


def test_a_prompt_the_server_counts_far_from_the_size_asked_is_not_ok():
    chat, _, _ = fake_chat(delay=0)
    def inflated(url, **k):
        out = chat(url, **k)
        out["usage"]["prompt_tokens"] = int(out["usage"]["prompt_tokens"] * 1.8)    # the 29 October first run: 7,400 for 4,000
        return out
    out = bench.run("http://127.0.0.1:8060/v1/chat/completions", "qwen4exp", {}, streams=2, prompt_tokens=4000, chat=inflated)
    assert out["size_ok"] is False


def test_the_child_reads_everything_from_the_worker(monkeypatch, tmp_path):
    chat, seen, _ = fake_chat(delay=0)
    monkeypatch.setenv("QV4_MODEL_URL", "http://127.0.0.1:8060/v1/chat/completions")
    monkeypatch.setenv("QV4_MODEL", "qwen4exp")
    monkeypatch.setenv("QV4_PROFILE", "text-reader")
    monkeypatch.setenv("QV4_MODEL_REQUEST", json.dumps({"chat_template_kwargs": {"enable_thinking": False}}))
    out = bench.from_env(3, 500, 16, out_path=str(tmp_path / "b.json"), chat=chat)
    assert out["profile"] == "text-reader" and json.loads((tmp_path / "b.json").read_text())["streams"] == 3
    assert all(s["extra"] == {"chat_template_kwargs": {"enable_thinking": False}, "max_tokens": 16} for s in seen)


def test_the_command_line_runs_the_bench_from_the_worker_env(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(bench, "from_env", lambda *a, **k: calls.append((a, k)) or {"streams": 8, "answered": 8,
                        "prompt_tokens_a_second": 1, "completion_tokens_a_second": 1, "wall_seconds": 1, "size_ok": True})
    assert cli.main(["rehearse", "bench", "--streams", "8", "--prompt-tokens", "4000", "--out", str(tmp_path / "o")]) == 0
    assert calls and calls[0][0][:2] == (8, 4000)


def test_the_model_rehearsal_sends_the_profiles_request(monkeypatch):
    sent = []
    monkeypatch.setattr(mc, "chat", lambda url, **k: sent.append(k) or {"model": "qwen4exp",
                        "choices": [{"message": {"content": "READY"}}]})
    monkeypatch.setenv("QV4_MODEL_URL", "http://127.0.0.1:8060/v1/chat/completions")
    monkeypatch.setenv("QV4_MODEL", "qwen4exp")
    monkeypatch.setenv("QV4_MODEL_REQUEST", json.dumps({"chat_template_kwargs": {"enable_thinking": True},
                                                        "thinking_token_budget": 2048, "max_tokens": 6144}))
    assert cli.main(["rehearse", "model"]) == 0
    assert sent[0]["extra"]["chat_template_kwargs"] == {"enable_thinking": True}
    assert sent[0]["extra"]["thinking_token_budget"] == 2048
