"""Session timings on the checks board (plan 1b.9; ruling 54, "It is
measured").

Reads the timer's file (`<work>/times/session-times.jsonl`: a `prompt`
line and a `stop` line per turn, with the session's name and weight), pairs
each prompt with the next stop of the same session, and reports the
typical (median) and the worst wait for each weight over the last seven
days against the starting targets. A missed target is reported, never a
red: it is recorded and looked at weekly. Trims the file to 30 days.
"""
import datetime as dt
import json
import os
import statistics

WORK = os.environ.get("QV4_WORK") or "/home/user/querynzv4-work"
TIMES = os.environ.get("QV4_TIMES") or os.path.join(WORK, "times", "session-times.jsonl")
WINDOW_DAYS = 7
KEEP_DAYS = 30
#: starting targets, typical seconds (index: "Keeping the work quick")
TARGETS = {"question": 120, "fix": 1200}


def parse_when(s: str) -> dt.datetime:
    t = dt.datetime.fromisoformat(s)
    return t if t.tzinfo else t.astimezone()


def read_rows(path: str = None) -> list:
    out = []
    try:
        with open(path or TIMES, encoding="utf-8") as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return []
    return out


def waits(rows: list, now: dt.datetime, window_days: int = WINDOW_DAYS) -> dict:
    """weight → list of seconds, prompt to the next stop of the same session,
    inside the window."""
    since = now - dt.timedelta(days=window_days)
    open_prompt = {}
    out = {}
    for r in rows:
        try:
            at = parse_when(r["at"])
        except (KeyError, ValueError):
            continue
        key = r.get("id") or r.get("session") or ""
        if r.get("event") == "prompt":
            open_prompt[key] = (at, r.get("weight") or "unknown")
        elif r.get("event") == "stop" and key in open_prompt:
            start, weight = open_prompt.pop(key)
            if at >= since and at >= start:
                out.setdefault(weight, []).append((at - start).total_seconds())
    return out


def trim(path: str, now: dt.datetime, keep_days: int = KEEP_DAYS) -> int:
    rows = read_rows(path)
    keep = []
    for r in rows:
        try:
            if parse_when(r["at"]) >= now - dt.timedelta(days=keep_days):
                keep.append(r)
        except (KeyError, ValueError):
            continue
    if len(keep) != len(rows):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in keep:
                f.write(json.dumps(r) + "\n")
        os.replace(tmp, path)
    return len(rows) - len(keep)


def check(now: dt.datetime = None, path: str = None, do_trim: bool = True) -> dict:
    now = now or dt.datetime.now().astimezone()
    path = path or TIMES
    rows = read_rows(path)
    by = waits(rows, now)
    items = []
    if not by:
        items.append({"name": "timings", "ok": True, "detail": "no timed turns in the last 7 days"})
    for weight, secs in sorted(by.items()):
        typical, worst = statistics.median(secs), max(secs)
        target = TARGETS.get(weight)
        missed = target is not None and typical > target
        detail = f"{len(secs)} turn(s): typical {typical:.0f} s, worst {worst:.0f} s"
        if target is not None:
            detail += f"; target {target} s" + (" MISSED (recorded, not red)" if missed else "")
        items.append({"name": weight, "ok": True, "detail": detail})
    if do_trim and os.path.exists(path):
        gone = trim(path, now)
        if gone:
            items.append({"name": "trim", "ok": True, "detail": f"{gone} line(s) older than {KEEP_DAYS} days removed"})
    return {"check": "session-times", "ok": True, "items": items, "alarms": []}
