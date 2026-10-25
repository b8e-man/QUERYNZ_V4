"""The board's three connections. The search scans run on the product
reader, which sees `pub` and nothing else (ruling 90: the logins carry no
cap of their own; the server's max_connections is the one cap, and the nav
bar counts what is in use). One connection
per page goes through the session reader for the document names in `docs`
(through support.docstore) and the board's own state. Pins and saved paths
are written through the owner, in short connections, and nothing else is
ever written. Every statement has a time limit. Connection strings are read
from the credential files at the moment of use and never printed (hard
limit 1)."""
from __future__ import annotations

import os

from support import db as sdb

READ_DB = "querynz_v4"
STATEMENT_MS = int(os.environ.get("QV4_BOARD_STATEMENT_MS") or 20_000)
#: where pins and saved paths live: "<database>/<schema>". The merged board uses
#: querynz_v4/board; a build session points it at its scratch schema in the sample.
STATE = os.environ.get("QV4_BOARD_STATE") or "querynz_v4/board"


def state_target() -> tuple:
    database, _, schema = STATE.partition("/")
    if not schema or not sdb.NAME.match(schema) or database not in sdb.DATABASES:
        raise ValueError("QV4_BOARD_STATE is <database>/<schema>, the database one of the estate's two")
    return database, schema


def read_connect():
    return sdb.connect(sdb.READ_KEY, READ_DB, options=f"-c statement_timeout={STATEMENT_MS}", autocommit=True)


def scan_connect():
    """The product reader: pub only."""
    return sdb.connect(sdb.PRODUCT_KEY, READ_DB, options=f"-c statement_timeout={STATEMENT_MS}", autocommit=True)


def state_connect():
    database, _ = state_target()
    return sdb.connect(sdb.OWNER_KEY, database, options=f"-c statement_timeout={STATEMENT_MS}")


def rows(conn, sql: str, params=()) -> list:
    cur = conn.execute(sql, params)
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur]


def has_relation(conn, schema: str, name: str) -> bool:
    cur = conn.execute("select 1 from information_schema.tables where table_schema = %s and table_name = %s", (schema, name))
    return cur.fetchone() is not None


def pub_views(conn) -> set:
    cur = conn.execute("select table_name from information_schema.tables where table_schema = 'pub'")
    return {r[0] for r in cur}


#: ruling 90: the connections in use by login and the server's maximum, one query; a login that is not
#: a superuser still sees every row's usename in pg_stat_activity, so the counts are whole
CONNECTIONS = ("select current_setting('max_connections')::int as max, "
               "(select coalesce(jsonb_object_agg(u, n), '{}'::jsonb) from (select coalesce(usename::text, '') as u, count(*) as n "
               "from pg_stat_activity where backend_type = 'client backend' group by 1) s) as by")


def connections(conn) -> dict:
    """{'max': max_connections, 'by': {login: connections}} on the connection given (the board's product reader)."""
    return rows(conn, CONNECTIONS)[0]
