"""The model server's watchdog (Arthur, 2 November 2026: "make the gpu watchdog too").

`qv4-radiance` stalled at 15:48 on 2 November inside the graphics driver (every step thread waiting in
kfd_wait_on_events): eleven requests held, no token made for half an hour, every reader timing out at 900 s,
and nothing restarted it. This job, every two minutes (qv4-radiance-watchdog.timer), reads the server's own
counters and restarts the unit when it is stuck:

- stuck = the unit is active, has been up longer than WARM_S, requests are running or waiting, and the
  server's generation_tokens_total has not moved for STALL_S; a metrics endpoint that does not answer for
  STALL_S while the unit is active is stuck too;
- a stopped unit is never started: the card manager stops it on purpose in the night window (ruling 129);
- an idle server is never stuck: no request in flight, nothing owed;
- at most MAX_RESTARTS in RESTART_WINDOW_S; past that it alarms and leaves the server alone, so a driver
  fault that comes back at once is a person's to look at, not a restart loop.

Every restart and every refusal to restart is an alarm (support.alarm) and a line in
`<live>/checks/radiance-watchdog-<box>.jsonl`. The decision is `decide()`, a pure function; tests in
support/scheduler/tests/test_watchdog.py.

    python -m support.scheduler.watchdog          one look (the timer's job)
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.request
from support import appendline

UNIT = "qv4-radiance"
METRICS = os.environ.get("QV4_RADIANCE_METRICS") or "http://127.0.0.1:8060/metrics"
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
BOX = os.uname().nodename
# one box's own (5 November 2026): with `live` shared over NFS, a watchdog that read the other box's counters
# would restart its own server for the other's stall. The ledger before that day is radiance-watchdog.jsonl (node2).
STATE = os.path.join(LIVE, "checks", f"radiance-watchdog-state-{BOX}.json")
LOG = os.path.join(LIVE, "checks", f"radiance-watchdog-{BOX}.jsonl")
STALL_S = 600              # ten minutes with work in flight and no token made
WARM_S = 900               # a server up for less than this is still loading its model
MAX_RESTARTS = 3
RESTART_WINDOW_S = 6 * 3600

_METRIC = re.compile(r'^vllm:(generation_tokens_total|num_requests_running|num_requests_waiting)\{[^}]*\}\s+([0-9.eE+]+)\s*$', re.M)


def parse(text: str) -> dict:
    """The three counters the decision reads, summed over engines."""
    out = {}
    for name, value in _METRIC.findall(text or ""):
        out[name] = out.get(name, 0.0) + float(value)
    return out if "generation_tokens_total" in out else {}


def decide(state: dict, now: float, active_s, metrics: dict) -> tuple[dict, str, str]:
    """(new state, action, reason). action is "none", "restart" or "alarm".

    state: tokens (last seen), moved_at (when tokens last moved, or the server was last idle or warming),
    restarts (times of past restarts). active_s: seconds the unit has been active, None when it is not.
    metrics: parse()'s dict, {} when the endpoint did not answer."""
    st = {"tokens": state.get("tokens"), "moved_at": state.get("moved_at", now),
          "restarts": [t for t in state.get("restarts", []) if now - t < RESTART_WINDOW_S]}
    if active_s is None:
        return {**st, "tokens": None, "moved_at": now}, "none", "the unit is not active (the night window or a person stopped it)"
    if active_s < WARM_S:
        return {**st, "tokens": None, "moved_at": now}, "none", f"up {active_s:.0f} s: still warming"
    if metrics:
        tokens = metrics["generation_tokens_total"]
        busy = metrics.get("num_requests_running", 0) + metrics.get("num_requests_waiting", 0)
        if st["tokens"] is None or tokens != st["tokens"] or not busy:
            return {**st, "tokens": tokens, "moved_at": now}, "none", "moving" if busy else "idle"
        what = f"{busy:.0f} requests in flight and no token made"
    else:
        what = "the metrics endpoint does not answer"
    stalled = now - st["moved_at"]
    if stalled < STALL_S:
        return st, "none", f"{what} for {stalled:.0f} s"
    reason = f"{what} for {stalled / 60:.0f} min"
    if len(st["restarts"]) >= MAX_RESTARTS:
        return {**st, "moved_at": now}, "alarm", f"{reason}; {len(st['restarts'])} restarts in 6 h already, left alone"
    return {**st, "tokens": None, "moved_at": now, "restarts": st["restarts"] + [now]}, "restart", reason


def _load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save(path: str, obj: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def metrics_now(url: str = METRICS) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return parse(r.read().decode("utf-8", "replace"))
    except Exception:
        return {}


def main(argv=None) -> int:
    from support import alarm
    from support.scheduler import cards
    now = time.time()
    state = _load(STATE)
    active_s = cards.unit_active_seconds(UNIT) if cards.systemctl_user("is-active", UNIT, timeout=15) == 0 else None
    new, action, reason = decide(state, now, active_s, metrics_now() if active_s is not None else {})
    if action == "restart":
        t0 = time.monotonic()
        rc = cards.systemctl_user("restart", UNIT)
        reason += f"; restarted (exit {rc}, {time.monotonic() - t0:.0f} s)"
        alarm.send(f"qv4 {BOX}: model server restarted by its watchdog", reason)
    elif action == "alarm":
        alarm.send(f"qv4 {BOX}: model server stuck, watchdog stopped restarting it", reason)
    if action != "none":
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        appendline.append_json(LOG, {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                                     "action": action, "reason": reason})
    _save(STATE, new)
    print(f"radiance watchdog: {action}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
