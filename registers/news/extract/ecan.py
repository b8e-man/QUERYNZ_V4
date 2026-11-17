"""ecan.govt.nz — Environment Canterbury (Canterbury regional council):
consents, flood/water management, public transport decisions. The ONLY
council of 16 probed with an RSS feed (/news/rss); the rest serve bot-wall
stubs and are deferred as a class. Open robots. Generic RSS."""
from __future__ import annotations
from . import genericrss
SOURCE = "ecan.govt.nz"
discover = genericrss.make_discover("https://www.ecan.govt.nz/news/rss")
extract = genericrss.extract
