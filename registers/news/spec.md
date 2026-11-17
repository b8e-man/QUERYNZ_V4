owns: schema `news_private` (`articles`: one row per article address from the old estate's copy and the provider, the longer text kept, `held_by` naming each source; regenerable. `provider_read` and `old_taken`: ledgers, never wiped) and schema `news` (`sites`: each site's move, rebuilt every load; `retirements`: each site whose old collection was stopped, never wiped); `registers/news/extract`: the old estate's news parsers, `extract(html, url)` is all the load calls, carried over on 17 November 2026; base.py keeps no client and no fetch, so the old discovery functions some modules still hold cannot fetch
reads: `old_incoming_news_private.articles` (support.oldcopy's copy of the old estate's `incoming_news.articles`, while the old collection runs); the ingest MCP's `estate-news` pages, landed whole by `qv4-mcp-pull` (`mcpsource.files`, the document store); fetches nothing
publishes: nothing in `pub` yet; article text can print a home address (hard limit 15), so the register stays private until a product applies the limit at its surface
outside check: `news.sites` per host: `ready` only when the provider published from the site in the last 7 days and its earliest article reaches within 2 days of where the old copy stops; every provider page read has a `provider_read` line (read, no text, no parser, failed)
jobs: `qv4-news-load` (queued by each `qv4-mcp-pull`; `python -m registers.news.load --job`)

## The move, site by site (Arthur, 17 November 2026)

"take everything under News, by site (the old estate's copy) and move it into the new estate so we can retire the
old estate"; "go site by site. after the site is migrated and the provider is providing, retire the old".

1. Migrated: the site's old articles are in `news_private.articles` (every load takes the old copy's new rows).
2. Providing: `news.sites.state = 'ready'`.
3. Retired: the old estate's collection is stopped for the site and a `news.retirements` line records how and on
   whose word. In the old estate a site is collected by `querynz-coverage.timer` (`ops/coverage_backwalk.py`), which
   takes every host whose `status` is `ready` in `ingestion/newsscrapers/registry.py`; its `newsscrapers` timers
   were disabled on 11 November. There is no per-site switch but that status field.
