"""Loading the archive (step 7.2; step 8.6): one streaming pass of the dump, in chunks, resumable.

`run(conn, schema, ...)` streams the dump's Papers Past rows (`capture.rows`), reads each through the named stages
(`read.Reading`), writes its text to the store's compressed files on /mnt/hdd2 (`store.py`) and its catalogue row to the
database (no text in the database). Every `chunk` rows in, the chunk commits: the store is flushed and synced to the disk,
the chunk's catalogue rows are COPYed (a second row for an article already held is refused by the key and set aside at
`once`), its catches are COPYed, each file's committed length and the chunk's checkpoint (its last dump line and the
stride's count) are written, a sample of the chunk's items is read back from the files against their sha256, and then the
transaction commits. Memory is bounded by the chunk: nothing of an earlier chunk is held.

A stopped run (deadline, kill, crash) restarts after its last committed chunk: the store's files are cut back to their
committed lengths (only frames no catalogue row points at go), and the dump is streamed again from its top, rows up to the
checkpoint's line skipped undecoded (gzip cannot seek; the skip costs the gunzip of the dump up to that line, measured in
docs/research/papers-past-2026-11-02.md). When the dump is exhausted (or `items` rows are in), the stages are written from
the chunks' sums, the whole batch reconciles (items in = items landed + set aside, the catalogue's and the catch log's own
counts agreeing) and 2,000 items read back, or it raises.

    python -m registers.papers_past.load --schema staging_papers_past [--database querynz_v4] [--items N] [--every k]
                                         [--chunk 1000000] [--fresh]

Without --fresh a schema holding a run of the same dump and stride resumes it; --fresh rebuilds the schema and the store
whole (regenerable). `--every k` takes every k-th Papers Past row: a sample spread over the dump. `--items 0` is the whole
dump. Every line printed is a count. `publish(conn, staging)` moves the tables into `papers_past` and makes the view.
"""
import argparse
import bisect
import json
import os
import random
import subprocess
import sys
import time
from array import array

from registers.papers_past import capture, read, store

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "papers_past"
TABLES = ("sources", "batches", "files", "chunks", "items", "stages", "catches")
ITEM_COLUMNS = ("key", "paper", "published_on", "title", "chars", "sha256", "upstream_id", "held_in_old", "batch", "line",
                "file", "frame_at", "frame_bytes", "at", "bytes", "url")
#: the dump's Papers Past rows, counted by one full pass (docs/research/papers-past-2026-11-02.md)
DUMP_ROWS = 90_651_423
URL = "https://paperspast.natlib.govt.nz/newspapers/"
CHUNK = 1_000_000           # rows in per committed chunk
READ_BACK_CHUNK = 200       # items of each chunk read back from the files before it commits
READ_BACK = 2_000           # items of the whole batch read back at the end
TWICE = "a second row for an article the catalogue already holds"


def tables_sql(schema: str) -> str:
    return open(os.path.join(HERE, "tables.sql"), encoding="utf-8").read().replace("papers_past.", f"{schema}.")


def create_tables(conn, schema: str) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {schema}.{t} CASCADE")
    conn.execute(tables_sql(schema))


class Held:
    """The upstream ids of the old estate's Papers Past rows, sorted in one array (8 bytes an id, 4.6 M ids, ~37 MB)."""

    def __init__(self, ids):
        self.ids = array("q", sorted(ids))

    def __contains__(self, x) -> bool:
        i = bisect.bisect_left(self.ids, x)
        return i < len(self.ids) and self.ids[i] == x

    def __len__(self):
        return len(self.ids)


