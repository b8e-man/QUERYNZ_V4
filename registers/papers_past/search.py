"""The keyword index searched, read only (step 8.6; Arthur, 5 November 2026: a search tab on the board). A query goes to the
tantivy index beside the store (`index.py`), each hit's upstream id is read back through the catalogue (`papers_past.items`),
and a short window of the text around the first word asked comes from the store's files (`store.text`, its sha256 checked).
Searched, never mined (hard limit 17): nothing here finds a name, builds a person, a claim or a link, or writes anything.

    search(conn, query, limit=20, offset=0, sort="relevance", paper="", year_from=None, year_to=None, min_chars=None)
        -> {"count", "hits": [{key, paper, published_on, title, url, chars, snippet}], "seconds", "error", "sort",
            "unavailable", "papers"}
    article(conn, key) -> {key, paper, published_on, title, url, chars, text} or None

Words are joined by AND unless the query says OR; "a phrase" in quotes; a word ending in * is a prefix only where tantivy's
parser takes it. One index is opened per process and kept (its files are mapped, clean pages the kernel takes back).

Order (Arthur, 5 November 2026: "sort by date"): relevance, oldest or newest, on the index's `day` field; an undated item
comes last either way. Filters: one paper by its code, exactly; a year from and to; a minimum length in characters. An
index built before those fields (the one built 3 November 2026) has none of them: the search then runs by relevance with
no filter, and `unavailable` says what waits for the rebuild (qv4-papers-past-index), so nothing is silently dropped.
`papers`: the hits counted by paper, the ten largest, where the index has the field and the hits are at most PAPERS_UPTO."""
from __future__ import annotations

import os
import re
import time

from registers.papers_past import store
from support import textindex
#: the reader is support/textindex/read.py since 10 November 2026 (moved from here, behaviour unchanged)
from support.textindex.read import LIMIT, OFFSET, PAPERS_UPTO, SKIP, SNIPPET, SORTS, fields_of, opened, snippet, words  # noqa: F401

FIELDS = ["title", "text"]


def index_path(store_dir: str) -> str:
    return os.path.join(store_dir, "index", "tantivy")


def store_dir(conn) -> str:
    """The folder the catalogue's text (and the index beside it) is in: the first batch's (one store per catalogue)."""
    row = conn.execute("SELECT store FROM papers_past.batches ORDER BY batch LIMIT 1").fetchone()
    if row is None:
        raise LookupError("the catalogue has no batch")
    return row[0]


def _year(y):
    try:
        y = int(y)
    except (TypeError, ValueError):
        return None
    return y if 1000 <= y <= 2999 else None


def _rows(conn, ids: list) -> dict:
    cur = conn.execute("SELECT i.upstream_id, i.key, i.paper, i.published_on, i.title, i.chars, "
                       "coalesce(i.url, 'https://paperspast.natlib.govt.nz/newspapers/' || i.key) AS url, "
                       "f.path, i.frame_at, i.frame_bytes, i.at, i.bytes, i.sha256 "
                       "FROM papers_past.items i JOIN papers_past.files f USING (file) WHERE i.upstream_id = ANY(%s)", (ids,))
    names = [d[0] for d in cur.description]
    return {r[0]: dict(zip(names, r)) for r in cur}


def _text(sdir: str, r: dict) -> str:
    return store.text(sdir, r["path"], r["frame_at"], r["frame_bytes"], r["at"], r["bytes"], r["sha256"])


def search(conn, query: str, limit: int = 20, offset: int = 0, sdir: str = None, sort: str = "relevance",
           paper: str = "", year_from=None, year_to=None, min_chars=None) -> dict:
    """One page of hits in `sort` order, the whole count, and the seconds the index and the reading took. A query the
    parser cannot read whole is read as far as it can, and `error` says what it dropped; an order or filter the index
    cannot serve is listed in `unavailable` and not applied."""
    query = (query or "").strip()[:500]
    limit, offset = max(1, min(int(limit), LIMIT)), max(0, min(int(offset), OFFSET))
    sort = sort if sort in SORTS else "relevance"
    paper = re.sub(r"[^A-Za-z0-9]", "", paper or "")[:20]
    year_from, year_to = _year(year_from), _year(year_to)
    try:
        min_chars = max(0, int(min_chars)) if min_chars not in (None, "") else None
    except ValueError:
        min_chars = None
    out = {"query": query, "count": 0, "hits": [], "seconds": 0.0, "error": "", "limit": limit, "offset": offset,
           "sort": sort, "unavailable": [], "papers": None}
    if not query:
        return out
    t0 = time.perf_counter()
    sdir = sdir or store_dir(conn)
    path = index_path(sdir)
    have = textindex.read.have(path)
    terms, ranges = [], []
    if paper:
        if "paper" in have:
            terms.append(("paper", paper))
        else:
            out["unavailable"].append("the paper filter")
    if year_from or year_to:
        if "day" in have:
            lo = year_from * 10_000 + 101 if year_from else None
            hi = year_to * 10_000 + 1231 if year_to else None
            ranges.append(("day", lo, hi))
        else:
            out["unavailable"].append("the year range")
    if min_chars:
        if "chars" in have:
            ranges.append(("chars", min_chars, None))
        else:
            out["unavailable"].append("the minimum length")
    order_by = None
    if sort != "relevance":
        if "day" in have:
            order_by = "day"
        else:
            out["unavailable"].append(f"{sort} first")
            out["sort"] = "relevance"
    found = textindex.read.search(path, query, FIELDS, limit, offset, key="id", terms=terms, ranges=ranges,
                                  order_by=order_by, descending=sort == "newest",
                                  facet="paper" if "paper" in have else None, facet_upto=PAPERS_UPTO)
    ids, errors = found["keys"], found["errors"]
    out["papers"] = found["facets"]
    out["count"] = found["count"]
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
