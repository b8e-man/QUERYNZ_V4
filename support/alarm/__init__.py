"""The alarm: the one way a `qv4-` job reaches Arthur (plan step 1.6).

It reads the ntfy address from the old estate's alarm file at the moment it
sends and never prints it, logs it or copies it anywhere (hard limit 1; map:
"How an alarm reaches Arthur"). Every alarm, sent or not, is appended to
`<live>/checks/alarms.jsonl`, so the board can show it and a test can read
it back. An absent channel file is not an error: the ledger is then the
channel, and the record says so.

A title is kept to ASCII (an HTTP header), a body may be any text. Neither
may carry a person's home address or a suppressed name (hard limits 11, 15,
16): a caller says *that* something arrived, never *what* it said.

    from support.alarm import send
    send("qv4 node2: release red", "no green release in 26 h")

Stdlib only. Tests: support/alarm/tests/."""
import datetime as dt
import json
import os
import socket
import urllib.request

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
CHANNEL_FILE = os.environ.get("QV4_ALARM_FILE") or os.path.join(OLD_LIVE, "ops", "config", "alert-channel.env")
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
LEDGER = os.path.join(LIVE, "checks", "alarms.jsonl")
KEY = "ALERT_NTFY_URL"


def channel_url(path: str = None):
    """The address, read fresh each time; None when the file or the key is
    absent. Never return this to anything that prints."""
    path = path or CHANNEL_FILE
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(KEY + "="):
                    url = line.split("=", 1)[1].strip().strip("\"'")
                    return url or None
    except OSError:
        return None
    return None


def _post(url: str, title: str, body: str, priority: str) -> bool:
    req = urllib.request.Request(
        url, data=body.encode("utf-8"), method="POST",
        headers={"Title": title, "Priority": priority, "Tags": "rotating_light",
                 "Content-Type": "text/plain; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return 200 <= r.status < 300


def ascii_title(title: str) -> str:
    return title.encode("ascii", "replace").decode("ascii")[:120]


def send(title: str, body: str, priority: str = "high", *, channel_file: str = None,
         post=None, ledger: str = None) -> bool:
    """Send one alarm. Returns True when the channel accepted it. Always
    writes the ledger line, with `why` when it was not sent."""
    title = ascii_title(title)
    url = channel_url(channel_file)
    sent, why = False, ""
    if url is None:
        why = "no alarm channel: the ledger is the channel"
    else:
        try:
            sent = bool((post or _post)(url, title, body, priority))
            why = "" if sent else "the channel refused it"
        except Exception as exc:  # noqa: BLE001 — an alarm must never crash the job that raises it
            why = f"send failed: {type(exc).__name__}"
    rec = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
           "host": socket.gethostname(), "title": title, "body": body,
           "priority": priority, "sent": sent, "why": why}
    ledger = ledger or LEDGER
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return sent
