owns: schema `news_private` (`articles`: one row per article address from the old estate's copy and the provider, the longer text kept, `held_by` naming each source; regenerable. `provider_read` and `old_taken`: ledgers, never wiped) and schema `news` (`sites`: each site's move, rebuilt every load; `retirements`: each site whose old collection was stopped, never wiped); `registers/news/extract`: the old estate's news parsers, `extract(html, url)` is all the load calls, carried over on 17 November 2026; base.py keeps no client and no fetch, so the old discovery functions some modules still hold cannot fetch
reads: `old_incoming_news_private.articles` (support.oldcopy's copy of the old estate's `incoming_news.articles`, while the old collection runs); the ingest MCP's `estate-news` pages, landed whole by `qv4-mcp-pull` (`mcpsource.files`, the document store); and, for the sites the new estate takes by a lane of its own (Arthur, 18 November 2026), `beehive.releases` (origin `mcp` only) and `gazette.notices` (DigitalNZ's only, never the old export's), counted as the new estate's copy of beehive.govt.nz and gazette.govt.nz; fetches nothing
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
   were disabled on 11 November. There is no per-site switch but that status field. A ready site the registry does not hold (the Gazette, collected by the old estate's own `ingestion/gazette` program) is not listed or logged; the load reports it under "outside the registry" for Arthur.

### A site held in another collection (Arthur, 20 November 2026)

"count as new copy but check it is the same as the copy it is replaceing". The provider named 38 old-only sites it
holds outside estate-news (courts, council minutes, Hansard, disclosure statements, the Electoral Commission,
estate-media; `load.ELSEWHERE`). Its word moves nothing: such a site is `ready` only when the new estate holds,
outside estate-news (`load.ELSEWHERE_SOURCES`: every provider record of another corpus and the lanes' own tables),
every address the old copy holds for it. Until then it is `held elsewhere, gap`, with the count missing. On 20
November 9 were ready and 29 not.

## Comments (Arthur, 18 November 2026)

"we want all comments and we want to efficiently link them to both the articles and also the user"; "start with the
sites we already have. build the schema and ask the mcp to update their capture process to capture the comments
going forward. dont worry about backwalking at this stage". Linking a commenter across sites or to a known person is
"a secondary processing question": not built.

- `news_private.comments`: one row per (site, comment id), read from the provider's pages by extract/wpcomments.py
  (WordPress markup: kiwiblog, thestandard, newsroom, baybuzz). `url_key` joins `news_private.articles`;
  `commenter_key` joins `news_private.commenters`; `parent_id` is the comment replied to. A comment a later capture
  of the article no longer shows gets `absent_since`; an edited text is a new `comment_versions` line.
- `news_private.commenters`: rebuilt every load. `key_kind` is `site user` (the site's own `comment-author-<slug>`
  mark), `profile link`, or `display name` (two people may share one).
- `news_private.comment_read`: every page read for comments. Each `qv4-news-load` reads the new pages.
- Sites whose comments load after the page opens (nzherald, stuff, rnz, the Spinoff's Coral) hold none in the
  provider's pages; the provider was asked to capture them going forward (`estate-news-comments@2026-11-18`).

## The first read (Arthur, 25 November 2026)

"I'd like to read the media corpora and extract signal from them"; "let's not apply these rules to tranche 8. I want
to judge liberally, but let's apply these rules to the first read we do."

- `registers.news.read`: one article a piece of `qv4-news-read` (text-reader profile), newest first, in the golden
  sample's four passes with the trial's prompts unchanged (registers.news.gold.trial: the read, quotes, claims, tones).
  The reading is stored ungated in the reader store by the hash of the masked text and replayed from there; a brief
  (under 300 characters), a page ending on a paywall prompt and one over 50,000 characters are not read.
- `registers.news.gates`: one gate per kind, no model call; every item lands in `news_private.read_items` kept or not,
  with the rule. Quotes: the speaker named within 250 characters and not a document (a document's words are a
  citation). Roles: a title word, no "of" or possessive, no leading descriptor. Claims: the claimant and a verb of
  saying or finding in the span's own sentence, the writer's own claims passing. Tones: four words of evidence.
- `news_private.read_done`: one row per article read, naming the stored reading; never wiped. `read_items`: rewritten
  from the store by `--regate` whenever the gates change.
- Measured by `python -m registers.news.gold.gates_check` on Arthur's judged answers of tranches 2-7. The golden
  sample's tranches are never gated.
- Queued by hand on Arthur's word only; no timer queues it.