def held_in_old(connect=None) -> Held:
    """The old estate's incoming_news Papers Past upstream ids, read once, read-only, streamed."""
    from support import db
    connect = connect or (lambda: db.connect(db.OLD_READ_KEY, "incoming_news", connect_timeout=10))
    out = array("q")
    with connect() as c:
        c.execute("SET statement_timeout = '600s'")
        c.execute("SET default_transaction_read_only = on")
        with c.cursor(name="pp_held") as cur:
            cur.itersize = 200_000
            cur.execute("SELECT upstream_id FROM articles WHERE upstream_id IS NOT NULL "
                        "AND news_url LIKE 'https://paperspast.natlib.govt.nz/%'")
            for (uid,) in cur:
                out.append(uid)
    return Held(out)


def _rel_bytes(conn, name: str) -> int:
    return conn.execute("SELECT pg_total_relation_size(%s::regclass)", (name,)).fetchone()[0]


def _year(it: dict) -> int:
    return int(it["key"][len(it["paper"]):len(it["paper"]) + 4])


def _exists(conn, schema: str) -> bool:
    return conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"{schema}.chunks",)).fetchone()[0]


def state(conn, schema: str, batch: int):
    """The run under `schema` as its tables hold it, or None: its batch row, its checkpoint and its files."""
    if not _exists(conn, schema):
        return None
    b = conn.execute(f"SELECT document, every, store FROM {schema}.batches WHERE batch = %s", (batch,)).fetchone()
    if b is None:
        return None
    last = conn.execute(f"SELECT coalesce(max(chunk), 0), coalesce(max(last_line), 0), coalesce(max(seen), 0), "
                        f"coalesce(sum(rows_in), 0) FROM {schema}.chunks WHERE batch = %s", (batch,)).fetchone()
    done = conn.execute(f"SELECT count(*) > 0 FROM {schema}.stages WHERE batch = %s", (batch,)).fetchone()[0]
    files = {p: (f, n) for f, p, n in conn.execute(f"SELECT file, path, bytes FROM {schema}.files").fetchall()}
    reasons = {r[0] for r in conn.execute(f"SELECT DISTINCT stage || ': ' || reason FROM {schema}.catches "
                                          f"WHERE batch = %s AND example IS NOT NULL", (batch,)).fetchall()}
    return {"document": b[0], "every": b[1], "store": b[2], "chunk": last[0], "line": last[1], "seen": last[2],
            "rows_in": int(last[3]), "done": done, "files": files, "reasons": reasons}


def read_back(conn, schema: str, sdir: str, n: int, keys=None, seed=None) -> list:
    """Items read back from the store's files and checked against their catalogued sha256 and length in characters:
    `keys` if given, else the first and last by key and n chosen at random in the database. The problems, as lines."""
    if keys is None:
        keys = [r[0] for r in conn.execute(f"(SELECT key FROM {schema}.items ORDER BY key LIMIT 1) UNION ALL "
                                           f"(SELECT key FROM {schema}.items ORDER BY key DESC LIMIT 1) UNION ALL "
                                           f"(SELECT key FROM {schema}.items ORDER BY random() LIMIT %s)", (n,)).fetchall()]
    out, got = [], 0
    for key, path, frame_at, frame_bytes, at, nb, sha, chars in conn.execute(
            f"SELECT i.key, f.path, i.frame_at, i.frame_bytes, i.at, i.bytes, i.sha256, i.chars FROM {schema}.items i "
            f"JOIN {schema}.files f USING (file) WHERE i.key = ANY(%s)", (list(set(keys)),)).fetchall():
        got += 1
        try:
            t = store.text(sdir, path, frame_at, frame_bytes, at, nb, sha)
            if len(t) != chars:
                out.append(f"{key}: {len(t)} characters read back, {chars} catalogued")
        except Exception as exc:
            out.append(f"{key}: {exc}")
    if got != len(set(keys)):
        out.append(f"{len(set(keys)) - got} of the keys asked for are not in the catalogue")
    return out


class _Chunk:
    def __init__(self):
        self.rows, self.first, self.last, self.seen = 0, None, None, 0
        self.rows_cat = []          # (key, paper, published_on, title, chars, upstream_id, held, line, url or None)
        self.t0 = time.monotonic()


