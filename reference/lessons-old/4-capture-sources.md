> Part of [LESSONS](../LESSONS.md) — living memory, one section per file
> since 2026-10-04 so that "read the relevant section" is a thing a reader
> can do. The rules of the file, and why it exists, are in LESSONS.md.

## 4. Capture & sources

- **A blinder has to cover what you go and ASK for, not only what you
  publish.** *Paid for by:* 2026-09-27, C168. Ruling 347 put the window at
  2019 and every surface obeyed it. The EC results gatherer's `YEARS` tuple
  began `(2017, 2020, 2023)`, and because its queue walks the years in order,
  **every request it had ever made — three attempts, three walls, nine hours
  of cooling — went to `electionresults_2017/`**, an election that does not
  exist for this use case. The blinder was real and the work was outside it.
  Sibling of *a constant the work cannot reach is a constant the work will not
  obey* (§3).

- **A CLIENT THAT PARSES A RECORD AND DROPS A FIELD MAKES THE FIELD LOOK
  ABSENT FROM THE SOURCE — AND TO TELL A PERSONAL FIELD FROM A SHARED ONE,
  COMPARE IT ACROSS THE PEOPLE ON THE SAME RECORD.** C180, 2026-10-10. The
  day-log had it written down as a fact about the world: *"What is NOT held is
  any director residential address — no register table carries one — so the
  filed donor address cannot be corroborated."* True of our TABLES, and the
  NZBN v5 API had carried it all along. `nzbn_canonical`'s `directors_from`
  reads `roles[].rolePerson` for first/middle/last and never looks at
  `roles[].roleAddress`, which is the sibling key — so a parser's scope became
  a claim about the register, and a card was raised to collect what one `GET`
  already returned.
  **THE FIELD IS ON THE ROLE, NOT THE PERSON**, which is why looking in the
  obvious place found nothing: `rolePerson` holds only
  `firstName / middleNames / lastName / title`.
  **AND IS IT THE DIRECTOR'S OWN ADDRESS OR THE COMPANY'S?** That decides
  whether the axis is worth anything, and the test is one call: on
  `FAIRVIEW METAL INDUSTRIES LIMITED` seven directors have **seven DISTINCT
  `roleAddress` values and not one equals an entity address** (registered
  office or postal). A shared value would have meant the office under another
  name. Compare across the people on the record before building on the field.
  Measured end to end: 11 directorships from our own register, 12 addresses
  collected, 2 distinct street keys, and both filed rows for the $500,000
  donation match by `street_key` equality.
  **EVIDENCE IS NOT A CARRYING ARM.** Ruling 221 named two legs that may CARRY
  a person's identity, and its `address` leg is *"an address of a COMPANY the
  identity directs"* — the office. A director's own address is a different and
  stronger axis, so making it carry amends 221 and is a ruling, not a
  refactor (#c20929). Collect the axis, prove the fold, leave the arm alone.

- **A URL is not a document identity, and the corpus never said it was.**
  `articles` is unique on `upstream_id` — the capture — not on `news_url`. So
  one URL legitimately holds many rows, and a consumer that assumes 1:1 has
  made an assumption the store does not enforce and cannot enforce for it.
  The fix belongs in the consumer, never in the corpus: a global
  "collapse by URL" would be WRONG.
  *Paid for by:* 2026-09-21, and the counter-example is the proof. Corpus-wide
  3,672 rows exceed distinct URLs (0.05%), concentrated in four hosts, and
  they are not the same thing at all: `hansard.parliament.nz` has 2,322 rows
  over 110 URLs because one sitting day is captured as its 71 separate
  debates — correct, deliberate, and destroyed by any URL-level dedupe.
  `gazette.govt.nz` has 1,328 because one notice was captured twice. Same
  arithmetic, opposite meanings. Ask what the source calls a document before
  deciding what a duplicate is.

- **Robots is the permission surface: read the BLOCKS, don't count them — and
  the unlock is always a permission ask, never evasion.** An honest UA that
  matches no named block falls under `*`; never let a fetch fall back to a
  default UA that IS named-and-blocked. A permissive reading must be retreated
  from when neighbouring evidence contradicts it. "Unreadable robots.txt" is
  two different facts: a 404 means the site publishes no rules (permitted, RFC
  9309) and a 5xx or timeout means the site cannot tell you (refuse). And a
  bot-wall that blocks the headless shell may pass a real headed browser by
  itself — try the honest browser BEFORE calling a wall final.
  *Paid for by:* NZME's robots.txt, whose ~450 `Disallow: /` blocks are every
  one under a NAMED bad-actor/AI bot (ClaudeBot, GPTBot, CCBot, Scrapy,
  Python-urllib…) while `User-agent: *` disallows only /premium/,
  /my-account/, search and query-junk · MOJ's `Disallow: /assets/`, read as
  crawl-budget hygiene, captured ~65 docs until explicit blocking elsewhere on
  the same estate forced the strict re-ruling — sources paused, held docs
  QUARANTINED not purged, one email able to unlock the lot
  (COURTS_PIPELINE.md) · 2026-08-23 (O.1): collapsing the 404 and the 5xx into
  one refusal blocked a sanctioned host for four days · 2026-09-07/08 (the overnight run,
  ruling 243): elections.nz's Incapsula served only its challenge shell to Playwright's
  headless shell AND to Chromium's "new headless" (both announce
  `HeadlessChrome`), while a real headed Chromium on the desktop, with its own
  UA and nothing patched, rendered at once — the ruling-133 class, not evasion:
  no CAPTCHA solved, no UA spoofed, no identity rotated · "Live" is not
  permanent: a source that worked in one batch added a CAPTCHA by the next, and
  a domain's permission status can change with an acquisition
  (coastandcountrynews folded into a licence-blocked owner while its sister
  paper stayed independent) — verify the redirect chain, not just robots.

- **Terms can bar what robots permits, and "LLM-free" is not "ML-free".** When
  a source's terms bar our extraction but robots permits our UA:
  CAPTURE-AND-HOLD — store the documents and run NO model of any kind over
  them until a licence lands. The hold is only real if every model path is
  closed. Occupational registers go further: several carry explicit
  purpose-limitation / anti-scraping terms, so they are verification lookups
  per record at question time, NEVER bulk-scraped — robots-absolutism extends
  to purpose-limitation terms (PGDB plumbers; insolvency practitioners,
  statutory proper-purpose; MCNZ doctors, vetted paid CSV;
  registers-survey-2026-08-18).
  *Paid for by:* 2026-08-24 (ruling 115) — NZME's terms bar use for "LLMs,
  machine learning and/or AI", and our era-4 extractor is LLM-free but runs
  spaCy `en_core_web_lg`/`_sm`, trained statistical models, so it IS machine
  learning; semantic search is ML too, since embeddings come from a trained
  model. "We don't touch it with AI" was wrong on both counts. The extractor
  AND the embedder both exclude `pipeline_status='held'`, and the embedder's
  tier check fail-closes an unknown source, backed by a direct held exclusion
  in its SELECT so a mis-seeded `llm` row cannot leak it.

- **Recon a source before writing its scraper, and look for a metadata API
  before writing a listing scraper at all.** What protects it, whether it has
  its own API, and where its real text floor sits — all three change the plan.
  Try plain HTTP before reaching for a browser (a cost argument, never an
  evasion one). Check the surface a source's ARCHETYPE actually writes to.
  "Can't resolve" is not "down" — retry through the runner, not a shell curl,
  because the sandbox blocks new external hosts.
  *Paid for by:* Hansard returning a WAF page to a plain GET while the site is
  a Blazor app over a clean OData API that enumerates the whole back-catalogue,
  with a text floor of 2003-02-11 and 1854-2002 as scans on foreign hosts · the
  Gazette needing no listing scraper at all, because DigitalNZ's API indexes
  ~205k notices with canonical URLs, anonymously — aggregator APIs (DigitalNZ,
  CKAN, SDMX) often already index the site you were about to crawl · FMA
  reporting "staged 0", someone checking `articles`, finding nothing and
  concluding the run and the restored dump were both broken, when
  `fma_warnings` held the rows all along and the proposed "fix" would have
  duplicated rows on every sweep.

- **Never hand-pick an organisation's pages: capture the whole site from its
  homepage, then read — and a site's NAVIGATION says what a page is, where a
  path census only says what a URL is called.** An implausible absence is a
  prompt to look, not a finding.
  *Paid for by:* ruling 180 (2026-09-04; RESCINDED by 266 on 2026-09-15 —
  the crawl stays the METHOD, admission is no longer a gate; now MO §4
  doctrine) — three selective party-site efforts in one week each missed the
  primary record: the governance-URL census matched press releases and missed
  board pages, the board-page capture list needed Arthur to point at
  national.org.nz/bod, and the frozen constitution list declared TOP had none;
  the first full crawl, 40 pages of the smallest site, held the Women's Rights
  Party's 2025 constitution, a structure-and-roles deck and a policy document
  no list had named (`ops/party_sites_capture.py`: robots per host, paced,
  resumable, fused loudly) · 2026-09-03: the DL-10 census matched governance
  pages by path words against the Wayback URL listing and missed National's
  live board page because the site names it `/bod`, while every page's footer
  link read "Board of Directors" — compounded by me recording "nothing on the
  live site today" instead of opening the site, when a major party with no
  board page in 2026 was implausible enough to check by hand. The probe now
  crawls the homepage and one level of governance-named links by ANCHOR TEXT.

