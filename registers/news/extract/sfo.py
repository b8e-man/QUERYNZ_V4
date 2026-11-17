"""sfo.govt.nz — Serious Fraud Office media releases: fraud/corruption
prosecutions, guilty pleas, sentencings — maximum register density per word.
Official source, open robots (CMS internals only). The media-releases listing
renders its items client-side, so discovery AND articles go through the
headless browser (same shape as mpi). Names charged persons: capture rides the
news path; person-link DISPLAY is governed by the compliance gates."""
from __future__ import annotations

import re
from urllib.parse import urljoin

from . import base, genericrss

SOURCE = "sfo.govt.nz"
_LIST = "https://www.sfo.govt.nz/media-cases/media-releases"
_ART = re.compile(r"/media-cases/media-releases/[a-z0-9-]{8,}")
_SETTLE_MS = 5000


async def discover(client) -> list[base.FeedItem]:
    from . import browserfetch
    pairs = await browserfetch.render_all([_LIST], settle_ms=_SETTLE_MS)
    if not pairs:
        return []
    urls = sorted({urljoin(_LIST, m) for m in _ART.findall(pairs[0][1])})
    return [base.FeedItem(url=u) for u in urls]


async def fetch_all(urls: list[str]) -> list[tuple[str, str]]:
    from . import browserfetch
    return await browserfetch.render_all(urls, settle_ms=_SETTLE_MS)


extract = genericrss.extract
