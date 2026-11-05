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
SORTS = ("relevance", "oldest", "newest")
PAPERS_UPTO = 2_000_000     # hits counted by paper only up to this many (an aggregation over all of them)
_FIELDS = {}                # index path -> the order and filter fields it has


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


def fields_of(ix, path: str) -> set:
    """Which of day, paper, chars the index at `path` was built with (asked of its schema once)."""
    if path not in _FIELDS:
        import tantivy
        have = set()
        for f in ("day", "chars"):
            try:
                tantivy.Query.range_query(ix.schema, f, tantivy.FieldType.Integer, 1, None)
                have.add(f)
            except ValueError:
                pass
        try:
            tantivy.Query.term_query(ix.schema, "paper", "x")
            have.add("paper")
        except ValueError:
            pass
        _FIELDS[path] = have
    return _FIELDS[path]


def _year(y):
    try:
        y = int(y)
    except (TypeError, ValueError):
        return None
    return y if 1000 <= y <= 2999 else None


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


def search(conn, query: str, limit: int = 20, offset: int = 0, sdir: str = None, sort: str = "relevance",
           paper: str = "", year_from=None, year_to=None, min_chars=None) -> dict:
    """One page of hits in `sort` order, the whole count, and the seconds the index and the reading took. A query the
    parser cannot read whole is read as far as it can, and `error` says what it dropped; an order or filter the index
    cannot serve is listed in `unavailable` and not applied."""
    import tantivy
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
    with _LOCK:
        path = index_path(sdir)
        ix = opened(path)
        have = fields_of(ix, path)
        parsed, errors = ix.parse_query_lenient(query, FIELDS, conjunction_by_default=True)
        must, schema = [], ix.schema
        if paper:
            if "paper" in have:
                must.append(tantivy.Query.term_query(schema, "paper", paper))
            else:
                out["unavailable"].append("the paper filter")
        if year_from or year_to:
            if "day" in have:
                lo = year_from * 10_000 + 101 if year_from else None
                hi = year_to * 10_000 + 1231 if year_to else None
                must.append(tantivy.Query.range_query(schema, "day", tantivy.FieldType.Integer, lo, hi))
            else:
                out["unavailable"].append("the year range")
        if min_chars:
            if "chars" in have:
                must.append(tantivy.Query.range_query(schema, "chars", tantivy.FieldType.Integer, min_chars, None))
            else:
                out["unavailable"].append("the minimum length")
        if must:
            parsed = tantivy.Query.boolean_query([(tantivy.Occur.Must, parsed)] + [(tantivy.Occur.Must, m) for m in must])
        order = {}
        if sort != "relevance":
            if "day" in have:
                order = {"order_by_field": "day", "order": tantivy.Order.Asc if sort == "oldest" else tantivy.Order.Desc}
            else:
                out["unavailable"].append(f"{sort} first")
                out["sort"] = "relevance"
        s = ix.searcher()
        found = s.search(parsed, limit, count=True, offset=offset, **order)
        ids = [s.doc(addr)["id"][0] for _, addr in found.hits]
        if "paper" in have and found.count and found.count <= PAPERS_UPTO:
            agg = s.aggregate(parsed, {"papers": {"terms": {"field": "paper", "size": 10}}})
            out["papers"] = [(b["key"], b["doc_count"]) for b in agg["papers"]["buckets"]]
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