def run(conn, schema: str, *, database: str = "querynz_v4", batch: int = 1, items: int = 0, every: int = 1,
        chunk: int = CHUNK, fresh: bool = False, root: str = store.ROOT, rows_from=None, held=None, source=None,
        log=print, after_commit=None) -> dict:
    """The streaming load (see the module's text). rows_from(after, seen, n) -> rows replaces the dump for tests;
    after_commit(chunk_number) is called after each chunk commits (tests stop a run there)."""
    t0 = time.monotonic()
    path, sha, size, verified = source or capture.source()
    sdir = store.store_dir(database, schema, root)
    os.makedirs(root, exist_ok=True)
    st = None if fresh else state(conn, schema, batch)
    if st is not None and (st["document"] != sha or st["every"] != every or st["store"] != sdir):
        raise RuntimeError(f"{schema} holds a run of another dump, stride or store; rebuild it with --fresh")
    if st is None:
        store.wipe(sdir, root)
        create_tables(conn, schema)
        conn.execute(f"INSERT INTO {schema}.sources VALUES (%s, %s, %s, %s)", (sha, path, size, verified))
        conn.execute(f"INSERT INTO {schema}.batches (batch, document, reader, store, every) VALUES (%s, %s, %s, %s, %s)",
                     (batch, sha, read.READER, sdir, every))
        conn.commit()
        st = state(conn, schema, batch)
        log(f"papers_past: fresh run into {schema}")
    elif st["done"] and not (items and items > st["rows_in"]):
        log(f"papers_past: {schema} batch {batch} is complete; nothing to do")
        return summary(conn, schema, batch, sdir, t0, log)
    else:
        if st["done"]:      # a run that stopped at its `items` taken further: its stages are written again at the end
            conn.execute(f"DELETE FROM {schema}.stages WHERE batch = %s", (batch,))
            conn.commit()
        cut = store.restore(sdir, {p: n for p, (_, n) in st["files"].items()})
        log(f"papers_past: resumed after chunk {st['chunk']} (dump line {st['line']}, {st['rows_in']} rows in); "
            f"{len(cut)} files cut back by {sum(cut.values())} uncommitted bytes")
    held = held if held is not None else held_in_old()
    log(f"papers_past: the old estate's ids {len(held)}")
    files = {p: f for p, (f, _) in st["files"].items()}
    remaining = (items - st["rows_in"]) if items else 1 << 62
    if remaining <= 0:
        rows = iter(())
    elif rows_from is not None:
        rows = rows_from(st["line"], st["seen"], remaining)
    else:
        rows = capture.rows(remaining, st["line"], every=every, seen=st["seen"])
    writer = store.Writer(sdir)
    reading = read.Reading(batch, sha, keep_text=False, dedupe=False, seen_reasons=st["reasons"])
    n_chunk, c = st["chunk"], _Chunk()
    try:
        for r in rows:
            c.rows += 1
            c.first = c.first or r["_line"]
            c.last, c.seen = r["_line"], r.get("_seen", 0)
            it = reading.take(r)
            if it is not None:
                writer.add(it["key"], it["paper"], _year(it), it["text"], ref=it["upstream_id"])
                c.rows_cat.append((it["key"], it["paper"], it["published_on"], it["title"], it["chars"],
                                   it["upstream_id"], it["upstream_id"] in held, it["line"],
                                   None if it["url"] == URL + it["key"] else it["url"]))
            if c.rows >= chunk:
                n_chunk += 1
                _commit(conn, schema, batch, n_chunk, c, writer, reading, files, sdir, log)
                if after_commit:
                    after_commit(n_chunk)
                c = _Chunk()
        if c.rows:
            n_chunk += 1
            _commit(conn, schema, batch, n_chunk, c, writer, reading, files, sdir, log)
            if after_commit:
                after_commit(n_chunk)
    finally:
        writer.close()
        close = getattr(rows, "close", None)
        if close:
            close()
    return finish(conn, schema, batch, sdir, t0, log)


