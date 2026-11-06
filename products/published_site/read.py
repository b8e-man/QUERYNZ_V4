"""What the shape reads, and from where (design: "A product reads only the
published tables its template names").

Two connections, opened per build and closed after. The product reader
sees `pub` and nothing else; every published view the template names is
read through it. The session reader is used for one thing beside: the
names a cited document arrived under (`docs.names`, through
support.docstore.landing), so a figure can link to its document by a
name a reader recognises. Every statement has a time limit, and nothing is
ever written: the build writes files, never the estate.

`Tables.get(view)` refuses a view the template does not name, so the
template is the whole of what the build may read, in code and not by
remembering.
"""
from __future__ import annotations

import datetime as dt
import decimal
import os

from support import db as sdb
from support.docstore import landing as docstore

DATABASE = "querynz_v4"
STATEMENT_MS = int(os.environ.get("QV4_SITE_STATEMENT_MS") or 120_000)
#: a read that waits this long for a lock gives up and the build tries again (7 November 2026: on 4, 5 and 6 November the
#: 08:00 build's read, normally 4 s, waited 120 s behind a lock while the links build and the bulk readers ran, and the day
#: had no version)
LOCK_MS = int(os.environ.get("QV4_SITE_LOCK_MS") or 60_000)
#: how often the watcher asks who the build's read is waiting on
WATCH_S = float(os.environ.get("QV4_SITE_WATCH_S") or 10)
#: views read whole; the rest are read for the window and the registers this template shows
ROSTER_VIEWS = {"pub.parties", "pub.party_names", "pub.elections", "pub.electorates", "pub.candidates",
                "pub.members", "pub.broadcasting_allocations", "pub.party_expenses", "pub.party_expense_returns",
                "pub.promoters", "pub.promoter_expenses", "pub.promoter_people",
                "pub.party_financial_statements", "pub.party_statement_figures", "pub.disclosure_items"}
#: the registers whose rows this template names; pub.names and pub.groups are read for these alone
REGISTERS = ("party_returns", "disclosures", "house", "party_finance", "mp_interests")


def _options() -> str:
    return f"-c statement_timeout={STATEMENT_MS} -c lock_timeout={LOCK_MS} -c application_name=qv4-site-build"


def product_connect():
    return sdb.connect(sdb.PRODUCT_KEY, DATABASE, options=_options(), autocommit=True)


def read_connect():
    return sdb.connect(sdb.READ_KEY, DATABASE, options=_options(), autocommit=True)


#: who a waiting backend waits on: the chain's every blocker, with what it is running
BLOCKERS_SQL = """
select b.pid, coalesce(nullif(b.application_name, ''), b.usename::text) as who, b.state,
       to_char(b.xact_start, 'HH24:MI:SS') as since, left(regexp_replace(b.query, '\\s+', ' ', 'g'), 160) as query,
       l.mode, l.relation::regclass::text as relation
  from pg_stat_activity b
  left join lateral (select mode, relation from pg_locks where pid = b.pid and relation is not null and granted
                      order by mode desc limit 1) l on true
 where b.pid = any(pg_blocking_pids(%s))
"""


def blocker_line(r) -> str:
    pid, who, state, since, query, mode, relation = r
    return f"pid {pid} {who} ({state}, in a transaction since {since}; {mode or '?'} on {relation or '?'}): {query}"


class WaitWatcher:
    """Asks, every WATCH_S seconds while the build reads, which backends hold
    the lock its read waits on, and keeps each distinct one as a line. The
    lock that stalled the build is gone by the time a timeout is raised, so
    it is caught while it is held or not at all."""

    def __init__(self, pid: int, connect=None, every: float = None):
        import threading
        self.pid, self.connect, self.every = pid, connect or read_connect, every or WATCH_S
        self.lines, self._stop = [], threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *a):
        self._stop.set()
        self._thread.join(timeout=self.every + 5)
        return False

    def _run(self):
        try:
            with self.connect() as conn:
                while not self._stop.wait(self.every):
                    for r in conn.execute(BLOCKERS_SQL, (self.pid,)):
                        line = blocker_line(r)
                        if line not in self.lines:
                            self.lines.append(line)
        except Exception as exc:  # noqa: BLE001 — the watcher is a witness; the build goes on without it
            self.lines.append(f"(the wait watcher stopped: {type(exc).__name__}: {exc})")


