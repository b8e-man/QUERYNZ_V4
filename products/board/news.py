"""The news tab (Arthur, 26 November 2026: "a list of read news articles sortable by article publish date and sortable
by read date. searchable").

    GET /news?q=&sort=read|published&dir=desc|asc&all=1&page=N&open=<url_key>

One row an article the news read has finished with (pub.news_read, registers/news/publish.sql): published, read,
site, title (a link to the article's own address), author, the items the gates kept (quotes, roles, tones), and how
it was read. Searched in the title, the author and the site. By default only the articles read (read or replayed);
`all=1` adds those skipped (te reo Māori, a paywall stub) or unusable, with the reason.

THE INSPECTOR (Arthur, 26 November 2026: "when the headline is clicked ... open an inspector pane that shows all the
extracted data held and is scrollable"): a headline opens `open=<url_key>`, a pane beside the list, scrolling on its
own. It shows the stored reading whole, opened by its key in the reader store (the article's entities, roles,
relations, descriptors, quotes, events, numbers, tones, traps and checks; every entity number written as its name),
each quote, role and tone with the gates' decision and rule (pub.news_read_items), and the reading's own record
(reader, model, serving, commit). The raw reading at the end. The article's own page is the ↗ beside the headline.
"""
from __future__ import annotations

import urllib.parse

