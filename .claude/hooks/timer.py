#!/usr/bin/env python3
"""The timer (plan 1b.9; ruling 54: every prompt is timed).

Registered on the events Claude Code raises when a prompt is submitted
(UserPromptSubmit) and when the session stops answering (Stop). Each adds
one line to `/home/user/querynzv4-work/times/session-times.jsonl`: the
session's name and weight from the scope file, the event, the time, and
Claude Code's session id. Never the prompt, never the answer. A board job
(`checks/session_times.py`) reports the typical and the worst wait for each
weight over seven days and trims the file to 30 days. Exit 0 always: a
timer must never stop a session. Stdlib only."""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fence  # noqa: E402

EVENTS = {"UserPromptSubmit": "prompt", "Stop": "stop"}


def main() -> int:
    try:
        ev = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0
    kind = EVENTS.get(ev.get("hook_event_name", ""))
    if not kind:
        return 0
    try:
        scope = fence.read_scope() or {}
    except fence.ScopeError:
        scope = {}
    row = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "event": kind,
           "session": scope.get("name") or "", "weight": scope.get("weight") or "",
           "id": str(ev.get("session_id") or "")[:36]}
    path = os.environ.get("QV4_TIMES") or fence.TIMES
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
