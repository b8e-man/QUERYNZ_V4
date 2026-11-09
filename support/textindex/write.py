"""The index writer (moved from registers/papers_past/index.py's tantivy_index, 10 November 2026; behaviour unchanged).

A `Spec` names the index's fields: the key (stored: a hit is a key, read back through its owner's catalogue), the text
fields (indexed with positions, never stored), and the fast fields in declaration order: integers (indexed when asked, for a
range) and exact fields (the raw tokenizer: a paper's code, a publisher). `fold` folds macrons in the text before tantivy's default tokenizer reads
it (read.fold), so "Maori" finds "Māori" and the other way; a query on such an index is folded the same way.

`build` writes into `path` + '.new' and then moves it into place whole: an index half built is never the one searched.
Nothing of the stream is held; tantivy's heap is capped at `heap` bytes over at most `threads` threads."""
from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass

from support.textindex.read import fold as _fold

HEAP = 1_500_000_000        # tantivy's indexing memory, across its threads
THREADS = 2
COMMIT_EVERY = 5_000_000    # documents between commits: each commit closes segments and frees the heap


@dataclass(frozen=True)
class Spec:
    key: str = "id"
    key_kind: str = "int"               # "int" or "text"
    texts: tuple = ("title", "text")    # indexed with positions, not stored
    extra: tuple = ()                   # ((name, "int" | "exact", indexed), ...) in declaration order: fast fields
    fold: bool = False                  # macrons folded before the tokenizer


#: the news index (docs/research/step-9-news-search.md, "Lane side"): `ref` stored, headline and text folded, publisher and
#: day fast. The lane `news` builds it; the report searches it (products/report/news.py).
NEWS = Spec(key="ref", key_kind="text", texts=("headline", "text"), extra=(("day", "int", True), ("publisher", "exact", False)),
            fold=True)


def schema(spec: Spec):
    import tantivy
    sb = tantivy.SchemaBuilder()
    if spec.key_kind == "int":
        sb.add_integer_field(spec.key, stored=True, indexed=True, fast=True)
    else:
        sb.add_text_field(spec.key, stored=True, tokenizer_name="raw", index_option="basic")
    for t in spec.texts:
        sb.add_text_field(t, stored=False, tokenizer_name="default", index_option="position")
    for name, kind, indexed in spec.extra:
        if kind == "int":
            sb.add_integer_field(name, stored=False, indexed=indexed, fast=True)
        else:
            sb.add_text_field(name, stored=False, fast=True, tokenizer_name="raw", index_option="basic")
    return sb.build()


def document(spec: Spec, values: dict):
    """One tantivy document from {field: value}; a field whose value is None or empty gets no value at all (an undated
    item has no `day`, so it sorts last either way and a range never matches it)."""
    import tantivy
    doc = tantivy.Document()
    k = values.get(spec.key)
    if spec.key_kind == "int":
        doc.add_integer(spec.key, int(k))
    else:
        doc.add_text(spec.key, str(k))
    for t in spec.texts:
        v = values.get(t) or ""
        doc.add_text(t, _fold(v) if spec.fold else v)
    for name, kind, _ in spec.extra:
        v = values.get(name)
        if kind == "int":
            if v is not None:
                doc.add_integer(name, int(v))
        elif v:
            doc.add_text(name, str(v))
    return doc


def build(docs, path: str, spec: Spec, threads: int = THREADS, heap: int = HEAP, commit_every: int = COMMIT_EVERY,
          progress=None) -> dict:
    """The index at `path`, built from a stream of {field: value}, moved into place whole. `progress(n, seconds)` is called
    after each intermediate commit. Returns {"items", "build seconds"}."""
    import tantivy
    work = path + ".new"
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    t0 = time.monotonic()
    ix = tantivy.Index(schema(spec), path=work)
    w = ix.writer(heap_size=heap, num_threads=threads)
    n = 0
    for values in docs:
        w.add_document(document(spec, values))
        n += 1
        if n % commit_every == 0:
            w.commit()
            if progress:
                progress(n, round(time.monotonic() - t0))
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
    return {"items": n, "build seconds": built}