def _commit(conn, schema, batch, n_chunk, c, writer, reading, files, sdir, log) -> None:
    writer.flush()
    places = writer.drain()
    catches = reading.drain()
    if len(places) != len(c.rows_cat):
        raise RuntimeError(f"chunk {n_chunk}: {len(c.rows_cat)} items read, {len(places)} placed in the store")
    store.sync(sdir)
    new = sorted({p.file for p in places.values()} - set(files))
    top = max(files.values(), default=0)
    for i, f in enumerate(new, start=top + 1):
        files[f] = i
    try:
        conn.execute(f"CREATE TEMP TABLE IF NOT EXISTS pp_incoming (LIKE {schema}.items) ON COMMIT DELETE ROWS")
        with conn.cursor().copy(f"COPY pp_incoming ({', '.join(ITEM_COLUMNS)}) FROM STDIN") as cp:
            for key, paper, on, title, chars, uid, h, line, url in c.rows_cat:
                p = places[uid]
                cp.write_row((key, paper, on, title, chars, p.sha256, uid, h, batch, line, files[p.file], p.frame_at,
                              p.frame_bytes, p.at, p.bytes, url))
        landed = conn.execute(f"INSERT INTO {schema}.items SELECT * FROM pp_incoming ON CONFLICT (key) DO NOTHING").rowcount
        twice = conn.execute(f"SELECT i.upstream_id, i.line, i.key FROM pp_incoming i WHERE NOT EXISTS "
                             f"(SELECT 1 FROM {schema}.items x WHERE x.upstream_id = i.upstream_id)").fetchall()
        if landed + len(twice) != len(c.rows_cat):
            raise RuntimeError(f"chunk {n_chunk}: {len(c.rows_cat)} items, {landed} landed, {len(twice)} refused")
        with conn.cursor().copy(f"COPY {schema}.catches (batch, stage, item, place, reason, example) FROM STDIN") as cp:
            for stage, item, place, reason, example in catches:
                cp.write_row((batch, stage, item, place, reason, json.dumps(example, ensure_ascii=False) if example else None))
            for uid, line, key in twice:
                cp.write_row((batch, "once", str(uid), f"scraper_results line {line}", TWICE,
                              json.dumps({"key": key, "id": uid, "line": line})))
        sizes = store.sizes(sdir)
        touched = {p.file for p in places.values()}
        with conn.cursor() as cur:
            cur.executemany(f"INSERT INTO {schema}.files (file, path, bytes) VALUES (%s, %s, %s) "
                            f"ON CONFLICT (file) DO UPDATE SET bytes = excluded.bytes",
                            [(files[f], f, sizes[f]) for f in sorted(touched)])
        no_article = sum(1 for x in catches if x[0] == "article id")
        no_text = sum(1 for x in catches if x[0] == "text")
        if c.rows != no_article + no_text + len(c.rows_cat):
            raise RuntimeError(f"chunk {n_chunk}: {c.rows} rows in, {no_article + no_text} set aside, {len(c.rows_cat)} read")
        conn.execute(f"INSERT INTO {schema}.chunks (batch, chunk, first_line, last_line, seen, rows_in, no_article, "
                     f"no_text, twice, landed, store_bytes, seconds) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                     (batch, n_chunk, c.first, c.last, c.seen, c.rows, no_article, no_text, len(twice), landed,
                      sum(sizes.values()), round(time.monotonic() - c.t0)))
        sample = random.sample([x[0] for x in c.rows_cat], min(READ_BACK_CHUNK, len(c.rows_cat)))
        bad = read_back(conn, schema, sdir, 0, keys=[k for k in sample if k not in {t[2] for t in twice}])
        if bad:
            raise RuntimeError(f"chunk {n_chunk}: {len(bad)} items do not read back from the store: {bad[:3]}")
        conn.commit()
    except BaseException:
        conn.rollback()
        for f in new:
            files.pop(f, None)
        raise
    log(f"papers_past: chunk {n_chunk} committed: {c.rows} in, {landed} landed, {c.rows - landed} set aside, "
        f"dump line {c.last}, {round(time.monotonic() - c.t0)} s")


