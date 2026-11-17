"""The Stuff masthead sites (thepost.co.nz, thepress.co.nz, waikatotimes.co.nz): the provider lands each article as
the sites' own JSON (`content.contentBody.body` is the article's HTML), not a page. Added 18 November 2026: the
old estate never collected these sites, so it had no parser for them. Fetches nothing.
"""
from __future__ import annotations

import json
from datetime import datetime

from bs4 import BeautifulSoup

from . import base


def _when(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
    except ValueError:
        return None


def extract(html: str, url: str) -> base.Extracted | None:
    try:
        d = json.loads(html)
    except ValueError:
        return None
    if not isinstance(d, dict):
        return None
    content = d.get("content") or {}
    body = (content.get("contentBody") or {}).get("body") or ""
    soup = BeautifulSoup(body, "html.parser")
    parts = [p.get_text(" ", strip=True) for p in soup.find_all(["p", "h2", "h3", "li"])]
    text = base.clean_text(parts)
    if not text:
        return None
    names = [a.get("name") for a in d.get("author") or [] if isinstance(a, dict) and a.get("name")]
    author = ", ".join(names) or d.get("byline") or None
    meta = d.get("metadata") or {}
    cats = [c for c in [meta.get("section")] + list(meta.get("topic") or []) if c]
    return base.Extracted(title=content.get("title") or url, text=text, author=author,
                          published_at=_when(d.get("publishedDate") or d.get("date")), categories=cats)
