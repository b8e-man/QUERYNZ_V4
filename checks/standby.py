"""The standby on the checks board (24 November 2026: node2's database had replayed nothing since 7 November and
nothing said so; the old estate's T7.28 lag check stopped with v3-audit). Asks the primary, on the read login:
red when no standby is connected, when no standby slot is active, or when an active slot holds more than LAG_GB
of WAL the standby has not confirmed. The primary keeps at most 100 GB for a slot (max_slot_wal_keep_size), so a
standby that falls past that can only come back by a full copy (handover/rebuild-node2-standby.sh)."""
import datetime as dt

from support import db

NAME = "standby"
LAG_GB = 20


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


def check(now: dt.datetime = None, conn=None) -> dict:
    try:
        if conn is None:
            with db.connect(db.READ_KEY, db.LIVE, autocommit=True) as c:
                m = measure(c)
        else:
            m = measure(conn)
    except Exception as exc:  # noqa: BLE001 — a primary that cannot be asked is a red item
        return {"check": NAME, "ok": False, "alarms": [],
                "items": [{"name": "asked", "ok": False, "detail": f"{type(exc).__name__}: {str(exc)[:200]}"}]}
    items = judge(m)
    return {"check": NAME, "ok": all(i["ok"] for i in items), "items": items, "alarms": []}
