"""The standby on the checks board (24 November 2026: node2's database had replayed nothing since 7 November and
nothing said so; the old estate's T7.28 lag check stopped with v3-audit). Asks the primary, on the read login:
red when no standby is connected, when no standby slot is active, or when an active slot holds more than LAG_GB
of WAL the standby has not confirmed; and, on the box it runs on, red when that box's takeover agent is the standby and
says it is not caught up (its `caught_up` was false for 17 days and nothing read it). The primary keeps at most 100 GB
for a slot (max_slot_wal_keep_size), so a standby that falls past that can only come back by a full copy
(handover/rebuild-node2-standby.sh).

    python -m checks.standby [--alarm]     print the items; with --alarm (the qv4-standby-check job, every 15 minutes
                                           on whichever box claims it) send one alarm while red, at most every 6 hours"""
import datetime as dt
import json
import os
import subprocess
import sys

from support import db

NAME = "standby"
LAG_GB = 20
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
LAST_ALARM = os.path.join(LIVE, "checks", "standby-last-alarm.json")
ALARM_EVERY_H = 6
JOB = "qv4-standby-check"


def measure(conn) -> dict:
    connected = conn.execute("SELECT count(*) FROM pg_stat_replication").fetchone()[0]
    slots = conn.execute(
        "SELECT slot_name, active, CASE WHEN restart_lsn IS NULL THEN NULL "
        "ELSE pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) / 1e9 END, wal_status "
        "FROM pg_replication_slots WHERE slot_type = 'physical' ORDER BY slot_name").fetchall()
    return {"connected": connected, "slots": [{"name": n, "active": a, "behind_gb": g, "wal_status": w}
                                              for n, a, g, w in slots]}


def judge(m: dict) -> list:
    items = []
    active = [s for s in m["slots"] if s["active"]]
    items.append({"name": "connected", "ok": m["connected"] > 0 and bool(active),
                  "detail": (f"{m['connected']} standby connected; slots: "
                             + ", ".join(f"{s['name']} {'active' if s['active'] else 'INACTIVE'}"
                                         + (f" ({s['wal_status']})" if s["wal_status"] else "") for s in m["slots"])
                             if m["slots"] else f"{m['connected']} standby connected; no physical slot")
                  + ("" if m["connected"] and active else ": the primary has no live copy; rebuild the standby")})
    for s in active:
        g = s["behind_gb"]
        items.append({"name": f"lag/{s['name']}", "ok": g is not None and g <= LAG_GB,
                      "detail": f"{s['name']} holds {g:.1f} GB not confirmed (red past {LAG_GB})" if g is not None
                      else f"{s['name']} active with no restart point"})
    return items


def agent_status(run=subprocess.run) -> dict | None:
    """This box's takeover agent, through its own command (it reads its key itself); None when it does not answer."""
    try:
        p = run([sys.executable, "-m", "support.takeover", "status"], capture_output=True, text=True, timeout=20)
        return json.loads(p.stdout) if p.returncode == 0 else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def judge_agent(st: dict | None) -> dict:
    if not st:
        return {"name": "agent", "ok": False, "detail": "this box's takeover agent gave no answer"}
    role, box = st.get("role"), st.get("box")
    if role == "standby" and not st.get("caught_up"):
        return {"name": "agent", "ok": False, "detail": f"{box}'s agent is the standby and is not caught up"}
    return {"name": "agent", "ok": True, "detail": f"{box}'s agent: {role}" + (", caught up" if role == "standby" else "")}


def check(now: dt.datetime = None, conn=None, status=agent_status) -> dict:
    try:
        if conn is None:
            with db.connect(db.READ_KEY, db.LIVE, autocommit=True) as c:
                m = measure(c)
        else:
            m = measure(conn)
    except Exception as exc:  # noqa: BLE001 — a primary that cannot be asked is a red item
        return {"check": NAME, "ok": False, "alarms": [],
                "items": [{"name": "asked", "ok": False, "detail": f"{type(exc).__name__}: {str(exc)[:200]}"}]}
    items = judge(m) + [judge_agent(status())]
    return {"check": NAME, "ok": all(i["ok"] for i in items), "items": items, "alarms": []}


def main(argv=None) -> int:
    import socket
    from support import alarm, jobrun
    argv = sys.argv[1:] if argv is None else argv
    started = jobrun.now()
    r = check()
    for i in r["items"]:
        print(f"  {'ok ' if i['ok'] else 'RED'}  {i['name']}  {i['detail']}")
    if "--alarm" in argv:
        now = dt.datetime.now().astimezone()
        try:
            with open(LAST_ALARM, encoding="utf-8") as f:
                last = dt.datetime.fromisoformat(json.load(f)["at"])
        except (OSError, ValueError, KeyError):
            last = None
        if not r["ok"] and (last is None or (now - last).total_seconds() > ALARM_EVERY_H * 3600):
            alarm.send(f"qv4 {socket.gethostname()}: standby red",
                       "; ".join(i["detail"] for i in r["items"] if not i["ok"]))
            os.makedirs(os.path.dirname(LAST_ALARM), exist_ok=True)
            with open(LAST_ALARM, "w", encoding="utf-8") as f:
                json.dump({"at": now.isoformat()}, f)
        elif r["ok"] and last is not None:
            os.remove(LAST_ALARM)        # green again: the next red alarms at once
        jobrun.record(JOB, r["ok"], "; ".join(i["detail"] for i in r["items"])[:500], started, {})
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