- **A parser is only as good as the page SHAPES it has been measured against
  — when the site is captured and a board still reads empty, open the page and
  read it as a person would.** Dry-run the derive per party, print the live
  rows, and for every one at zero add the shape WITH the page as the test
  fixture. The press tier is no substitute: it cannot tell a campaign chair
  from the board chair (ruling 181).
  *Paid for by:* 2026-09-04, Arthur — "this is something easy for a person to
  do, try another strategy": Labour's 25-seat NZ Council sat on
  labour.org.nz/party-information all day as `Role:` / `Name` pairs, and the
  line parser skipped a 'Policy Council Representative:' line because the
  nav-noise rule saw "policy". Each site had its own shape (Opportunity: name /
  bio / name; ACT: role lines that look like two-token names; NZOFP: 'Name
  (Role)'; ALCP: 'Role Name').

- **A traversal bound is not a population bound: a cap, a streak or a limit
  below the source's own unit will stall silently and read as done.** `--limit`
  must EXCEED the largest sub-sitemap; time-since-last-hit on the wall clock
  survives a sparse patch where no streak threshold does, and a BLOCKED attempt
  is not a miss — the clock measures walking, not waiting. Walk by window, not
  by day, when the source bisects.
  *Paid for by:* 2026-08-24, times.co.nz / stoppress.co.nz have 1000-article
  post-sitemaps and runs at `--limit` 500/800 advanced nothing, because the
  walker marks a sub-sitemap done only when it fetched everything listed, so
  the loop reported "0 sub-sitemaps done" with no error · the daywalker's
  30-empty-day floor, which assumed the dashboard ends at a date when it runs
  to 1840 with a near-empty 1960s–70s in between, and had already falsely
  completed at 1990-12-25 (ruling 23) · handing the client whole years instead
  of windows turned a ~55,000-query walk into a few hundred and banked a
  million articles overnight — the traversal was the bottleneck, never the
  fetch.

- **Measure the corpus against its SOURCE before believing our ingest is
  complete, and prefer a bulk export to re-crawling.** Prove subset/superset by
  a URL diff, not by counts alone; drive completeness from an enumerable
  corpus, because a change feed buys freshness only.
  *Paid for by:* 2026-08-26 (Hetzner recovery) — our Papers Past holding
  (4.65M items) was a strict subset, ~5%, of the 90.65M-item corpus sitting on
  the old news-dashboard backend, and the era-backfill/daywalker had been
  slowly re-fetching what one bulk dump already held · V1 legislation polling a
  recent-changes Atom feed, which could never express repeal status, so it was
  never ingested.

- **Held means a REAL file, checked — never a manifest row or a name.** A bulk
  pull can archive the WALL rather than the document: the Wayback Machine
  archives whatever the origin SERVED its crawler, which for a WAF-fronted site
  can be the challenge page with status 200. Quarantine the shells beside the
  archive, never delete.
  *Paid for by:* 2026-09-07/08 — 35 of the Wayback pull's 71 "2026 disclosure
  PDFs" were the 212-byte challenge page saved under the asset name, and 31
  larger files were cut at exactly 1 MiB; every one had passed as "held" for
  three weeks and OCR read nothing from them · 2026-08-23 (O.1): "91 files
  mostly duplicates" was written without opening the manifest, and 16 were that
  year's >$20k disclosures held nowhere else. **Before asking Arthur for a
  ruling, profile the population the ruling is about.**

- **Every new landing path bypasses source policy unless explicitly enrolled
  — and a status-value guard misses NULL.** Capture is the only irreplaceable
  layer: everything else regenerates from observations plus judgments, which is
  why off-site backup gates walk-away autonomy (terminal Layer 0). No coverage
  without a paired correctness gate — volume without a floor, sum-check or
  zero-violation corpus buys numbers, not truth (the GDELT lesson).
  *Paid for by:* a PDF materialiser that became a third writer into `articles`,
  so its rows arrived with `pipeline_status` NULL, sailed past a guard that
  excluded `for_review` but not NULL, and put 210 OIA responses addressed "Dear
  <requester>" into the graph · the 2026-08-18 cutover reset of
  `pipeline_status`, which took 6,612 dashboard copies of gazette/Hansard from
  parked to captured and got 6,327 extracted as news while the ledger still
  said `for_review` for every one — two tables that must agree, with no
  invariant asserting it, and T7.2 sat red as "pre-existing" for days (→ plan
  B0, ruling 24) · a feed that keys idempotence on a row id the derive
  regenerates is not idempotent: WorkSafe's derive deletes and re-inserts a
  page's rows with a new `row_id` each night, so the feed deleted "its" claims
  by row_id, found none, and emitted a fresh copy of all 144 every night (288
  after two) — page-regenerated registers key their claims on the PAGE ref, and
  the check that would have caught it on day one is claims-per-family ==
  rows-per-family after two runs
  (`register_claims._delete_register_claims_by_ref`) · content-hash dedup is
  blind to a page that changes a nonce: WorkSafe's HTML carried a per-response
  token, so every 3-hourly sweep re-captured every page — 222 documents, 229
  articles, duplicate claims for 142 pages after one day. The unit of identity
  for a DocSource is its REF (`scrapers.docsource.discover(skip_refs)`, with a
  test).

- **A register that records only one of a boolean's two values does not carry
  a boolean, and a feed that TRUNCATES cannot answer about what it never
  held.** Serve the fact and its basis separately; record an honest empty as a
  checked sentinel rather than re-asking; and where a body is not on the
  register at all, abstain by design rather than force it into a
  classification.
  *Paid for by:* 2026-09-03 — the official results we hold record ELECTORATE
  outcomes only, with no list row in any year flagged elected (0 of 4,159), so
  the MP page's first render called Chris Bishop "not elected" in 2014 and
  2020, both years he entered on the list; `elected` is None with its basis
  stated until the list allocation is a held source · 2026-08-26: the Companies
  Office BULK BIC feed is live-register-only and the importer TRUNCATEs on
  every load, so a company removed before our first package (mid-2026) is in
  neither `bulk.companies_business_industry_classification` nor its `_history`
  and never will be — an MP's historic directorships are mostly at removed
  companies, so an NZBN anchor is not enough; the per-NZBN backfill is the NZBN
  API v5, which retains removed entities, and it MUST land in its own durable
  table (the monthly TRUNCATE would wipe it) and be UNIONed at query time · the
  same API does NOT resurrect BIC for old removed companies — of 292
  anchored-org gaps only ~17 yielded a code · Te Ohu Kai Moana, Māori Trust
  Boards, Parliamentary trusts and Crown committees are not on the companies
  register, so a BIC anchor is impossible and a lookalike-company match would
  be a fabrication: their home is the Gazette (statutory/Crown board
  APPOINTMENTS are gazetted) and the Public Service Commission's governance
  lists, classified as a body-TYPE, never an ANZSIC code · party BOARDS are
  knowable only for the parties that are incorporated SOCIETIES — Labour, the
  Greens and Te Pāti Māori give their governing-body officers through the NZBN
  v5 `roles` array, dated and with status, while National, ACT and NZ First are
  not societies and have no board obtainable this way: an honest declared gap,
  never a fabricated roster (the society ENTITIES are in the bulk, the OFFICERS
  are API-only, `ops/backfill_society_officers.py`).

- **Captured text fuses at block boundaries, and OCR reads a form's letters as
  digits — repair conservatively, at capture where you can.** Only reinsert a
  space where the fused tail is one of the source's own function words or a
  Title-Case run follows a known place/verb; a generic lower→upper split breaks
  McGrath and MacLeod. A page-1 total that fails to parse is DERIVED from its
  parts and labelled, not left blank. A text layer is per PAGE: a PDF with
  5,000 chars of auditor's report and image-only schedule pages is a SCAN for
  the pages that matter, so OCR falls back per page, not per file.
  *Paid for by:* the gazette's "appointLance Clifford Rowe, solicitor of
  Wanganuito be" (2026-08-23; the real fix is a re-pull with block separators)
  · "Total (A+C+D+F+6)" and a Part A amount with no "$" (2727334.14) costing
  National three years of totals until the parser accepted them · `--scans`
  keyed on total chars < 200, which never re-read the pages that mattered
  · telling Arthur a `-audited` filing "contains no return" because
  `pdftotext` found no `TOTAL PARTY DONATIONS` in it — page 1 was an IMAGE
  of the declaration and the recogniser read every part off it (C446,
  2026-09-24). On a corpus two thirds of which has no text layer, the
  absence of a phrase in the text layer is evidence of nothing.

- **The sub-threshold band is the biggest block.** For the major parties more
  than half of all declared donations is Part G — money the return states as
  one figure and that no row will ever carry; a size map must draw it as a
  labelled block or it lies by omission.

- **Before carding a reader as unreliable, look at what it was GIVEN.** A model
  asked to pick a total out of a table whose columns have been destroyed is not
  being careless — it cannot see which number belongs to which label, and no
  prompt can repair that. Read the extractor's actual output before blaming the
  thing downstream of it.
  *Paid for by:* 2026-09-22, C407 — Labour's 2026 total assets came back as
  15,822.8, then as 16,027.6 under a prompt that said NEVER compute a figure,
  for a number the document prints as 11,266.0. `pdfpipe/convert.py` runs
  `pdftotext` without `-layout`, so the reader received "Total Assets" alone on
  a line with its number elsewhere in the file. Three cards (C407, C306, C171)
  blamed the reader; one `-layout` flag sat between a 46-document lane and
  every wrong figure in it. Measured after: 3 of 46 reads contradict a printed
  total, one of them reading the PRIOR-YEAR column.

- **Never gate on a model's note for the WORD; gate on the DEED.** A reader
  explaining what it declined to do uses the same vocabulary as one confessing
  what it did, so a keyword rule punishes restraint — and a reader punished for
  explaining itself learns to stop explaining, which costs you the only channel
  that made the defect legible.
  *Paid for by:* 2026-09-22 — my first derived-figure gate matched
  "calculat|sum|add" anywhere and failed 8 of 46 reads, six wrongly. ACT's note
  said "though sum is calculable, the prompt asks for 'total liabilities' as
  stated" — it had DECLINED to sum, and the gate failed it for saying so. The
  working rule matches arithmetic on the page (`4556.8 + 11266.0`).

- **Diff a robots.txt; never summarise one from memory — and identify the host
  before you name the organisation.** Reporting the weekly re-read (ruling
  288) I said `hrc.govt.nz` had added `Disallow: /` and called it the Human
  Rights Commission. Both were wrong: it had added **two paths** (`/search?`
  and `/index.php/search?`), and it is the **Health Research Council**. A
  tightening is a decision about what we may fetch, so the report has to be
  the diff plus the measured verdict through `fetchgate.decide` for the paths
  we actually want — the gate is the only thing whose opinion counts, and it
  disagreed with my reading of the file. (2026-10-05.)

- **A challenge page is an HTTP 200.** The Hansard scraper treated any 200 as
  a successful read, so a bot-check interstitial parsed as "no results" and
  the lane reported an empty House with a clean exit. It now raises
  `Challenged` on a non-200 **and on a 200 whose body is not the JSON the
  endpoint promises**, fails hard on a warm-up that does not come back right,
  and exits 3 so `RestartPreventExitStatus=3` stops systemd restarting it into
  the same wall. A challenged read is a failed read (doctrine) — the lesson is
  that it does not announce itself in the status code. (2026-10-05, C501.)

- **Pace after a REQUEST, not after a success — and put the pace in a `finally`
  at the chokepoint.** `docsource`'s delay sat at the bottom of each loop body,
  so every early exit jumped over it: two `except … continue` paths after a
  fetch that FAILED, and the `break` on the first all-seen page of a
  back-catalogue walk. A failed fetch is a request the host served, and a
  failure is the moment pacing matters most — an error is often the host saying
  slow down, and a sweep walking a run of them went at it with no delay at all.
  The fix is not a delay added to each exit: it is one `_paced(cfg, fetch, url)`
  wrapper whose `finally` cannot be skipped by a path somebody adds later. A
  rule applied per call site is a rule a call site can fail to apply.
  (2026-10-06, C216.)

- **A politeness floor is a rate against a HOST, not a delay per worker.**
  `docsource.gather` enqueued under a semaphore of four, each task sleeping the
  floor and then firing — four requests per floor against one host, so the
  floor was divided by four and every number in the code still looked right.
  The wait has to be `workers × floor` for the aggregate to honour it. Same
  card, the same lane also passed NO HOST to `polite_sleep`, although that
  function's own docstring says the floor comes from `fetchgate` *"which is why
  every call site that knows its host passes it"* — latent rather than live,
  because every registered source is a government host with nothing in
  `FLOORS`, so the default happened to equal the floor. That is what made it
  worth fixing before it cost anything: C217 was this same defect at 80×.
  **And the host comes from `base`, never from the `source` tag** — the
  shared-host registries tag themselves `justice.govt.nz/lcdt`, which is not a
  host and would miss the floor table silently. (2026-10-06, C216.)

- **A backwalk reports how much is LEFT, not how much is done — and the index
  it already fetches knows.** The NZME archive lane printed *"4,314
  sub-sitemaps already done"* for **378 runs** and could not answer "when does
  this finish", although `make_sitemap_archive_discover` computed `len(subs)`
  from the sitemap index on every single run and threw it away. A count without
  its population is the same shape as *"a gate proves nothing until you know
  what it ENUMERATED"*: it looks like progress and supports no decision. With
  the denominator recorded, the lane's shape came out clean and measurable —
  one sub-sitemap per DAY, 4,314 done and perfectly contiguous (2015-03-04 to
  2026-10-04, every year 365/366, no gaps), 9 completed per run at 12 runs a
  day, so **108 days of archive per day of wall clock**. Before measuring, the
  lane was a thing that had been running for months; after, it is a thing with
  a finish line. (2026-10-06, C313.)

  **AND THE SAME INDEX CAN BE THE WHOLE QUEUE** (C168, 2026-10-10). The
  electorate-results gatherer carried a HAND-WRITTEN list of three URLs a year
  and reported `{"done": true, "read": 6}` on every 20-minute firing for two
  days while the card said "0 of 9 read". It was not blocked — `walls: 0`,
  `cooling_until: None`: the patience had worked and nobody looked. Two of the
  six were plain **404s** from a guessed path (`e9/e9_part8.html`, 1,833 and
  1,744 bytes of "404 Not Found" — a patient read apiece, spent, and reading as
  progress). The other four were INDEXES: 2023's `electorate-status.html` holds
  **72 `./electorate-details-N.html` links** and a table giving only the leading
  candidate, the runner-up and the margin. The per-candidate vote counts the
  card exists for — NOT ONE of 2,078 electorate candidates has one — were one
  link away on pages nothing had queued. Deriving the queue from the files
  already on disk took it from 6 URLs to **155, of which 144 are the electorate
  pages**, and the next firing read one. A crawler that says `done` is
  reporting its LIST, not the corpus; make the list come from the fetches.

- **A polite lane's latency is mostly the politeness, and that is not a
  defect.** C313 carried *"≈46 s/fetch, still owed a measurement"* as an open
  worry. Measured on a real run: **3.87 s/fetch** (5,802 s for 1,500 fetches,
  0 errors), of which **2.0 s is the floor we chose** and ~1.9 s is upstream —
  and 2 min 18 s of CPU across 1 h 36 m, so the lane is almost entirely
  waiting, which is exactly what a paced lane looks like from the outside. The
  46 s belonged to a run that hit the 9,000 s ceiling, i.e. it was the symptom
  of the timeout the card had already fixed, not a second problem. **Before
  optimising a capture lane, divide its wall clock by its fetch count and
  subtract the floor** — what is left is the only part that was ever yours to
  improve. (2026-10-06, C313.)

- **A CALLER THAT ASKED AND GOT NOTHING LOOKS EXACTLY LIKE A CALLER THAT DID
  NOT ASK.** `proxies.get_proxy` is opt-in by policy — light fetches go direct,
  and only a heavy scrape asks via `heavy=True` — and it returns `None` for
  four different reasons: the source is excluded, the caller did not ask, the
  run did not set the override, **or no pool is configured at all.** The last
  one is a provisioning failure wearing the costume of a routing decision. The
  estate's one asking lane (`ingestion/courts/scraper.py:107`, the NZCA/NZHC
  back-catalogue) therefore egressed DIRECT for weeks after §AB retired
  `ingestion/.env`: `proxies.py` is inert by design when unset and says
  nothing, its unit loaded `factory-db.env` alone while the pool lives in the
  newsscrapers credential file, and the paid subscription may have been billing
  for a pool nothing used. **An opt-in default that protects the common case
  will hide the rare case that was promised the thing** — so when a caller
  asks EXPLICITLY and the answer is "no", that is an event, not a default.
  T7.60 is the standing form of it: the asking lane's own UNIT must see a file
  carrying the key, asked of the unit and never of the auditor's own
  environment. (2026-10-06, C062.)

