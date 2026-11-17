"""The old estate's news parsers, carried into the news register on 17 November 2026 (Arthur: news site by site into
the new estate, then the old retired). Pure only: each site's `extract(html, url)` reads a page the ingest MCP's
provider fetched; this package fetches nothing (its client, fetch and runner were left behind).

Kept from the old file: newsscrapers — direct-to-backlog NZ news scrapers (ports of the Java
scraper-service in ops/scraper-service-standalone).

Design (kept from the Java framework): per-source module with two phases —
DISCOVERY (RSS/sitemap → candidate items) and CONTENT (fetch page → extract
title/body/author/date). The persistence differs deliberately: instead of the
dashboard's Postgres+ES, every article lands in OUR backlog via
querynz.ingestion.land_document (contract 1, idempotent on upstream_id) — these
ports REPLACE the stalled dashboard as the fresh-news path. Parking (A0.4) and
content-dedup apply at land time exactly as for dashboard rows.

Each source module provides:
    FEEDS: list[str]                      (RSS/atom URLs)
    def extract(html: str, url: str) -> Extracted | None   (pure — golden-testable)
    optionally discover() for non-RSS sources.

Politeness: one fetch at a time per host, POLITE_SLEEP between requests.
"""
from __future__ import annotations

import email.utils
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

@dataclass
class Extracted:
    title: str
    text: str
    author: str | None = None
    published_at: datetime | None = None
    categories: list[str] = field(default_factory=list)


@dataclass
class FeedItem:
    url: str
    title: str | None = None
    published_at: datetime | None = None
    category: str | None = None


def parse_rss(xml_text: str) -> list[FeedItem]:
    """RSS 2.0 / Atom → FeedItems (stdlib only)."""
    root = ET.fromstring(xml_text.encode() if isinstance(xml_text, str) else xml_text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    items: list[FeedItem] = []
    for it in root.iter("item"):                       # RSS 2.0
        link = (it.findtext("link") or "").strip()
        if not link:
            continue
        pub = it.findtext("pubDate")
        items.append(FeedItem(
            url=link, title=(it.findtext("title") or "").strip() or None,
            published_at=_rfc2822(pub), category=(it.findtext("category") or "").strip() or None))
    for it in root.iter("{http://www.w3.org/2005/Atom}entry"):   # Atom
        link_el = it.find("a:link[@rel='alternate']", ns) or it.find("a:link", ns)
        link = (link_el.get("href") if link_el is not None else "") or ""
        if not link:
            continue
        pub = it.findtext("a:published", None, ns) or it.findtext("a:updated", None, ns)
        items.append(FeedItem(url=link.strip(),
                              title=(it.findtext("a:title", "", ns) or "").strip() or None,
                              published_at=_iso(pub)))
    return items


def _rfc2822(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return email.utils.parsedate_to_datetime(s.strip())
    except (TypeError, ValueError):
        return None


def _iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def clean_text(parts: list[str]) -> str:
    """Join paragraph strings into the golden-sample content shape."""
    out = [re.sub(r"[ \t ]+", " ", p).strip() for p in parts]
    return "\n\n".join(p for p in out if p)
