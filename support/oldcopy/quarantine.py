"""Rows the copy holds but the inventory now leaves out, set aside (the deletion rule, CLAUDE.md: a captured
document is never deleted, it is withdrawn or quarantined; a quarantined thing is kept for a fixed period, then
removable on Arthur's word with a logged line).

First use: ruling 168 (Arthur, 11 November 2026), "you can delete fyi. We will get rid of that entirely". The old
estate's fyi.org.nz rows were copied on 10 November (ruling 163); the inventory now leaves them out, so the copy
never takes them again, and this moves the rows already copied out of `old_<database>_private` into
`quarantine_private.<database>__<schema>__<table>`, row for row, with one ledger line per table.

What is moved, per inventory table entry:
  - every copied row matching one of its `leave_out` pairs (column as text ILIKE pattern), and
  - every row, when the entry says `"quarantine_whole": true` (a table set OUT whose copy is all of one source).

In one transaction per table: the rows are inserted into the quarantine table, deleted from the copy, and the two
counts must agree, or nothing is kept. Nothing here removes a quarantined row; that waits for Arthur's word after
`removable_after` (DAYS from the move) and is a separate, logged step.

    python -m support.oldcopy quarantine --dry-run    what would move, counted, nothing written
    python -m support.oldcopy quarantine              move it
    python -m support.oldcopy quarantine --remove --why 'ruling 168' --word "Arthur, <date>: <his words>" [--early] [--dry-run]
        the removal: every ledger line of that ruling not yet removed, its held table dropped and the line
        stamped with the word and the time; before `removable_after` only with --early (his word moved the day)
"""
import datetime as dt
import re

from psycopg import sql

from support.oldcopy.tables import dest_schema, dest_table

SCHEMA = "quarantine_private"
DAYS = 30

LEDGER_SQL = """
CREATE SCHEMA IF NOT EXISTS {s};
CREATE TABLE IF NOT EXISTS {s}.ledger (
    id               bigserial PRIMARY KEY,
    at               timestamptz NOT NULL DEFAULT now(),
    source_table     text NOT NULL,          -- where the rows were: old_<database>_private.<table>
    held_in          text NOT NULL,          -- where they are now
    rows             bigint NOT NULL,
    rule             text NOT NULL,          -- what matched: the leave_out pairs, or 'whole'
    why              text NOT NULL,          -- the ruling
    removable_after  date NOT NULL,          -- removable on Arthur's word from this day, with a logged line
    removed_at       timestamptz,
    removed_on_word  text
);
"""


def ensure(conn, schema: str = SCHEMA) -> None:
    for stmt in LEDGER_SQL.format(s=schema).split(";"):
        if stmt.strip():
            conn.execute(stmt)


def plan(inv: dict) -> list:
    """[(database, schema, table, pairs or None for whole, why)] from the inventory: every entry with a leave_out or
    marked quarantine_whole."""
    out = []
    for e in inv.get("tables") or []:
        db_, sch, tab = e.get("database"), e.get("schema") or "public", e.get("table")
        if not (db_ and tab):
            continue
        if e.get("quarantine_whole") is True:
            out.append((db_, sch, tab, None, str(e.get("out_why") or "set OUT")))
        pairs = tuple((str(r["column"]), str(r["like"]), str(r.get("why") or "")) for r in (e.get("leave_out") or []))
        if pairs:
            out.append((db_, sch, tab, tuple((c, p) for c, p, _ in pairs), "; ".join(sorted({w for *_, w in pairs}))))
    return out


def _match(pairs):
    if pairs is None:
        return sql.SQL("true")
    return sql.SQL(" OR ").join(sql.SQL("COALESCE({}::text ILIKE {}, false)").format(sql.Identifier(c), sql.Literal(p))
                                for c, p in pairs)


def _exists(conn, schema, table) -> bool:
    return conn.execute("SELECT to_regclass(%s) IS NOT NULL",
                        (sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(table)).as_string(conn),)
                        ).fetchone()[0]