- **A LANE THAT RUNS AND LANDS NOTHING IS WORSE THAN ONE THAT REFUSES, BECAUSE
  ONLY THE SECOND IS VISIBLE.** Dry-verifying three government news scrapers on
  the real surface: police and SFO each discovered, fetched and landed real
  releases; `rbnz.govt.nz` discovered 1, fetched 1, landed **0** — and its
  registry status said `ready`, so the daily sweep had been reporting success
  for a lane that cannot produce a document. The cause is an escalation of a
  known one: the browser fetch was ALREADY this host's WAF workaround ("403
  curl-class TLS, same class as stoppress"), and the browser now renders a
  32 KB SHELL — no `og:title`, the `h1` is the site banner, four `<p>` elements
  with the longest at 152 chars. The extractor correctly declines it. Marked
  `blocked:antibot`, which its own sibling entry has carried since B1/S1 — two
  entries for one host disagreeing about whether it answers is how a lane gets
  trusted by one caller and not another. **Dry-verify on the real surface
  before trusting a sweep, and count what LANDED, never what ran.**
  (2026-10-06, C200.)

- **THE FIRST TWO DIAGNOSES WERE MINE, NOT THE LANE'S.** `discovered: 1` looked
  like a broken feed — the feed is healthy with 50 items, and the run window is
  what reduces it to the recent one. Then `extract()` returning None looked
  like a broken extractor, until I noticed I had called `extract(url, html)`
  against a signature of `extract(html, url)`; a defect reported there would
  have been my own. Only the third reading found the shell. **When a lane looks
  broken, suspect the instrument twice before the lane** — and in a session
  that has already caught three keyword sweeps counting prose, the prior should
  be that the measurement is wrong, not the system. (2026-10-06, C200.)

