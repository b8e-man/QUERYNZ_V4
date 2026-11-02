"""The keyword index over whole documents (step 7.2's keyword-index row; step 8.6), built outside PostgreSQL over the store's
files on /mnt/hdd2 from a catalogue: the 1-million sample's, to size it, and then the whole archive's (qv4-papers-past-index).

Arthur, 2 November 2026: tantivy is the engine ("for papers past use tantivity and go"); FTS5 stays as the measured
alternative. tantivy (its Python wheel, pinned in requirements.txt; text not stored, so a hit is the item's upstream id,
read back through the catalogue) and SQLite FTS5 (Python's own sqlite3, contentless). The documents stream from the store's
files in file and frame order, each frame decompressed once, nothing held; built at low priority into the store's folder:

    /mnt/hdd2/qv4-papers-past/<store>/index/fts5.sqlite
    /mnt/hdd2/qv4-papers-past/<store>/index/tantivy/

and measured: bytes on disk per item, the build's seconds, and each query's time (first run and the median of the next
five) with its count of hits and its top twenty by rank. The index is searched only: it is never a name index and nothing
reads it into links/ (hard limit 17).

    python -m registers.papers_past.index --schema scratch_… --database querynz_v4_sample [--engine tantivy|fts5] [--heap-mb 1500] [--threads 2]
"""
import argparse
import json
import os
import shutil
import sqlite3
import statistics
import subprocess
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


HEAP = 1_500_000_000        # tantivy's indexing memory, across its threads
THREADS = 2
COMMIT_EVERY = 5_000_000    # documents between commits: each commit closes segments and frees the heap


def tantivy_index(docs, path: str, threads: int = THREADS, heap: int = HEAP, commit_every: int = COMMIT_EVERY,
                  log=None) -> dict:
    """The tantivy index built from a stream of (upstream id, title, text), into `path` + '.new' and then moved into
    place whole (an index half built is never the one searched). Nothing of the stream is held: tantivy's heap is capped
    at `heap` bytes over at most `threads` threads."""
    import tantivy
    work = path + ".new"
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    t0 = time.monotonic()
    sb = tantivy.SchemaBuilder()
    sb.add_integer_field("id", stored=True, indexed=True, fast=True)
    sb.add_text_field("title", stored=False, tokenizer_name="default", index_option="position")
    sb.add_text_field("text", stored=False, tokenizer_name="default", index_option="position")
    ix = tantivy.Index(sb.build(), path=work)
    w = ix.writer(heap_size=heap, num_threads=threads)
    n = 0
    for uid, title, text in docs:
        w.add_document(tantivy.Document(id=uid, title=title, text=text))
        n += 1
        if n % commit_every == 0:
            w.commit()
            if log:
                log(f"papers_past index: {n} documents committed, {round(time.monotonic() - t0)} s")
    w.commit()
    w.wait_merging_threads()
    built = round(time.monotonic() - t0)
    del w
    old = path + ".old"
    shutil.rmtree(old, ignore_errors=True)
    if os.path.exists(path):
        os.rename(path, old)
    os.rename(work, path)
    shutil.rmtree(old, ignore_errors=True)
    ix = tantivy.Index.open(path)
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
                      f"{threads} threads, heap {heap // 1_000_000} MB)", "items": n, "docs in index": s.num_docs,
            "bytes": _size(path), "build seconds": built, "queries": queries}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--engine", default="tantivy")
    ap.add_argument("--heap-mb", type=int, default=HEAP // 1_000_000)
    ap.add_argument("--threads", type=int, default=THREADS)
    a = ap.parse_args(argv)
    if a.threads > 2:
        raise SystemExit("at most 2 threads")
    subprocess.run(["ionice", "-c3", "-p", str(os.getpid())], check=False)
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        sdir = conn.execute(f"SELECT store FROM {a.schema}.batches ORDER BY batch LIMIT 1").fetchone()[0]
        n_items = conn.execute(f"SELECT count(*) FROM {a.schema}.items").fetchone()[0]
        os.makedirs(os.path.join(sdir, "index"), exist_ok=True)
        for engine in a.engine.split(","):
            with conn.transaction():
                docs = documents(conn, a.schema, sdir)
                if engine == "fts5":
                    out = fts5(docs, os.path.join(sdir, "index", "fts5.sqlite"))
                elif engine == "tantivy":
                    out = tantivy_index(docs, os.path.join(sdir, "index", "tantivy"), threads=a.threads,
                                        heap=a.heap_mb * 1_000_000, log=print)
                else:
                    raise SystemExit(f"no engine {engine}")
            out["bytes per item"] = round(out["bytes"] / out["items"]) if out["items"] else 0
            print(json.dumps(out, ensure_ascii=False))
            if out["items"] != n_items or out.get("docs in index", n_items) != n_items:
                print(f"FAILS the index holds {out.get('docs in index', out['items'])} documents, the catalogue {n_items}")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
