"""The comments on a WordPress article page, as the page serves them (Arthur, 18 November 2026: "we want all
comments and we want to efficiently link them to both the articles and also the user"). Pure: reads a page the
provider fetched, fetches nothing.

WordPress marks each comment with an element whose id is `comment-<n>` (or `li-comment-<n>` / `div-comment-<n>`
around it), nests replies in a `children` list under their parent, and marks a logged-in commenter with the classes
`byuser comment-author-<slug>`. Read on kiwiblog, thestandard and newsroom, whose markup differs only in where the
name and the time sit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

_ID = re.compile(r"^(?:li-|div-)?comment-(\d+)$")
_SLUG = re.compile(r"^comment-author-(.+)$")
_NZ = ZoneInfo("Pacific/Auckland")
_KIWIBLOG_DATE = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4} \d{1,2}:\d{2}[ap]m)")


@dataclass
class Comment:
    comment_id: str
    parent_id: str | None
    author_name: str | None
    author_slug: str | None       # the site's own mark for a logged-in commenter
    author_url: str | None        # the profile link the commenter gave
    avatar_url: str | None
    posted_at: datetime | None
    text: str
    votes_up: int | None = None
    votes_down: int | None = None


def has_comments(html: str) -> bool:
    return 'id="comment-' in html or "id='comment-" in html or 'id="li-comment-' in html


def _when(box) -> datetime | None:
    t = box.find("time", attrs={"datetime": True})
    if t:
        try:
            return datetime.fromisoformat(t["datetime"].replace("Z", "+00:00"))
        except ValueError:
            pass
    d = box.select_one(".comdate")                     # kiwiblog: "November 8, 2026 3:37am", New Zealand time
    m = _KIWIBLOG_DATE.search(d.get_text(" ", strip=True)) if d else None
    if m:
        try:
            return datetime.strptime(m.group(1), "%B %d, %Y %I:%M%p").replace(tzinfo=_NZ)
        except ValueError:
            pass
    return None


def _int(box, sel) -> int | None:
    el = box.select_one(sel)
    try:
        return int(el.get_text(strip=True)) if el else None
    except ValueError:
        return None


def _parent(el, cid) -> str | None:
    """The comment a reply answers: replies sit in a `children` list, inside the parent's <li> (thestandard,
    newsroom) or just after the parent's <article> (kiwiblog)."""
    kids = el.find_parent(["ul", "ol"], class_="children")
    if kids is None:
        return None
    prev = kids.find_previous_sibling(id=_ID)
    if prev is not None:
        return _ID.match(prev["id"]).group(1)
    up = kids.parent
    while up is not None and hasattr(up, "get"):
        m = _ID.match(up.get("id") or "")
        if m and m.group(1) != cid:
            return m.group(1)
        if up.name == "li":
            inner = up.find(id=_ID)
            if inner is not None and _ID.match(inner["id"]).group(1) != cid:
                return _ID.match(inner["id"]).group(1)
        up = up.parent
    return None


def extract(html: str) -> list[Comment]:
    """Every comment on the page, in page order. A comment with no content box is not one (a widget's link)."""
    if not has_comments(html):
        return []
    soup = BeautifulSoup(html, "html.parser")
    bodies: dict[str, object] = {}
    for el in soup.find_all(id=_ID):
        cid = _ID.match(el["id"]).group(1)
        if el.select_one(".comment-content") is not None:
            bodies[cid] = el                         # the innermost element with an id that holds the content
    out = []
    for cid, body in bodies.items():
        content = body.select_one(".comment-content")
        classes = list(body.get("class") or [])
        for x in [body.find_parent("li"), body.find("div", class_="comment")]:
            if x is not None and (x is body.find("div", class_="comment") or _ID.match(x.get("id") or "")):
                classes += x.get("class") or []
        slug = next((m.group(1) for c in classes if (m := _SLUG.match(c))), None) if "byuser" in classes else None
        who = body.select_one(".comment-author")
        name_el = who.select_one(".fn, h3, cite") if who else None
        link = None
        if name_el is not None:
            link = name_el if name_el.name == "a" else name_el.find("a", href=True)
        img = who.find("img", src=True) if who else None
        out.append(Comment(
            comment_id=cid, parent_id=_parent(body, cid),
            author_name=(name_el.get_text(" ", strip=True) or None) if name_el else None,
            author_slug=slug,
            author_url=(link.get("href") or None) if link is not None else None,
            avatar_url=(img.get("src") or None) if img else None,
            posted_at=_when(body),
            text=("\n\n".join(t for p in content.find_all("p") if (t := p.get_text(" ", strip=True)))
                  or content.get_text(" ", strip=True)),
            votes_up=_int(body, f"#karma-{cid}-up"), votes_down=_int(body, f"#karma-{cid}-down")))
    return out
