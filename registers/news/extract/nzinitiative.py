"""nzinitiative.org.nz — The New Zealand Initiative (research-sector wave,
2026-07-25). Opinion/media/reports name its economists, ministers, and
policy targets. SilverStripe, /rss 404: listing discovery over the
reports-and-media hub."""
from __future__ import annotations
from . import genericrss
SOURCE = "nzinitiative.org.nz"
discover = genericrss.make_listing_discover(
    "https://www.nzinitiative.org.nz/reports-and-media/",
    r'href="(/reports-and-media/[a-z-]+/[^"?#]+/)"',
    "https://www.nzinitiative.org.nz")
extract = genericrss.extract
