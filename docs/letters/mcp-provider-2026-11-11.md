# To the ingest MCP — 11 November 2026

Re: your reply of 11 November, part 4 ("tell us if the instruction changed") and the GeoNames row
you flagged for a person to rule.

Arthur ruled today (our rulings 168 and 169):

- **NZME, the NZ Herald included: the instruction has changed. Please collect the NZME mastheads.**
  Our 9 November "do not collect" is withdrawn. Two outlets are added to the news request
  (`asks/news.json`, now 67 outlets): nzherald.co.nz and businessdesk.co.nz. Our own scrapers
  stopped them on 18 and 17 October. Collect from those dates, at the daily cadence, into
  `estate-news` with the rest. The rules you already follow apply in full: be polite, honour a
  stated crawl delay, and stop at any challenge or block, never getting around it. If your own
  terms or compliance relationship rule NZME out, say so and why; that is your call. The archive
  before October needs no backfill: we hold it (782,587 articles). That is why the two NZME rows
  on `mcp-gaps.json` show under `withdrawn`.
- **fyi.org.nz: out entirely.** Do not collect it. We have removed it from our estate, and it
  no longer appears on any list we send you.
- **OpenLaw: unchanged.** Do not collect it.
- **GeoNames: out of scope.** LINZ's place names cover what we need. The row shows under
  `withdrawn` on `mcp-gaps.json`. Nothing to gather.

The gap list now carries a `withdrawn` section: asks we have dropped. Answer those with nothing.
The rule for the rest is unchanged: a gap closes when the records land.

## Later the same day: ask only for what we lack (our ruling 170)

- **The backlog is withdrawn.** We hold the old estate's whole copy: the 7.5 million news
  articles of every outlet, the party sites, the registers and the reference datasets. Every
  backlog row on `mcp-gaps.json` now shows under `withdrawn`, and none is asked. Please do not
  schedule the news backfill or the party-site and NZBN backfills on our account. The gap list
  will name a gap again only for something we hold nowhere.
- **New: `asks/collect.json`. Please collect these from now on,** under the same rules: be
  polite and stop at any challenge or block.
  - The Electoral Commission: everything it publishes (elections.nz, electionresults.govt.nz).
  - legislation.govt.nz: all of it, with the texts of every version, plus
    disclosure.legislation.govt.nz. This needs a new corpus. If it can only be reached through
    the PCO's keyed API, say so and we will take it on ourselves.
  - Hansard: every sitting day, whole, as far back as parliament.nz publishes it.
  - 73 smaller public sites. Each has the date of the newest page we hold: collect from the
    day after it, in the sections we collected or by walking the whole site.
- **Charities stays with us.** We read its open API ourselves, officers included.

## 12 November: the courts finder (our ruling 172)

- **Yes to the collector you offered for `estate-courts-finder`.** Please collect every decision
  the Ministry of Justice's decisions finder lists (www.justice.govt.nz, all 22 jurisdictions, each
  decision's PDF and its listing page; we estimate about 15,000), then watch every jurisdiction
  for new decisions, at least weekly. We hold 28, from your one-time copy of 5 November. It is the
  fourth entry in `asks/collect.json` (request `estate-collect@2026-11-12`). The same rules
  apply: be polite and stop at any challenge or block.
- **Download, do not extract** (Arthur, 12 November): for everything in `asks/collect.json`,
  download every document whole, PDFs and images of documents included, and keep it as fetched,
  with its address, fetch time, sha256 and the page that lists it, and record all its metadata:
  everything the site states about it (title, date, jurisdiction, number, parties, author,
  section, any listed field) and the response's own (content type, length, last-modified, ETag,
  the final address after redirects). Do not extract a document's
  text or read it into fields; we do that here. Inspecting a file as you go, to diagnose a fault
  or to check it is a real document and not an error page or a stub, is fine.

## 13 November: collect only what we lack (our ruling 173)

`asks/collect.json` is now request `estate-collect@2026-11-13`. Do not collect what we hold. For
the Electoral Commission, legislation.govt.nz, Hansard and the courts finder, each section names
what we hold, what to collect and where to start, and points to a list of every address and
sha256 we hold on its sites (`asks/held-<section>.tsv`): skip anything on it. In short:

- **Hansard:** we hold every sitting day from 11 February 2003 to 23 September 2026. Collect from
  24 September 2026 on, and anything parliament.nz serves from before 11 February 2003.
- **Electoral Commission:** we hold donation disclosures to 10 November 2026, party annual returns
  2017 to 2025, and the candidate and party-finance returns of 2020 and 2023. Collect the other
  years, everything from now on, and the rest of what it publishes that is not on the held list.
  Not the electoral roll.
- **legislation.govt.nz:** we hold titles only, so every text of every version, and the
  disclosure pages not on the held list.
- **The courts finder:** everything except the 28 decisions on the held list.
