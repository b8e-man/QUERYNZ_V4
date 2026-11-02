"""Loading a batch (step 7.2; step 8.6): `build(conn, schema, ...)` streams the batch from the dump, reads it through the named
stages, writes each item's text to the store's compressed files on /mnt/hdd2 (store.py), lands the catalogue under `schema`
(no text in the database) with each stage's count and every catch, reads a sample of the items back from the files against
their sha256, and measures what the files and the catalogue take; `publish(conn, staging)` moves the tables into
`papers_past` and makes the view, in one transaction.

Rebuilt whole every load (regenerable): the schema's tables and the store's files together. A batch that does not
reconcile, or whose text does not read back, raises before anything is committed.

    python -m registers.papers_past.load --schema staging_papers_past [--batch 1] [--items 10000] [--after 0] [--every 1]
                                         [--database querynz_v4_sample]

`--every k` takes every k-th Papers Past row of the dump: a sample spread over the whole dump, not its first rows.
Every line printed is a count.
"""
import argparse
import json
import os
import random
import sys
import time

from registers.papers_past import capture, read, store

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "papers_past"
TABLES = ("sources", "batches", "files", "items", "stages", "catches")
ITEM_COLUMNS = ("key", "paper", "published_on", "title", "chars", "sha256", "upstream_id", "held_in_old", "batch", "line",
                "file", "frame_at", "frame_bytes", "at", "bytes", "url")
#: the dump's Papers Past rows, counted by one full pass (docs/research/papers-past-2026-11-02.md)
DUMP_ROWS = 90_651_423
URL = "https://paperspast.natlib.govt.nz/newspapers/"
READ_BACK = 500             # items read back from the files and checked against their sha256, per batch


def tables_sql(schema: str) -> str:
    return open(os.path.join(HERE, "tables.sql"), encoding="utf-8").read().replace("papers_past.", f"{schema}.")


def create_tables(conn, schema: str) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {schema}.{t} CASCADE")
    conn.execute(tables_sql(schema))


def held_in_old(ids: list, connect=None, chunk: int = 100_000) -> set:
    """The upstream ids the old estate's incoming_news holds, read-only, one statement per chunk under a time limit."""
    from support import db
    connect = connect or (lambda: db.connect(db.OLD_READ_KEY, "incoming_news", connect_timeout=10))
    out = set()
    with connect() as c:
        c.execute("SET statement_timeout = '120s'")
        c.execute("SET default_transaction_read_only = on")
        for i in range(0, len(ids), chunk):
            out |= {r[0] for r in c.execute("SELECT upstream_id FROM articles WHERE upstream_id = ANY(%s)",
                                            (ids[i:i + chunk],)).fetchall()}
    return out


def _rel_bytes(conn, name: str) -> int:
    return conn.execute("SELECT pg_total_relation_size(%s::regclass)", (name,)).fetchone()[0]


def _year(it: dict) -> int:
    return int(it["key"][len(it["paper"]):len(it["paper"]) + 4])


