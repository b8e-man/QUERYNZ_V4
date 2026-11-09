"""The lane's request to the ingest MCP's provider (ruling 165, 10 November 2026): the orders the Ministry lists that
neither our register nor the provider's copy holds, soonest to be taken down first.

After a `--from-mcp` run every order still without a document is one the copy lacks (the run took every one it
held), so `document IS NULL` is the list. The file names each order by the Ministry's own order id and its take-down
date, with counts by month; no order's content and no party's name (hard limit 11). checks.source_lights folds every
file under <work>/handover/asks/ into the provider's page and mcp-stale.json.

    write(conn, schema)   rewrite <work>/handover/asks/tenancy_tribunal.json; returns the summary"""
import datetime as dt
import json
import os

WORK = os.environ.get("QV4_WORK") or "/home/user/querynzv4-work"
ASK_FILE = os.path.join(WORK, "handover", "asks", "tenancy_tribunal.json")
CORPUS = "estate-tenancy_tribunal"
ASKED = "gather these orders before their take-down dates, soonest first, or say they cannot be gathered and why"


def short(conn, schema: str = "tenancy_tribunal") -> dict:
    rows = conn.execute(
        f"SELECT order_id, unpublished_date FROM {schema}.orders WHERE document IS NULL "
        f"ORDER BY unpublished_date NULLS LAST, order_id").fetchall()
    months = {}
    for _, d in rows:
        k = d.strftime("%Y-%m") if d else "undated"
        months[k] = months.get(k, 0) + 1
    listed = conn.execute(f"SELECT count(*) FROM {schema}.orders").fetchone()[0]
    first = next((d for _, d in rows if d), None)
    return {"schema_version": 1, "corpus": CORPUS, "source": "Tenancy Tribunal orders (the Ministry of Justice's listing)",
            "listed": int(listed), "missing": len(rows), "earliest_take_down": first.isoformat() if first else None,
            "by_take_down_month": [{"month": k, "orders": v} for k, v in months.items()],
            "orders": [{"order_id": o, "take_down": d.isoformat() if d else None} for o, d in rows],
            "asked": ASKED, "request_id": f"{CORPUS}@short-{len(rows)}-{first.isoformat() if first else 'undated'}"}


def write(conn, schema: str = "tenancy_tribunal", path: str = None, now: dt.datetime = None) -> dict:
    s = short(conn, schema)
    s["written_at"] = (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec="seconds")
    path = path or ASK_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return {k: s[k] for k in ("missing", "earliest_take_down", "request_id")}