def plain(v):
    """A value as JSON will carry it: Decimal to float, dates to ISO text."""
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return v


def rows(conn, sql: str, params=()) -> list:
    cur = conn.execute(sql, params)
    names = [d[0] for d in cur.description]
    return [{k: plain(v) for k, v in zip(names, r)} for r in cur]


class Tables:
    """The template's views, fetched once each and kept for the build."""

    def __init__(self, template, conn, window_from: int):
        self.template = template
        self.allowed = {r.table for r in template.reads}
        self.conn = conn
        self.window_from = int(window_from)
        self._cache = {}
        self.counts = {}

    def get(self, view: str) -> list:
        if view not in self.allowed:
            raise PermissionError(f"{view} is not among the published tables the template names; the build may not read it")
        if view not in self._cache:
            self._cache[view] = self._fetch(view)
            self.counts[view] = len(self._cache[view])
        return self._cache[view]

    def _fetch(self, view: str) -> list:
        w = self.window_from
        if view == "pub.party_return_totals":
            return rows(self.conn, f"select * from {view} where year >= %s order by party_key, year, document", (w,))
        if view == "pub.party_return_donors":
            return rows(self.conn, f"select * from {view} where year >= %s order by party_key, year, document, ordinal", (w,))
        if view == "pub.party_return_loans":
            return rows(self.conn, f"select * from {view} where year >= %s order by party_key, year, document, ordinal", (w,))
        if view == "pub.mp_interests":
            return rows(self.conn, f"select * from {view} where extract(year from as_at) >= %s order by as_at, member_return, key", (w,))
        if view == "pub.mp_interest_returns":
            return rows(self.conn, f"select * from {view} where extract(year from as_at) >= %s order by as_at, key", (w,))
        if view == "pub.candidate_return_totals":
            return rows(self.conn, f"select * from {view} where year >= %s order by year, electorate, surname, document", (w,))
        if view == "pub.candidate_return_donors":
            return rows(self.conn, f"select * from {view} where year >= %s order by year, return_key, ordinal, key", (w,))
        if view == "pub.disclosures":
            # a declaration's year is the gift's (given_on); the Commission's date only where no gift date is printed
            return rows(self.conn, f"select * from {view} where extract(year from coalesce(given_on, received_on, amended_on)) >= %s "
                                   "or coalesce(given_on, received_on, amended_on) is null order by key", (w,))
        if view == "pub.names":
            return rows(self.conn, f"select * from {view} where register = any(%s)", (list(REGISTERS),))
        if view == "pub.groups":
            return rows(self.conn, f"select g.* from {view} g where split_part(g.row_key, ':', 1) = any(%s)", (list(REGISTERS),))
        if view == "pub.decisions":
            return rows(self.conn, f"select * from {view} where split_part(row_a, ':', 1) = any(%s) or split_part(row_b, ':', 1) = any(%s)",
                        (list(REGISTERS), list(REGISTERS)))
        if view in ROSTER_VIEWS:
            return rows(self.conn, f"select * from {view}")
        raise PermissionError(f"{view}: the build has no reading rule for this view")

    def has_view(self, view: str) -> bool:
        schema, _, name = view.partition(".")
        cur = self.conn.execute("select 1 from information_schema.tables where table_schema = %s and table_name = %s", (schema, name))
        return cur.fetchone() is not None


def document_names(conn, hashes) -> dict:
    """{sha256: [names]} for the documents cited, through the session reader
    (docs.names is support's, not a lane's inside). Missing: 'not held'."""
    out = {}
    for h in sorted(set(x for x in hashes if x)):
        try:
            out[h] = docstore.names_of(h, conn)
        except Exception:  # noqa: BLE001 — a name is a convenience; the hash is the citation
            out[h] = []
    return out
