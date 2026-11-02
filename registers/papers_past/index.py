"""The keyword index over whole documents, sized before an engine is chosen (step 7.2's keyword-index row; step 8.6). Built
outside PostgreSQL, over the store's files on /mnt/hdd2, from a sample's catalogue; the full index is not built here.

Two engines that run on the box: SQLite FTS5 (in Python's own sqlite3; contentless, so the index holds no text, only
postings, and a hit is the item's upstream id, read back through the catalogue), and tantivy (its Python wheel, where it
imports; text not stored). Each is built at low priority into the store's own folder:

    /mnt/hdd2/qv4-papers-past/<store>/index/fts5.sqlite
    /mnt/hdd2/qv4-papers-past/<store>/index/tantivy/

and measured: bytes on disk per item, the build's seconds, and each query's time (first run and the median of the next
five) with its count of hits and its top twenty by rank. The index is searched only: it is never a name index and nothing
reads it into links/ (hard limit 17).

    python -m registers.papers_past.index --schema scratch_… --database querynz_v4_sample [--engine fts5,tantivy] [--lib DIR]
"""
import argparse
import json
import os
import shutil
import sqlite3
import statistics
import sys
import time

from registers.papers_past import store

#: the queries each engine is timed on: a common word, a rarer one, a phrase, a prefix, a conjunction, a Māori word
QUERIES = {
    "a common word": ("wellington", "wellington"),
    "a rarer word": ("kauri", "kauri"),
    "a phrase": ('"bank of new zealand"', '"bank of new zealand"'),
    "a prefix": ("telegra*", None),
    "two words, both": ("gold AND otago", "+gold +otago"),
    "a Māori word": ("whare", "whare"),
}


def documents(conn, schema: str, sdir: str):
    """(upstream id, title, text) of every catalogued item, each frame decompressed once."""
    with conn.cursor(name=f"pp_index_{time.monotonic_ns()}") as cur:
        cur.itersize = 20_000
        cur.execute(f"SELECT i.upstream_id, i.title, f.path, i.frame_at, i.frame_bytes, i.at, i.bytes FROM {schema}.items i "
                    f"JOIN {schema}.files f USING (file) ORDER BY f.path, i.frame_at")
        last, raw = None, b""
        for uid, title, path, frame_at, frame_bytes, at, n in cur:
            if (path, frame_at) != last:
                raw, last = store.frame(sdir, path, frame_at, frame_bytes), (path, frame_at)
            yield uid, title or "", raw[at:at + n].decode("utf-8")


def _size(path: str) -> int:
    if os.path.isfile(path):
        return os.stat(path).st_blocks * 512
    return sum(os.stat(os.path.join(d, f)).st_blocks * 512 for d, _, fs in os.walk(path) for f in fs)


def _time(run, reps: int = 5):
    t = time.perf_counter()
    first = run()
    cold = time.perf_counter() - t
    warm = []
    for _ in range(reps):
        t = time.perf_counter()
        run()
        warm.append(time.perf_counter() - t)
    return first, round(cold * 1000, 2), round(statistics.median(warm) * 1000, 2)


def fts5(docs, path: str) -> dict:
    if os.path.exists(path):
        os.remove(path)
    t0 = time.monotonic()
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode = OFF")
    db.execute("PRAGMA synchronous = OFF")
    db.execute("CREATE VIRTUAL TABLE words USING fts5(title, text, content='', detail=full, "
               "tokenize='unicode61 remove_diacritics 2')")
    n = 0
    batch = []
    for uid, title, text in docs:
        batch.append((uid, title, text))
        n += 1
        if len(batch) >= 5_000:
            db.executemany("INSERT INTO words(rowid, title, text) VALUES (?, ?, ?)", batch)
            batch = []
    if batch:
        db.executemany("INSERT INTO words(rowid, title, text) VALUES (?, ?, ?)", batch)
    db.commit()
    db.execute("INSERT INTO words(words) VALUES ('optimize')")
    db.commit()
    db.execute("VACUUM")
    built = round(time.monotonic() - t0)
    queries = {}
    for label, (q, _) in QUERIES.items():
        def run(q=q):
            hits = db.execute("SELECT count(*) FROM words WHERE words MATCH ?", (q,)).fetchone()[0]
            top = [r[0] for r in db.execute("SELECT rowid FROM words WHERE words MATCH ? ORDER BY rank LIMIT 20", (q,))]
            return hits, top
        (hits, top), cold, warm = _time(run)
        queries[label] = {"query": q, "hits": hits, "top": len(top), "first ms": cold, "median ms": warm}
    db.close()
    return {"engine": f"SQLite FTS5 {sqlite3.sqlite_version} (contentless, detail=full, unicode61 remove_diacritics 2)",
            "items": n, "bytes": _size(path), "build seconds": built, "queries": queries}


def tantivy_index(docs, path: str, threads: int = 2) -> dict:
    import tantivy
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path)
    t0 = time.monotonic()
    sb = tantivy.SchemaBuilder()
    sb.add_integer_field("id", stored=True, indexed=True, fast=True)
    sb.add_text_field("title", stored=False, tokenizer_name="default", index_option="position")
    sb.add_text_field("text", stored=False, tokenizer_name="default", index_option="position")
    ix = tantivy.Index(sb.build(), path=path)
    w = ix.writer(heap_size=512_000_000, num_threads=threads)
    n = 0
    for uid, title, text in docs:
        w.add_document(tantivy.Document(id=uid, title=title, text=text))
        n += 1
    w.commit()
    w.wait_merging_threads()
    built = round(time.monotonic() - t0)
    ix.reload()
    s = ix.searcher()
    queries = {}
    for label, (_, q) in QUERIES.items():
        if q is None:
            continue
        parsed = ix.parse_query(q, ["title", "text"])

        def run(parsed=parsed):
            return s.search(parsed, 20, count=True)
        res, cold, warm = _time(run)
        queries[label] = {"query": q, "hits": res.count, "top": len(res.hits), "first ms": cold, "median ms": warm}
    return {"engine": f"{getattr(tantivy, '__version__', 'tantivy')} (positions, text not stored, default tokenizer, "
                      f"{threads} threads)", "items": n, "bytes": _size(path), "build seconds": built, "queries": queries}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--engine", default="fts5")
    ap.add_argument("--lib", help="a folder holding the tantivy wheel's files, where it is not in the venv")
    a = ap.parse_args(argv)
    if a.lib:
        sys.path.append(a.lib)
    from support import db
    with db.connect(db.OWNER_KEY if a.database.endswith("_sample") else db.READ_KEY, a.database) as conn:
        sdir = conn.execute(f"SELECT store FROM {a.schema}.batches ORDER BY batch LIMIT 1").fetchone()[0]
        os.makedirs(os.path.join(sdir, "index"), exist_ok=True)
        for engine in a.engine.split(","):
            with conn.transaction():
                docs = documents(conn, a.schema, sdir)
                if engine == "fts5":
                    out = fts5(docs, os.path.join(sdir, "index", "fts5.sqlite"))
                elif engine == "tantivy":
                    out = tantivy_index(docs, os.path.join(sdir, "index", "tantivy"))
                else:
                    raise SystemExit(f"no engine {engine}")
            out["bytes per item"] = round(out["bytes"] / out["items"]) if out["items"] else 0
            print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
