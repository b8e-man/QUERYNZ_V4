"""Saved reports: the only thing the report writes, into its own schema, and
only ever added to (design rule 2: a product never writes into the estate;
it writes its own state)."""
from __future__ import annotations

import contextlib
import json
import os

from support import db as sdb
from products.report import db

HERE = os.path.dirname(os.path.abspath(__file__))


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
    import datetime as dt
    import decimal
    if isinstance(x, (dt.date, dt.datetime)):
        return x.isoformat()
    if isinstance(x, decimal.Decimal):
        return str(x)
    if isinstance(x, (set, frozenset, tuple)):
        return list(x)
    return str(x)


def save(report: dict, memo_text: str, note: str = "") -> int:
    _, schema = db.state_target()
    title = (report.get("subject") or {}).get("title") or report["ref"]
    with db.state_connect() as conn:
        cur = conn.execute(f"insert into {schema}.reports (ref, template, version, as_of, title, note, memo, report, problems) "
                           f"values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s) returning report_id",
                           (report["ref"], report["template"]["name"], report["template"]["version"], report["as_of"], title[:500], note[:2000],
                            memo_text, json.dumps(report, default=_json), len(report.get("problems") or [])))
        report_id = cur.fetchone()[0]
        conn.commit()
    return report_id


@contextlib.contextmanager
def _reader(conn):
    database, _ = db.state_target()
    if database == db.READ_DB:
        yield conn
        return
    with sdb.connect(sdb.READ_KEY, database, autocommit=True) as c:
        yield c


def saved(conn, limit: int = 200) -> list:
    _, schema = db.state_target()
    with _reader(conn) as c:
        if not db.has_relation(c, schema, "reports"):
            return []
        return db.rows(c, f"select report_id, ref, template, version, as_of, title, note, problems, made_at from {schema}.reports "
                          f"order by made_at desc, report_id desc limit %s", (limit,))


def one(conn, report_id: int) -> dict | None:
    _, schema = db.state_target()
    with _reader(conn) as c:
        if not db.has_relation(c, schema, "reports"):
            return None
        got = db.rows(c, f"select * from {schema}.reports where report_id = %s", (report_id,))
        return got[0] if got else None
