"""The scan's connections. Reads of `pub` run on the product reader, which
sees `pub` and nothing else, with a long statement limit because a scan
over a whole register is one query (QV4_SCAN_STATEMENT_MS, ten minutes).
The scan's own tables are written through the owner into the schema
QV4_SCAN_STATE names (`querynz_v4/register_scan` when merged; a build
session points it at its scratch schema in the sample database) and read
back on the session reader. Connection strings are read from the credential
files at the moment of use and never printed (hard limit 1)."""
from __future__ import annotations

import os

from support import db as sdb

READ_DB = "querynz_v4"
STATEMENT_MS = int(os.environ.get("QV4_SCAN_STATEMENT_MS") or 600_000)
STATE = os.environ.get("QV4_SCAN_STATE") or "querynz_v4/register_scan"


def state_target() -> tuple:
    database, _, schema = STATE.partition("/")
    if not schema or not sdb.NAME.match(schema) or database not in sdb.DATABASES:
        raise ValueError("QV4_SCAN_STATE is <database>/<schema>, the database one of the estate's two")
    return database, schema


def pub_connect():
    """The product reader: pub only, autocommit (a named cursor needs a transaction: the runner opens one)."""
    return sdb.connect(sdb.PRODUCT_KEY, READ_DB, options=f"-c statement_timeout={STATEMENT_MS}")


def state_connect():
    database, _ = state_target()
    return sdb.connect(sdb.OWNER_KEY, database, options=f"-c statement_timeout={STATEMENT_MS}")


def state_read_connect():
    database, _ = state_target()
    return sdb.connect(sdb.READ_KEY, database, options=f"-c statement_timeout={STATEMENT_MS}", autocommit=True)


def rows(conn, sql: str, params=()) -> list:
    cur = conn.execute(sql, params)
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur]


def has_relation(conn, schema: str, name: str) -> bool:
    cur = conn.execute("select 1 from information_schema.tables where table_schema = %s and table_name = %s", (schema, name))
    return cur.fetchone() is not None


def pub_views(conn) -> set:
    return {r[0] for r in conn.execute("select table_name from information_schema.tables where table_schema = 'pub'")}


def pub_columns(conn, view: str) -> set:
    return {r[0] for r in conn.execute("select column_name from information_schema.columns where table_schema = 'pub' and table_name = %s", (view,))}
