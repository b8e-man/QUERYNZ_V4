"""The paper tab (Arthur, 26 November 2026: "a custom newsfeed dressed up as a newspaper with pictures and
everything"; "latest read, by theme"; "we get the pictures from the sites as we load it"; "we just have a blurb and
clicking the item opens the link to the original").

    GET /paper                     the front page: the newest articles the news read has finished, in sections by the
                                   first theme the reader gave each (registers.news.read: article.themes)
    GET /paper?desk=&site=&name=&subject=   only the stories with that tag (Arthur, 26 November 2026: "let's put a few tags on
                                   them so we can navigate easier"): a story's tags are its desk, its site, two of its
                                   subjects and up to three people, organisations or places its reading names; a desk or a name is
                                   looked for among the newest WINDOW stories, a site among all
    GET /paper/picture?k=<url_key> the story's lead picture: a redirect to the address the publisher's page names
                                   (og:image, twitter:image), which the browser then loads from the publisher; 404 when
                                   there is none

A picture's address is found once and kept (`<live>/board/news-pictures.jsonl`, append-only): from our captured copy
of the page where we hold one, else by reading the article's own page through the fetch gate
(docs/legal/positions/news-article-pictures.md: its head only, 64 KB at most, paced per host, a block or a challenge a
failed read and a held host). A story with no picture is set as type. Only a story the front page has just shown can
ask for its picture, so the board fetches nothing it was not asked to show. Every story opens the original article.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import threading
import urllib.parse

from products.board import panes, subjects
from products.board.panes import esc

TAB = "paper"
PATH = "/paper"
PICTURE = "/paper/picture"
STORIES = 120
WINDOW = 800
TAG_KINDS = ("person", "organisation", "place")
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
PICTURES = os.path.join(LIVE, "board", "news-pictures.jsonl")
#: what the paper page lets the browser load: the board's own files and the publishers' pictures (https)
POLICY = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https: data:; "
          "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
NONE = "none"
META = re.compile(r"""<meta\b[^>]*?(?:property|name)\s*=\s*["'](?:og:image(?::secure_url|:url)?|twitter:image(?::src)?)["'][^>]*>""", re.I)
CONTENT = re.compile(r"""\bcontent\s*=\s*["']([^"']+)["']""", re.I)

CSS = """
.paper{max-width:78rem;margin:0 auto;padding:0 1rem 4rem;font-family:Georgia,'Times New Roman',serif;color:#e8e4da}
.pp-mast{text-align:center;border-bottom:3px double #8a8578;padding:.75rem 0 .4rem;margin-bottom:.6rem}
.pp-mast h1{font-size:46px;letter-spacing:.02em;margin:0;font-weight:700;font-family:Georgia,serif}
.pp-mast .line{display:flex;justify-content:space-between;font-size:12px;color:#aaa497;border-top:1px solid #5d594f;
  margin-top:.4rem;padding-top:.25rem;text-transform:uppercase;letter-spacing:.08em}
.pp-sec{margin:1.6rem 0 .5rem;border-top:2px solid #8a8578;padding-top:.3rem}
.pp-sec h2{font-size:13px;text-transform:uppercase;letter-spacing:.14em;margin:0 0 .6rem;color:#d9c9a3}
.pp-grid{display:grid;grid-template-columns:repeat(12,1fr);gap:1.1rem 1.4rem}
.pp-story{grid-column:span 4;display:block;color:inherit;text-decoration:none}
.pp-story.lead{grid-column:span 8;grid-row:span 2}
.pp-story.wide{grid-column:span 6}
.pp-story .pic{aspect-ratio:16/9;background:#24221e;overflow:hidden;margin-bottom:.45rem;border-radius:2px}
.pp-story .pic img{width:100%;height:100%;object-fit:cover;display:block}
.pp-story .pic.none{display:flex;align-items:center;justify-content:center;background:#2b2823}
.pp-story .pic.none::after{content:attr(data-site);font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#8a8578}
.pp-story h3{font-size:20px;line-height:1.2;margin:.1rem 0 .3rem;font-weight:700}
.pp-story.lead h3{font-size:34px;line-height:1.12}
.pp-story p{font-size:15px;line-height:1.45;margin:0 0 .3rem;color:#cfcabd}
.pp-story.lead p{font-size:17px}
.pp-story .by{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#9c968a;font-family:system-ui,sans-serif}
.pp-story a.go{color:inherit;text-decoration:none;display:block}
.pp-story a.go:hover h3{text-decoration:underline}
.pp-tags{margin-top:.35rem;display:flex;flex-wrap:wrap;gap:.3rem;font-family:system-ui,sans-serif}
.pp-tags a{font-size:11px;padding:.1rem .45rem;border:1px solid #5d594f;border-radius:10px;color:#d9c9a3;text-decoration:none}
.pp-tags a:hover{background:#3a362f}
.pp-tags a.desk{border-color:#8a7a52}
.pp-tags a.site{color:#aaa497}
.pp-tags a.subj{border-color:#4f6a8a;color:#b9cde6}
.pp-nav{display:flex;flex-wrap:wrap;justify-content:center;gap:.2rem 1rem;font-family:system-ui,sans-serif;font-size:12px;
  text-transform:uppercase;letter-spacing:.1em;padding:.3rem 0 .5rem;border-bottom:1px solid #5d594f}
.pp-nav a{color:#d9c9a3;text-decoration:none}
.pp-nav a.on{color:#fff;border-bottom:2px solid #d9c9a3}
.pp-nav .n{color:#8a8578;margin-left:.2rem}
.pp-filter{font-family:system-ui,sans-serif;font-size:13px;margin:.8rem 0;color:#cfcabd}
.pp-filter a{color:#d9c9a3}
@media (max-width:900px){.pp-story,.pp-story.lead,.pp-story.wide{grid-column:span 12}}
"""

_LOCK = threading.Lock()
_FOUND: dict | None = None          # url_key → picture address, or "none: why"
_SHOWN: dict = {}                   # url_key → (url, capture sha): the stories a front page has shown


def _found() -> dict:
    global _FOUND
    if _FOUND is None:
        _FOUND = {}
        try:
            with open(PICTURES, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line)
                        _FOUND[r["url_key"]] = r["picture"]
        except FileNotFoundError:
            pass
    return _FOUND


def _keep(url_key: str, picture: str, how: str) -> None:
    from support import appendline
    os.makedirs(os.path.dirname(PICTURES), exist_ok=True)
    appendline.append_json(PICTURES, {"url_key": url_key, "picture": picture, "how": how,
                                      "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}, ensure_ascii=False)


def picture_in(page: bytes, base: str) -> str | None:
    """The lead picture a page's head names (og:image, then twitter:image), as an absolute https address."""
    head = page[:65536].decode("utf-8", "replace")
    for m in META.finditer(head):
        c = CONTENT.search(m.group(0))
        if c:
            u = urllib.parse.urljoin(base, html.unescape(c.group(1).strip()))
            if u.startswith("http://"):
                u = "https://" + u[len("http://"):]
            if u.startswith("https://"):
                return u
    return None


def find(url_key: str, url: str, sha: str = "", read_capture=None, open_url=None) -> str:
    """The picture's address, or "none: why"; looked for once (our capture first, else the page through the gate)."""
    if sha:
        try:
            if read_capture is None:
                from products.board import document
                p = document.path_in_store(sha)
                page = open(p, "rb").read(65536) if p else b""
            else:
                page = read_capture(sha)
            got = picture_in(page, url) if page else None
            if got:
                return got
        except OSError:
            pass
    if open_url is None:
        from support import fetchgate
        open_url = fetchgate.open_url
    try:
        f = open_url(url, timeout=15, max_bytes=65536, follow=2)
    except Exception as e:                       # refused by the gate, a reset, a timeout: a failed read, kept
        return f"{NONE}: {type(e).__name__}: {str(e)[:160]}"
    if f.blocked:
        return f"{NONE}: {f.blocked[:160]}"
    if f.status != 200:
        return f"{NONE}: HTTP {f.status}"
    return picture_in(f.body, f.final_url or url) or f"{NONE}: the page names no picture"


def picture(url_key: str, read_capture=None, open_url=None) -> str | None:
    """For /paper/picture: the address to send the browser to, or None. Only a story a front page showed is looked for."""
    with _LOCK:
        have = _found().get(url_key)
        shown = _SHOWN.get(url_key)
    if have is None and shown is not None:
        got = find(url_key, shown[0], shown[1], read_capture, open_url)
        with _LOCK:
            if url_key not in _found():
                _found()[url_key] = got
                _keep(url_key, got, "capture or page")
        have = got
    return have if have and not have.startswith(NONE) else None


def blurb(opening: str, title: str, words: int = 42) -> str:
    """The first sentences of the article, about `words` long, its headline left off when the text repeats it."""
    t = re.sub(r"\s+", " ", opening or "").strip()
    if title and t.lower().startswith(title.lower()):
        t = t[len(title):].lstrip(" .:-–—")
    w = t.split(" ")
    if len(w) <= words:
        return t
    cut = " ".join(w[:words])
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return cut[:end + 1] if end > len(cut) // 2 else cut.rstrip(",;:") + "…"


def tags_of(store, reading_key: str, subjects_key: str = None) -> tuple[list, list, list]:
    """(broad subjects, names, subjects): the reader's broad subjects (for the desk); the people, organisations and
    places it named, the most often named first (by the forms the article used), each once; and the subjects to tag,
    the specific first, then the broad from the most specific (IPTC labels are written broad to specific)."""
    try:
        got = json.loads(store.get(reading_key).text or "null") or {}
    except Exception:
        return [], [], []
    got = subjects.merged(got, store, subjects_key)
    th = subjects.broad(got)
    subj = [x["name"] for x in subjects.specific(got)] + list(reversed(th))
    ents = got.get("entities") if isinstance(got.get("entities"), dict) else {}
    seen, names = set(), []
    for _, e in sorted(ents.items(), key=lambda kv: (-len((kv[1] or {}).get("forms") or []), kv[0])):
        e = e or {}
        n = (e.get("name") or "").strip()
        if n and e.get("kind") in TAG_KINDS and n.lower() not in seen:
            seen.add(n.lower())
            names.append(n)
    seen, tags = set(), []
    for n in subj:
        if n.lower() not in seen:
            seen.add(n.lower())
            tags.append(n)
    return th, names, tags


def args(qs: dict) -> dict:
    def one(k):
        return ((qs.get(k) or [""])[0] or "").strip()[:200]
    return {"desk": one("desk"), "site": one("site").lower(), "name": one("name"), "subject": one("subject")}


def href(**f) -> str:
    keep = {k: v for k, v in f.items() if v}
    return PATH + ("?" + urllib.parse.urlencode(keep) if keep else "")


def stories(conn, store=None, a: dict = None) -> list[dict]:
    """The stories the page shows: the newest, or the newest with the tag asked for; each with its desk and names."""
    a = a or {"desk": "", "site": "", "name": "", "subject": ""}
    where, params = "", []
    if a["site"]:
        where, params = " AND host = %s", [a["site"]]
    cur = conn.execute("SELECT url_key, url, host, title, author, published_at, reading_key, capture_sha256, opening, "
                       "quotes_kept, roles_kept, subjects_key FROM pub.news_read WHERE outcome IN ('read', 'replayed') AND title IS NOT NULL "
                       f"AND published_at <= now() + interval '1 day'{where} ORDER BY published_at DESC NULLS LAST LIMIT %s",
                       params + [WINDOW if (a["desk"] or a["name"] or a["subject"]) else STORIES])
    cols = [c.name for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    if store is None:
        from support import reader as rd
        store = rd.Store()
    for r in rows:
        r["themes"], r["names"], r["subjects"] = tags_of(store, r["reading_key"], r.get("subjects_key"))
        r["desk"] = desk(r["themes"])
    if a["desk"]:
        rows = [r for r in rows if r["desk"] == a["desk"]]
    if a["name"]:
        rows = [r for r in rows if a["name"].lower() in (n.lower() for n in r["names"])]
    if a["subject"]:
        rows = [r for r in rows if a["subject"].lower() in (n.lower() for n in r["subjects"])]
    rows = rows[:STORIES]
    with _LOCK:
        for r in rows:
            _SHOWN[r["url_key"]] = (r["url"], r["capture_sha256"] or "")
    return rows


#: the paper's desks, in page order, each with the words that put a reader's theme on it (themes are the reader's own
#: free words: "business and finance", "crime and law", ...); a story goes to the desk of its first theme that matches
DESKS = (("politics", ("politic", "government", "election", "parliament", "policy", "public sector")),
         ("business", ("business", "econom", "financ", "market", "insurance", "real estate", "property", "trade", "employment", "industry", "agricultur", "dairy", "farming")),
         ("crime and justice", ("crime", "law", "justice", "court", "police", "safety and security", "human rights")),
         ("world", ("world", "international", "foreign", "military", "conflict", "war")),
         ("environment", ("environment", "climate", "weather", "disaster", "accident", "emergenc", "energy", "conservation")),
         ("health", ("health", "medic", "hospital")),
         ("science and technology", ("science", "technolog", "computer", "internet", "space")),
         ("arts and life", ("arts", "culture", "entertainment", "music", "film", "fashion", "food", "lifestyle", "religion", "education", "society", "community", "transport", "automotive")),
         ("sport", ("sport", "rugby", "cricket", "football", "netball")))
MORE = "more news"


def desk(themes: list) -> str:
    for t in themes or []:
        t = t.lower()
        for name, words in DESKS:
            if any(w in t for w in words):
                return name
    return MORE


def sections(rows: list) -> list[tuple[str, list]]:
    """The front page (the six newest), then the desks in page order; each story in one section only, an empty desk left out."""
    front, rest = rows[:6], rows[6:]
    by: dict[str, list] = {}
    for r in rest:
        by.setdefault(r.get("desk") or desk(r["themes"]), []).append(r)
    order = [(n, by[n]) for n, _ in DESKS if n in by] + ([(MORE, by[MORE])] if MORE in by else [])
    return [("front page", front)] + order


def story(r: dict, cls: str = "") -> str:
    when = r["published_at"].strftime("%-d %b %H:%M") if r.get("published_at") else ""
    by = " · ".join(x for x in (r.get("author") or "", when) if x)
    pic = (f'<div class="pic" data-site="{esc(r["host"])}"><img src="{esc(PICTURE + "?" + urllib.parse.urlencode({"k": r["url_key"]}))}" '
           f'alt="" loading="lazy" referrerpolicy="no-referrer"></div>')
    d = r.get("desk") or desk(r.get("themes") or [])
    tags = [f'<a class="desk" href="{esc(href(desk=d))}">{esc(d)}</a>', f'<a class="site" href="{esc(href(site=r["host"]))}">{esc(r["host"])}</a>']
    tags += [f'<a class="subj" href="{esc(href(subject=n))}">{esc(n)}</a>' for n in (r.get("subjects") or [])[:2]]
    tags += [f'<a href="{esc(href(name=n))}">{esc(n)}</a>' for n in (r.get("names") or [])[:3]]
    return (f'<article class="pp-story {cls}"><a class="go" href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">{pic}'
            f'<h3>{esc(r["title"])}</h3><p>{esc(blurb(r.get("opening") or "", r["title"]))}</p></a>'
            f'<div class="by">{esc(by)}</div><div class="pp-tags">{"".join(tags)}</div></article>')


def nav(a: dict) -> str:
    on = a["desk"] if not (a["site"] or a["name"]) else None
    links = [f'<a class="{"on" if not any(a.values()) else ""}" href="{PATH}">everything</a>']
    links += [f'<a class="{"on" if on == n else ""}" href="{esc(href(desk=n))}">{esc(n)}</a>' for n, _ in DESKS + ((MORE, ()),)]
    return f'<nav class="pp-nav">{"".join(links)}</nav>'


def render(conn, store=None, now=None, qs: dict = None) -> str:
    from products.board import assets
    a = args(qs or {})
    try:
        rows = stories(conn, store, a)
        error = ""
    except Exception as e:
        rows, error = [], f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
    today = (now or dt.datetime.now()).strftime("%A %-d %B %Y")
    mast = (f'<div class="pp-mast"><h1>The Daily Register</h1><div class="line"><span>{esc(today)}</span>'
            f'<span>the newest {len(rows)} articles read</span><span>QueryNZ</span></div></div>')
    asked = [(k, v) for k, v in (("desk", a["desk"]), ("site", a["site"]), ("name", a["name"]), ("subject", a["subject"])) if v]
    filt = ""
    if asked:
        say = " and ".join(f"{k} <b>{esc(v)}</b>" for k, v in asked)
        scope = "" if a["site"] and not (a["desk"] or a["name"] or a["subject"]) else f" among the newest {WINDOW}"
        filt = f'<p class="pp-filter">{len(rows)} stories, {say}{scope} · <a href="{PATH}">all stories</a></p>'
    if error:
        body = f'<p class="why">the paper could not be set: {esc(error)}</p>'
    elif not rows:
        body = '<p class="why">no read article has that tag</p>' if asked else '<p class="why">no article read yet</p>'
    else:
        groups = [(asked[0][1], rows)] if asked else sections(rows)
        out = []
        for name, items in groups:
            cards = []
            for i, r in enumerate(items):
                cls = "lead" if i == 0 else ("wide" if (name == "front page" or asked) and i < 3 else "")
                cards.append(story(r, cls))
            out.append(f'<section class="pp-sec"><h2>{esc(name)}</h2><div class="pp-grid">{"".join(cards)}</div></section>')
        body = "".join(out)
    script = f'<script src="{esc(assets.url("paper.js"))}" defer></script>'
    return panes.page("", [], [f'<style>{CSS}</style><div class="paper">{mast}{nav(a)}{filt}{body}</div>{script}'], tab=TAB)