def finish(conn, schema: str, batch: int, sdir: str, t0: float, log=print) -> dict:
    """The stages from the chunks' sums, the whole batch reconciled and read back, the measures written; or it raises."""
    s = conn.execute(f"SELECT coalesce(sum(rows_in),0), coalesce(sum(no_article),0), coalesce(sum(no_text),0), "
                     f"coalesce(sum(twice),0), coalesce(sum(landed),0) FROM {schema}.chunks WHERE batch = %s",
                     (batch,)).fetchone()
    n_in, no_article, no_text, twice, landed = (int(x) for x in s)
    stages = [("in", n_in, n_in, 0), ("article id", n_in, n_in - no_article, no_article),
              ("text", n_in - no_article, n_in - no_article - no_text, no_text),
              ("once", n_in - no_article - no_text, landed, twice), ("landed", landed, landed, 0)]
    n_items = conn.execute(f"SELECT count(*) FROM {schema}.items WHERE batch = %s", (batch,)).fetchone()[0]
    n_catches = conn.execute(f"SELECT count(*) FROM {schema}.catches WHERE batch = %s", (batch,)).fetchone()[0]
    why = []
    if n_in != landed + no_article + no_text + twice:
        why.append(f"{n_in} in, {landed} landed, {no_article + no_text + twice} set aside")
    if n_items != landed:
        why.append(f"the catalogue holds {n_items} items, the chunks landed {landed}")
    if n_catches != no_article + no_text + twice:
        why.append(f"the catch log holds {n_catches}, the chunks set aside {no_article + no_text + twice}")
    committed = {p: n for p, n in conn.execute(f"SELECT path, bytes FROM {schema}.files").fetchall()}
    on_disk = store.sizes(sdir)
    if on_disk != committed:
        why.append(f"the store's files are not the committed ones ({len(set(on_disk.items()) ^ set(committed.items()))} differ)")
    why += read_back(conn, schema, sdir, READ_BACK)
    if why:
        conn.rollback()
        raise RuntimeError(f"batch {batch} does not reconcile: {why[:5]}")
    conn.execute(f"DELETE FROM {schema}.stages WHERE batch = %s", (batch,))
    catalogue = sum(_rel_bytes(conn, f"{schema}.{t}") for t in ("items", "files", "batches", "chunks"))
    disk = store.disk_bytes(sdir)
    measured = {"landed": catalogue}
    for seq, (stage, a, b, aside) in enumerate(stages, start=1):
        conn.execute(f"INSERT INTO {schema}.stages VALUES (%s, %s, %s, %s, %s, %s, %s)",
                     (batch, seq, stage, a, b, aside, measured.get(stage)))
    conn.execute(f"INSERT INTO {schema}.stages VALUES (%s, %s, 'text files (measured)', %s, %s, 0, %s)",
                 (batch, len(stages) + 1, landed, landed, disk))
    conn.execute(f"ANALYZE {schema}.items")
    conn.commit()
    return summary(conn, schema, batch, sdir, t0, log)


