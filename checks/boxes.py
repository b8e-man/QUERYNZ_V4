"""The two boxes on the checks board (24 November 2026: the old audit's box arms stopped with v3-audit and nothing
replaced them; the October WAL settings were lost from node1 for 17 days and nothing compared the boxes).

Each box gives one reading (`python -m checks.boxes --reading`, run here and over ssh on the other box, from the
same release copy): free disk, out-of-memory kills since boot, memory pressure, the boot, whether it holds the
database address, its release commit, and its database's settings that must match. The check judges both:

    disk        each box keeps at least DISK_FLOOR_GB free on /                                     (old T7.33)
    memory      no out-of-memory kill since the last reading, memory pressure under PRESSURE_RED   (old T7.13)
    reboot      a box that booted since the last reading: red when the boot before did not shut down cleanly (T7.61)
    address     exactly one box holds the database address, and it is the database primary         (old T7.30)
    voter       the voter answers, and names as holder the box that holds the address
    settings    the two databases agree on every setting in SAME                                    (old T7.53)
    release     the two release copies stand at one commit, or the newer is under an hour old      (old T7.27, T7.54)

    python -m checks.boxes [--alarm]     print the items; with --alarm (the qv4-boxes-check job, every 15 minutes)
                                         keep the readings and send one alarm while red, at most every 6 hours"""
import datetime as dt
import json
import os
import socket
import subprocess
import sys

NAME = "boxes"
BOXES = ("node1", "node2")
VIP = "10.0.0.10"
DISK_FLOOR_GB = 150
PRESSURE_RED = 10.0          # % of the last 5 minutes every task waited on memory ("full avg300")
SAME = ("checkpoint_timeout", "max_wal_size", "min_wal_size", "wal_compression", "checkpoint_completion_target",
        "max_slot_wal_keep_size", "shared_buffers", "work_mem", "maintenance_work_mem", "effective_cache_size",
        "max_connections", "wal_level", "max_wal_senders", "hot_standby", "archive_mode", "listen_addresses")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWN_HOSTS = os.path.join(REPO, "checks", "known_hosts")     # both boxes' host keys, checked 24 November 2026
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
READINGS = os.path.join(LIVE, "checks", "boxes")
LAST_ALARM = os.path.join(LIVE, "checks", "boxes-last-alarm.json")
ALARM_EVERY_H = 6
JOB = "qv4-boxes-check"


def _run(cmd, timeout=20) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.stdout if p.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def reading() -> dict:
    """This box, now."""
    out = {"box": socket.gethostname().split(".")[0], "at": dt.datetime.now().astimezone().isoformat()}
    st = os.statvfs("/")
    out["free_gb"] = round(st.f_bavail * st.f_frsize / 1e9, 1)
    try:
        with open("/proc/vmstat") as f:
            out["oom_kills"] = next(int(l.split()[1]) for l in f if l.startswith("oom_kill "))
    except (OSError, StopIteration, ValueError):
        out["oom_kills"] = None
    try:
        with open("/proc/pressure/memory") as f:
            full = next(l for l in f if l.startswith("full"))
        out["pressure"] = float(full.split("avg300=")[1].split()[0])
    except (OSError, StopIteration, ValueError, IndexError):
        out["pressure"] = None
    try:
        with open("/proc/sys/kernel/random/boot_id") as f:
            out["boot_id"] = f.read().strip()
    except OSError:
        out["boot_id"] = None
    last = _run(["journalctl", "-b", "-1", "-n", "3", "-o", "cat", "--no-pager"]).strip().splitlines()
    out["previous_boot_clean"] = any(("Journal stopped" in l or "Shutting down" in l or "System Power Off" in l
                                      or "System Reboot" in l) for l in last) if last else None
    out["holds_vip"] = f" {VIP}/" in _run(["ip", "-4", "-o", "addr", "show"])
    out["release"] = _run(["git", "-C", REPO, "rev-parse", "HEAD"]).strip() or None
    out["release_time"] = int(_run(["git", "-C", REPO, "log", "-1", "--format=%ct"]).strip() or 0) or None
    try:
        from support import db
        with db.connect(db.READ_KEY, db.LIVE, host="127.0.0.1", connect_timeout=5) as c:
            out["db_primary"] = not c.execute("SELECT pg_is_in_recovery()").fetchone()[0]
            out["settings"] = dict(c.execute("SELECT name, setting FROM pg_settings WHERE name = ANY(%s)",
                                             (list(SAME),)).fetchall())
    except Exception as exc:  # noqa: BLE001 — a database that cannot be asked is judged red below
        out["db_primary"], out["settings"], out["db_error"] = None, None, type(exc).__name__
    return out


def remote_reading(box: str) -> dict | None:
    """The other box's reading, over ssh, from the same release path; None when it does not answer."""
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o", f"UserKnownHostsFile={KNOWN_HOSTS}",
           "-o", "StrictHostKeyChecking=yes", box,
           f"cd '{REPO}' && .venv/bin/python -m checks.boxes --reading"]
    try:
        return json.loads(_run(cmd, timeout=60))
    except ValueError:
        return None


def ask_voter(tries: int = 2, wait_s: float = 5.0) -> dict | None:
    """The voter's answer; asked again once before it counts as none (25 November 2026: two checks in a row at 04:15
    and 04:30 got no answer in 4 s, and every ask since answered)."""
    import time
    for k in range(tries):
        try:
            return json.loads(_run([sys.executable, "-m", "support.takeover", "ask-voter"], timeout=20))
        except ValueError:
            if k + 1 < tries:
                time.sleep(wait_s)
    return None


