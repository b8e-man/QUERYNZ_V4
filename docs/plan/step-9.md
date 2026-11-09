# Step 9: The one report

Arthur, 9 November 2026 (rulings 150 to 153). This step is for an integrator
session (`bin/start-session --main one-report`) to set up as one large build,
in the tranches below. It is a plan: nothing in it has been started.

## What changes

One product, one lookup, one report, comprehensive. The report uses every
link the estate holds to bring in as many records as it can, and a search
of the news to connect those records to articles.

- Rulings 146 (significance per product) and 149 (product by product) are
  withdrawn. The use-case templates 02 to 13 retire. Their code stays until
  the one report passes on real data, then it goes.
- The diagnostic template is the base. It already reads every published
  table that names a person or a body.
- The frozen site (`ftm`) is untouched and keeps running as a reference.

## The report has two stages

- **Stage 1, the first report.** One lookup. Every confirmed link is
  followed, with the company-number and officer links to the companies and
  the people on them. The integrator measures how deep this goes, and where
  hubs swell it, on real subjects before setting any limit.
- **Stage 2, near links, on request.** From a finished first report the
  reader activates a second pass. It follows the near links (name matches
  without a confirming fact), each item marked near with its reason. A near
  link is never followed in stage 1.

## News

The estate gathers no news itself. It reads keyed APIs and handles the
corpora; the scrapers, already built, run elsewhere, with the website-crawl
provider (ruling 156).

### 9.1 The old scrapers, packaged for the website-crawl provider

- Source: the reference copy of the old repository, `/home/user/qnz3-ref`.
  Never the live folder `/home/user/Git Repos/QueryNZ_V3`.
- Take every news scraper and its documentation, by path. **The session
  does not read the documentation** (Arthur: a fresh start; decisions made
  back then led down wrong paths). It lists, packs and checks; it does not
  study.
- These are left out, found by file name and pattern search, not by reading:
  - Credentials, `.env` files and keys (limits 1 and 2). If one is found,
    note where it is and tell Arthur.
- Output: one archive with a manifest of every file (path and sha256),
  in `/home/user/querynzv4-work/handover/`. Arthur passes it to the provider.
  From then on, the crawls are the provider's.

### 9.2 The news corpora, brought over whole

- Every news table of the old estate, copied **wholesale and verbatim** into
  a new lane `news`. Its columns and rows are as they stand, with no
  cleaning and no reshaping.
- The schema is taken from the database catalogue, not from the old docs.
- The copy only reads the old estate. It writes nothing there (limit 22).
- The old Papers Past
  items join the existing `papers_past` lane under limit 17: searched, never
  mined.
- Disk is measured first. The copy goes in bounded batches, off-peak, and
  never scans a store whole (the 1 November out-of-memory kill).
- A one-page legal position for news as a class is written before the
  report shows an article (limit 9).

### 9.3 The search: registers first, then the news

- The corpus gets a local search index. Any model used runs on the boxes
  (limit 10).
- **The registers are read first, the news after** (Arthur, 9 November).
  The context from the registers is what makes sense of the news. The
  search runs only once the stage-1 records are built, and it searches with
  what they hold: the subject's names, its companies, trading names, bodies,
  roles and co-officers. Each hit is judged against those records.

### 9.4 What a hit means (Arthur: "4 is right")

- A hit is shown as "an article that mentions this name", never as a link
  to the person.
- It becomes a connection only when the article also names something from
  the subject's own records: a company, a role, a body, a co-officer, a
  place of record.
- Papers Past hits are shown as search results and are never stored as
  links (limit 17).

## The registers working: contextual connections

The connections worth having are made through the registers, not through
the name. Arthur's horse farm example is the pattern. An article names a
thing, such as a farm, a trading name or a company. The registers tie that
thing to the subject. The article is then connected to the subject by the
register's link, and the subject's own name need not appear in it.
(Arthur to write the example in.)

For this, every register's light has to be green or grey (Arthur, 4
November). The things the search looks for come from the stage-1 records:
companies, trading names, bodies and roles.

## Tranches, in order

Each tranche closes with a check that can fail against real data, a status
line and a pushed commit (ruling 244).

1. **Rulings and retirement.** Rulings 150 to 153 recorded. The templates
   are marked retired. The board's report tab points at the one report.
2. **The archive (9.1).** Built and checked against its manifest, then
   handed to Arthur.
3. **Measure the old news tables.** Their count, size and rows, from the
   catalogue. Arthur sees the list before any copy starts.
4. **The copy (9.2).** Table by table, with the row count and checksum
   checked against the source.
5. **Registers to green or grey.** Every register the report reads.
6. **Stage 1 of the one report.** On the diagnostic base, with the depth
   measured.
7. **The search index and the news section (9.3, 9.4).** This includes a
   contextual connection made through a register, shown on a real subject.
8. **Stage 2: near links on request.**

## Open, for Arthur

- **The checks.** One combined set of red, amber and clear on the one
  report, or the records with no verdicts. Not yet answered.
- **The horse farm example,** in his words.
- **Two sources to be looked at from scratch, with Arthur, before any work
  touches them.** The recovered news dump held on node1, and the news
  publisher group that the withdrawn hard limit 8 named. Earlier work on both had problems that
  kept coming back. No session relies on past notes about either.
