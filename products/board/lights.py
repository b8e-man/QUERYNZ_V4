"""The source lights beside the registers on the search pane (Arthur,
4 November 2026). The board reads one file, `<live>/checks/source-lights.json`,
written every 30 minutes by the `qv4-source-lights` job (checks/source_lights.py):
for each register a light, red, orange, green or grey, and a reason. The
file is read at most once a minute. Missing, unreadable, or computed more
than STALE_S ago, every dot is grey with the reason "the lights are stale".
A register the file does not name is grey, "no light computed".
A register the ingest MCP feeds carries one short `fresh` line beside its
reason (ruling 159: the provider's newest arrival against its source's
cadence), shown after the reason on hover and to a screen reader."""
from __future__ import annotations

import datetime as dt
import json
import os
import threading
import time

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
PATH = os.path.join(LIVE, "checks", "source-lights.json")
STALE_S = 2 * 3600
CACHE_S = 60
LIGHTS = ("red", "orange", "green", "grey")
WORDS = {"red": "updates not working", "orange": "corpus incomplete, updates working",
         "green": "up to date, full corpus held", "grey": "no update job"}
STALE = "the lights are stale"
UNKNOWN = "no light computed"

_LOCK = threading.Lock()
_CACHE = {"at": None, "path": None, "data": None}


def _read(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def parse(data, now: dt.datetime) -> dict:
    """register -> (light, reason), or {} with the stale reason under None."""
    if not isinstance(data, dict):
        return {None: STALE + ": no lights file"}
    try:
        at = dt.datetime.fromisoformat(str(data["computed_at"]))
        if at.tzinfo is None:
            at = at.replace(tzinfo=dt.timezone.utc)
    except (KeyError, ValueError):
        return {None: STALE + ": the file says no time"}
    age = (now - at).total_seconds()
    if age > STALE_S:
        return {None: f"{STALE}: computed {age / 3600:.1f} hours ago"}
    out = {}
    for x in data.get("lights") or []:
        if isinstance(x, dict) and x.get("light") in LIGHTS and x.get("register"):
            reason, fresh = str(x.get("reason") or ""), str(x.get("fresh") or "").strip()
            out[x["register"]] = (x["light"], f"{reason}; {fresh}" if reason and fresh else reason or fresh)
    return out


def current(path: str = None, now: dt.datetime = None, clock=time.monotonic) -> dict:
    """The lights as the page shows them; the file read at most once a minute."""
    path = path or PATH
    now = now or dt.datetime.now(dt.timezone.utc)
    with _LOCK:
        t = clock()
        if _CACHE["path"] != path or _CACHE["at"] is None or t - _CACHE["at"] > CACHE_S:
            _CACHE.update(at=t, path=path, data=_read(path))
        data = _CACHE["data"]
    return parse(data, now)


def light_for(lights: dict, register: str) -> tuple:
    """(light, reason) for one register."""
    if None in lights:
        return "grey", lights[None]
    return lights.get(register) or ("grey", UNKNOWN)


# ── the Sources tab (Arthur, 14 November 2026): every source, a link and one line on hover ──
KINDS = (("register", "Registers"), ("copy", "The provider's copies"), ("news", "News, by site (the old estate's copy)"),
         ("request", "Asked of the provider, not landed yet"))


def sources(path: str = None, now: dt.datetime = None, clock=time.monotonic) -> tuple:
    """(rows, stale): the file's `sources` rows as written, each {kind, name, label, url, light, line}; `stale` is ""
    or why every light is to be read as grey (the same rule as the register dots)."""
    current(path, now, clock)
    with _LOCK:
        data = _CACHE["data"]
    parsed = parse(data, now or dt.datetime.now(dt.timezone.utc))
    stale = parsed.get(None, "")
    rows = [x for x in ((data or {}).get("sources") or []) if isinstance(x, dict) and x.get("light") in LIGHTS
            and x.get("kind") in dict(KINDS)]
    return rows, stale
