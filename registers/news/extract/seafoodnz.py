"""seafood.co.nz — Seafood New Zealand, the fisheries industry body's own wire
(trade-press wave tier 1, 2026-07-25). Quota decisions, company moves, sector
appointments — directly fattens the thin Fisheries paper. seafood.org.nz 302s
here, so this one module covers both names in the todo.

TYPO3 (tx_news extension), no RSS: discovery scrapes /news-and-events/news
listing pages (first two — the wire is low-cadence) for /detail/ links. The
"in-the-media" section is reposted external coverage and is deliberately
skipped (originals arrive via their own outlets' scrapers). Articles carry
clean schema.org markup: h1[itemprop=headline], time[itemprop=datePublished],
div[itemprop=articleBody]. robots blocks only /fileadmin /uploads /typo3.
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from . import base

SOURCE = "seafood.co.nz"
_HOME = "https://www.seafood.co.nz"
_LIST = _HOME + "/news-and-events/news"
_DETAIL = re.compile(r"/news-and-events/news/detail/[^\"'#?]+")
# TYPO3 pagination widget links carry the page number + a cHash we must keep
_PAGE2 = re.compile(r'href="(/news-and-events/news\?tx_news[^"]*currentPage%5D=2[^"]*)"')


async def discover(client) -> list[base.FeedItem]:
    first = (await base.fetch(client, _LIST)).text
    urls = {_HOME + m for m in _DETAIL.findall(first)}
    p2 = _PAGE2.search(first)
    if p2:
        await asyncio.sleep(0.3)
        try:
            page2 = (await base.fetch(client, _HOME + p2.group(1).replace("&amp;", "&"))).text
            urls |= {_HOME + m for m in _DETAIL.findall(page2)}
        except Exception as e:  # noqa: BLE001
            print(f"  seafoodnz page-2 error: {type(e).__name__}: {e}")
    return [base.FeedItem(url=u) for u in sorted(urls)]


def extract(html: str, url: str) -> base.Extracted | None:
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.select_one("h1[itemprop=headline]")
    body_el = soup.select_one("[itemprop=articleBody]")
    if title_el is None or body_el is None:
        return None
    title = " ".join(title_el.get_text().split())
    paras = [" ".join(p.get_text().split()) for p in body_el.find_all("p")]
    text = "\n\n".join(p for p in paras if p)
    if not title or len(text) < 200:
        return None
    published = None
    time_el = soup.select_one("time[itemprop=datePublished]")
    if time_el and time_el.get("datetime"):
        try:
            published = datetime.fromisoformat(time_el["datetime"]).replace(
                tzinfo=timezone.utc)
        except ValueError:
            pass
    return base.Extracted(title=title, text=text, author=None,
                          published_at=published, categories=[])