def judge(now: dict, before: dict, voter: dict | None, at: float) -> list:
    """now / before: {box: reading or None}. Returns the items."""
    items = []
    for b in BOXES:
        r, p = now.get(b), before.get(b) or {}
        if not r:
            items.append({"name": f"{b}/answers", "ok": False, "detail": f"{b} gave no reading"})
            continue
        items.append({"name": f"{b}/disk", "ok": r["free_gb"] >= DISK_FLOOR_GB,
                      "detail": f"{b}: {r['free_gb']:.0f} GB free (floor {DISK_FLOOR_GB})"})
        new_oom = (r["oom_kills"] or 0) - (p.get("oom_kills") or 0) if p.get("boot_id") == r["boot_id"] else 0
        pres = r["pressure"] or 0.0
        items.append({"name": f"{b}/memory", "ok": new_oom <= 0 and pres < PRESSURE_RED,
                      "detail": f"{b}: {max(new_oom, 0)} out-of-memory kill(s) since the last reading, "
                                f"memory pressure {pres:.1f}% (red at {PRESSURE_RED:.0f})"})
        if p.get("boot_id") and r["boot_id"] != p.get("boot_id"):
            clean = r.get("previous_boot_clean")
            items.append({"name": f"{b}/reboot", "ok": bool(clean),
                          "detail": f"{b} rebooted since the last reading; the boot before "
                                    + ("shut down cleanly" if clean else "did not shut down cleanly (crash or power)")})
        if r.get("db_error"):
            items.append({"name": f"{b}/database", "ok": False, "detail": f"{b}'s database did not answer: {r['db_error']}"})
    got = {b: r for b, r in now.items() if r}
    holders = sorted(b for b, r in got.items() if r["holds_vip"])
    primaries = sorted(b for b, r in got.items() if r.get("db_primary"))
    items.append({"name": "address", "ok": len(holders) == 1 and holders == primaries,
                  "detail": f"the address held by {', '.join(holders) or 'no box'}; "
                            f"database primary on {', '.join(primaries) or 'no box'}"})
    if voter is None:
        items.append({"name": "voter", "ok": False, "detail": "the voter gave no answer"})
    else:
        items.append({"name": "voter", "ok": voter.get("holder") in holders and len(holders) == 1,
                      "detail": f"the voter names {voter.get('holder') or 'no holder'} (epoch {voter.get('epoch')}"
                                + (", held for maintenance" if voter.get("held") else "") + ")"})
    s = {b: r.get("settings") for b, r in got.items() if r.get("settings")}
    if len(s) == 2:
        a, b = (s[x] for x in BOXES)
        diff = sorted(k for k in SAME if a.get(k) != b.get(k))
        items.append({"name": "settings", "ok": not diff,
                      "detail": "the two databases agree on " + str(len(SAME)) + " settings" if not diff else
                      "the databases differ: " + "; ".join(f"{k} {a.get(k)} on node1, {b.get(k)} on node2" for k in diff)})
    rel = {b: (r.get("release"), r.get("release_time") or 0) for b, r in got.items()}
    if len(rel) == 2:
        (c1, t1), (c2, t2) = (rel[x] for x in BOXES)
        young = at - max(t1, t2) < 3600
        items.append({"name": "release", "ok": c1 == c2 or young,
                      "detail": f"both release copies at {str(c1)[:7]}" if c1 == c2 else
                      f"node1 at {str(c1)[:7]}, node2 at {str(c2)[:7]}" + (" (the newer under an hour old)" if young else
                                                                            ": run the installer's release on the older")})
    return items


def _load(box: str) -> dict:
    try:
        with open(os.path.join(READINGS, f"{box}.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def check(now: dt.datetime = None, keep: bool = False) -> dict:
    me = socket.gethostname().split(".")[0]
    readings = {b: (reading() if b == me else remote_reading(b)) for b in BOXES}
    before = {b: _load(b) for b in BOXES}
    items = judge(readings, before, ask_voter(), (now or dt.datetime.now()).timestamp())
    if keep:
        os.makedirs(READINGS, exist_ok=True)
        for b, r in readings.items():
            if r:
                tmp = os.path.join(READINGS, f"{b}.json.tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(r, f)
                os.replace(tmp, os.path.join(READINGS, f"{b}.json"))
    return {"check": NAME, "ok": all(i["ok"] for i in items), "items": items, "alarms": []}


def alarm_once(r: dict, last_path: str, title: str, every_h: float = ALARM_EVERY_H) -> None:
    """One alarm while `r` is red, at most every `every_h` hours; green clears, so the next red alarms at once."""
    from support import alarm
    now = dt.datetime.now().astimezone()
    try:
        with open(last_path, encoding="utf-8") as f:
            last = dt.datetime.fromisoformat(json.load(f)["at"])
    except (OSError, ValueError, KeyError):
        last = None
    if not r["ok"] and (last is None or (now - last).total_seconds() > every_h * 3600):
        alarm.send(title, "; ".join(i["detail"] for i in r["items"] if not i["ok"]))
        os.makedirs(os.path.dirname(last_path), exist_ok=True)
        with open(last_path, "w", encoding="utf-8") as f:
            json.dump({"at": now.isoformat()}, f)
    elif r["ok"] and last is not None:
        os.remove(last_path)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--reading" in argv:
        print(json.dumps(reading()))
        return 0
    from support import jobrun
    started = jobrun.now()
    r = check(keep="--alarm" in argv)
    for i in r["items"]:
        print(f"  {'ok ' if i['ok'] else 'RED'}  {i['name']}  {i['detail']}")
    if "--alarm" in argv:
        alarm_once(r, LAST_ALARM, f"qv4 {socket.gethostname()}: boxes red")
        jobrun.record(JOB, r["ok"], "; ".join(i["detail"] for i in r["items"] if not i["ok"])[:500] or "green",
                      started, {})
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