def summary(conn, schema: str, batch: int, sdir: str, t0: float, log=print) -> dict:
    every = conn.execute(f"SELECT every FROM {schema}.batches WHERE batch = %s", (batch,)).fetchone()[0]
    ch = conn.execute(f"SELECT count(*), coalesce(sum(rows_in),0), coalesce(max(last_line),0), coalesce(max(seen),0), "
                      f"coalesce(sum(seconds),0) FROM {schema}.chunks WHERE batch = %s", (batch,)).fetchone()
    n, held, chars, nbytes = conn.execute(f"SELECT count(*), count(*) FILTER (WHERE held_in_old), coalesce(sum(chars),0), "
                                          f"coalesce(sum(bytes),0) FROM {schema}.items WHERE batch = %s",
                                          (batch,)).fetchone()
    by = {f"{a}: {b}": int(k) for a, b, k in conn.execute(
        f"SELECT stage, reason, count(*) FROM {schema}.catches WHERE batch = %s GROUP BY 1, 2", (batch,)).fetchall()}
    catalogue = sum(_rel_bytes(conn, f"{schema}.{t}") for t in ("items", "files", "batches", "chunks"))
    disk = store.disk_bytes(sdir)
    n_in = int(ch[1])
    rate = n / n_in if n_in else 0
    vfs = os.statvfs(os.path.dirname(sdir))
    counts = {"batch": batch, "every": every, "chunks": ch[0], "in": n_in, "landed": n, "set aside": sum(by.values()),
              "held in the old estate": held, "last dump line": ch[2], "papers past rows passed": ch[3],
              "files": len(store.sizes(sdir)),
              "text bytes per item": round(nbytes / n) if n else 0,
              "text chars per item": round(chars / n) if n else 0,
              "disk bytes per item": round(disk / n) if n else 0,
              "catalogue bytes per item": round(catalogue / n) if n else 0,
              "projected items": round(DUMP_ROWS * rate),
              "projected disk GB": round(DUMP_ROWS * rate * disk / n / 1e9, 1) if n else 0,
              "projected catalogue GB": round(DUMP_ROWS * rate * catalogue / n / 1e9, 1) if n else 0,
              "store free GB": round(vfs.f_bavail * vfs.f_frsize / 1e9, 1),
              "chunk seconds": int(ch[4]), "seconds": round(time.monotonic() - t0)}
    for k, v in counts.items():
        log(f"papers_past: {k} {v}")
    for k, v in sorted(by.items()):
        log(f"papers_past: set aside, {k}: {v}")
    return {**counts, "reasons": by, "store": sdir}


def build(conn, schema: str, batch: int = 1, items: int = 10_000, after: int = 0, every: int = 1,
          database: str = "querynz_v4", rows=None, held=None, source=None, root: str = store.ROOT, log=print) -> dict:
    """A small batch rebuilt whole (fresh), one chunk: the first `items` rows (or every k-th). `after` is not used by the
    streaming load (a resume takes its line from the checkpoint) and must be 0."""
    if after:
        raise ValueError("build starts at the dump's top; a resume takes its line from the checkpoint")
    rows_from = (lambda a, s, n: iter(rows)) if rows is not None else None
    return run(conn, schema, database=database, batch=batch, items=items, every=every, chunk=max(items, 1), fresh=True,
               root=root, rows_from=rows_from, held=held if held is not None else None, source=source, log=log)


def publish(conn, staging: str) -> None:
    """The lane's tables replaced by the staged ones, and the view made, in one transaction."""
    with conn.transaction():
        conn.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
        conn.execute(f"ALTER SCHEMA {staging} RENAME TO {SCHEMA}")
        conn.execute(open(os.path.join(HERE, "publish.sql"), encoding="utf-8").read())


def _low_priority() -> None:
    """Idle IO class for this process (the scheduler sets the niceness; the gunzip child is already idle IO)."""
    subprocess.run(["ionice", "-c3", "-p", str(os.getpid())], check=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--items", type=int, default=0, help="rows in at most; 0 is the whole dump")
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--chunk", type=int, default=CHUNK)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    if a.schema == SCHEMA:
        print("load builds into a staging or scratch schema; publish moves it", file=sys.stderr)
        return 2
    _low_priority()
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '3600s'")
        run(conn, a.schema, database=a.database, batch=a.batch, items=a.items, every=a.every, chunk=a.chunk,
            fresh=a.fresh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