import json

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
.nw-split{display:grid;grid-template-columns:minmax(0,1fr);gap:1rem}
.nw-split.open{grid-template-columns:minmax(0,1fr) minmax(24rem,40%)}
.news table.grid tr.on td{background:#1b2a40}
.news a.out{color:#aab1bc;text-decoration:none;margin-left:.3rem}
.nw-insp{position:sticky;top:.5rem;align-self:start;max-height:calc(100vh - 5rem);overflow-y:auto;background:#161a20;
  border:1px solid #3a404c;border-radius:8px;padding:.75rem 1rem;font-size:13px}
.nw-insp h2{font-size:16px;margin:.1rem 0 .4rem;font-weight:600;line-height:1.3}
.nw-insp h3{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#aab1bc;margin:1rem 0 .35rem;font-weight:600}
.nw-insp .meta{color:#aab1bc;margin:.1rem 0}
.nw-insp .link{margin:.1rem 0 .3rem;word-break:break-all}
.nw-insp .link a{color:#8cb8ff}
.nw-insp .close{float:right;color:#aab1bc;text-decoration:none;font-size:18px}
.nw-insp ol,.nw-insp ul{margin:.2rem 0;padding-left:1.3rem}
.nw-insp li{margin:.35rem 0;line-height:1.45}
.nw-insp q{color:#e8eaed}
.nw-insp .k{color:#aab1bc}
.nw-insp .kept{color:#4cc38a}
.nw-insp .dropped{color:#e07a5f}
.nw-insp table{border-collapse:collapse;width:100%}
.nw-insp td{border-top:1px solid #2a303a;padding:.15rem .35rem;vertical-align:top}
.nw-insp pre{white-space:pre-wrap;font-size:12px;background:#0e1014;padding:.5rem;border-radius:4px}
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
            "all": one("all", 1) == "1", "page": page, "open": one("open", 600)}


def href(a: dict, **change) -> str:
    b = {**a, **change}
    keep = {k: v for k, v in (("q", b["q"]), ("sort", b["sort"]), ("dir", b["dir"]), ("all", "1" if b["all"] else ""),
                              ("page", str(b["page"]) if b["page"] else ""), ("open", b.get("open") or "")) if v}
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
        on = ' class="on"' if r["url_key"] == a.get("open") else ""
        body.append(
            f'<tr{on}><td class="when">{esc(_when(r["published_at"]))}</td><td class="when">{esc(_when(r["read_at"]))}</td>'
            f'<td>{esc(r["host"])}</td><td><a href="{esc(href(a, open=r["url_key"]))}">{esc(title)}</a>'
            f'<a class="out" href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer" title="the article\'s own page">↗</a></td>'
            f'<td>{esc(r["author"] or "")}</td><td class="n">{r["quotes_kept"]}</td><td class="n">{r["roles_kept"]}</td>'
            f'<td class="n">{r["tones_kept"]}</td><td class="why">{esc(how)}</td></tr>')
    return f'<table class="grid">{head}{"".join(body)}</table>'


#: the reading's sections in the order the pane shows them; any other a later reader adds follows, by name
SECTIONS = ("article", "authors", "entities", "roles", "relations", "descriptors", "quotes", "events", "numbers",
            "sentiment", "traps", "checks", "quotes_first_pass", "sentiment_dropped")
LABELS = {"sentiment": "tones", "sentiment_dropped": "tones the reader dropped", "quotes_first_pass": "quotes, the first pass"}
#: the reading's section a gated kind is, and the gated kind a section's items carry (read_items.kind)
GATED = {"quotes": "quotes", "roles": "roles", "sentiment": "sentiment", "claims": "claims"}
WHO = ("who", "of", "speaker", "about", "target", "subject", "object", "a", "b", "to", "from", "by")


def _name(ents: dict, x) -> str:
    """An entity number written as its name ("e3" → "Zac Pe (person)"); a list of them joined; anything else as is."""
    if isinstance(x, list):
        return ", ".join(_name(ents, y) for y in x)
    if isinstance(x, str) and x in ents:
        e = ents[x] or {}
        return f"{e.get('name') or x} ({e.get('kind') or '?'})"
    return "" if x is None else str(x)


def _fields(ents: dict, d: dict, skip=("text",)) -> str:
    out = []
    for k, v in d.items():
        if k in skip or v in (None, "", [], {}):
            continue
        val = _name(ents, v) if k in WHO else (", ".join(map(str, v)) if isinstance(v, list) else
                                               json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else str(v))
        out.append(f'<span class="k">{esc(k)}:</span> {esc(val)}')
    return " · ".join(out)


def _gate(gates: dict, kind: str, n: int) -> str:
    g = gates.get((kind, n))
    if g is None:
        return ""
    cls, word = ("kept", "kept") if g["kept"] else ("dropped", "dropped")
    cit = ", a citation" if g.get("citation") else ""
    return f' <span class="{cls}">[{word}{cit}: {esc(g["rule"])}]</span>'


def section(name: str, value, ents: dict, gates: dict) -> str:
    label = LABELS.get(name, name)
    if value in (None, [], {}, ""):
        return f'<h3>{esc(label)}</h3><p class="meta">none</p>'
    if name == "entities" and isinstance(value, dict):
        rows = "".join(f'<tr><td class="k">{esc(k)}</td><td>{esc((e or {}).get("name"))}</td><td class="k">{esc((e or {}).get("kind"))}</td>'
                       f'<td>{esc(", ".join((e or {}).get("forms") or []))}</td></tr>' for k, e in value.items())
        head = '<tr><td class="k">number</td><td class="k">name</td><td class="k">kind</td><td class="k">forms in the article</td></tr>'
        return f'<h3>{esc(label)} ({len(value)})</h3><table>{head}{rows}</table>'
    if isinstance(value, dict):
        return f'<h3>{esc(label)}</h3><p>{_fields(ents, value, skip=())}</p>'
    kind = GATED.get(name)
    items = []
    for n, x in enumerate(value):
        if isinstance(x, dict):
            text = x.get("text") or x.get("claim")
            head = f"<q>{esc(text)}</q> " if text else ""
            rest = _fields(ents, x, skip=("text", "claim"))
            items.append(f"<li>{head}{rest}{_gate(gates, kind, n) if kind else ''}</li>")
        else:
            items.append(f"<li>{esc(_name(ents, x))}</li>")
    return f'<h3>{esc(label)} ({len(value)})</h3><ol start="0">{"".join(items)}</ol>'


def inspector(conn, url_key: str, a: dict = None, store=None) -> str:
    """The pane for one article: its record, then every section of its stored reading, the gates beside each item."""
    cur = conn.execute("SELECT url_key, url, host, title, author, published_at, read_at, outcome, model, reader, gates, "
                       "seconds, reading_key, skipped_why, capture_sha256 FROM pub.news_read WHERE url_key = %s", (url_key,))
    cols = [c.name for c in cur.description]
    row = cur.fetchone()
    close = f'<a class="close" href="{esc(href({**a, "open": ""}))}" title="close">×</a>' if a else ""
    if row is None:
        return f'<aside class="nw-insp">{close}<p class="why">no read article {esc(url_key)}</p></aside>'
    r = dict(zip(cols, row))
    secs = f" · {r['seconds']:.0f} s" if r["seconds"] else ""
    gates = {(k, n): {"kept": kept, "citation": cit, "rule": rule} for k, n, kept, cit, rule in conn.execute(
        "SELECT kind, n, kept, citation, rule FROM pub.news_read_items WHERE url_key = %s", (url_key,)).fetchall()}
    head = (f'{close}<h2>{esc(r["title"] or r["url_key"])}<a class="out" href="{esc(r["url"])}" target="_blank" '
            f'rel="noopener noreferrer" title="the article\'s own page">↗</a></h2>'
            f'<p class="link"><a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">{esc(r["url"])}</a>'
            + (f' · <a href="/doc/{esc(r["capture_sha256"])}" target="_blank">our captured copy</a>' if r.get("capture_sha256") else "")
            + '</p>'
            f'<p class="meta">{esc(r["host"])}{" · " + esc(r["author"]) if r["author"] else ""} · published '
            f'{esc(_when(r["published_at"]))} · read {esc(_when(r["read_at"]))}</p>'
            f'<p class="meta">{esc(r["outcome"])}{": " + esc(r["skipped_why"]) if r["skipped_why"] else ""} · {esc(r["model"])}'
            f' · {esc(r["reader"])} · {esc(r["gates"])}{secs}</p>')
    try:
        from support import reader as rd
        reading = (store or rd.Store()).get(r["reading_key"])
    except Exception as e:                       # a reading missing from the store is said, never a blank pane
        return f'<aside class="nw-insp">{head}<p class="why">the stored reading could not be opened: {esc(type(e).__name__)}: {esc(str(e)[:200])}</p></aside>'
    stamp = (f'<p class="meta">reading: {esc(reading.reader)} · {esc(reading.profile)} v{esc(reading.profile_version)}'
             f' · serving {esc(reading.serving or "not recorded")} · commit {esc((reading.commit or "")[:8] or "not recorded")}'
             f' · made {esc(reading.made_at)}</p>')
    try:
        got = json.loads(reading.text) if reading.text else None
    except ValueError:
        got = None
    if not isinstance(got, dict):
        return f'<aside class="nw-insp">{head}{stamp}<p class="why">the reading holds no data (unusable)</p></aside>'
    ents = got.get("entities") if isinstance(got.get("entities"), dict) else {}
    names = [k for k in SECTIONS if k in got] + sorted(k for k in got if k not in SECTIONS)
    body = "".join(section(k, got[k], ents, gates) for k in names)
    raw = f'<details><summary>the reading as stored</summary><pre>{esc(json.dumps(got, ensure_ascii=False, indent=1))}</pre></details>'
    return f'<aside class="nw-insp">{head}{stamp}{body}<h3>raw</h3>{raw}</aside>'



def render(conn, qs: dict, store=None) -> str:
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
    pane = ""
    if a["open"]:
        try:
            pane = inspector(conn, a["open"], a, store)
        except Exception as e:
            pane = f'<aside class="nw-insp"><p class="why">the inspector could not be read: {esc(type(e).__name__)}: {esc(str(e)[:200])}</p></aside>'
    split = f'<div class="nw-split{" open" if pane else ""}"><div>{body}</div>{pane}</div>'
    return panes.page("", [], [f'<style>{CSS}</style><section class="news">{form}{split}</section>'], tab=TAB)
