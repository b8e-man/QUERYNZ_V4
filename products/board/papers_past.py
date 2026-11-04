"""The Papers Past tab (Arthur, 5 November 2026: "let's add a search interface tab in the querynz board interface"): the
lane's keyword index searched through the lane's own read-only module (`registers.papers_past.search`), the board's one
reach into a lane (tests/test_imports_one_way.py and tests/test_papers_past_search_only.py name this file alone). A query
box, one page of hits by relevance (title, paper, issue date, a window of the text, the link to Papers Past and to the text
the store holds), the whole count and the seconds taken, and one article's text whole. Searched, never mined (hard limit
17): no name is found, no row is linked or joined, nothing is written.

    GET /papers-past?q=<words>&o=<offset>      the tab
    GET /papers-past/text?k=<article id>&q=    one article's text, the words asked marked"""
from __future__ import annotations

import urllib.parse

from products.board import panes
import registers.papers_past.search as pp

TAB = "papers past"
PATH = "/papers-past"
TEXT = "/papers-past/text"
PAGE = 20
NOTE = ("The Papers Past archive's keyword index: every word asked must be in the article's title or text (a word between "
        "words joined by OR is either; \"words in quotes\" are a phrase; -word leaves it out). Hits by relevance. The text is "
        "the copy the archive holds; the title opens the article on Papers Past. Searched, never mined: nothing here is "
        "linked to any other register.")


def href(q: str, offset: int = 0) -> str:
    return PATH + "?" + urllib.parse.urlencode([("q", q)] + ([("o", offset)] if offset else []))


def text_href(key: str, q: str = "") -> str:
    return TEXT + "?" + urllib.parse.urlencode([("k", key)] + ([("q", q)] if q else []))


def _marks(q: str) -> list:
    return [panes.fold_chars(w) for w in pp.words(q)]


def form(q: str) -> str:
    return (f'<form method="get" action="{PATH}"><input type="search" name="q" value="{panes.esc(q)}" '
            'placeholder="words, or &quot;a phrase&quot;" aria-label="search Papers Past" autofocus> <button>search</button></form>')


def search_pane(q: str, found: dict = None, failed: str = "") -> str:
    out = ['<section class="pane wide" id="papers-past">', '<div class="reg">papers past · keyword index</div>',
           "<h2>Search Papers Past</h2>", form(q), f'<p class="note">{panes.esc(NOTE)}</p>']
    if failed:
        out.append(f'<p class="warn">the search could not answer: {panes.esc(failed)}</p></section>')
        return "\n".join(out)
    if not q or found is None:
        out.append("</section>")
        return "\n".join(out)
    n, at, hits = found["count"], found["offset"], found["hits"]
    shown = f"{at + 1:,}–{at + len(hits):,} of " if hits else ""
    out.append(f'<p><strong>{shown}{n:,} articles</strong> <span class="meta">in {found["seconds"]:.2f} s '
               f'(the index {found.get("index seconds", 0):.2f} s)</span></p>')
    if found.get("error"):
        out.append(f'<p class="why">part of the query could not be read and was left out: {panes.esc(found["error"])}</p>')
    if not hits:
        out.append('<p class="why">none found</p>')
    words = _marks(q)
    for h in hits:
        if not h.get("key"):
            out.append(f'<article class="hit"><span class="why">index id {panes.esc(h.get("upstream_id"))}: '
                       f'{panes.esc(h["snippet"])}</span></article>')
            continue
        out.append('<article class="hit">'
                   f'{panes.new_tab(panes.mark(h["title"] or h["key"], words), h["url"], "row")}'
                   f'<div class="meta">{panes.esc(h["paper"])}, {panes.esc(h["published_on"] or "undated")}, '
                   f'{h["chars"]:,} characters · <a href="{panes.esc(text_href(h["key"], q))}">the text held</a> · '
                   f'<code>{panes.esc(h["key"])}</code></div>'
                   f'<div class="cite">{panes.mark(h["snippet"], words)}</div></article>')
    nav = []
    if at > 0:
        nav.append(f'<a href="{panes.esc(href(q, max(0, at - found["limit"])))}">previous {found["limit"]}</a>')
    if at + len(hits) < n and at + found["limit"] <= pp.OFFSET:
        nav.append(f'<a href="{panes.esc(href(q, at + found["limit"]))}">next {found["limit"]}</a>')
    if nav:
        out.append('<div class="actions">' + " ".join(nav) + "</div>")
    out.append("</section>")
    return "\n".join(out)


def text_pane(item: dict, q: str = "", failed: str = "") -> str:
    out = ['<section class="pane wide" id="papers-past-text">', '<div class="reg">papers past · the text held</div>']
    if failed or item is None:
        out.append(f'<p class="why">{panes.esc(failed or "no article by that id in the catalogue")}</p></section>')
        return "\n".join(out)
    out.append(f'<h2>{panes.esc(item["title"] or item["key"])}</h2>'
               f'<p class="meta">{panes.esc(item["paper"])}, {panes.esc(item["published_on"] or "undated")}, '
               f'{item["chars"]:,} characters · {panes.new_tab("on Papers Past", item["url"])}'
               + (f' · <a href="{panes.esc(href(q))}">back to the hits</a>' if q else "") +
               f' · <code>{panes.esc(item["key"])}</code></p>'
               f'<div class="text">{panes.mark(item["text"], _marks(q))}</div></section>')
    return "\n".join(out)


def offset_of(qs: dict) -> int:
    o = (qs.get("o") or ["0"])[0]
    return min(int(o), pp.OFFSET) if o.isdigit() else 0


def render(conn, q: str, offset: int = 0, db=None) -> str:
    """The tab on `conn`, a session-reader connection (the catalogue is the lane's own table, read only)."""
    found, failed = None, ""
    if q:
        try:
            found = pp.search(conn, q, limit=PAGE, offset=offset)
        except Exception as exc:  # noqa: BLE001 — the pane says what failed
            failed = f"{type(exc).__name__}: {exc}"
    return panes.page("", [], [search_pane(q, found, failed)], tab=TAB, db=db)


def render_text(conn, key: str, q: str = "", db=None) -> str:
    item, failed = None, ""
    try:
        item = pp.article(conn, key)
    except Exception as exc:  # noqa: BLE001
        failed = f"the text could not be read: {type(exc).__name__}: {exc}"
    return panes.page("", [], [text_pane(item, q, failed)], tab=TAB, db=db)
