"""The keyword index over whole documents (step 7.2's keyword-index row; step 8.6), built outside PostgreSQL over the store's
files on /mnt/hdd2 from a catalogue: the 1-million sample's, to size it, and then the whole archive's (qv4-papers-past-index).

Arthur, 2 November 2026: tantivy is the engine ("for papers past use tantivity and go"); FTS5 stays as the measured
alternative. tantivy (its Python wheel, pinned in requirements.txt; text not stored, so a hit is the item's upstream id,
read back through the catalogue; beside the words a fast `day`, `paper` and `chars` for order and filters, 5 November 2026) and SQLite FTS5 (Python's own sqlite3, contentless). The documents stream from the store's
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


def day_of(published_on):
    """The issue date as the index's `day`: yyyymmdd, an integer; None (no value written) for an undated item."""
    return published_on.year * 10_000 + published_on.month * 100 + published_on.day if published_on else None


def documents(conn, schema: str, sdir: str):
    """(upstream id, title, text, paper, day, chars) of every catalogued item, each frame decompressed once; `day` is
    day_of(published_on), the issue date publish.sql publishes."""
    with conn.cursor(name=f"pp_index_{time.monotonic_ns()}") as cur:
        cur.itersize = 20_000
        cur.execute(f"SELECT i.upstream_id, i.title, f.path, i.frame_at, i.frame_bytes, i.at, i.bytes, i.paper, "
                    f"i.published_on, i.chars FROM {schema}.items i "
                    f"JOIN {schema}.files f USING (file) ORDER BY f.path, i.frame_at")
        last, raw = None, b""
        for uid, title, path, frame_at, frame_bytes, at, n, paper, published_on, chars in cur:
            if (path, frame_at) != last:
                raw, last = store.frame(sdir, path, frame_at, frame_bytes), (path, frame_at)
            yield uid, title or "", raw[at:at + n].decode("utf-8"), paper, day_of(published_on), chars


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
    for uid, title, text, *_ in docs:
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


def memory_mb(pid: str = "self") -> dict:
    """The process's memory in MB, split as /proc/<pid>/smaps_rollup splits it: Pss (what the scheduler's worker
    reads), Pss_Anon (the heap: what the build holds) and Pss_File (pages of the index's own segment files that tantivy
    maps to read them while it merges: clean page cache, given back to the kernel on demand). Measured 3 November 2026
    on 8 passes of the 1M streamed catalogue: Pss_Anon stays at 1.1-2.5 GB with the 1.5 GB heap, while Pss_File rises
    with every merge to the size of the segments merged; on the whole archive that is what grew to 9.6 GB."""
    out = {}
    try:
        with open(f"/proc/{pid}/smaps_rollup", encoding="utf-8") as f:
            for line in f:
                k, _, v = line.partition(":")
                if k in ("Pss", "Pss_Anon", "Pss_File", "Pss_Shmem"):
                    out[k] = int(v.split()[0]) // 1024
    except OSError:
        pass
    return out


HEAP = 1_500_000_000        # tantivy's indexing memory, across its threads
THREADS = 2
COMMIT_EVERY = 5_000_000    # documents between commits: each commit closes segments and frees the heap


def tantivy_index(docs, path: str, threads: int = THREADS, heap: int = HEAP, commit_every: int = COMMIT_EVERY,
                  log=None) -> dict:
    """The tantivy index built from a stream of (upstream id, title, text), into `path` + '.new' and then moved into
    place whole (an index half built is never the one searched). Nothing of the stream is held: tantivy's heap is capped
    at `heap` bytes over at most `threads` threads.

    Beside the words, three fields for order and filters (Arthur, 5 November 2026: "sort by date"; a paper, a year range
    and a minimum length): `day` (yyyymmdd, fast and indexed), `paper` (the paper's code, exact: the raw tokenizer, fast)
    and `chars` (fast). An undated item gets no `day` at all: tantivy sorts a document with no value last in both orders
    (tests/test_papers_past_search.py), so the absence is the sentinel, and a year range never matches it. A stream of
    (upstream id, title, text) alone still builds, with no value in the three."""
    import tantivy
    work = path + ".new"
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    t0 = time.monotonic()
    sb = tantivy.SchemaBuilder()
    sb.add_integer_field("id", stored=True, indexed=True, fast=True)
    sb.add_text_field("title", stored=False, tokenizer_name="default", index_option="position")
    sb.add_text_field("text", stored=False, tokenizer_name="default", index_option="position")
    sb.add_integer_field("day", stored=False, indexed=True, fast=True)
    sb.add_text_field("paper", stored=False, fast=True, tokenizer_name="raw", index_option="basic")
    sb.add_integer_field("chars", stored=False, indexed=False, fast=True)
    ix = tantivy.Index(sb.build(), path=work)
    w = ix.writer(heap_size=heap, num_threads=threads)
    n = 0
    for uid, title, text, *more in docs:
        paper, day, chars = (list(more) + [None, None, None])[:3]
        doc = tantivy.Document(id=uid, title=title, text=text)
        if paper:
            doc.add_text("paper", paper)
        if day is not None:
            doc.add_integer("day", int(day))
        if chars is not None:
            doc.add_integer("chars", int(chars))
        w.add_document(doc)
        n += 1
        if n % commit_every == 0:
            w.commit()
            if log:
                m = memory_mb()
                log(f"papers_past index: {n} documents committed, {round(time.monotonic() - t0)} s, memory MB "
                    f"pss {m.get('Pss')} anon {m.get('Pss_Anon')} file {m.get('Pss_File')}")
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
