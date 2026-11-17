"""odt.co.nz (Otago Daily Times) — port of the Java ODT scraper
(ops/scraper-service-standalone .../scraper/odtconz/).

Discovery: sitemap-based (discover()), following the Java pipeline
(OdtSitemapParser over https://www.odt.co.nz/sitemap.xml). The Java code
assumed "the first N sitemap pages are the recent ones" — live in 2026 that is
FALSE: the ~12 child pages hold ~50k URLs each and are NOT date-ordered (page
1 is all 2008-2010; the current articles are scattered inside one middle page).
So discover() scans every child page and filters by <lastmod>, returning
newest-first; base.run_source then applies its own recency window + limit.
Cost: ~60-70 MB per full run (each child page is ~6 MB) — acceptable at ODT's
30-min cadence and polite (POLITE_SLEEP between pages), but heavier than a feed.

ODT does expose https://www.odt.co.nz/rss.xml (FEEDS below, for reference) but
it is unusable as a fresh-news source: it serves a small fixed/rotating set of
featured + sponsored items dated 2016-2022, not the live front page. discover()
is therefore the real path; base.run_source prefers it over FEEDS.

Content parsing follows OdtContentScraper selectors:
  title    h1.page-header, fallback meta[property=og:title]
  date     div.dateline — "EEEE, d MMMM yyyy" (start of day UTC, as in Java)
  content  div.field-items div.field-item.even[property=content:encoded],
           skipping text inside <li> (Java filtered li-nested elements);
           fallback: article p
  author   article .field-name-field-source...term-reference a
  cats     breadcrumb <li>s (".breadcrumb li" — live pages have no
           .breadcrumb-wrapper ancestor any more), fallback: URL path
           segments before the hyphenated slug
Deviation: content is paragraph-joined via base.clean_text ("\n\n") instead
of Jsoup's single space-joined text() blob (house style for the ports).

The Java service needed a proxy for ODT (server IP was blocked); direct
connection works from this runtime — if 403/429s appear, wire
ingestion/proxies.py in at the runner level.
"""
from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup

from . import base

SOURCE = "odt.co.nz"
FEEDS = ["https://www.odt.co.nz/rss.xml"]  # unusable — see docstring; discover() is used

# moved 2026-07-25 (old /sitemap.xml now 404s; robots.txt names the new pair —
# the rurallife index is a separate masthead and is not walked here)
SITEMAP_INDEX = "https://www.odt.co.nz/sitemaps/odt/sitemap_index.xml"
_SM = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
_ROOTS = {"https://www.odt.co.nz/", "https://www.odt.co.nz"}
# only surface urls modified within this window as discovery candidates
# (base.run_source narrows further via its own `since`); bounds candidate volume
_RECENT_DAYS = 21

_CONTENT_SEL = 'div.field-items div.field-item.even[property="content:encoded"]'
_AUTHOR_SEL = ("article .field.field-name-field-source."
               "field-type-taxonomy-term-reference.field-label-hidden a")


def _text(el) -> str:
    """Jsoup Element.text() equivalent: whitespace-collapsed, trimmed."""
    return " ".join(el.get_text().split()) if el is not None else ""


def _parse_date(dateline: str) -> datetime | None:
    """"Thursday, 3 February 2022" → start of day UTC (OdtContentScraper)."""
    s = " ".join((dateline or "").split())
    try:
        return datetime.strptime(s, "%A, %d %B %Y").replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _categories_from_url(url: str) -> list[str]:
    """Path segments before the hyphenated slug
    (OdtSitemapParser.ArticleLink.extractCategoriesFromUrl)."""
    path = re.sub(r"^https?://[^/]+/", "", url or "")
    parts = [p for p in path.split("/") if p]
    cats: list[str] = []
    for part in parts:
        if "-" in part and parts and parts[-1] == part:
            break
        cats.append(part)
    return cats


def _sitemap_lastmod(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def discover(client) -> list[base.FeedItem]:
    """Scan every child sitemap page, keep recent-lastmod article urls,
    newest first (see module docstring for why paging can't be short-cut)."""
    try:
        index = (await base.fetch(client, SITEMAP_INDEX)).text
    except Exception as e:  # noqa: BLE001
        print(f"  sitemap index error: {type(e).__name__}: {e}")
        return []
    pages = [loc.text.strip() for loc in ET.fromstring(index.encode()).iter(_SM + "loc")
             if loc.text and loc.text.strip()]

    cutoff = datetime.now(timezone.utc) - timedelta(days=_RECENT_DAYS)
    items: list[base.FeedItem] = []
    for page in pages:
        await asyncio.sleep(base.POLITE_SLEEP)
        try:
            root = ET.fromstring((await base.fetch(client, page)).text.encode())
        except Exception as e:  # noqa: BLE001
            print(f"  sitemap page error {page}: {type(e).__name__}: {e}")
            continue
        for u in root.iter(_SM + "url"):
            loc = (u.findtext(_SM + "loc") or "").strip()
            if not loc or loc in _ROOTS:
                continue
            lastmod = _sitemap_lastmod(u.findtext(_SM + "lastmod"))
            if lastmod is None or lastmod < cutoff:
                continue
            items.append(base.FeedItem(
                url=loc, published_at=lastmod,
                category=(_categories_from_url(loc) or [None])[0]))
    items.sort(key=lambda i: i.published_at or datetime.min.replace(
        tzinfo=timezone.utc), reverse=True)
    return items


def extract(html: str, url: str) -> base.Extracted | None:
    soup = BeautifulSoup(html, "html.parser")

    title = _text(soup.select_one("h1.page-header"))
    if not title:
        og = soup.select_one('meta[property="og:title"]')
        title = (og.get("content") or "").strip() if og else ""

    published_at = None
    dateline = _text(soup.select_one("div.dateline"))
    if dateline:
        published_at = _parse_date(dateline)

    # content: the content:encoded container, minus anything nested in <li>
    parts: list[str] = []
    container = soup.select_one(_CONTENT_SEL)
    if container is not None:
        for el in container.find_all(["p", "h2", "h3"]):
            if el.find_parent("li") is None:
                parts.append(_text(el))
        if not any(parts):  # bare-text container without <p> wrappers
            parts = [_text(container)]
    if not any(parts):  # Java fallback: article p
        parts = [_text(p) for p in soup.select("article p")]
    text = base.clean_text(parts)
    if not text:
        return None

    author = None
    author_el = soup.select_one(_AUTHOR_SEL)
    if author_el is not None:
        author = _text(author_el) or None

    categories = [_text(li) for li in soup.select(".breadcrumb li")]
    categories = [c for c in categories if c]
    if not categories:
        categories = _categories_from_url(url)

    return base.Extracted(title=title, text=text, author=author,
                          published_at=published_at, categories=categories)
