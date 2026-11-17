"""greaterauckland.org.nz — Greater Auckland: transport/urban policy analysis,
agency- and project-dense. robots blocks named AI/search bots but the general
agent is Allow: /. WordPress feed."""
from __future__ import annotations
from . import genericrss
SOURCE = "greaterauckland.org.nz"
discover = genericrss.make_discover("https://www.greaterauckland.org.nz/feed/")
extract = genericrss.extract


# B11 ruling 28 (2026-08-24, ARCHIVE_SURVEY_2026-08-24): 38 sub-sitemaps back to 2011; robots Crawl-delay 30.
# Walked by newsscrapers.backwalk (resumable, oldest sub-sitemap first).
ARCHIVE = {
    "index": "https://www.greaterauckland.org.nz/sitemap.xml",
    "sitemap_re": r"/post-sitemap",
    "polite": 30.0,
}
POLITE_SLEEP = 30.0   # robots Crawl-delay, binds article fetches too
