"""Pins and saved paths: the only things the board writes, into its own
schema, and only ever added to."""
from __future__ import annotations

import contextlib
import os

from support import db as sdb
from products.board import db

HERE = os.path.dirname(os.path.abspath(__file__))


def tables_sql(schema: str) -> str:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        return f.read().replace("{schema}", schema)


def apply():
    database, schema = db.state_target()
    with db.state_connect() as conn:
        conn.execute(tables_sql(schema))
        # the session reader lists pins and paths; in `board` support.db grants this already, in a scratch schema it is the owner's to give
        conn.execute(f"grant usage on schema {schema} to {sdb.ROLES['read']}; grant select on all tables in schema {schema} to {sdb.ROLES['read']};")
        conn.commit()
    return database, schema


def pin(view: str, key: str, title: str, note: str = "") -> int:
    _, schema = db.state_target()
    with db.state_connect() as conn:
        cur = conn.execute(f"insert into {schema}.pins (view, key, title, note) values (%s, %s, %s, %s) returning pin_id",
                           (view, key, title[:500], note[:2000]))
        pin_id = cur.fetchone()[0]
        conn.commit()
    return pin_id


def save_path(name: str, query: str, path: list, boxes: str = "") -> int:
    """A path saved, with `boxes`, the check boxes of its address as a query string (ruling 119: a fold by hand rides it)."""
    _, schema = db.state_target()
    with db.state_connect() as conn:
        cur = conn.execute(f"insert into {schema}.paths (name, query, path, boxes) values (%s, %s, %s, %s) returning path_id",
                           (name[:200] or "(unnamed)", query[:500], "\n".join(path), boxes[:16000]))
        path_id = cur.fetchone()[0]
        conn.commit()
    return path_id


@contextlib.contextmanager
def _reader(conn):
    """The page's session-reader connection when the state lives in the same
    database (the merged board); a build session's scratch state lives in
    the sample database, so a reader connection there is opened for the call."""
    database, _ = db.state_target()
    if database == db.READ_DB:
        yield conn
        return
    with sdb.connect(sdb.READ_KEY, database, autocommit=True) as c:
        yield c


def pins(conn) -> list:
    _, schema = db.state_target()
    with _reader(conn) as c:
        if not db.has_relation(c, schema, "pins"):
            return []
        return db.rows(c, f"select * from {schema}.pins order by made_at desc, pin_id desc limit 500")


def paths(conn) -> list:
    _, schema = db.state_target()
    with _reader(conn) as c:
        if not db.has_relation(c, schema, "paths"):
            return []
        return db.rows(c, f"select * from {schema}.paths order by made_at desc, path_id desc limit 500")
