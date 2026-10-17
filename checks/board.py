"""The checks board (plan 1.6, "Two tiers of checks": the nightly full tier).

It runs every registered check, writes `<live>/checks/board.json` (the
current state, overwritten) and a run record, alarms on every red item and
every alarm a check raises, and exits 1 on red so the unit itself shows
failed (old lesson: a watcher is proven by stopping something, and a board
leaves its unit failed rather than printing a warning). It starts with one
check, the frozen product, and grows with every lane.

    python -m checks.board               run the board
    python -m checks.board --heartbeat   alarm if the board has not run in 26 h
    python -m checks.board --test-alarm  send one test alarm to Arthur
    python -m checks.board --show        print the last board

The heartbeat runs from its own timer, so a board that never starts is
noticed. Stdlib only. Tests: checks/tests/test_board.py."""
import argparse
import datetime as dt
import json
import os
import socket
import sys

from support import alarm, jobrun

from checks import frozen_product

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
STATE_DIR = os.path.join(LIVE, "checks")
BOARD = os.path.join(STATE_DIR, "board.json")
WINDOW_HOURS = 26
JOB = "qv4-checks-board"
REGISTRY = [frozen_product.check]


def run_board(checks=None, *, now: dt.datetime = None, board_path: str = None, send=alarm.send,
              runs_path: str = None) -> int:
    now = now or dt.datetime.now().astimezone()
    started = now
    board_path = board_path or BOARD
    host = socket.gethostname()
    results = []
    for c in (checks if checks is not None else REGISTRY):
        name = getattr(c, "__module__", "?").split(".")[-1].replace("_", "-")
        try:
            r = c(now=now)
        except Exception as exc:  # noqa: BLE001 — a crashed check is a red item, not a dead board
            r = {"check": name, "ok": False, "items": [{"name": "crashed", "ok": False,
                                                        "detail": f"{type(exc).__name__}: {exc}"}], "alarms": []}
        results.append(r)
    sent = 0
    for r in results:
        for item in r["items"]:
            if not item["ok"]:
                send(f"qv4 {host}: {r['check']}/{item['name']} red", item["detail"])
                sent += 1
        for title, body in r.get("alarms", []):
            send(f"qv4 {host}: {title}", body)
            sent += 1
    ok = all(r["ok"] for r in results)
    board = {"ran_at": now.isoformat(timespec="seconds"), "host": host, "ok": ok, "alarms_sent": sent,
             "results": results}
    os.makedirs(os.path.dirname(board_path), exist_ok=True)
    tmp = board_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(board, f, ensure_ascii=False, indent=1)
    os.replace(tmp, board_path)
    red = sum(1 for r in results for i in r["items"] if not i["ok"])
    jobrun.record(JOB, ok, f"{len(results)} check(s), {red} red item(s), {sent} alarm(s)", started,
                  {"red": red, "alarms": sent}, path=runs_path)
    print(render(board))
    return 0 if ok else 1


def render(board: dict) -> str:
    lines = [f"checks board on {board['host']} at {board['ran_at']}: {'GREEN' if board['ok'] else 'RED'}"]
    for r in board["results"]:
        for i in r["items"]:
            lines.append(f"  {'ok ' if i['ok'] else 'RED'}  {r['check']}/{i['name']:<12} {i['detail']}")
    if board.get("alarms_sent"):
        lines.append(f"  {board['alarms_sent']} alarm(s) sent")
    return "\n".join(lines)


def heartbeat(*, now: dt.datetime = None, board_path: str = None, send=alarm.send) -> int:
    """Alarm if the board has not run inside the window."""
    now = now or dt.datetime.now().astimezone()
    board_path = board_path or BOARD
    host = socket.gethostname()
    try:
        with open(board_path, encoding="utf-8") as f:
            ran_at = frozen_product.parse_when(json.load(f)["ran_at"], now.tzinfo)
    except (OSError, ValueError, KeyError):
        send(f"qv4 {host}: checks board has never run", f"no board at {board_path}")
        return 1
    age = (now - ran_at).total_seconds() / 3600
    if age > WINDOW_HOURS:
        send(f"qv4 {host}: checks board stale", f"the board last ran {age:.0f} h ago (window {WINDOW_HOURS} h)")
        return 1
    print(f"board ran {age:.1f} h ago")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the QueryNZV4 checks board")
    ap.add_argument("--heartbeat", action="store_true")
    ap.add_argument("--test-alarm", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args(argv)
    if a.test_alarm:
        host = socket.gethostname()
        ok = alarm.send(f"qv4 {host}: test alarm", "the QueryNZV4 watcher for the frozen product is installed; "
                        "this is its test alarm (plan step 1.6). Nothing is wrong.", priority="default")
        print("sent" if ok else "not sent: see the alarm ledger")
        return 0 if ok else 1
    if a.heartbeat:
        return heartbeat()
    if a.show:
        try:
            with open(BOARD, encoding="utf-8") as f:
                print(render(json.load(f)))
            return 0
        except (OSError, ValueError):
            print("no board yet")
            return 1
    return run_board()


if __name__ == "__main__":
    sys.exit(main())
