"""The index reader (moved from registers/papers_past/search.py, 10 November 2026; behaviour unchanged): read only.

One index is opened per process and kept (its files are mapped, clean pages the kernel takes back), and one search runs at a
time under one lock: the Papers Past index is on a spinning disk. A query the parser cannot read whole is read as far as it
can and the errors are returned; a hit is the key the index stores, for the owner to read back.

    search(path, query, fields, limit, offset, key="id", terms=(), ranges=(), order_by=None, descending=False,
           facet=None, facet_upto=PAPERS_UPTO, folded=False) -> {"count", "keys", "errors", "facets"}
    phrase(path, words, fields, limit, key="ref") -> {"count", "keys"}
    have(path, ints=("day", "chars"), exact=("paper",)) -> the fields of those the index was built with
    words(query), snippet(text, words, n=SNIPPET), fold(text)"""
from __future__ import annotations

import os
import re
import threading
import unicodedata

LIMIT = 100                 # hits on one page, at most
OFFSET = 10_000             # how deep a page may start
SNIPPET = 320               # characters of text around the first word asked
SKIP = {"and", "or", "not"}
SORTS = ("relevance", "oldest", "newest")
PAPERS_UPTO = 2_000_000     # hits counted by a facet only up to this many (an aggregation over all of them)
_LOCK = threading.Lock()    # one open at a time, and one search at a time
_OPEN = {}                  # index path -> tantivy.Index
_FIELDS = {}                # (index path, fields asked) -> the fields it has


def fold(text: str) -> str:
    """Lower case, macrons and other marks folded, every character not a letter or digit a space; the same length as the
    text, so an offset in the folded text is the offset in the text (the evidence is re-read at it)."""
    out = []
    for ch in text or "":
        if ch.isalnum():
            base = unicodedata.normalize("NFKD", ch)[0]
            low = base.lower()
            out.append(low if len(low) == 1 else base)
        else:
            out.append(" ")
    return "".join(out)


def opened(path: str):
    """The index at `path`, opened once per process."""
    import tantivy
    ix = _OPEN.get(path)
    if ix is None:
        if not os.path.isdir(path):
            raise FileNotFoundError(f"no keyword index at {path}")
        ix = _OPEN[path] = tantivy.Index.open(path)
    return ix


def forget(path: str) -> None:
    """Drop the process's open index at `path` (a rebuilt index is opened afresh)."""
    with _LOCK:
        _OPEN.pop(path, None)
        for k in [k for k in _FIELDS if k[0] == path]:
            _FIELDS.pop(k, None)


def fields_of(ix, path: str, ints=("day", "chars"), exact=("paper",)) -> set:
    """Which of the integer and exact fields the index at `path` was built with (asked of its schema once)."""
    k = (path, tuple(ints), tuple(exact))
    if k not in _FIELDS:
        import tantivy
        got = set()
        for f in ints:
            try:
                tantivy.Query.range_query(ix.schema, f, tantivy.FieldType.Integer, 1, None)
                got.add(f)
            except ValueError:
                pass
        for f in exact:
            try:
                tantivy.Query.term_query(ix.schema, f, "x")
                got.add(f)
            except ValueError:
                pass
        _FIELDS[k] = got
    return _FIELDS[k]


def have(path: str, ints=("day", "chars"), exact=("paper",)) -> set:
    with _LOCK:
        return fields_of(opened(path), path, ints, exact)


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


def search(path: str, query: str, fields: list, limit: int = 20, offset: int = 0, key: str = "id", terms=(), ranges=(),
           order_by: str = None, descending: bool = False, facet: str = None, facet_upto: int = PAPERS_UPTO,
           folded: bool = False) -> dict:
    """One page of keys in order, the whole count, the parser's errors, and the hits counted by `facet` (its ten largest)
    where the hits are at most `facet_upto`. Words are joined by AND unless the query says OR. `terms` are (field, value)
    an exact field must equal; `ranges` (field, low, high) an integer field must fall in (None: open). A caller asks
    `have` first and passes only the fields the index has. `folded`: the index folds its text, so the query is folded too
    (its operators and quotes kept)."""
    import tantivy
    if folded:
        query = _fold_query(query)
    with _LOCK:
        ix = opened(path)
        parsed, errors = ix.parse_query_lenient(query, list(fields), conjunction_by_default=True)
        schema = ix.schema
        must = [tantivy.Query.term_query(schema, f, v) for f, v in terms]
        must += [tantivy.Query.range_query(schema, f, tantivy.FieldType.Integer, lo, hi) for f, lo, hi in ranges]
        if must:
            parsed = tantivy.Query.boolean_query([(tantivy.Occur.Must, parsed)] + [(tantivy.Occur.Must, m) for m in must])
        order = {}
        if order_by:
            order = {"order_by_field": order_by, "order": tantivy.Order.Desc if descending else tantivy.Order.Asc}
        s = ix.searcher()
        found = s.search(parsed, limit, count=True, offset=offset, **order)
        keys = [s.doc(addr)[key][0] for _, addr in found.hits]
        facets = None
        if facet and found.count and found.count <= facet_upto:
            agg = s.aggregate(parsed, {"f": {"terms": {"field": facet, "size": 10}}})
            facets = [(b["key"], b["doc_count"]) for b in agg["f"]["buckets"]]
    return {"count": found.count or 0, "keys": keys, "errors": errors, "facets": facets}


def _fold_query(query: str) -> str:
    """A query's words folded, its quotes, signs, brackets and field names kept."""
    return re.sub(r"[^\W_]+", lambda m: m.group(0) if m.group(0) in ("AND", "OR", "NOT") else fold(m.group(0)), query or "")


def phrase(path: str, ws: list, fields: list, limit: int = 500, key: str = "ref") -> dict:
    """The documents where the folded words `ws` stand together in order in any of `fields`: the whole count and the top
    `limit` keys by relevance. One word is a term."""
    import tantivy
    ws = [w for w in fold(" ".join(ws)).split() if w]
    if not ws:
        return {"count": 0, "keys": []}
    with _LOCK:
        ix = opened(path)
        schema = ix.schema
        qs = [tantivy.Query.term_query(schema, f, ws[0]) if len(ws) == 1 else tantivy.Query.phrase_query(schema, f, ws)
              for f in fields]
        q = qs[0] if len(qs) == 1 else tantivy.Query.boolean_query([(tantivy.Occur.Should, x) for x in qs])
        s = ix.searcher()
        found = s.search(q, limit, count=True)
        keys = [s.doc(addr)[key][0] for _, addr in found.hits]
    return {"count": found.count or 0, "keys": keys}