def move(conn, database, schema, table, pairs, why, *, src_schema=None, q_schema=SCHEMA, dry_run=False,
         today=None) -> dict:
    """Move one copied table's matching rows into quarantine. The caller commits; on a count disagreement this
    raises and the caller rolls back."""
    s = src_schema or dest_schema(database)
    t = dest_table(schema, table)
    out = {"table": f"{s}.{t}", "rows": 0, "moved": False}
    if not _exists(conn, s, t):
        out["why"] = "not in the copy"
        return out
    src = sql.SQL("{}.{}").format(sql.Identifier(s), sql.Identifier(t))
    n = conn.execute(sql.SQL("SELECT count(*) FROM {} WHERE {}").format(src, _match(pairs))).fetchone()[0]
    out["rows"] = n
    if dry_run or n == 0:
        return out
    qname = f"{database}__{t}"[:63]
    qrel = sql.SQL("{}.{}").format(sql.Identifier(q_schema), sql.Identifier(qname))
    conn.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} (LIKE {})").format(qrel, src))
    ins = conn.execute(sql.SQL("INSERT INTO {} SELECT * FROM {} WHERE {}").format(qrel, src, _match(pairs))).rowcount
    dele = conn.execute(sql.SQL("DELETE FROM {} WHERE {}").format(src, _match(pairs))).rowcount
    left = conn.execute(sql.SQL("SELECT count(*) FROM {} WHERE {}").format(src, _match(pairs))).fetchone()[0]
    if not (ins == dele == n and left == 0):
        raise RuntimeError(f"{s}.{t}: counted {n}, quarantined {ins}, deleted {dele}, {left} left; nothing kept")
    rule = "whole" if pairs is None else "; ".join(f"{c} ILIKE {p}" for c, p in pairs)
    after = (today or dt.date.today()) + dt.timedelta(days=DAYS)
    conn.execute(sql.SQL("INSERT INTO {}.ledger (source_table, held_in, rows, rule, why, removable_after) "
                         "VALUES (%s, %s, %s, %s, %s, %s)").format(sql.Identifier(q_schema)),
                 (f"{s}.{t}", f"{q_schema}.{qname}", n, rule, why, after))
    out.update(moved=True, held_in=f"{q_schema}.{qname}", removable_after=after.isoformat())
    return out


def run(conn, inv: dict, *, dry_run=False, log=print, **kw) -> list:
    if not dry_run:
        ensure(conn, kw.get("q_schema", SCHEMA))
        conn.commit()
    done = []
    for database, schema, table, pairs, why in plan(inv):
        try:
            r = move(conn, database, schema, table, pairs, why, dry_run=dry_run, **kw)
            conn.rollback() if dry_run else conn.commit()
        except Exception:
            conn.rollback()
            raise
        log(f"{r['table']}: {r['rows']} row(s)" + (f" -> {r['held_in']} (removable after {r['removable_after']})"
                                                     if r.get("moved") else f" {r.get('why', '')}".rstrip()))
        done.append(r)
    return done


def remove(conn, why: str, word: str, *, early=False, dry_run=False, q_schema=SCHEMA, today=None) -> list:
    """Drop the quarantine tables of the ledger lines whose `why` names `why` and that are not yet removed,
    each stamped `removed_at` and `removed_on_word` in the same transaction as its drop. A table whose rows are not
    the ledger's count is refused (something else wrote to it): nothing of that line is touched. Before
    `removable_after` only `early` (Arthur's word moved the day). The caller commits."""
    if not (word or "").strip():
        raise ValueError("a quarantine is removed on Arthur's word: --word names it")
    if not (why or "").strip():
        raise ValueError("--why names the ruling whose lines go: an empty one would match every line")
    today = today or dt.date.today()
    # the ruling as whole words anywhere in the line (a line quotes it mid-sentence; "ruling 168" is never "ruling 1680")
    lines = conn.execute(sql.SQL("SELECT id, held_in, rows, removable_after FROM {}.ledger WHERE why ~ %s "
                                 "AND removed_at IS NULL ORDER BY id").format(sql.Identifier(q_schema)),
                         (r"\m" + re.escape(why.strip()) + r"\M",)).fetchall()
    out = []
    for lid, held_in, rows, after in lines:
        if after > today and not early:
            raise RuntimeError(f"{held_in}: removable after {after}; --early only on Arthur's word that moves the day")
        sch, _, tab = held_in.partition(".")
        if sch != q_schema:
            raise RuntimeError(f"ledger line {lid} holds {held_in}, outside {q_schema}: never dropped from here")
        rel = sql.SQL("{}.{}").format(sql.Identifier(sch), sql.Identifier(tab))
        n = conn.execute(sql.SQL("SELECT count(*) FROM {}").format(rel)).fetchone()[0] if _exists(conn, sch, tab) else None
        # one table may hold the lines of several moves (a second run of the same table): its count is their sum
        due = conn.execute(sql.SQL("SELECT sum(rows) FROM {}.ledger WHERE held_in = %s AND removed_at IS NULL")
                           .format(sql.Identifier(q_schema)), (held_in,)).fetchone()[0]
        if n is not None and n != due:
            raise RuntimeError(f"{held_in}: {n} rows, the ledger says {due}; nothing removed")
        if not dry_run:
            if n is not None:
                conn.execute(sql.SQL("DROP TABLE {}").format(rel))
            conn.execute(sql.SQL("UPDATE {}.ledger SET removed_at = now(), removed_on_word = %s WHERE id = %s")
                         .format(sql.Identifier(q_schema)), (word.strip(), lid))
        out.append({"line": lid, "held_in": held_in, "rows": rows, "found": n, "removed": not dry_run})
    return out
