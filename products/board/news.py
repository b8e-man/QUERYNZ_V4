"""The news tab (Arthur, 26 November 2026: "a list of read news articles sortable by article publish date and sortable
by read date. searchable").

    GET /news?q=&sort=read|published&dir=desc|asc&all=1&page=N

One row an article the news read has finished with (pub.news_read, registers/news/publish.sql): published, read,
site, title (a link to the article's own address), author, the items the gates kept (quotes, roles, tones), and how
it was read. Searched in the title, the author and the site. By default only the articles read (read or replayed);
`all=1` adds those skipped (te reo Māori, a paywall stub) or unusable, with the reason.
"""
from __future__ import annotations

import urllib.parse

from products.board import panes
from products.board.panes import esc

TAB = "news"
PATH = "/news"
PAGE = 100
SORTS = {"read": "read_at", "published": "published_at"}
READ = ("read", "replayed")

CSS = """
.news{padding:0 .5rem 3rem}
.nw-top{display:flex;flex-wrap:wrap;gap:.5rem 1rem;align-items:center;margin:.5rem 0}
.nw-top input[type=search]{min-width:22rem;font-size:14px;padding:.3rem .5rem}
.nw-top .count{color:#aab1bc;font-size:13px}
.news table.grid{width:100%;font-size:13px}
.news table.grid td.n{text-align:right;font-variant-numeric:tabular-nums}
.news table.grid td.when{white-space:nowrap;font-variant-numeric:tabular-nums}
.news table.grid th a{color:#aab1bc;text-decoration:none}
.news table.grid th a.on{color:#e8eaee}
.news .why{color:#aab1bc}
.nw-pages{margin:.75rem 0;display:flex;gap:1rem}
"""


def args(qs: dict) -> dict:
    one = lambda k, n=200: (qs.get(k) or [""])[0].strip()[:n]
    sort = one("sort", 20)
    d = one("dir", 4)
    try:
        page = max(0, int(one("page", 6) or 0))
    except ValueError:
        page = 0
    return {"q": one("q"), "sort": sort if sort in SORTS else "read", "dir": d if d in ("asc", "desc") else "desc",
            "all": one("all", 1) == "1", "page": page}


def href(a: dict, **change) -> str:
    b = {**a, **change}
    keep = {k: v for k, v in (("q", b["q"]), ("sort", b["sort"]), ("dir", b["dir"]), ("all", "1" if b["all"] else ""),
                              ("page", str(b["page"]) if b["page"] else "")) if v}
    return PATH + ("?" + urllib.parse.urlencode(keep) if keep else "")


def query(a: dict) -> tuple[str, list]:
    """The page's SQL and its parameters: one more row than the page, to know whether there is a next."""
    where, params = [], []
    if not a["all"]:
        where.append("outcome = ANY(%s)")
        params.append(list(READ))
    if a["q"]:
        like = "%" + a["q"].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        where.append("(title ILIKE %s OR author ILIKE %s OR host ILIKE %s)")
        params += [like, like, like]
    col = SORTS[a["sort"]]
    sql = ("SELECT url_key, url, host, title, author, published_at, read_at, outcome, model, quotes_kept, roles_kept, "
           "tones_kept, skipped_why FROM pub.news_read" + (" WHERE " + " AND ".join(where) if where else "")
           + f" ORDER BY {col} {a['dir'].upper()} NULLS LAST, url_key LIMIT {PAGE + 1} OFFSET {a['page'] * PAGE}")
    return sql, params


def _when(x) -> str:
    return x.strftime("%Y-%m-%d %H:%M") if x is not None else ""


def table(a: dict, rows: list) -> str:
    def th(label: str, key: str) -> str:
        on = a["sort"] == key
        arrow = (" ↓" if a["dir"] == "desc" else " ↑") if on else ""
        flip = "asc" if on and a["dir"] == "desc" else "desc"
        return f'<th><a class="{"on" if on else ""}" href="{esc(href(a, sort=key, dir=flip, page=0))}">{esc(label)}{arrow}</a></th>'
    head = ("<tr>" + th("published", "published") + th("read", "read") + "<th>site</th><th>title</th><th>author</th>"
            "<th>quotes</th><th>roles</th><th>tones</th><th>how</th></tr>")
    body = []
    for r in rows[:PAGE]:
        how = r["outcome"] + (f": {r['skipped_why']}" if r.get("skipped_why") else "")
        title = r["title"] or r["url_key"]
        body.append(
            f'<tr><td class="when">{esc(_when(r["published_at"]))}</td><td class="when">{esc(_when(r["read_at"]))}</td>'
            f'<td>{esc(r["host"])}</td><td><a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">{esc(title)}</a></td>'
            f'<td>{esc(r["author"] or "")}</td><td class="n">{r["quotes_kept"]}</td><td class="n">{r["roles_kept"]}</td>'
            f'<td class="n">{r["tones_kept"]}</td><td class="why">{esc(how)}</td></tr>')
    return f'<table class="grid">{head}{"".join(body)}</table>'


def render(conn, qs: dict) -> str:
    a = args(qs)
    sql, params = query(a)
    try:
        cur = conn.execute(sql, params)
        cols = [c.name for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        error = ""
    except Exception as e:                       # a slow search or a view not made yet: said, never a blank page
        rows, error = [], f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
    form = (f'<form class="nw-top" method="get" action="{PATH}">'
            f'<input type="search" name="q" value="{esc(a["q"])}" placeholder="title, author or site" autofocus>'
            f'<input type="hidden" name="sort" value="{esc(a["sort"])}"><input type="hidden" name="dir" value="{esc(a["dir"])}">'
            f'<label><input type="checkbox" name="all" value="1"{" checked" if a["all"] else ""}> skipped and unusable too</label>'
            f'<button>search</button>'
            f'<span class="count">{"" if error else f"articles {a["page"] * PAGE + 1 if rows else 0}–{a["page"] * PAGE + min(len(rows), PAGE)}"}</span></form>')
    pages = ('<div class="nw-pages">'
             + (f'<a href="{esc(href(a, page=a["page"] - 1))}">← previous page</a>' if a["page"] else "")
             + (f'<a href="{esc(href(a, page=a["page"] + 1))}">next page →</a>' if len(rows) > PAGE else "") + "</div>")
    body = (f'<p class="why">the list could not be read: {esc(error)}</p>' if error
            else table(a, rows) + pages if rows else '<p class="why">no read article matches</p>')
    return panes.page("", [], [f'<style>{CSS}</style><section class="news">{form}{body}</section>'], tab=TAB)