def build(conn, schema: str, batch: int = 1, items: int = 10_000, after: int = 0, every: int = 1, database: str = "querynz_v4",
          rows=None, held=None, source=None, root: str = store.ROOT, log=print) -> dict:
    t0 = time.monotonic()
    path, sha, size, verified = source or capture.source()
    scan = {}
    rows = rows if rows is not None else capture.rows(items, after, every=every, counts=scan)
    sdir = store.store_dir(database, schema, root)
    os.makedirs(root, exist_ok=True)
    store.wipe(sdir, root)
    writer = store.Writer(sdir)
    reading = read.Reading(batch, sha, keep_text=False)
    cat, n_rows, in_bytes, last_line = [], 0, 0, after
    for r in rows:
        n_rows += 1
        in_bytes += r.get("_bytes", 0)
        last_line = max(last_line, r["_line"])
        it = reading.take(r)
        if it is not None:
            writer.add(it["key"], it["paper"], _year(it), it["text"])
            cat.append({k: v for k, v in it.items() if k != "text"})
    places = writer.close()
    res = reading.finish()
    held = held if held is not None else held_in_old([it["upstream_id"] for it in cat])
    files = {f: i for i, f in enumerate(sorted({p.file for p in places.values()}), start=1)}
    if len(places) != len(cat):
        raise RuntimeError(f"batch {batch}: {len(cat)} items landed, {len(places)} placed in the store")

    create_tables(conn, schema)
    conn.execute(f"INSERT INTO {schema}.sources VALUES (%s, %s, %s, %s)", (sha, path, size, verified))
    conn.execute(f"INSERT INTO {schema}.batches (batch, document, reader, store, every) VALUES (%s, %s, %s, %s, %s)",
                 (batch, sha, read.READER, sdir, every))
    with conn.cursor().copy(f"COPY {schema}.files (file, path) FROM STDIN") as cp:
        for f, i in files.items():
            cp.write_row((i, f))
    with conn.cursor().copy(f"COPY {schema}.items ({', '.join(ITEM_COLUMNS)}) FROM STDIN") as cp:
        for it in cat:
            p = places[it["key"]]
            cp.write_row((it["key"], it["paper"], it["published_on"], it["title"], it["chars"], p.sha256, it["upstream_id"],
                          it["upstream_id"] in held, batch, it["line"], files[p.file], p.frame_at, p.frame_bytes, p.at,
                          p.bytes, None if it["url"] == URL + it["key"] else it["url"]))
    with conn.cursor().copy(f"COPY {schema}.catches (batch, stage, item, place, reason, example) FROM STDIN") as cp:
        for stage, item, place, reason, example in res.catches:
            cp.write_row((batch, stage, item, place, reason, json.dumps(example, ensure_ascii=False) if example else None))
    conn.execute(f"ANALYZE {schema}.items")
    bad = read_back(conn, schema, sdir, READ_BACK)
    if bad:
        raise RuntimeError(f"batch {batch}: {len(bad)} items do not read back from the store: {bad[:3]}")
    catalogue = sum(_rel_bytes(conn, f"{schema}.{t}") for t in ("items", "files", "batches"))
    disk = store.disk_bytes(sdir)
    measured = {"in": in_bytes, "landed": catalogue}
    for seq, (stage, n_in, n_out, aside) in enumerate(res.stages, start=1):
        conn.execute(f"INSERT INTO {schema}.stages VALUES (%s, %s, %s, %s, %s, %s, %s)",
                     (batch, seq, stage, n_in, n_out, aside, measured.get(stage)))
    conn.execute(f"INSERT INTO {schema}.stages VALUES (%s, %s, 'text files (measured)', %s, %s, 0, %s)",
                 (batch, len(res.stages) + 1, len(cat), len(cat), disk))
    n = len(cat)
    rate = n / n_rows if n_rows else 0
    counts = {"batch": batch, "every": every, "in": n_rows, "landed": n, "set aside": len(res.catches),
              "held in the old estate": sum(1 for it in cat if it["upstream_id"] in held),
              "last dump line": last_line, "papers past rows passed": scan.get("seen", n_rows),
              "files": len(files), "frames": writer.frames, "read back": min(READ_BACK, n),
              "dump bytes per item": round(in_bytes / n_rows) if n_rows else 0,
              "text bytes per item": round(sum(p.bytes for p in places.values()) / n) if n else 0,
              "text chars per item": round(sum(it["chars"] for it in cat) / n) if n else 0,
              "disk bytes per item": round(disk / n) if n else 0,
              "catalogue bytes per item": round(catalogue / n) if n else 0,
              "projected items": round(DUMP_ROWS * rate),
              "projected disk GB": round(DUMP_ROWS * rate * disk / n / 1e9, 1) if n else 0,
              "projected catalogue GB": round(DUMP_ROWS * rate * catalogue / n / 1e9, 1) if n else 0,
              "store free GB": round(os.statvfs(root).f_bavail * os.statvfs(root).f_frsize / 1e9, 1),
              "seconds": round(time.monotonic() - t0)}
    by = {}
    for stage, _, _, reason, _ in res.catches:
        by[f"{stage}: {reason}"] = by.get(f"{stage}: {reason}", 0) + 1
    for k, v in counts.items():
        log(f"papers_past: {k} {v}")
    for k, v in sorted(by.items()):
        log(f"papers_past: set aside, {k}: {v}")
    return {**counts, "reasons": by, "store": sdir}


def read_back(conn, schema: str, sdir: str, n: int, seed: int = 8_6) -> list:
    """n items (the first, the last and a random spread) read back from the store's files and checked against their
    catalogued sha256 and length in characters. The problems, as plain lines."""
    keys = [r[0] for r in conn.execute(f"SELECT key FROM {schema}.items ORDER BY key").fetchall()]
    pick = sorted(set(keys[:1] + keys[-1:] + random.Random(seed).sample(keys, min(n, len(keys)))))
    out = []
    for key, path, frame_at, frame_bytes, at, nb, sha, chars in conn.execute(
            f"SELECT i.key, f.path, i.frame_at, i.frame_bytes, i.at, i.bytes, i.sha256, i.chars FROM {schema}.items i "
            f"JOIN {schema}.files f USING (file) WHERE i.key = ANY(%s)", (pick,)).fetchall():
        try:
            t = store.text(sdir, path, frame_at, frame_bytes, at, nb, sha)
            if len(t) != chars:
                out.append(f"{key}: {len(t)} characters read back, {chars} catalogued")
        except Exception as exc:
            out.append(f"{key}: {exc}")
    return out


def publish(conn, staging: str) -> None:
    """The lane's tables replaced by the staged ones, and the view made, in one transaction."""
    with conn.transaction():
        conn.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
        conn.execute(f"ALTER SCHEMA {staging} RENAME TO {SCHEMA}")
        conn.execute(open(os.path.join(HERE, "publish.sql"), encoding="utf-8").read())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--items", type=int, default=10_000)
    ap.add_argument("--after", type=int, default=0)
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    if a.schema == SCHEMA:
        print("load builds into a staging or scratch schema; publish moves it", file=sys.stderr)
        return 2
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '1800s'")
        build(conn, a.schema, a.batch, a.items, a.after, a.every, a.database)
        conn.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
