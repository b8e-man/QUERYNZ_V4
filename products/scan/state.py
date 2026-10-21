"""The scan's own tables: runs, lines, citations (tables.sql), in the
schema QV4_SCAN_STATE names. Written through the owner, read on the
session reader. Only ever added to."""
from __future__ import annotations

import datetime as dt
import decimal
import json
import os

from support import db as sdb
from products.scan import db

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 200


def tables_sql(schema: str) -> str:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        return f.read().replace("{schema}", schema)


def apply():
    database, schema = db.state_target()
    with db.state_connect() as conn:
        conn.execute(tables_sql(schema))
        conn.execute(f"grant usage on schema {schema} to {sdb.ROLES['read']}; grant select on all tables in schema {schema} to {sdb.ROLES['read']};")
        conn.commit()
    return database, schema


def _json(x):
    if isinstance(x, (dt.date, dt.datetime)):
        return x.isoformat()
    if isinstance(x, decimal.Decimal):
        return str(x)
    if isinstance(x, (set, frozenset, tuple)):
        return list(x)
    return str(x)


def dumps(x) -> str:
    return json.dumps(x, default=_json)


def open_run(conn, t, settings: dict, views: list, sql_text: str, note: str, limited) -> int:
    _, schema = db.state_target()
    cur = conn.execute(f"insert into {schema}.runs (scan, version, question, started_at, settings, views, note, sql, limited) "
                       f"values (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s) returning run_id",
                       (t.name, t.version, t.question, dt.datetime.now().astimezone(), dumps(settings), dumps(views), note[:2000], sql_text, limited))
    run_id = cur.fetchone()[0]
    conn.commit()
    return run_id


def write_lines(conn, run_id: int, first_n: int, lines: list) -> None:
    _, schema = db.state_target()
    with conn.cursor() as cur:
        cur.executemany(f"insert into {schema}.lines (run_id, n, grade, reasons, hubs, cites, steps) values (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s::jsonb)",
                        [(run_id, first_n + i, ln["grade"], dumps(ln["reasons"]), dumps(ln["hubs"]), ln["cites"], dumps(ln["steps"]))
                         for i, ln in enumerate(lines)])
    conn.commit()


def write_citations(conn, run_id: int, citations: list) -> None:
    _, schema = db.state_target()
    with conn.cursor() as cur:
        for i in range(0, len(citations), 5000):
            cur.executemany(f"insert into {schema}.citations (run_id, n, view, key, register, document, page, place, url) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            [(run_id, c["n"], c["view"], c["key"], c["register"], c["document"], c["page"], c["place"], c["url"]) for c in citations[i:i + 5000]])
    conn.commit()


def close_run(conn, run_id: int, seconds: float, lines: int, starts: list, grades: dict, hubs: int, problems: list) -> None:
    _, schema = db.state_target()
    conn.execute(f"update {schema}.runs set finished_at = %s, seconds = %s, lines = %s, starts = %s::jsonb, grades = %s::jsonb, hubs = %s, problems = %s::jsonb "
                 f"where run_id = %s", (dt.datetime.now().astimezone(), round(seconds, 3), lines, dumps(starts), dumps(grades), hubs, dumps(problems), run_id))
    conn.commit()


# ── reading back ────────────────────────────────────────────────────────────

def runs(conn, scan: str = None, limit: int = 50) -> list:
    _, schema = db.state_target()
    if not db.has_relation(conn, schema, "runs"):
        return []
    sql = f"select * from {schema}.runs" + (" where scan = %s" if scan else "") + " order by run_id desc limit %s"
    return db.rows(conn, sql, ((scan, limit) if scan else (limit,)))


def latest(conn, scan: str) -> dict | None:
    """The latest finished run of a scan."""
    _, schema = db.state_target()
    if not db.has_relation(conn, schema, "runs"):
        return None
    got = db.rows(conn, f"select * from {schema}.runs where scan = %s and finished_at is not null order by run_id desc limit 1", (scan,))
    return got[0] if got else None


def run(conn, run_id: int) -> dict | None:
    _, schema = db.state_target()
    got = db.rows(conn, f"select * from {schema}.runs where run_id = %s", (run_id,))
    return got[0] if got else None


def lines(conn, run_id: int, page: int = 1, size: int = PAGE, grade: str = None):
    """(lines of the page, total): paged by the line number, the whole run's order."""
    _, schema = db.state_target()
    where = " and grade = %s" if grade else ""
    params = [run_id] + ([grade] if grade else [])
    total = db.rows(conn, f"select count(*) as n from {schema}.lines where run_id = %s{where}", params)[0]["n"]
    got = db.rows(conn, f"select n, grade, reasons, hubs, cites, steps from {schema}.lines where run_id = %s{where} order by n limit %s offset %s",
                  params + [size, (max(page, 1) - 1) * size])
    return got, total


def all_lines(conn, run_id: int, size: int = 5000):
    """Every line of a run, streamed in pages (for the files)."""
    page = 1
    while True:
        got, total = lines(conn, run_id, page, size)
        for ln in got:
            yield ln
        if page * size >= total or not got:
            return
        page += 1


def citations(conn, run_id: int, numbers: list = None) -> list:
    _, schema = db.state_target()
    if numbers is not None:
        return db.rows(conn, f"select * from {schema}.citations where run_id = %s and n = any(%s) order by n", (run_id, list(numbers)))
    return db.rows(conn, f"select * from {schema}.citations where run_id = %s order by n", (run_id,))
