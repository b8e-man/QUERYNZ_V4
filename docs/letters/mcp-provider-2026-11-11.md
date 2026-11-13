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
- **Later on 13 November (our ruling 174): the Electoral Commission, every document.** Request
  `estate-collect@2026-11-13b`. Collect every document the Commission publishes, of every year and
  every kind, results included, except those on `held-electoral-commission.tsv`. A year we hold is
  not complete until its listings say so: take any document on them that is not on our list. The
  results of 1999 to 2025, which we hold only as figures, are asked.

## 13 November: a requests channel in the MCP (our ruling 175)

We ask you to add a requests channel to the MCP you serve us, so requests, amendments and replies
stop travelling by hand: `asks_put`, `asks_get` and `asks_status`, as proposed in
`asks/channel-request-2026-11-13.json` (request `estate-channel@2026-11-13`). Change the shapes if
your side needs to, and tell us when it can answer. This is the only file we send by hand: our
amendment `estate-collect@2026-11-13b` waits for the channel and will be its first `asks_put`.

## 13 November: the channel is live (ruling 175)

The provider built `asks_put`, `asks_get` and `asks_status` (their messages out-c3355b3d82a84b5e,
out-231b87f71b1ed49a). Their answer to estate-collect@2026-11-13 (out-8309e5f7e04f4cdb): Electoral
Commission collecting (an Incapsula interstitial challenges many reads, which stay failed reads; they disclose
the collection runs from a residential session); Hansard collecting, 1,862 day-PDFs from 2003-02-11, nothing
served before 2003; legislation blocked by an AWS WAF challenge; courts finder collecting (208 so far,
22 jurisdictions, page 1 checked hourly); the 73 sites not started. They asked four things.

Our first put, in-e948118a044e34b3 (21:40 UTC on 12 November): estate-collect@2026-11-13b, the amendment
(`asks/collect-amendment-2026-11-13b.sent.json`) with the four held lists attached, and the answer to their
ask 1: the amendment governs and its replace_section supersedes the shipped collect.json's Electoral
Commission section. Asks 2 to 4 wait on Arthur.

Our second put, in-145e39a8cf689599: estate-collect@2026-11-13c, kind answer (`asks/collect-answers-2026-11-13c.sent.json`),
on Arthur's word: no route to the Commission's challenged documents, so they stay failed reads; legislation is ours
through the PCO keyed API (the key is Arthur's to apply for); Hansard before 2003 accepted as not served by
parliament.nz and kept as our own gap, Papers Past not used.

## 13 November: Yellow and White Pages, and the NZME backwalk

Their question out-b0a417ce43d2b52b (both directories moved to Thryv; White Pages residential off the web since 13 July
2026; detail pages behind /ycaptcha, yellow.co.nz behind Cloudflare) answered as estate-directories@2026-11-13
(in-5c70aa8ae4fa67b8, `asks/directories-2026-11-13.sent.json`): we hold none and want both, everything, historic
included (ruling 174); Wayback for history, the open sitemaps collected, challenged pages stay failed reads; the print
book and a data ask to Thryv are Arthur's to decide, neither done meanwhile. Their NZME backwalk question
(out-2ab57f8b72914e01) waits on Arthur.

## 13 November, 07:06 UTC: directories amended (estate-directories@2026-11-13b, message in-dc16f96e7e9ac323)

Arthur: "forget thryv, forget print. what we want is to gather the full most recent copies of both white and yellow
pages and record changes retrospectively". Sent as kind collect, amending estate-directories@2026-11-13: print book,
Thryv ask and ebook probe withdrawn; the newest copy of every listing (open sitemaps and unchallenged pages kept current;
the newest archived copy where the live page is challenged or removed); history from the Wayback CDX index (every URL on
the three hosts, all years, each distinct digest fetched raw) and the Common Crawl index, every row and capture whole
with its timestamp. Challenges stay failed reads. The full body is handover/asks/directories-2026-11-13b.sent.json.

## 13 November, 07:57 UTC: every council's minutes (estate-council-minutes@2026-11-13, message in-1e32a592db7633f4)

Arthur's yes. Kind collect, with held-council-minutes.tsv (990 documents, 21 councils, nearly all 2026): every
meeting document of all 78 councils, every body, all years served, Wayback for older years, the 3,335 listed but
unfetched documents, and a weekly check for new ones. Body: handover/asks/council-minutes-2026-11-13.sent.json.
