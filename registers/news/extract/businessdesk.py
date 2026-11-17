"""businessdesk.co.nz — port of the Java Businessdesk scraper
(ops/scraper-service-standalone .../scraper/businessdesk/). Paywalled; the
Java scraper was DISABLED at the client's request because automated login
stopped working (suspected added CAPTCHA / device fingerprinting).

Discovery: sitemap-based (SitemapParser). discover() fetches
https://businessdesk.co.nz/index-sitemap.xml, keeps the monthly
"articles-sitemap-YYYYMM" child sitemaps for the last _MONTHS_TO_SCAN months
(the Java incremental mode fetched only months covering [newest-in-DB ..
today]; run_source's hours-window replaces the DB high-watermark), and reads
loc + lastmod per entry (both required, as in Java).

Content parsing follows BusinessdeskScraper.collectInnerInfo(): article
container "div.row.individual-story" with "section div.row" fallback; title
".article-title" (fallback: the URL string, as Java did); content
".article-body"; date ".story-date" via RFC-1123 — with " 00:00:00 GMT"
appended when the text has no time — else ISO offset; categories the
".d-flex.justify-content-between" breadcrumb split on "/" and de-duplicated;
author ".author-name a" (profile href not kept — Extracted has no field).
Deviation: content is paragraph-joined via base.clean_text instead of raw
textContent (no goldens pin the shape). Java's per-field try/catch +
partial-save becomes: container or body missing -> None; everything else
best-effort.

AUTH (BLOCKED — and known-broken even in Java): login flow ported from
performSignIn()/signInPage(): open the site, check #navbarNav for
"My Account", else the /login page — input[name=email], input[name=password],
#set-remember checkbox, button[type=submit] (Java typed human-like to dodge
bot detection). Credentials from BUSINESSDESK_EMAIL / BUSINESSDESK_PASSWORD
(names as in docker/.env.example); a clear error is raised when unset.
"""
from __future__ import annotations

import asyncio
import email.utils
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from . import base

SOURCE = "businessdesk.co.nz"
FEEDS: list[str] = []  # sitemap discovery — see discover()

BASE_URL = "https://businessdesk.co.nz"
SITEMAP_INDEX = "https://businessdesk.co.nz/index-sitemap.xml"
_MONTHS_TO_SCAN = 2
_SM = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

_LOGIN_URL = (BASE_URL + "/login?redirect_uri=https%3A%2F%2Fbusinessdesk.co.nz"
              "%2Farticle%2Ftechnology%2Frocket-lab-at-20-from-pipe-dream-to-"
              "50-billion-space-empire")


def _text(el) -> str:
    """Jsoup Element.text() equivalent: whitespace-collapsed, trimmed."""
    return " ".join(el.get_text().split()) if el is not None else ""


# --------------------------------------------------------------------------
# Discovery (SitemapParser)
# --------------------------------------------------------------------------

