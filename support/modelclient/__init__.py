"""The model client's contract (plan 1.9; docs/contracts/model-client.md).
Step 1.10 moves the old client behind it, with refusal on for every lane.

Every call names its model and refuses an answer from a different one: the
old client recorded a wrong model in 13.8% of one lane's calls and carried
on. Local addresses only (hard limit 10: no text leaves the boxes for a
cloud model): the loopback, the two boxes' addresses and the floating one.
Every call is recorded (lane, model, served model, tokens, seconds) in the
calls ledger, which never holds the prompt.

    from support.modelclient import chat
    out = chat("http://127.0.0.1:8090/v1/chat/completions", lane="party_returns",
               model="qwen3.6-35b-a3b-q4km", messages=[...])

Raises `Refused` before any bytes leave the box, `WrongModel` after an
answer from the wrong model (the answer is discarded). Stdlib only; a
caller may pass `post` for a test.
"""
import datetime as dt
import json
import os
import time
import urllib.parse
import urllib.request

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
LEDGER = os.path.join(LIVE, "checks", "model-calls.jsonl")
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "10.0.0.1", "10.0.0.2", "10.0.0.10", "node1", "node2"})


class Refused(RuntimeError):
    pass


class WrongModel(RuntimeError):
    def __init__(self, requested: str, served: str, lane: str):
        super().__init__(f"{lane}: asked for {requested!r}, {served!r} answered")
        self.requested, self.served, self.lane = requested, served, lane


def endpoint_refusal(url: str) -> str:
    try:
        host = urllib.parse.urlsplit(url).hostname or ""
    except ValueError:
        return f"not a URL: {url!r}"
    if host not in LOCAL_HOSTS:
        return f"{host!r} is not a local model address (hard limit 10)"
    return ""


def _post(url: str, body: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "querynz-v4"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _record(entry: dict, ledger: str = None) -> None:
    ledger = ledger or LEDGER
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def chat(url: str, *, lane: str, model: str, messages: list, extra: dict = None, timeout: float = 300.0,
         post=None, ledger: str = None) -> dict:
    if not model:
        raise Refused(f"{lane}: every call names its model")
    entry = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "lane": lane, "model": model,
             "url": url, "prompt_chars": sum(len(str(m.get("content") or "")) for m in messages)}
    why = endpoint_refusal(url)
    if why:
        entry.update(ok=False, refused=why)
        _record(entry, ledger)
        raise Refused(f"{lane}: {why}")
    body = {"model": model, "messages": messages, **(extra or {})}
    t0 = time.monotonic()
    try:
        out = (post or _post)(url, body, timeout)
    except Exception as exc:  # noqa: BLE001 — recorded, then re-raised
        entry.update(ok=False, error=f"{type(exc).__name__}: {str(exc)[:200]}", seconds=round(time.monotonic() - t0, 1))
        _record(entry, ledger)
        raise
    served = out.get("model")
    usage = out.get("usage") or {}
    entry.update(ok=True, served_model=served, seconds=round(time.monotonic() - t0, 1),
                 prompt_tokens=usage.get("prompt_tokens"), completion_tokens=usage.get("completion_tokens"))
    if not served or served.strip() != model.strip():
        entry.update(ok=False, model_mismatch=True)
        _record(entry, ledger)
        raise WrongModel(model, served, lane)
    _record(entry, ledger)
    return out