- **COVERAGE COUNTS CALL SITES; THE QUESTION IS DOCUMENTS THAT LANDED TWICE.**
  A card stood for weeks as "the content dedup covers 7 of 19 landing lanes",
  re-measured once and still phrased as a ratio, with the conclusion that all
  twelve uncovered lanes needed enrolling — "a session with the lanes, not a
  patch". Measuring the OUTCOME instead of the coverage: **4,973 documents with
  a content hash, 4,973 distinct, 0 redundant, and 0 cross-source duplicates**,
  which is the one thing a cross-source index uniquely catches. And the reason
  is structural rather than luck: only **two** of the twelve uncovered lanes
  land HTML, where a content hash is defeated by nonce-bearing markup; the rest
  land PDFs, where the store's own sha dedup works and the zero proves it. The
  HTML case is not hypothetical — it is the 2026-08-24 WorkSafe incident, 229
  articles for 149 pages in a day — and it was already fixed by a DIFFERENT
  mechanism, ref-skipping in `store.enqueue`. **Before enrolling twelve lanes
  in a safeguard, measure what the safeguard would have caught**, and say which
  named mechanism is doing the work instead. This is not "the harm has not
  happened yet": the harm is prevented by identified means, and the measurement
  shows both means working on the exact lanes in question. (2026-10-06, C218.)
  **CORRECTED 2026-10-08, and the correction is the sharper rule: BOTH ZEROES ABOVE
  WERE UNFALSIFIABLE.** `content_hash` is the PRIMARY KEY of `content_index` and
  `sha256` is unique in `documents`, so one hash has exactly one row and exactly one
  source. "Count the hashes held by more than one source" asks whether a primary key
  has two values — 0 on an empty table, 0 on a perfect corpus, 0 on a corpus riddled
  with duplicates. The structural argument (two of twelve lanes land HTML; the rest
  land PDFs where the store's own sha dedup works) still stands on its own, and the
  conclusion has not changed. The MEASUREMENT I offered for it proved nothing, and it
  took two readings of the same table to see it, because a zero that agrees with you
  is the one you do not interrogate. **The observable a de-duplicator has is the
  REFUSAL, not the state of the table it writes** — `register_content` returning False
  because a different item already holds this content. Nothing recorded one: the six
  callers increment `stats["dup_content"]`, which conflates one outlet re-registering
  a re-headlined URL with a genuinely different source, and the count dies with the
  run's log line. `content_collisions` (one bounded row per day and source pair, with
  one example hash) is now that counter, and cross-source is `loser_source <>
  owner_source`. (2026-10-08, C218, amending #968b7d.)

- **A SOURCE THAT PRINTS TWO DATES FOR ONE EVENT MUST BE SERVED WITH BOTH, OR
  THE PAGE ARGUES WITH ITS SOURCE.** An Electoral Commission s 210C row carries
  the date the PARTY received the money and the date the COMMISSION received the
  declaration — weeks apart — and the Commission's own table leads each row with
  the second. We stored and served only the first, so our newest row read
  `29 September` where the same declaration read `5 October` on elections.nz.
  Arthur reported the donations as out of date. **They were not:** every one of
  the 255 linked declarations in the table had a register row and the capture
  held them to the 5 October filing. A register can be complete, current and
  correct and still be DISBELIEVED, because the reader checks it against the
  source by looking at the top row. Store every date the source prints, label
  which is which, and say in the prose which one orders the list.
  (2026-10-06, C514.)

- **`commission_date` WAS PARSED FOR A WEEK AND READ BY NOTHING.** The field was
  produced by `ec_disclosure_index.read()` on 2026-09-29 and the only place its
  name appeared in the whole repo was the line that produced it. A parsed field
  with no consumer is not "available for later" — it is a fact the estate has
  and does not use, and nothing will fail while that is true. When a reader
  starts producing a field, either a surface consumes it in the same tranche or
  the field is carded. (2026-10-06, C514.)

- **THE COMMISSION NAMES THE DECLARATION IT AMENDS — SO SUPERSESSION IS ASSERTED,
  NOT INFERRED.** An amended s 210C row does not merely say "amended": its date
  cell reads *"4 September 2026 (amended return received 28 September 2026)"*,
  naming the declaration being replaced. That matters because the estate's
  existing fold — (party, year, total) plus one shared identifying word — is
  STRUCTURALLY BLIND to an amendment: an amendment changes the total, so
  Cartmell's superseded $100,000 reading never matches the $120,000 that
  replaced it, and both were live. Where a register states a relationship, read
  the statement; a fuzzy match is for where it does not. **And parse it, never
  grep it:** one row reads *"amended on 22 April 2024 and amendment withdrawn on
  8 May 2024"* — the original STANDS, and a rule keyed on the substring "amend"
  supersedes exactly the figure the Commission still stands behind. A filename
  grep also finds only 4 of the 9 amendments, because three say so only in the
  date text. (2026-10-06, C515.)

- **A FEED'S GUID MUST SURVIVE A DERIVE, SO IT CANNOT BE A ROW ID.** The
  declared-donations feed's obvious key was the payload's own `ref` —
  `ddis:<id>`. But `registers.donation_disclosures` is TRUNCATED and reloaded by
  every derive, so those ids are renumbered nightly: a feed keyed on them
  re-notifies every subscriber about every declaration, every night, for ever, and
  **nothing in the estate would have said so** because the XML stays perfectly
  well-formed and the page stays right. The guid is the declaration's own
  identity instead — the Commission's address for the scan where we hold it, else
  a digest of party + donor + amount + declared date, the four things that make
  one declaration that declaration. The general rule: anything a SUBSCRIBER
  remembers between visits must be keyed on the fact, never on the row.
  (2026-10-07, C526.)

- **A FEED IS DATED BY THE PUBLICATION EVENT, NOT BY WHEN THE THING HAPPENED.**
  An s 210C declaration carries two dates weeks apart. Dating items by the money
  would put a six-week-old donation at the top of the feed on the day it is
  declared, and a reader watching for new money would see noise. `pubDate` is the
  date the Commission received the declaration — the same date its own table
  leads with (C514) — with the money date in the item's text beside it, so a
  subscriber can still check us against the source. (2026-10-07, C526.)

- **BEFORE PLANNING WORK ON A BLOCKED SOURCE, READ THE RUNSHEET — THE ANSWER MAY
  ALREADY BE THERE.** On 2026-10-07 I diagnosed parliament.nz from scratch: the
  home page clears, the JSON API serves a Radware CAPTCHA, an hour later the
  content pages were refused too, so there is no technical route and the unlock is
  a permission ask. All of it was already in `ARTHUR_RUNSHEET.md` §AN, written on
  2026-10-05, down to *"my own probing being the likely cause, so I stopped"* and
  *"there is no technical route and I will not look for one."* The card I planned
  from said "re-read the API's shape", and I believed the card. **The lessons tool
  searches LESSONS; a source that is BLOCKED ON A PERSON lives in the runsheet, and
  nothing cross-references them** — so a card naming a blocked source gets a
  runsheet grep before it gets a plan. The cost of skipping it was several more
  browser launches at a bot-managed government host, which is the one cost this
  estate's own rules exist to avoid. (2026-10-07, C524.)

- **A PAGE CHECKPOINT IS ONLY SOUND WHILE THE RESULT SET HAS NOT MOVED.** The
  gazette backwalk was stateful per YEAR and not within one, so a run that stopped
  at page 50 of 75 asked DigitalNZ for pages 1-49 again — four minutes of somebody
  else's anonymous tier, paced at 2-3 s a page, spent rediscovering notices already
  held. The obvious fix, "remember the last page", is WRONG on its own: DigitalNZ
  pages are date-ordered, so a year whose count grows has different page
  boundaries, and resuming at 50 steps over exactly the notices that shifted. So
  the checkpoint is stored WITH the count it was taken at and honoured only while
  that count still matches — the same self-invalidation the residue rows already
  used. A closed year always resumes; the current year never does, and that is the
  rule working rather than a limitation. Two orderings matter as much as the rule:
  the checkpoint is written AFTER the page is landed (so a crash mid-page re-reads
  it instead of skipping it), and it is per DIRECTION, because the walk tries
  `desc` then `asc` from opposite ends of the year. (2026-10-07, C073.)

- **THE VERBATIM HASH SAW 52 OF 943: A CAVEAT CARRIED FOR TEN WEEKS WAS RIGHT, AND
  CHEAPER TO SETTLE THAN TO CARRY.** The duplicate-article dismissal rested on exact
  text plus title collisions, with a note attached in July saying it tested verbatim
  republication only and that *"the shingle/minhash pass has never run. Every
  coverage/recall number inherits this caveat."* Running it took thirteen seconds of
  CPU over 41,583 articles: **943 near-duplicate pairs at Jaccard ≥ 0.9, of which 52
  were byte-identical**, and 629 of the rest cross-source — RNZ copy carried by 1News,
  ODT, Stuff and Guardian Online under rewritten headlines, bodies 0.99 identical.
  2.7 % of the window's documents, 4.9 % at ≥ 0.8. The instrument was a 100-line script
  and no dependency; the caveat had been inherited by every coverage number since July.
  **A caveat is a measurement somebody has decided not to take.** Price the measurement
  before you attach the note, because the note costs every number downstream and the
  measurement usually costs an afternoon.
  **And the finding did NOT want a fix.** The obvious next move — de-duplicate at land
  time — would destroy the fact that a second outlet carried the story, which is
  precisely what the press tier and the influence work read. What the corpus owed was an
  honest denominator, not fewer rows: the measured share is now printed in
  COVERAGE_2026-09.md's own generated header, where the counts are read, saying that a
  record is one outlet's copy and not one story. Recover over exclude applies to
  duplicates too.
  *Paid for by:* 2026-10-08 (C108), ten weeks after the caveat was filed.

- **A RULE, A ROW AND A REFUSAL ARE NOT A SAFEGUARD UNTIL SOMETHING CAN JOIN THEM.**
  T7.19 was red for **28 consecutive boards** over a host whose robots.txt is unreadable.
  Every piece of the answer was already in the estate: ruling 78 makes an unreadable
  robots a refusal, `fetchgate.decide` had been refusing every request to that host since
  the read and says so in its own words, `v3.source_policy` held the row, and ruling 290
  says a source we have stopped fetching is not a red. **Nothing was being fetched and
  the board could not tell.** Its only notion of a stop was one registry's
  `status="blocked:robots"`, and the host is a party-site lane that is not in that
  registry — so the red was permanent by construction and no amount of work on the
  CAPTURE side could ever have cleared it.
  **The fix changed nothing about what we fetch**, which is the tell for this whole
  class: when an arm reds over a decision that has already been taken correctly, suspect
  the arm's ability to SEE the decision before suspecting the decision. A verdict of
  WRONG on a red is not an insult to the arm; it is where a third of a day's capture work
  would otherwise go.
  **And a predicate that mirrors another one must say which is the authority, keep its
  ORDER, and refuse to answer what it cannot see.** `host_refused_by_record` carries
  `decide()`'s two host-level cases in `decide()`'s order — unreadable BEFORE absent,
  because a 4xx is the host answering and an unreadable read is not — with a test that
  compares the two, and it deliberately cannot read a per-path `Disallow`, because a
  host-level answer that pretended to would read one blocked directory as a blocked site.
  The failure branch returns NOT-stopped, so a database outage leaves the arm red rather
  than producing a clean board.
  *Paid for by:* 2026-10-08 (C535), 28 boards after the refusal was first made.

- **A CHALLENGE SHELL IS BIGGER THAN A REAL ARTICLE, SO SIZE WAS THE WRONG
  SIGNAL — AND A REFUSAL COUNTED AS `thin` BLAMES THE PUBLISHER.**
  `browserfetch.render_all` waited out a challenge, then broke out of the wait
  `if _CHALLENGE_MARKER not in html or len(html) > 20_000`. Two holes in one
  line: the marker was Incapsula's and the host serving us a challenge is
  **Cloudflare**, and its "Just a moment..." interstitial measures **29,045
  bytes** — so the size escape defeated the check it guarded even for the vendor
  it did know. An interstitial is mostly inlined CSS and script; a short real
  article is small. **The shell was then handed to the extractor, returned
  nothing, and the lane counted it `thin`** — and `thin` says the publisher
  published little, while `challenged` says we were refused. An archive walk
  reported 19 of 20 pages thin and the refusal was invisible for weeks.
  Reproduced exactly: the FIRST page of a batch renders fully (258 KB, 3,834
  chars), every page after it is the 29 KB shell.
  **Under the standing rule a challenged read is a FAILED read, so the remedy is
  to stop asking, never to try harder.** stoppress.co.nz is now
  `blocked:antibot` — which also removes it from `coverage_backwalk.plan`, since
  that only schedules a `ready` source, so the stop is the whole remedy (290).
  robots PERMITS us there: this is the WAF, not the permission surface, and
  nothing about it is to be worked around. On the last probe even the first page
  came back challenged, the host having tightened against repeated asking — one
  more reason the answer is to stop.
  **And the two sources named in one card behaved differently.** times.co.nz
  does NOT challenge: four of four archive pages rendered with 2,264–6,624
  chars. Stopping it as well would have thrown away an archive back to 2018 that
  demonstrably reads. One card, two hosts, opposite verdicts — census each,
  never the pair.
  **The other half was a batch that could not survive its own slice cap.**
  `fetch_all` was ATOMIC over the whole discovered set — an archive walk
  discovers up to `--limit 1500` urls and every one is rendered before the
  landing loop begins — while the coverage service caps an archive slice at **8
  minutes**. So the process was killed mid-render every time and nothing landed:
  times.co.nz ran that walk on 10-05, 10-06, 10-07 and 10-08, reported `0
  sub-sitemaps already done` each run, **exited rc 0**, and holds 719 records
  whose earliest post_date is 2026-07-16 against an archive going back to 2018.
  Eight polite minutes a day against a real publisher, for nothing, reported as
  success — #51242b's rule (a traversal bound below the source's own unit stalls
  silently and reads as done) with `rc 0` as the thing that made it read as done.
  Chunked and landed `FETCH_CHUNK` at a time, so a killed run banks what it
  rendered and the next run's pre-fetch dedup skips it, which is how ruling 28
  already intends progress to be measured. **Opt-in, because the authenticated
  lanes log in once per `fetch_all` call**: chunking nbr or businessdesk would
  turn one login into thirty inside eight minutes against a paywall, which is a
  different kind of request. Only the lanes with no login and a real archive
  declare it.
  *Paid for by:* 2026-10-08 (C215), four measured days of a daily walk landing
  nothing and weeks of a refusal recorded as thin content.

