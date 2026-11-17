"""newsroom.co.nz — port of the Java Newsroom scraper
(ops/scraper-service-standalone .../scraper/newsroom/).

Discovery: single RSS feed (NewsroomRssScraper). RSS is the ONLY discovery
mechanism in the Java design — sitemap crawling was considered and dropped
because Newsroom is subscriber-gated and aggressive crawling risks the
session being blocked.

Content parsing follows NewsroomContentScraper selectors exactly:
title "h1.entry-title.entry-title--with-subtitle" (space-normalised);
date "time.entry-date.published[datetime]" (ISO offset); author
"span.author.vcard a" (profile href not kept — Extracted has no field);
categories "span.cat-links" text lowercased, "posted in" removed,
comma-split. Content is the RAW textContent of "div.entry-content"
(deliberately NOT clean_text/paragraph-joined — the golden samples store
Playwright textContent verbatim, whitespace and all). Articles categorised
"puzzles" return None (Java stored a "content skipped" placeholder row);
likewise the Java "Text content not found" author-only placeholder becomes
None here — a metadata-only stub is not a landable document.

AUTH: in the Java service login was performed ONCE manually in a browser and
the Playwright storageState (cookies + localStorage) was persisted to the DB
by BrowserService and restored per run — login was never automated. The port
keeps that shape: fetch_authenticated() restores a storage-state JSON file
(env NEWSROOM_STORAGE_STATE) and requires NEWSROOM_EMAIL/NEWSROOM_PASSWORD
(the session's identity, same names as docker/.env.example) — it raises a
clear error when unconfigured. base.run_source's plain-httpx path still
yields the non-gated articles.
"""
from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime

from bs4 import BeautifulSoup

from . import base

SOURCE = "newsroom.co.nz"
FEEDS = ["https://www.newsroom.co.nz/feed/rss"]

_TITLE_SEL = "h1.entry-title.entry-title--with-subtitle"
_CONTENT_SEL = "div.entry-content"
_DATE_SEL = "time.entry-date.published"
_AUTHOR_SEL = "span.author.vcard a"
_CATEGORY_SEL = "span.cat-links"

# Java clearIframes() — regex over the *text*, kept for parity (no-op on
# textContent, meaningful if extract() is ever fed markup-bearing strings).
_IFRAME_RE = re.compile(r"(?s)<iframe[^>]*>.*?</iframe>")


class _AllTags(frozenset):
    """bs4 >= 4.13 collapses whitespace-only text nodes to a single \\n unless
    the parent tag is in preserve_whitespace_tags. The goldens store Playwright
    textContent() verbatim (tabs/newlines intact), so preserve everywhere."""

    def __contains__(self, item) -> bool:  # noqa: D105
        return True


def extract(html: str, url: str) -> base.Extracted | None:
    soup = BeautifulSoup(html, "html.parser", preserve_whitespace_tags=_AllTags())

    # Categories first (Java order): textContent of span.cat-links is
    # "Posted inForeign Affairs" -> lowercase, strip "posted in", comma-split.
    categories: list[str] = []
    cat_el = soup.select_one(_CATEGORY_SEL)
    if cat_el is not None:
        cat_text = cat_el.get_text().lower().replace("posted in", "").strip()
        categories = [c.strip() for c in cat_text.split(",") if c.strip()]

    if any(c == "puzzles" for c in categories):
        return None  # Java: "Puzzles article - content skipped" placeholder

    author = None
    author_el = soup.select_one(_AUTHOR_SEL)
    if author_el is not None:
        author = author_el.get_text().strip() or None

    content_el = soup.select_one(_CONTENT_SEL)
    title_el = soup.select_one(_TITLE_SEL)
    if content_el is None or title_el is None:
        # Java stored "Text content not found" when an author was present;
        # nothing landable either way.
        return None

    text = _IFRAME_RE.sub("", content_el.get_text()).strip()
    if not text:
        return None
    title = " ".join(title_el.get_text().split())  # StringUtils.normalizeSpace

    published_at: datetime | None = None
    date_el = soup.select_one(_DATE_SEL)
    if date_el is not None and date_el.get("datetime"):
        try:
            published_at = datetime.fromisoformat(
                date_el["datetime"].strip().replace("Z", "+00:00"))
        except ValueError:
            published_at = None

    return base.Extracted(title=title, text=text, author=author,
                          published_at=published_at, categories=categories)


# --------------------------------------------------------------------------
# Authenticated fetch (BLOCKED without a manually captured subscriber session)
# --------------------------------------------------------------------------

def _credentials() -> tuple[str, str]:
    email = os.environ.get("NEWSROOM_EMAIL")
    password = os.environ.get("NEWSROOM_PASSWORD")
    if not email or not password:
        raise RuntimeError(
            "newsroom credentials not configured: set NEWSROOM_EMAIL and "
            "NEWSROOM_PASSWORD (names as in ops/scraper-service-standalone/"
            "docker/.env.example)")
    return email, password


def _storage_state_path() -> str:
    path = os.environ.get("NEWSROOM_STORAGE_STATE")
    if not path or not os.path.exists(path):
        raise RuntimeError(
            "newsroom session not available: NEWSROOM_STORAGE_STATE must "
            "point to a Playwright storage-state JSON captured from a manual "
            "login (the Java BrowserService persisted this state in its DB; "
            "login was never automated)")
    return path


async def fetch_authenticated(urls: list[str], *,
                              headless: bool | None = None) -> list[tuple[str, str]]:
    """Fetch article pages with the restored subscriber session.

    Port of BrowserService.withBrowserPage(): restore storageState, navigate
    with retries, return (url, rendered html) pairs. Requires playwright and
    a captured session — raises RuntimeError otherwise.
    """
    _credentials()
    state = _storage_state_path()
    if headless is None:
        headless = os.environ.get("NEWSROOM_HEADLESS", "true").lower() != "false"

    from playwright.async_api import async_playwright  # lazy — optional dep

    out: list[tuple[str, str]] = []
    import proxies   # the ONE proxy helper (C207): opt-in, None unless a heavy run asks
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless,
                                           proxy=proxies.playwright_proxy("newsroom"))
        context = await browser.new_context(storage_state=state)
        page = await context.new_page()
        for url in urls:
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            out.append((url, await page.content()))
            await asyncio.sleep(base.POLITE_SLEEP)
        await browser.close()
    return out


# B11 ruling 28 (2026-08-24, ARCHIVE_SURVEY_2026-08-24): 16 sub-sitemaps back to 2023-11 (corpus floor 2025-11); gentle by design — subscriber-gated site.
# Walked by newsscrapers.backwalk (resumable, oldest sub-sitemap first).
ARCHIVE = {
    "index": "https://newsroom.co.nz/sitemap.xml",
    "sitemap_re": r"/post-sitemap",
    "polite": 10.0,
}
