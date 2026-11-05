"""The Papers Past tab (Arthur, 5 November 2026: "let's add a search interface tab in the querynz board interface"): the
lane's keyword index searched through the lane's own read-only module (`registers.papers_past.search`), the board's one
reach into a lane (tests/test_imports_one_way.py and tests/test_papers_past_search_only.py name this file alone). A query
box, one page of hits (title, paper, issue date, a window of the text, the link to Papers Past and to the text the store
holds), the whole count and the seconds taken, and one article's text whole. Order: relevance, oldest or newest (`s=`;
Arthur, 5 November 2026: "sort by date"); filters: one paper by its code (`paper=`), a year from and to (`yf=`, `yt=`), a
minimum length (`min=`); all kept across paging. An index built before those fields serves relevance alone and the page
says what waits for the rebuild. Searched, never mined (hard limit 17): no name is found, no row is linked or joined,
nothing is written.

    GET /papers-past?q=<words>&o=<offset>&s=&paper=&yf=&yt=&min=      the tab
    GET /papers-past/text?k=<article id>&q=    one article's text, the words asked marked"""
from __future__ import annotations

import urllib.parse

from products.board import panes
import registers.papers_past.search as pp

TAB = "papers past"
PATH = "/papers-past"
TEXT = "/papers-past/text"
PAGE = 20
#: the form's choices besides the words, as the address carries them
ASKED = ("s", "paper", "yf", "yt", "min")
SORT_LABEL = {"relevance": "relevance", "oldest": "oldest first", "newest": "newest first"}
REBUILD = "after the index rebuild"
NOTE = ("The Papers Past archive's keyword index: every word asked must be in the article's title or text (a word between "
        "words joined by OR is either; \"words in quotes\" are a phrase; -word leaves it out). Hits by relevance, or by issue date oldest or newest first (an undated article last); a paper by its code, a year range and a least length narrow them. The text is "
        "the copy the archive holds; the title opens the article on Papers Past. Searched, never mined: nothing here is "
        "linked to any other register.")


def asked_of(qs: dict) -> dict:
    """The form's choices from the address, cut to size; a blank or the default is left out."""
    out = {}
    for k in ASKED:
        x = (qs.get(k) or [""])[0].strip()[:20]
        if k == "s" and x not in pp.SORTS:
            x = ""
        if k in ("yf", "yt", "min") and not x.isdigit():
            x = ""
        if k == "paper":
            x = "".join(c for c in x if c.isalnum())
        if x and not (k == "s" and x == "relevance"):
            out[k] = x
    return out


def _params(asked: dict) -> list:
    return [(k, asked[k]) for k in ASKED if (asked or {}).get(k)]


def href(q: str, offset: int = 0, asked: dict = None) -> str:
    return PATH + "?" + urllib.parse.urlencode([("q", q)] + _params(asked) + ([("o", offset)] if offset else []))


def text_href(key: str, q: str = "", asked: dict = None) -> str:
    return TEXT + "?" + urllib.parse.urlencode([("k", key)] + ([("q", q)] if q else []) + _params(asked))


def _marks(q: str) -> list:
    return [panes.fold_chars(w) for w in pp.words(q)]


def form(q: str, asked: dict = None) -> str:
    a = asked or {}
    sort = "".join(f'<option value="{k}"{" selected" if a.get("s", "relevance") == k else ""}>{panes.esc(v)}</option>'
                   for k, v in SORT_LABEL.items())
    box = lambda k, label, size, hint: (f'<label>{label} <input name="{k}" value="{panes.esc(a.get(k, ""))}" size="{size}" '
                                        f'placeholder="{hint}" aria-label="{label}"></label>')
    return (f'<form method="get" action="{PATH}"><input type="search" name="q" value="{panes.esc(q)}" '
            'placeholder="words, or &quot;a phrase&quot;" aria-label="search Papers Past" autofocus> '
            f'<label>order <select name="s" aria-label="order">{sort}</select></label> <button>search</button>'
            '<div class="actions">' + box("paper", "paper", 6, "code: EP") + box("yf", "from year", 5, "1860")
            + box("yt", "to year", 5, "1900") + box("min", "at least", 6, "chars") + "</div></form>")


