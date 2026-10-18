"""The scheduler on the checks board (plan step 2, merge request scheduler-2a).
Reads `<live>/checks/scheduler.json`, written hourly by the `qv4-scheduler-report`
job (support/scheduler/worker.py: report). Red when the report is stale, a
running worker had gone silent when it was written, a reserved card holds a
profile, or a run failed inside the window. Stdlib only."""
import datetime as dt
import json
import os

from checks.frozen_product import parse_when

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
RECORD = os.path.join(LIVE, "checks", "scheduler.json")
REPORT_WINDOW_HOURS = 3      # the report job runs every hour
SILENT_MINUTES = 15          # a worker renews its row far more often than this
RUN_WINDOW_HOURS = 26


def _when(value, tz):
    try:
        return parse_when(str(value), tz)
    except (ValueError, TypeError):
        return None


def check(now: dt.datetime = None, path: str = None) -> dict:
    now = now or dt.datetime.now().astimezone()
    path = path or RECORD
    try:
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        written = parse_when(rec["written"], now.tzinfo)
    except (OSError, ValueError, KeyError):
        return {"check": "scheduler", "ok": False, "alarms": [],
                "items": [{"name": "report", "ok": False,
                           "detail": "no scheduler report here (qv4-scheduler-report writes checks/scheduler.json)"}]}
    items = []
    age = (now - written).total_seconds() / 3600
    queue = rec.get("queue") or {}
    depth = ", ".join(f"{k} {v}" for k, v in sorted(queue.items())) or "empty"
    if age > REPORT_WINDOW_HOURS:
        items.append({"name": "report", "ok": False,
                      "detail": f"last report {age:.0f} h ago (window {REPORT_WINDOW_HOURS} h); queue then: {depth}"})
    else:
        items.append({"name": "report", "ok": True, "detail": f"written {age:.1f} h ago; queue: {depth}"})

    running = [w for w in rec.get("workers") or [] if (w.get("state") or "running") == "running"]
    silent = []
    for w in running:
        seen = _when(w.get("last_seen"), now.tzinfo)
        if seen is None or (written - seen).total_seconds() > SILENT_MINUTES * 60:
            silent.append(w.get("name") or "?")
    names = ", ".join(w.get("name") or "?" for w in running) or "none"
    if not running:
        items.append({"name": "workers", "ok": False, "detail": "no worker was running when the report was written"})
    elif silent:
        items.append({"name": "workers", "ok": False,
                      "detail": f"silent at the report (no renewal for {SILENT_MINUTES} min): {', '.join(silent)}"})
    else:
        items.append({"name": "workers", "ok": True, "detail": f"running: {names}"})

    reserved = [c for c in rec.get("cards") or [] if c.get("reserved")]
    held = [f"{c.get('box')} card {c.get('card')}" for c in reserved if c.get("profile") or c.get("holder")]
    if held:
        items.append({"name": "reserved", "ok": False,
                      "detail": "a reserved card holds a profile or a job: " + ", ".join(held)})
    else:
        items.append({"name": "reserved", "ok": True,
                      "detail": f"{len(reserved)} reserved card(s), none holding a profile"})

    failed = []
    for r in rec.get("runs") or []:
        if r.get("outcome") in (None, "ok"):
            continue
        at = _when(r.get("finished_at") or r.get("started_at"), now.tzinfo)
        if at is not None and (now - at).total_seconds() / 3600 <= RUN_WINDOW_HOURS:
            failed.append(f"{r.get('job')} ({r.get('outcome')})")
    if failed:
        items.append({"name": "runs", "ok": False,
                      "detail": f"{len(failed)} failed run(s) in {RUN_WINDOW_HOURS} h: " + ", ".join(failed[:5])})
    else:
        items.append({"name": "runs", "ok": True, "detail": f"no failed run in the last {RUN_WINDOW_HOURS} h"})
    return {"check": "scheduler", "ok": all(i["ok"] for i in items), "items": items, "alarms": []}