- **A HOLD WINDOW TUNED TO A TIMER MAKES DISCOVERY DEPEND ON THE JOB NEVER
  RUNNING EARLY — AND THE CATCH-UP RUN IS THE ONE YOU NEEDED.** The party-site
  crawl holds what it fetched within `--min-age-days 6` against a 7-day timer,
  so a scheduled firing ages every URL out and re-reads the lot. The five real
  runs came **3.87, 11.67, 13.96 and 4.43 days apart**: half of them landed
  inside the window, found all 14,950 URLs held, walked a STORED map and
  reported `Result=success` with 292 documents while discovering nothing new.
  The 2026-10-07 firing was 4.43 days after the last *because C538 had just
  restarted a service dead for four days* — so the run whose whole purpose was
  to catch up was the run guaranteed to find nothing. A window measured against
  a cadence is a window measured against an assumption; an outage, a hand
  re-run and a restart all break it, and they are exactly when you look.
  **AND A HELD SITEMAP WAS NOT STALE, IT WAS GONE.** The skip branch walks on
  from a held copy only `if kind == "page" and prior.endswith(".html")`, and a
  sitemap stores as `.xml` — 184 of 193 do. So a held sitemap contributed **no
  URLs at all**: ACT's names 3,348 and ACT's frontier reached `seen 500` with
  every `found_on` an HTML page. Nor would walking it have worked, because
  `links()` reads `href`/`src`, not `<loc>`. One type test, written for HTML,
  silently deleted the publisher's own index of itself from discovery.
  **THE FIX IS A CLASS, NOT A CACHE SETTING: the entry points are not content.**
  A root and a sitemap are the site's index of ITSELF and their whole value is
  freshness; an article is an immutable observation and re-fetching it is waste.
  One hold rule for both is the error. 74 re-fetches a run across 17 hosts buys
  discovery that no longer depends on the phase of a timer — and it was paid for
  by folding the held key over scheme and `www.`, which removed 205 of 320.
  **THREE INSTRUMENTS FOR "WHICH PAGES ARE INDEXES" WERE REJECTED BY
  MEASUREMENT, EACH IN ONE QUERY.** `found_on` out-degree records which URL
  reached a page FIRST, which is BFS order — a sitemap is enqueued at position
  one and always wins, so `labour.org.nz/news` scores **0** and the instrument
  calls the index a leaf. `depth <= 1` is sitemap-contaminated: a sitemap sits
  at depth 0 and names 3,691 URLs, so the rule re-fetches **7,992** pages a run.
  Sitemap `<lastmod>` covers 7,364 of 15,715 `<loc>` entries and is **absent for
  ACT** (3,348 locs, zero lastmod), Vision, and Labour (no sitemap at all, 404)
  — a fix built on it would silently do nothing for two front-page parties.
  Cheap to test, and each would have shipped as a plausible rule.
  **A PER-RESPONSE NONCE MAKES BYTE-IDENTITY USELESS FOR "SAME PAGE".** One page
  answers at four spellings (`http`/`https` x bare/`www.`) and the raw-byte sha
  can never fold them, because these sites (NationBuilder behind Cloudflare) put
  a fresh `csrf-token`, `window._auth_token`, `data-cf-beacon` token and
  `__CF$cv$params` in every response. Measured: of 33 same-run pairs captured
  under two spellings, **26 were byte-identical and the 7 that differed differed
  ONLY in those nonces** — four of the seven at identical byte length. So
  C530's "63 of 64 cross-label duplicate bodies" is a consequence, not a
  separate problem, and a sha-over-bytes dedup will keep reporting zero. Fold
  the KEY; never fold the fetch host, because robots.txt is per host and
  `act.org.nz` is a different permission surface from `www.act.org.nz`.
  **AND A FUSE MUST COUNT WHAT IT IS THERE TO BOUND.** `--max-pages` exists to
  stop a runaway against the HOST, and it counted `n_fetched + n_skip` — so
  pages read from our own disk spent it. Harmless while a held sitemap's URLs never
  reached the frontier — and the first run with seeds re-read blew it on **three
  of the seven front-page parties**: ACT `held 3915 + fetched 85 = 4000` with
  **4,445 left in a frontier of 8,517**, Green `3948 + 52` with 926 left,
  National `3996 + 4` with 659 left. ACT asked for 85 pages of 8,517 and
  stopped. Fixing discovery made a dormant bound live in the same run, which is
  the convoy (#39), and the first thing to check was whether the fix merely
  moves the stall — `TimeoutStartUSec=5h`, so it does not. The cost moved too:
  wall clock 9m48s → **36m34s** and **2.6 GB** of stored files read, because the
  held-walk re-reads every stored copy to extract its links. Disk, not
  politeness — 261 requests across 17 hosts.
  *Paid for by:* 2026-10-08 (C542), two of four measured runs discovering
  nothing while reporting success. The fixed run made **261 requests against 320
  and found 189 never-held paths against 115** — fewer asks of every host, 64%
  more pages — and the party that correctly had nothing new fetched 6 pages, all
  of them seeds, which is what a correct zero should cost.

- **A CLOCK THAT WALKS A CODE LIST INSTEAD OF THE TABLE LEAVES THE ROWS NOBODY
  CODED — AND THE PERMISSION IT WAS GUARDING GOES STALE IN SILENCE.** Ruling 288
  re-reads every adopted host's robots.txt weekly. The pass walked
  `registry_hosts()`, a union of code registries; the record of adoption is
  `v3.source_policy`. Measured 2026-10-08: **registry 139, table 227, so 88 rows
  the clock had never touched.** Every one of the 84 rows older than a week was
  one of those 88 (median 33 days, max 46); of the 139 the clock did walk,
  **zero** were stale. The split was not random — `whole-site` 64 of 65 and
  `survey` 15 of 16, because the party-site crawl registers each document host it
  meets and no registry names them. **Nineteen of the orphans asserted
  `robots_absent`**, which under ruling 168 reads "403 = absent = permitted", on
  a reading up to 45 days old, every one with `disposition=extract`. That is the
  only direction that can breach robots absolutism: a stale "present, with
  disallows" merely makes us refuse more than we must, while a stale ABSENT is a
  standing permission nobody re-checked. **The first run over all 227 found five
  hosts STRICTER and all five were orphans** — `data.linz.govt.nz`,
  `www.tenancy.govt.nz`, `www.educationcounts.govt.nz` and
  `www.scionresearch.com` each added a `Disallow` for `*`, and
  `newstalkzb.co.nz` named more AI agents. Two of the five were in the
  nineteen. Nothing was owed a retraction — 2 held URLs across the five, neither
  now disallowed — but that was luck, not design, and it had to be checked
  before the finding could be acked.
  **The precedent was already in the function.** The council instances sit in
  `registry_hosts()` under the note *"a lane adopted for ingestion is adopted for
  permission; that is what this line makes structural rather than remembered."*
  That fixed ONE route by naming it, and the next route in arrived unnamed. The
  shape is the fix: the clock's population is the TABLE, so a row cannot exist
  off the clock whatever inserted it. The unit had been sized for it all along —
  `robots-audit.service` says "~230 hosts at 1/s" while the code walked 139.
  Stalest first, too, because a pass cut short by `--limit` or a timeout must
  re-read what has waited longest rather than the alphabetically first row again.
  *Paid for by:* 2026-10-08 (C547, found inside C530), 88 rows and up to 46 days
  of unchecked permission, closed to 0 stale and 0 stale-permitted in a 6m27s run.

- **THE SOURCE LABEL IS THE JOIN KEY TO A DOCUMENT'S PERMISSION, AND A MODULE
  NAME IN THAT COLUMN HIDES 8.8% OF THE CORPUS FROM EVERY GATE.** C530 was
  carded as "one organisation, two source labels", needing "a scope ruling plus
  one judged pass" over ~14,000 party articles split across `www.` labels.
  Measured, almost none of it held: **National and Labour do not split at all**,
  the pairs that exist are 98–99% asymmetric (greens 3,891/52, act 3,572/44,
  beehive 55,346/11) so the whole minority side is **174 rows, not 14,000**, and
  the biggest pair is not a party but `beehive.govt.nz`. **Folding the label
  would have been wrong:** robots is per host, and the record had
  `rbnz.govt.nz` at `403/absent` against `www.rbnz.govt.nz` at `200` with
  disallows — re-read live, both answer `absent`, so they were ONE surface
  measured a month apart, which is the clock defect above and not two labels for
  one organisation.
  **The real fault is a join.** 641,213 articles reach no `v3.source_policy` row
  at all, 640,836 of them labelled `'nzme'` — the scraper MODULE's name, where
  the registry key is a host. **And no scope ruling is needed, because the host
  is already in the row:** `news_url` gives it for 100% of them with ZERO nulls,
  and the mapping is a function — of 189 labels, 187 cover exactly one host, and
  `'nzme'` resolves to `www.nzherald.co.nz` for all 640,836. A card can ask for
  a ruling because nobody looked at the column next to the one they were reading.
  **THE PERMISSION WAS HONOURED ANYWAY, WHICH IS EXACTLY THE POINT.**
  `nzherald.co.nz` is `disposition=held, extract=False` and all 640,836 of its
  articles are `pipeline_status='held'`, 2014-04-24 to 2026-10-08. Nothing was
  breached, and nothing could CHECK it: the lane obeys the rule by remembering
  it, and the only way to confirm it was a hand-join through `news_url`. That is
  #acd73e again — a rule, a row and a refusal are not a safeguard until
  something can join them — and the repair is its own card because `mod.SOURCE`
  is what `is_review_source` and `held_reason` are keyed on, so changing the
  label changes the held discipline for 640,836 articles.
  **A SHRINK-ONLY COUNT OVER A LIVE LANE IS A TEST THAT FAILS BY THE CLOCK.** The
  first gate pinned the unjoinable total at 641,200 and failed at 641,213,
  because nzherald lands daily and the number moved between measuring it and
  asserting it. The invariant had to become structural: no NEW unjoinable label,
  no growth in the count of labels, a ceiling only on the lanes that are stopped,
  and "nzme is the only unjoinable label that is still large".
  *Paid for by:* 2026-10-08 (C530), a card whose four headline figures were all
  wrong and whose "judged pass" was a join.

- **`urllib.robotparser` IS OVER-PERMISSIVE TWICE, AND FIXING THE LIBRARY DID NOT
  FIX THE CALL SITES.** C220 found the first defect on 2026-09-20 and wrote it
  down plainly: the stdlib "implements NEITHER [`*` nor `$`]. Its rule match is
  `path.startswith(rule)`, so every rule beginning with `*` … silently never
  matches … Every `can_fetch` in this estate was answering for a file it had not
  understood." It then built the correct matcher, `sourcepolicy.path_allowed`,
  and **left six enforcement call sites on the stdlib** — the party-site crawler,
  the party-boards capture and probe, the fonts probe and the research webtools.
  A rule expressed once is half a rule, and the half that was left is the half
  that fetches.
  **THE SECOND DEFECT IS RULE ORDER.** Within a group the stdlib returns the
  FIRST matching rule's allowance; RFC 9309 2.2.2 requires the most specific —
  longest — match. Measured on Python 3.12.14: `Allow: /` then
  `Disallow: /search` gives `can_fetch('/search') == True`, and the same two
  lines in the other order give False. `publicdata.co.nz` writes its file the
  first way, so **285 of its disallowed paths read as permitted**, `/search`,
  `/threads/`, `/api/` and `/admin/` among them; shop.greens.org.nz (15),
  stonearrow (15), www.spc.int (22), nzx (4), worksafe (5), stuff (5) and six
  more are misread the same way. Two independent defects in one stdlib module,
  both in the permissive direction, which is the only direction that matters.
  **AND IT WAS NOT LATENT.** Judged against the robots text archived for each
  host, 4 of the 36,302 URLs the party crawler has fetched were forbidden by RFC
  9309 and permitted by the stdlib. Two are
  `www.educationcounts.govt.nz/__data/assets/pdf_file/…` under
  `Disallow:/*__data*` — C220's exact case — and that rule was in force at every
  archived reading **including the one taken two seconds before the fetch**. A
  real breach of the hardest standing rule in this estate, caused by trusting a
  parser instead of the file. Quarantined, never deleted; the landed rows moved
  `done`/NULL → `held`, which is reversible in one statement.
  **KEEP THE PARSER OUT OF THE MODULE, NOT JUST OUT OF THE DECISION.** The only
  reason these lanes still built one was `site_maps()`, so that moved into
  `sourcepolicy.sitemaps()` and the import is gone: a module that keeps the
  object around for one safe purpose invites the next reader to use it for the
  unsafe one. The single surviving stdlib call is `crawl_delay_for`, and it is
  labelled with WHY it is safe — Crawl-delay is a directive read per group, not a
  path decision, so neither matching defect touches it.
  **AND THE FIRST MEASUREMENT SAID THERE WAS NO BREACH.** It joined held URLs to
  archived robots files by parsing `robots-<host>-<stamp>.txt` with a split on
  the LAST `-`; the stamp is `2026-10-08T071852Z`, so every key came out as
  `host-2026-10`, nothing matched, and the answer was a confident "0 url(s)
  across 0 host(s)". A join that finds nothing and a population that is clean
  look identical in the output. Print the unmatched count beside the matched one,
  always.
  *Paid for by:* 2026-10-08 (C549, out of C328's catalogue re-read), two
  government PDFs fetched against a disallow that had been published all along.

- **THE BLOCKER WAS THE CARD'S REASONING, NOT THE CODE — AND THE CHANGE MADE THE
  SAFEGUARD REDUNDANT INSTEAD OF SINGLE-SIGNAL.** C548 was raised with a real-
  sounding reason not to relabel 650,483 articles: `mod.SOURCE` is what
  `is_review_source([mod.SOURCE])` and `held_reason([mod.SOURCE], url)` are keyed
  on, so changing it changes the held discipline for the lot. Measured by calling
  both functions with all three strings: `held_reason` returns the **identical**
  ruling-115 reason for `nzme`, `nzherald.co.nz` and `www.nzherald.co.nz`, because
  it substring-matches the URL as well as the label; `is_review_source` is False
  for all three, because no key of `DEDICATED_SOURCE_DOMAINS` is a substring of
  either. Two function calls against the actual code, where the card had a
  plausible sentence.
  **AND THE OPPOSITE OF THE FEAR WAS TRUE.** Asked WITHOUT a url,
  `held_reason(["nzme"])` is **False** and `held_reason(["nzherald.co.nz"])` is
  **True** — so the hold on 650,283 articles had been resting entirely on
  `news_url`, with the label contributing nothing. Nothing currently asks that
  way for this lane (`disposition_for` passes a host, `base.py` passes the url),
  so the risk was latent rather than live; after the relabel either signal alone
  suffices. A safeguard with two independent inputs is not the same safeguard as
  one with two inputs where one is dead.
  **641,213 UNJOINABLE ARTICLES BECAME 54**, which is 8.8% of the corpus to
  0.0007%, and the test that documented the gap became the gate that closes it:
  it used to establish by hand that every article from a `disposition=held` host
  was `held`, and now it ASSERTS it through the join. That is the whole value of a
  label that joins — not tidiness, but the difference between a rule obeyed and a
  rule checkable.
  **A RELABEL PASS EARNS ITS GUARDS.** Every target must already HAVE a policy row
  (or the relabel does not join, which was the point), every source label must map
  to exactly ONE `news_url` host, and no row may have a null url — all three
  asserted before the first UPDATE, all three cheap, and the second one is what
  keeps `motu.nz` and `scoop.co.nz` (two hosts each) out of a pass that assumes
  one. The manifest carries the reverse statement per class because the prior
  value is a single constant, which is what makes 650,483 rows a reversible move.
  **AND A LANE IN FLIGHT WILL OUTLIVE THE FIX BY ONE RUN.** 73 rows arrived
  labelled `nzme` after the pass, from an `nzme-archive-backfill` that had started
  at 06:00 with the old module loaded — not a second writer, the same one still
  running. The pass is idempotent precisely so the sweep is a re-run and not a
  new script, and the test now asserts zero rows under the old label so a genuine
  second writer would be loud.
  *Paid for by:* 2026-10-09 (C548, out of C530), and a blocker that cost a card's
  worth of deferral when two function calls would have cleared it.

- **A BARRED METHOD USUALLY NAMES ITS PERMITTED SIBLING — AND A RESTRICTION BEATS A
  GRANT IN THE SAME DOCUMENT.** C328's method was *"re-read their robots-permitted
  catalogue pages at each muster"*, and robots does permit it: `/data-sources` and
  `/developers` are allowed for our token with `Crawl-delay: 5`, checked against the
  archived text with the one RFC 9309 matcher. The TERMS say, under Prohibited Use,
  *"You may not: … Scrape or bulk download data without permission (**contact us for
  API access**)"* — so the card's recurring automated re-read is barred while the
  individual fetch is allowed, and **the sentence that bars it names the route that
  is not barred.** Read the prohibition to the end before concluding the source is
  closed.
  **The same page also offers the data under CC-BY 4.0**, which is the trap: a
  platform can republish openly-licensed government data and still forbid taking it
  FROM THEM. A classifier that matched the grant first would license a method the
  same page prohibits two paragraphs later, so restriction beats grant and the
  order of the two phrases must not change the verdict. And the grant is the hint
  for the real fix: the card wants the PRIMARY sources the catalogue names, and
  those are the openly-licensed ones — the platform was only ever the index.
  **The filed rule had no instrument, which is why none of this was recorded.**
  *Terms can bar what robots permits* has been a lesson since the NZX read, and of
  **237 policy rows THREE carried `terms_tier`** — all three written by hand on
  2026-08-23 (`fasttrack` unstated, `disclosure.legislation` open, `nzx`
  restricted). A rule with a column and no writer cannot be joined to a refusal
  (#acd73e). `ops/source_policy.py` now has `terms_tier_of` and `read_terms`, which
  archive the text beside the robots text and classify conservatively in BOTH
  directions — `unstated` on silence, never `open`, because a page that says nothing
  about re-use is not permission. It does not touch `disposition`: whether a
  restriction stops a lane is a judgment, and `nzx` is `restricted` AND `extract`
  because that judgment was taken separately.
  *Paid for by:* 2026-10-09 (C328), where the card's own method turned out to need
  an ask rather than a fetch.

- **ADOPTING A HOST CREATES OBLIGATIONS THE ADOPTION DOES NOT SATISFY — AND A DERIVE
  THAT DOES NOT KNOW A RULING WILL CONTRADICT IT POLITELY.** C554 closed by adding
  nine hosts to `v3.source_policy` from the landed labels, which is right: ruling
  266 withdrew source admission as a gate, so the remedy for a missing row is a row.
  It added the row and never ran the DERIVE that fills it, so the next board came
  back with two NEW reds — **10 rows with no `disposition`** and `comcom.govt.nz`
  active with no ruled `llm_tier`. **A row that exists and says nothing is not a
  permission record**, and "the host is now listed" is not the same claim as "the
  host's permission is recorded".
  **FILLING THEM SURFACED THE WORSE FAULT.** With the dispositions derived,
  `merch.opportunity.org.nz` came back **`extract`** — a host Arthur QUARANTINED on
  2026-09-22 (*"we dont need merch store data"*, then *"quarantine"*, C311). The
  capture refuses a commerce subdomain, and `ops/party_shop_quarantine.py` asks the
  capture's OWN predicate so that *"the sweep and the crawl cannot disagree"*. The
  policy table was the THIRD reader of that question and asked neither. **When a
  ruling is encoded as a predicate, every reader asks the predicate — a reader that
  re-derives the answer will eventually disagree with the ruling, and it will do it
  in the table that says what may be extracted.**
  **AND `extract` HAD DRIFTED FROM THE DISPOSITION IT CLAIMS TO MIRROR.**
  `review_sources.py` states the contract — *"Mirrored in
  `v3.source_policy.extract = false`"* — and the column was written from the HELD
  list ALONE, so measured 2026-10-10: **one `block` host, six `drop` hosts and one
  `held` host were all marked extractable.** "Do not take this" beside "you may
  extract this", in the table C324's reads-on-extract gate is going to consult. A
  mirror maintained by a different rule from the thing it mirrors is not a mirror.
  *Paid for by:* 2026-10-10 (C557), one night after C554 closed — the adoption and
  its consequence were visible on the first board firing, which is the only reason
  this was a night's work and not a quarter's.

- **"NOT REACHABLE" WAS AN ANSWER TO THE WRONG QUESTION, ASKED TWICE — AND AN
  ASSET URL BEHIND A WALL IS A URL INSIDE A SESSION.** C151's card recorded, on
  2026-10-09, that the 2026 candidate list *"has never been captured and no
  link to one exists"*, on the evidence of two headed renders that returned the
  Incapsula shell at 905–906 chars. Neither render went through
  `ops/ec_disclosures_feed.py`, whose whole reason for existing is this host and
  whose render loop WAITS and RE-REQUESTS after the shell sets its cookie — the
  step its own docstring names. Put through that loop the next day,
  `elections.nz/`, `/media-and-news` and `/getting-involved/candidate-hub`
  rendered with **zero challenges**, and the Commission's own news item
  *"Candidate and party lists released"* named both documents in one paragraph:
  the 469 electorate candidacies as a 30 KB spreadsheet and the ranked lists as
  a 2.3 MB PDF. The wall never refused us. **Before writing down that a source
  said no, ask it the way the estate already asks it** — a two-attempt ad-hoc
  probe is not a capability measurement, and "not retried" in the card was the
  tell.
  *Paid for by:* 2026-10-10 (C151). Thirty-four days of an empty served tier
  (ruling 194 withdrew the Wikipedia rows on 2026-09-06) behind a conclusion
  that cost two requests to reach and two requests to overturn.
  **AND THE SECOND HALF, WHICH IS A RULE ABOUT THE ROUTE.** The spreadsheet sits
  on `/assets/`, a path class this estate has pulled hundreds of files from, and
  `ctx.request.get` on it answered **403** with an Incapsula body — with the
  page rendered and all three session cookies (`visid_incap_*`, `incap_ses_*`,
  `___utmvc`) held in the same browser context. Clicking the link in that same
  browser downloaded 31,050 bytes. The wall admits a NAVIGATION and refuses an
  API-style request from the identical session, so an asset URL here is not a
  public URL — it is a URL inside a session, and the thing that obtains it is a
  browser doing what a person does with a published download link (no challenge
  solved, no UA spoofed, nothing patched: the ruling-133 GETS case). The
  manifest row therefore records WHICH ROUTE won, because that is exactly the
  fact that rots: a later reader who assumes a plain GET concludes the document
  is gone. The ordering matters too — a fetch before any render is a fetch
  before the cookie exists, which is why the feed's own download block has
  always run last.

- **TWO LANES FETCHING ONE PAGE BY DIFFERENT MECHANISMS: THE WEAKER ONE ROTS,
  AND ITS GUARD REPORTS A PARSE FAILURE.** `parties-capture.service` refused to
  write from 2026-10-08 with *"register parse looks broken (<5 parties) —
  refusing to write"*, and the parser was never the problem: the Register of
  Political Parties page that `ops/ec_disclosures_feed.py --party-register` had
  captured on 2026-09-26 parses to all SEVENTEEN registered parties, first try.
  What had stopped working was `browserfetch.render_all`, which no longer
  clears Incapsula — the same failure the Hansard lane's headless browser hit
  against Radware on 2026-10-05, and the "beehive precedent" the module's own
  docstring still cited as proof it worked. **The guard did its job perfectly
  and the lane was dead for two days**, because the message it chose named the
  symptom it could see (a short parse) rather than the step that failed (the
  render), and nobody reads a parse complaint as a browser problem.
  The estate was rendering that one page TWICE, by two mechanisms, and only one
  of them still worked. Fixed by deleting the weaker: the render belongs to the
  lane that demonstrably clears that wall (a headed Chromium on the desktop,
  rulings 242/243), `--party-register` joins its nightly run ahead of this
  lane's, and `parties.capture` parses what that lane HOLDS — with its own
  refusal if the held page is missing or older than four days, because writing
  a stale snapshot as current is the failure that module's docstring already
  records fifty-four days of.
  *Paid for by:* 2026-10-10. Two tells worth keeping: **a guard's message
  should name the step it could not complete, not the shape of what it got**;
  and when two lanes reach the same source, one of them is the one you test and
  the other is the one that rots. Same family as the drop-guard that must ask
  the serving layer (#bc81fa) and T7.42's arm reading the fetch's own stored
  response — the fix each time is one reader of one captured thing.

- **A COMPLETENESS ARM WITHOUT A LANE THAT ASKS FOR ITS OWN DIFFERENCE IS A RED
  THAT CANNOT GO GREEN.** T7.55 named
  `2023_ACT-New-Zealand_Christchurch-East_SEVERIN_Toni.pdf`, by file name, on
  **34 consecutive boards** — 470 of 471 held, one listed and absent. The
  document was one request away the whole time: the mode that asks,
  `--candidate-returns <year>`, costs 26 page renders per election and **no unit
  runs it**, so the nightly loop (`--annual-returns --candidates
  --party-register`) re-asked for truncated files and the party register and
  never for a return the wall had refused. The refusal itself was ordinary and
  transient: on 2026-09-25 the wall refused five downloads, one with a 403 and
  four with a **challenge page carrying HTTP 200**, and four of the five cleared
  on a later ask that hour. The fifth had no later ask. One hand-run of the
  existing mode on 2026-10-12 fetched it (20.2 MB, a scan; the Commission's own
  2023 summary table prints NIL/NIL/NIL for it, so no money was ever missing —
  the CAPTURE was).
  **The arm measures a difference; something must ASK for that difference, on
  the same schedule, reading the same two sides.** `--candidate-missing` is that
  lane: the index files the walk already wrote, minus what is held, with no walk
  and no render at all on the ordinary night when nothing is missing — cheap
  enough to run nightly, which is the only reason it will.
  *Paid for by:* 2026-10-12 (C174). Two tells: **a transient refusal becomes
  permanent at the moment the retry costs more than the nightly budget**; and
  the ledger row that would have said so said *"challenge or non-200"* beside
  `"status": 200`, which reads as a contradiction and so was read as noise — a
  failure note must name the refusal it saw — a stale reading and a false
  reading look identical in a status file (#464b73), and so do two different
  refusals filed under one word. Family: "The counter is a witness nobody
  calls."

- **A CASE-SENSITIVE GLOB AND A WINDOW RULE HID 39 DOCUMENTS FROM EACH OTHER FOR A
  MONTH.** `party_return_totals.staged_returns` listed the archive with
  `glob("*Annual-Return-*.pdf")`; the Commission names its 2016–2018 returns in
  lower case (`…__2019-returns__national-party-annual-return-2018.pdf`), so 39 of
  the 105 archived returns never matched. Nothing noticed, because ruling 347's
  window began at 2019 and every year the glob missed was a year the rule said
  did not exist — the gate that would have asked "where are the 2018 totals?"
  was the gate told not to ask. Found 2026-10-17 only because Arthur asked
  whether the 2018 returns were held. Two rules: a walker over a source's files
  matches names case-insensitively and reports the files it did NOT match; and
  when a window excludes years on purpose, measure once what lies outside it,
  so an exclusion by rule and an exclusion by accident are not the same silence.
  *Paid for by:* ruling 362 (2026-10-17) — the declared-total window moved to
  2018, the walker was fixed, and the 12 returns for 2018 were read that day,
  10 of them through the page reader.