def papers_line(q: str, found: dict, asked: dict) -> str:
    """The hits counted by paper, the ten largest, each a link that filters to it."""
    ps = found.get("papers")
    if not ps:
        return ""
    links = ", ".join(f'<a href="{panes.esc(href(q, 0, dict(asked or {}, paper=p)))}">{panes.esc(p)}</a> {n:,}'
                      for p, n in ps)
    return f'<p class="meta">by paper: {links}</p>'


def search_pane(q: str, found: dict = None, failed: str = "", asked: dict = None) -> str:
    asked = asked or {}
    out = ['<section class="pane wide" id="papers-past">', '<div class="reg">papers past · keyword index</div>',
           "<h2>Search Papers Past</h2>", form(q, asked), f'<p class="note">{panes.esc(NOTE)}</p>']
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
    if found.get("unavailable"):
        miss = found["unavailable"]
        said = ([f"date order {REBUILD}"] if any(m.endswith(" first") for m in miss) else [])
        filters = [m for m in miss if not m.endswith(" first")]
        said += [f"{', '.join(filters)} {REBUILD}"] if filters else []
        out.append(f'<p class="warn">{panes.esc("; ".join(said))}: the index in use was built before its date, paper and '
                   'length fields, so these hits are by relevance and those choices are not applied</p>')
    out.append(papers_line(q, found, asked))
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
                   f'{h["chars"]:,} characters · <a href="{panes.esc(text_href(h["key"], q, asked))}">the text held</a> · '
                   f'<code>{panes.esc(h["key"])}</code></div>'
                   f'<div class="cite">{panes.mark(h["snippet"], words)}</div></article>')
    nav = []
    if at > 0:
        nav.append(f'<a href="{panes.esc(href(q, max(0, at - found["limit"]), asked))}">previous {found["limit"]}</a>')
    if at + len(hits) < n and at + found["limit"] <= pp.OFFSET:
        nav.append(f'<a href="{panes.esc(href(q, at + found["limit"], asked))}">next {found["limit"]}</a>')
    if nav:
        out.append('<div class="actions">' + " ".join(nav) + "</div>")
    out.append("</section>")
    return "\n".join(out)


def text_pane(item: dict, q: str = "", failed: str = "", asked: dict = None) -> str:
    out = ['<section class="pane wide" id="papers-past-text">', '<div class="reg">papers past · the text held</div>']
    if failed or item is None:
        out.append(f'<p class="why">{panes.esc(failed or "no article by that id in the catalogue")}</p></section>')
        return "\n".join(out)
    out.append(f'<h2>{panes.esc(item["title"] or item["key"])}</h2>'
               f'<p class="meta">{panes.esc(item["paper"])}, {panes.esc(item["published_on"] or "undated")}, '
               f'{item["chars"]:,} characters · {panes.new_tab("on Papers Past", item["url"])}'
               + (f' · <a href="{panes.esc(href(q, 0, asked))}">back to the hits</a>' if q else "") +
               f' · <code>{panes.esc(item["key"])}</code></p>'
               f'<div class="text">{panes.mark(item["text"], _marks(q))}</div></section>')
    return "\n".join(out)


def offset_of(qs: dict) -> int:
    o = (qs.get("o") or ["0"])[0]
    return min(int(o), pp.OFFSET) if o.isdigit() else 0


def render(conn, q: str, offset: int = 0, db=None, asked: dict = None) -> str:
    """The tab on `conn`, a session-reader connection (the catalogue is the lane's own table, read only)."""
    found, failed, a = None, "", asked or {}
    if q:
        try:
            found = pp.search(conn, q, limit=PAGE, offset=offset, sort=a.get("s", "relevance"), paper=a.get("paper", ""),
                              year_from=a.get("yf"), year_to=a.get("yt"), min_chars=a.get("min"))
        except Exception as exc:  # noqa: BLE001 — the pane says what failed
            failed = f"{type(exc).__name__}: {exc}"
    return panes.page("", [], [search_pane(q, found, failed, a)], tab=TAB, db=db)


def render_text(conn, key: str, q: str = "", db=None, asked: dict = None) -> str:
    item, failed = None, ""
    try:
        item = pp.article(conn, key)
    except Exception as exc:  # noqa: BLE001
        failed = f"the text could not be read: {type(exc).__name__}: {exc}"
    return panes.page("", [], [text_pane(item, q, failed, asked)], tab=TAB, db=db)
