"""Loading a batch (step 7.2; step 8.6): `build(conn, schema, ...)` streams the batch from the dump, reads it through the named
stages, lands it under `schema` with each stage's count and every catch, and measures what each stage's output takes on disk;
`publish(conn, staging)` moves the tables into `papers_past` and makes the view, in one transaction.

Rebuilt whole every load (regenerable). A batch that does not reconcile raises before anything lands.

    python -m registers.papers_past.load --schema staging_papers_past [--batch 1] [--items 10000] [--after 0]

Every line printed is a count.
"""
import argparse
import json
import os
import sys
import time

from registers.papers_past import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "papers_past"
TABLES = ("sources", "items", "stages", "catches")
ITEM_COLUMNS = ("key", "paper", "published_on", "title", "text", "chars", "url", "upstream_id", "held_in_old", "batch",
                "document", "place", "reader")
#: the keyword index the batch is measured with (step 7.2's "Keyword index: needs sizing at this scale"): the whole text,
#: not the old index's title and first 1,500 characters (7.3)
KEYWORD_INDEX = "CREATE INDEX {name} ON {t} USING gin (to_tsvector('simple', coalesce(title, '') || ' ' || text))"


def tables_sql(schema: str) -> str:
    return open(os.path.join(HERE, "tables.sql"), encoding="utf-8").read().replace("papers_past.", f"{schema}.")


def create_tables(conn, schema: str) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {schema}.{t} CASCADE")
    conn.execute(tables_sql(schema))


def held_in_old(ids: list, connect=None) -> set:
    """The upstream ids the old estate's incoming_news holds, read-only, one statement under a time limit."""
    from support import db
    connect = connect or (lambda: db.connect(db.OLD_READ_KEY, "incoming_news", connect_timeout=10))
    with connect() as c:
        c.execute("SET statement_timeout = '120s'")
        c.execute("SET default_transaction_read_only = on")
        return {r[0] for r in c.execute("SELECT upstream_id FROM articles WHERE upstream_id = ANY(%s)", (ids,)).fetchall()}


def _rel_bytes(conn, name: str) -> int:
    return conn.execute("SELECT pg_total_relation_size(%s::regclass)", (name,)).fetchone()[0]


def build(conn, schema: str, batch: int = 1, items: int = 10_000, after: int = 0, rows=None, held=None, source=None,
          log=print) -> dict:
    t0 = time.monotonic()
    path, sha, size, verified = source or capture.source()
    rows = list(rows if rows is not None else capture.rows(items, after))
    in_bytes = sum(r.get("_bytes", 0) for r in rows)
    held = held if held is not None else held_in_old([int(r["id"]) for r in rows])
    res = read.read(rows, batch, sha, held)
    create_tables(conn, schema)
    conn.execute(f"INSERT INTO {schema}.sources VALUES (%s, %s, %s, %s)", (sha, path, size, verified))
    with conn.cursor().copy(f"COPY {schema}.items ({', '.join(ITEM_COLUMNS)}) FROM STDIN") as cp:
        for it in res.items:
            cp.write_row(tuple(it[c] for c in ITEM_COLUMNS))
    with conn.cursor().copy(f"COPY {schema}.catches (batch, stage, item, place, reason, example) FROM STDIN") as cp:
        for stage, item, place, reason, example in res.catches:
            cp.write_row((batch, stage, item, place, reason, json.dumps(example, ensure_ascii=False) if example else None))
    conn.execute(f"ANALYZE {schema}.items")
    table_bytes = _rel_bytes(conn, f"{schema}.items")
    conn.execute(KEYWORD_INDEX.format(name=f"{schema}_items_words", t=f"{schema}.items"))
    index_bytes = _rel_bytes(conn, f"{schema}.{schema}_items_words")
    measured = {"in": in_bytes, "landed": table_bytes}
    for seq, (stage, n_in, n_out, aside) in enumerate(res.stages, start=1):
        conn.execute(f"INSERT INTO {schema}.stages VALUES (%s, %s, %s, %s, %s, %s, %s)",
                     (batch, seq, stage, n_in, n_out, aside, measured.get(stage)))
    conn.execute(f"INSERT INTO {schema}.stages VALUES (%s, %s, 'keyword index (measured)', %s, %s, 0, %s)",
                 (batch, len(res.stages) + 1, len(res.items), len(res.items), index_bytes))
    n = len(res.items)
    counts = {"batch": batch, "in": len(rows), "landed": n, "set aside": len(res.catches),
              "held in the old estate": sum(1 for it in res.items if it["held_in_old"]),
              "last dump line": max((r["_line"] for r in rows), default=after),
              "dump bytes per item": round(in_bytes / len(rows)) if rows else 0,
              "table bytes per item": round(table_bytes / n) if n else 0,
              "keyword index bytes per item": round(index_bytes / n) if n else 0,
              "text chars per item": round(sum(it["chars"] for it in res.items) / n) if n else 0,
              "seconds": round(time.monotonic() - t0)}
    by = {}
    for stage, _, _, reason, _ in res.catches:
        by[f"{stage}: {reason}"] = by.get(f"{stage}: {reason}", 0) + 1
    for k, v in counts.items():
        log(f"papers_past: {k} {v}")
    for k, v in sorted(by.items()):
        log(f"papers_past: set aside, {k}: {v}")
    return {**counts, "reasons": by}


def publish(conn, staging: str) -> None:
    """The lane's tables replaced by the staged ones, and the view made, in one transaction."""
    with conn.transaction():
        conn.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
        conn.execute(f"ALTER SCHEMA {staging} RENAME TO {SCHEMA}")
        conn.execute(f"ALTER INDEX {SCHEMA}.{staging}_items_words RENAME TO {SCHEMA}_items_words")
        conn.execute(open(os.path.join(HERE, "publish.sql"), encoding="utf-8").read())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--items", type=int, default=10_000)
    ap.add_argument("--after", type=int, default=0)
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    if a.schema == SCHEMA:
        print("load builds into a staging or scratch schema; publish moves it", file=sys.stderr)
        return 2
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '1800s'")
        build(conn, a.schema, a.batch, a.items, a.after)
        conn.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
