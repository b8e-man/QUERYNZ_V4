"""A PAGE AT A TIME, MANY AT ONCE: the rehearsal that measures a profile
through the worker's own path (ruling 121's tranche 3).

The worker claims the `qv4-rehearsal-bench` row, hands the child the card's
address, the profile's model and what every request on the profile says
(QV4_MODEL_URL, QV4_MODEL, QV4_MODEL_REQUEST), and the child sends `streams`
requests at once through `support.modelclient.chat`, the client every lane
uses, so a wrong model is refused here as it would be there.

Each prompt is SYNTHETIC: numbered lines of made-up register rows, unique
per stream from its first line (a shared prompt is served from the prefix
cache and the prefill figure is a fiction, the experiment's caveat). No
document is read, so ruling 79 is untouched. The size is set in tokens and
checked against what the server counted (`usage.prompt_tokens`).

What comes back is counts and seconds only: per stream the prompt and
completion tokens and the wall time; for the run the wall time, prompt
tokens a second and completion tokens a second, all streams together.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import os
import statistics
import time

LANE = "rehearsal-bench"
# these lines, by the server's own count: 12,800 characters were 7,296 to 7,495 tokens (29 October 20:35), digits
# and separators tokenising short; a run whose count is off by more than SIZE_TOLERANCE fails rather than mislabel
CHARS_A_TOKEN = 1.73
SIZE_TOLERANCE = 0.15

_WORDS = ("Trust", "Holdings", "Limited", "Society", "Incorporated", "Board", "Council", "Foundation", "Partners",
          "Ventures", "Group", "Services", "Charitable", "Investments", "Farming", "Kāinga", "Rūnanga", "Properties")


def prompt(stream: int, tokens: int) -> str:
    """About `tokens` tokens of made-up register lines, unique from line one."""
    lines = [f"Run {time.time_ns()} stream {stream}: read the lines below and answer with the number of the line "
             f"whose amount is largest, and nothing else."]
    i = 0
    while sum(len(x) + 1 for x in lines) < tokens * CHARS_A_TOKEN:
        i += 1
        name = " ".join(_WORDS[(stream * 7 + i * k) % len(_WORDS)] for k in (1, 3, 5))
        lines.append(f"{i}. {name} {stream}-{i:05d} | filed {2019 + i % 7}-{1 + i % 12:02d}-{1 + i % 28:02d} | "
                     f"${(i * 7919 + stream * 104729) % 1000000:,}.00")
    return "\n".join(lines)


def run(url: str, model: str, request: dict, *, streams: int = 8, prompt_tokens: int = 4000, answer_tokens: int = 128,
        chat=None, timeout: float = 600.0) -> dict:
    if chat is None:
        from support.modelclient import chat
    extra = {**request, "max_tokens": answer_tokens}

    def one(s: int) -> dict:
        t0 = time.monotonic()
        out = chat(url, lane=LANE, model=model, messages=[{"role": "user", "content": prompt(s, prompt_tokens)}],
                   extra=extra, timeout=timeout)
        u = out.get("usage") or {}
        msg = (out.get("choices") or [{}])[0].get("message") or {}
        return {"stream": s, "seconds": round(time.monotonic() - t0, 2), "prompt_tokens": u.get("prompt_tokens") or 0,
                "completion_tokens": u.get("completion_tokens") or 0, "answered": bool((msg.get("content") or "").strip()),
                "served": out.get("model")}

    t0 = time.monotonic()
    with cf.ThreadPoolExecutor(max_workers=streams) as ex:
        rows = list(ex.map(one, range(streams)))
    wall = time.monotonic() - t0
    p = sum(r["prompt_tokens"] for r in rows)
    c = sum(r["completion_tokens"] for r in rows)
    secs = [r["seconds"] for r in rows]
    return {"model": model, "url": url, "streams": streams, "prompt_tokens_asked": prompt_tokens,
            "prompt_tokens_each": [r["prompt_tokens"] for r in rows], "answered": sum(r["answered"] for r in rows),
            "wall_seconds": round(wall, 2), "request_seconds_median": round(statistics.median(secs), 2),
            "request_seconds_max": round(max(secs), 2), "prompt_tokens_a_second": round(p / wall) if wall else None,
            "completion_tokens_a_second": round(c / wall) if wall else None, "request": extra,
            "size_ok": all(abs(r["prompt_tokens"] - prompt_tokens) <= SIZE_TOLERANCE * prompt_tokens for r in rows)}


def from_env(streams: int, prompt_tokens: int, answer_tokens: int, out_path: str | None = None, chat=None) -> dict:
    """The child's side: everything from what the worker set."""
    res = run(os.environ["QV4_MODEL_URL"], os.environ["QV4_MODEL"], json.loads(os.environ.get("QV4_MODEL_REQUEST") or "{}"),
              streams=streams, prompt_tokens=prompt_tokens, answer_tokens=answer_tokens, chat=chat)
    res.update(profile=os.environ.get("QV4_PROFILE"), card=os.environ.get("QV4_CARD"), run_id=os.environ.get("QV4_RUN_ID"))
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
    return res
