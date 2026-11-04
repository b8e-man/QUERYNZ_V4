"""The keyword index searched, read only (step 8.6; Arthur, 5 November 2026: a search tab on the board). A query goes to the
tantivy index beside the store (`index.py`), each hit's upstream id is read back through the catalogue (`papers_past.items`),
and a short window of the text around the first word asked comes from the store's files (`store.text`, its sha256 checked).
Searched, never mined (hard limit 17): nothing here finds a name, builds a person, a claim or a link, or writes anything.

    search(conn, query, limit=20, offset=0) -> {"count", "hits": [{key, paper, published_on, title, url, chars, snippet}],
                                               "seconds", "error"}
    article(conn, key) -> {key, paper, published_on, title, url, chars, text} or None

Words are joined by AND unless the query says OR; "a phrase" in quotes; a word ending in * is a prefix only where tantivy's
parser takes it. One index is opened per process and kept (its files are mapped, clean pages the kernel takes back)."""
from __future__ import annotations

import os
import re
import threading
import time

from registers.papers_past import store

FIELDS = ["title", "text"]
LIMIT = 100                 # hits on one page, at most
OFFSET = 10_000             # how deep a page may start
SNIPPET = 320               # characters of text around the first word asked
_LOCK = threading.Lock()    # one open at a time, and one search at a time: the index is on a spinning disk
_OPEN = {}                  # index path -> tantivy.Index
SKIP = {"and", "or", "not"}


def index_path(store_dir: str) -> str:
    return os.path.join(store_dir, "index", "tantivy")


def store_dir(conn) -> str:
    """The folder the catalogue's text (and the index beside it) is in: the first batch's (one store per catalogue)."""
    row = conn.execute("SELECT store FROM papers_past.batches ORDER BY batch LIMIT 1").fetchone()
    if row is None:
        raise LookupError("the catalogue has no batch")
    return row[0]


def opened(path: str):
    """The index at `path`, opened once per process."""
    import tantivy
    ix = _OPEN.get(path)
    if ix is None:
        if not os.path.isdir(path):
            raise FileNotFoundError(f"no keyword index at {path}")
        ix = _OPEN[path] = tantivy.Index.open(path)
    return ix


def words(query: str) -> list:
    """The plain words of a query, lower case, for the snippet's window and its marks (no operator, no field name)."""
    out = []
    for w in re.findall(r"[^\W_]+", re.sub(r"\b\w+:", " ", query or "")):
        w = w.lower()
        if w not in SKIP and w not in out:
            out.append(w)
    return out


def snippet(text: str, ws: list, n: int = SNIPPET) -> str:
    """About `n` characters of `text` around the first place a word asked begins a word; the text's start if none does."""
    text = text or ""
    at = None
    for w in ws:
        m = re.search(r"(?<!\w)" + re.escape(w), text, re.I)
        if m and (at is None or m.start() < at):
            at = m.start()
    start = 0 if at is None else max(0, at - n // 3)
    piece = re.sub(r"\s+", " ", text[start:start + n]).strip()
    return ("… " if start else "") + piece + (" …" if start + n < len(text) else "")


def _rows(conn, ids: list) -> dict:
    cur = conn.execute("SELECT i.upstream_id, i.key, i.paper, i.published_on, i.title, i.chars, "
                       "coalesce(i.url, 'https://paperspast.natlib.govt.nz/newspapers/' || i.key) AS url, "
                       "f.path, i.frame_at, i.frame_bytes, i.at, i.bytes, i.sha256 "
                       "FROM papers_past.items i JOIN papers_past.files f USING (file) WHERE i.upstream_id = ANY(%s)", (ids,))
    names = [d[0] for d in cur.description]
    return {r[0]: dict(zip(names, r)) for r in cur}


def _text(sdir: str, r: dict) -> str:
    return store.text(sdir, r["path"], r["frame_at"], r["frame_bytes"], r["at"], r["bytes"], r["sha256"])


def search(conn, query: str, limit: int = 20, offset: int = 0, sdir: str = None) -> dict:
    """One page of hits by relevance, the whole count, and the seconds the index and the reading took. A query the parser
    cannot read whole is read as far as it can, and `error` says what it dropped."""
    query = (query or "").strip()[:500]
    limit, offset = max(1, min(int(limit), LIMIT)), max(0, min(int(offset), OFFSET))
    out = {"query": query, "count": 0, "hits": [], "seconds": 0.0, "error": "", "limit": limit, "offset": offset}
    if not query:
        return out
    t0 = time.perf_counter()
    sdir = sdir or store_dir(conn)
    with _LOCK:
        ix = opened(index_path(sdir))
        parsed, errors = ix.parse_query_lenient(query, FIELDS, conjunction_by_default=True)
        s = ix.searcher()
        found = s.search(parsed, limit, count=True, offset=offset)
        ids = [s.doc(addr)["id"][0] for _, addr in found.hits]
    out["count"] = found.count or 0
    out["error"] = "; ".join(str(e) for e in errors)[:300]
    out["index seconds"] = round(time.perf_counter() - t0, 3)
    rows = _rows(conn, ids) if ids else {}
    ws = words(query)
    for i in ids:
        r = rows.get(i)
        if r is None:                       # the index holds an id the catalogue does not: said, never hidden
            out["hits"].append({"key": None, "upstream_id": i, "title": None, "snippet": "not in the catalogue"})
            continue
        try:
            snip = snippet(_text(sdir, r), ws)
        except (OSError, RuntimeError) as exc:
            snip = f"the text could not be read: {type(exc).__name__}"
        out["hits"].append({k: r[k] for k in ("key", "paper", "published_on", "title", "url", "chars")} | {"snippet": snip})
    out["seconds"] = round(time.perf_counter() - t0, 3)
    return out


def article(conn, key: str, sdir: str = None) -> dict | None:
    """One article's catalogue row and its whole text, read from the store's files with its sha256 checked; None if the
    catalogue has no such key."""
    cur = conn.execute("SELECT i.key, i.paper, i.published_on, i.title, i.chars, "
                       "coalesce(i.url, 'https://paperspast.natlib.govt.nz/newspapers/' || i.key) AS url, "
                       "f.path, i.frame_at, i.frame_bytes, i.at, i.bytes, i.sha256 "
                       "FROM papers_past.items i JOIN papers_past.files f USING (file) WHERE i.key = %s", ((key or "")[:100],))
    names = [d[0] for d in cur.description]
    row = cur.fetchone()
    if row is None:
        return None
    r = dict(zip(names, row))
    text = _text(sdir or store_dir(conn), r)
    return {k: r[k] for k in ("key", "paper", "published_on", "title", "url", "chars")} | {"text": text}
