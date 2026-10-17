"""The nightly full tier on the checks board (plan 1b.7): did it run, and
did it pass. Reads `<live>/checks/full-tier-last.json` written by
bin/full-tier. Red when it has not run inside the window or failed; a red
here raises an alarm through the board and never blocks a merge."""
import datetime as dt
import json
import os

from checks.frozen_product import parse_when

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
RECORD = os.path.join(LIVE, "checks", "full-tier-last.json")
WINDOW_HOURS = 26


def check(now: dt.datetime = None, path: str = None) -> dict:
    now = now or dt.datetime.now().astimezone()
    path = path or RECORD
    try:
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        at = parse_when(rec["at"], now.tzinfo)
    except (OSError, ValueError, KeyError):
        return {"check": "full-tier", "ok": False, "alarms": [],
                "items": [{"name": "ran", "ok": False, "detail": "the full tier has never run here (bin/full-tier)"}]}
    age = (now - at).total_seconds() / 3600
    items = []
    if age > WINDOW_HOURS:
        items.append({"name": "ran", "ok": False, "detail": f"last full tier {age:.0f} h ago (window {WINDOW_HOURS} h)"})
    else:
        items.append({"name": "ran", "ok": True, "detail": f"ran {age:.1f} h ago in {rec.get('seconds', 0):.0f} s"})
    items.append({"name": "result", "ok": bool(rec.get("ok")), "detail": rec.get("summary") or ("green" if rec.get("ok") else "RED")})
    return {"check": "full-tier", "ok": all(i["ok"] for i in items), "items": items, "alarms": []}