def _recent_month_tokens(n: int) -> list[str]:
    """['articles-sitemap-YYYYMM', ...] for the current and previous months."""
    now = datetime.now(timezone.utc)
    year, month = now.year, now.month
    out = []
    for _ in range(n):
        out.append(f"articles-sitemap-{year:04d}{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return out


def _lastmod(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def discover(client) -> list[base.FeedItem]:
    """index-sitemap -> monthly articles-sitemap-YYYYMM -> urls + lastmod."""
    index_xml = (await base.fetch(client, SITEMAP_INDEX)).text
    root = ET.fromstring(index_xml.encode())
    monthly = [(loc.text or "").strip()
               for sm in root.iter(_SM + "sitemap")
               for loc in sm.iter(_SM + "loc")
               if loc.text and "articles-sitemap-" in loc.text]
    wanted = _recent_month_tokens(_MONTHS_TO_SCAN)
    monthly = [u for u in monthly if any(tok in u for tok in wanted)]

    items: list[base.FeedItem] = []
    for sm_url in monthly:
        await asyncio.sleep(base.POLITE_SLEEP)
        try:
            page = ET.fromstring((await base.fetch(client, sm_url)).text.encode())
        except Exception as e:  # noqa: BLE001
            print(f"  sitemap error {sm_url}: {type(e).__name__}: {e}")
            continue
        for u in page.iter(_SM + "url"):
            loc = (u.findtext(_SM + "loc") or "").strip()
            lastmod = _lastmod(u.findtext(_SM + "lastmod"))
            if loc and lastmod is not None:  # Java requires both loc and lastmod
                items.append(base.FeedItem(url=loc, published_at=lastmod))
    items.sort(key=lambda i: i.published_at, reverse=True)  # newest-first
    return items


# --------------------------------------------------------------------------
# Extraction (BusinessdeskScraper.collectInnerInfo)
# --------------------------------------------------------------------------

def parse_article_date(date_str: str | None) -> datetime | None:
    """Port of BusinessdeskScraper.parseArticleDate: RFC-1123 (appending
    " 00:00:00 GMT" when the text carries no time) with ISO-offset fallback."""
    s = (date_str or "").strip()
    if not s:
        return None
    if ":" not in s:
        s += " 00:00:00 GMT"
    try:
        return email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None


#: the site's own note above every premium body; the body under it is whole when fetched under the session
_PREMIUM_NOTE = re.compile(r"^Reminder, this is a Premium article", re.I)


def _extract_arc(soup, html: str, url: str) -> base.Extracted | None:
    """The site's current (Arc) layout, read 18 November 2026: the body is the `section.article__body` blocks."""
    parts = []
    for sec in soup.select("section.article__body"):
        for p in sec.find_all(["p", "h2", "h3", "li"]):
            t = _text(p)
            if t and not _PREMIUM_NOTE.match(t):
                parts.append(t)
    text = base.clean_text(parts)
    if not text:
        return None
    og = soup.find("meta", property="og:title")
    title = (og.get("content") if og else None) or _text(soup.find("h1")) or url
    m = re.search(r'"(?:display_date|displayDate|publish_date|datePublished|first_publish_date)"\s*:\s*"([^"]+)"', html)
    published_at = None
    if m:
        try:
            published_at = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
        except ValueError:
            pass
    m = re.search(r'"credits"\s*:\s*\{\s*"by"\s*:\s*\[\s*\{[^{}]*?"name"\s*:\s*"([^"]+)"', html)
    return base.Extracted(title=title, text=text, author=m.group(1) if m else None, published_at=published_at,
                          categories=[])


def extract(html: str, url: str) -> base.Extracted | None:
    soup = BeautifulSoup(html, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")

    if soup.select_one("section.article__body"):
        return _extract_arc(soup, html, url)
    article = (soup.select_one("div.row.individual-story")
               or soup.select_one("section div.row"))
    if article is None:
        return None  # Java: "Article container not found"

    body = soup.select_one(".article-body")
    if body is None:
        return None  # Java: "Article body not found" (paywall wall page)
    parts = [_text(p) for p in body.find_all(["p", "h2", "h3", "li"])]
    text = base.clean_text(parts) or _text(body)
    if not text:
        return None

    title = _text(soup.select_one(".article-title")) or url  # Java fallback: URL

    published_at = parse_article_date(_text(soup.select_one(".story-date")))

    categories: list[str] = []
    crumb = soup.select_one(".d-flex.justify-content-between")
    if crumb is not None:
        seen: set[str] = set()
        for c in _text(crumb).split("/"):
            c = c.strip()
            if c and c not in seen:
                seen.add(c)
                categories.append(c)

    author_el = soup.select_one(".author-name a")
    author = (_text(author_el) or None) if author_el is not None else None

    return base.Extracted(title=title, text=text, author=author,
                          published_at=published_at, categories=categories)


# --------------------------------------------------------------------------
# Authenticated fetch (BLOCKED — login was broken even in the Java service)
# --------------------------------------------------------------------------

def _credentials() -> tuple[str, str]:
    em = os.environ.get("BUSINESSDESK_EMAIL")
    pw = os.environ.get("BUSINESSDESK_PASSWORD")
    if not em or not pw:
        raise RuntimeError(
            "businessdesk credentials not configured: set BUSINESSDESK_EMAIL "
            "and BUSINESSDESK_PASSWORD (names as in ops/scraper-service-"
            "standalone/docker/.env.example)")
    return em, pw


async def _perform_sign_in(page) -> None:
    """Port of performSignIn(): /login form fill + Remember Me + submit.
    Java typed human-like (per-char delay) to dodge bot detection."""
    em, pw = _credentials()
    await page.goto(_LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)
    await page.wait_for_selector("input[name='email']", timeout=10_000)
    await page.type("input[name='email']", em, delay=120)
    await page.type("input[name='password']", pw, delay=120)
    remember = await page.query_selector("#set-remember")
    if remember is not None and not await remember.is_checked():
        await remember.click()
    await page.click("button[type='submit']")


async def _sign_in_if_needed(page) -> None:
    """Port of signInPage(): #navbarNav must contain "My Account" once
    authenticated; otherwise run the login flow."""
    await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60_000)
    navbar = await page.wait_for_selector("#navbarNav", timeout=10_000)
    nav_text = (await navbar.text_content()) or ""
    if "my account" not in nav_text.lower():
        await _perform_sign_in(page)


async def fetch_all(urls: list[str]) -> list[tuple[str, str]]:
    """run_source's auth hook — one signed-in browser context for the batch."""
    return await fetch_authenticated(urls)


async def fetch_authenticated(urls: list[str], *,
                              headless: bool | None = None) -> list[tuple[str, str]]:
    """Sign in (if needed) then fetch article pages, returning (url, html).
    NOTE: automated login is the reason the Java scraper was shelved — expect
    this to need a manually captured session or CAPTCHA solving.
    """
    _credentials()  # fail fast with a clear error before launching a browser
    if headless is None:
        headless = os.environ.get("BUSINESSDESK_HEADLESS", "true").lower() != "false"

    from playwright.async_api import async_playwright  # lazy — optional dep

    out: list[tuple[str, str]] = []
    import proxies   # the ONE proxy helper (C207): opt-in, None unless a heavy run asks
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless,
                                           proxy=proxies.playwright_proxy("businessdesk"))
        page = await browser.new_page()
        await _sign_in_if_needed(page)
        for url in urls:
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            out.append((url, await page.content()))
            await asyncio.sleep(base.POLITE_SLEEP)
        await browser.close()
    return out
