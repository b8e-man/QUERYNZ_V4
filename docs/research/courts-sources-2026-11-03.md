# Court and tribunal decisions the MCP lacks: where each body publishes, and a capture plan (3 November 2026, ruling 140)

Tranche 0 of ruling 140: a survey, not a capture. For each body the MCP's courts corpus lacks
(`docs/research/mcp-coverage-2026-11-03.md` §courts) it records where the body publishes its decisions,
how they can be listed, what the publisher's robots file, terms and pages say, and an estimated count
from the listing itself. Every request went through the estate's fetch gate (`support/fetchgate`), at
least 5 s apart per host, about 60 in all; each answer is landed by hash, source `courts-survey`.
Nothing was fetched in bulk. No case name is recorded here.

Positions written or extended for it (hard limit 9, ruling 61):
`docs/legal/positions/court-judgments.md` (extended: JDO and the Ministry's decisions finder),
`specialist-court-and-authority-decisions.md`, `waitangi-tribunal-reports.md`,
`professional-disciplinary-tribunal-decisions.md` (all new).

## What each body publishes, and how it can be listed

"MCP holds" is from `mcpsource.files` (corpus `courts`) by host and path, 3 November 2026.

| Body | Where | How listed | Count from the listing | MCP holds | Blocker |
| --- | --- | --- | ---: | ---: | --- |
| High Court | JDO, `www.justice.govt.nz/jdo-search-api` (JSON), PDFs under `/jdo_documents/` | court + year, 50 a page | about 38,000 (2005 to 2026; 1,400 to 2,550 a year) | 5,702 JDO files across all courts; 2,704 NZHC documents | none |
| Court of Appeal | JDO | court + year | 6,995 | 851 NZCA | none |
| Supreme Court | JDO; courtsofnz.govt.nz | court | 3,014 in JDO | 3,940 NZSC (more than JDO) | none: held |
| District Court | JDO | court + year | 2,015 | 321 | none |
| Family Court | JDO (anonymised by statute) | court | 1,143 | 75 | none |
| Youth Court | JDO (anonymised by statute) | court | 233 | 2 | none |
| Employment Court | JDO; the Ministry's decisions finder (jurisdiction 17), linked from employmentcourt.govt.nz | court; finder `start=` 25 a page | 466 JDO; about 4,100 finder | 484 | none |
| Environment Court | JDO; finder 19; its own site sends to NZLII | court; finder | 390 JDO; about 102 finder | 231 | none |
| Māori Land Court | JDO; finder 24 (its own site sends to the finder) | court; finder | 408 JDO; about 2,225 finder | none | none |
| Māori Appellate Court | JDO; finder 468 | court; finder | 47 JDO; about 425 finder | none | none |
| Employment Relations Authority | `determinations.era.govt.nz`: search by date range (10 a page, `start=`), each `/determination/view/<n>` and a PDF under `/assets/elawpdf/<year>/` | year search pages, or the view number (1 to about 21,764) | about 21,700 (2015 alone about 740) | 581 PDFs | none |
| Disputes Tribunal | finder 26 | `start=` | about 3,550 | 2 | none |
| Legal Complaints Review Officer | finder 29 | `start=` | about 1,450 | 44 | none |
| ACC appeals (District Court registry) | finder 795 | `start=` | about 1,275 | 30 | none |
| Real Estate Agents Disciplinary Tribunal | finder 32 | `start=` | about 975 | 793 | none |
| Lawyers and Conveyancers Disciplinary Tribunal | finder 279 | `start=` | about 600 | 47 | none |
| Human Rights Review Tribunal | finder 27 | `start=` | about 600 | 701 (all held) | none |
| Private Security Personnel Licensing Authority | finder 745 | `start=` | about 575 | none | none |
| Social Security Appeal Authority | finder 275 | `start=` | about 450 | 13 | none |
| Weathertight Homes Tribunal | finder 35 | `start=` | about 410 | none | none |
| Land Valuation Tribunal | finder 636 | `start=` | about 225 | 64 | none |
| Others in the finder | Canterbury Earthquakes Insurance (about 65), ACC Appeal Authority (about 75), Review Authority (35), Customs Appeal Authority (13), Student Allowance (5), Pawnbrokers (2); Taxation and Charities Review, Copyright, Victims' Special Claims and Waitangi answer none there | `start=` | about 210 | few | none |
| Coroners | coronerscourt.govt.nz: findings of public interest, files under the Ministry's `/assets/Documents/Decisions/`; finder 18 (6) | page | a handful listed; coroners publish selected findings only | 166 | none; the MCP's "578 lacking" is counted against NZLII |
| Waitangi Tribunal | waitangitribunal.govt.nz `/tribunal-reports/by-wai-number`; PDFs on `forms.justice.govt.nz/search/Documents/WT/` | the one page | 206 report PDFs | 209 forms.justice files (some may be these) | **forms.justice.govt.nz reset the connection twice** |
| Immigration and Protection Tribunal | `forms.justice.govt.nz/search/IPT/` (three databases: refugee and protection, residence, deportation) | unknown until it answers | unknown | none | **forms.justice.govt.nz resets** |
| Alcohol Regulatory and Licensing Authority | after 2014: `forms.justice.govt.nz/search/ARLA/`; before: NZLII only | unknown | unknown | none | **forms.justice.govt.nz resets**; NZLII is not a source |
| Tenancy Tribunal | `forms.justice.govt.nz/search/TT/` | the tenancy lane (`registers/tenancy_tribunal`) | its own lane | n/a | the lane's capture has **failed three nights** (31 Oct to 2 Nov), likely the same resets: outside this survey, for its lane |
| Teachers Disciplinary Tribunal | `teachersdisciplinarytribunal.nz/disciplinary-tribunal-decisions`; PDFs on `res.cloudinary.com` | the one page | 30 PDFs on the page read (decisions years 2021 to 2026 named; more may load further down) | none | the PDF host is a shared CDN: name it in the position scoped to the tribunal's account path first |
| Health Practitioners Disciplinary Tribunal | hpdt.org.nz | search page open | unknown | 790 | its decisions-documents page sends to a login: out (hard limit 6) |
| Motor Vehicle Disputes Tribunal | the Ministry's page sends to NZLII only | — | — | none | NZLII only: not a source |
| Court Martial, Court Martial Appeal Court | no official listing found | — | — | none | none found; NZLII holds some; record, not a source |
| Supreme Court, Court of Appeal and High Court on courtsofnz.govt.nz | `/judgments/<court>` lists the last 90 days of public-interest judgments; `/judgments/RSS`; PDFs at `/assets/cases/<year>/`; old files are removed (three old addresses answered 404); `/search/` stays out | RSS | 90 days only | 5,141 | the MCP covers it; nothing to add |

Robots files: none of the hosts states a crawl delay. `www.justice.govt.nz` (and the Employment Court
and Coroners sites, which serve the same file) disallows `/*/jdo` and `/jdo_documents/`;
`determinations.era.govt.nz` disallows `/determination/` and `/assets/elawpdf/`. Under hard limit 5
(ruling 10) a robots file is read for a crawl delay only; these are the Ministry's and the Authority's
own proactive publications of decisions in which no copyright exists (s 27(1)(g)), so they are taken,
slowly and off-peak.

Suppression: JDO and the finder publish no restricted decision (the Ministry's pages); Family and Youth
Court decisions are anonymised by statute before publication; the finder's file names carry `REDACTED`
where a redacted version is published; the ERA publishes no PDF where a restriction applies. Every
captured decision goes through the courts lane's `suppress.py` like the MCP's: any banner or order
withholds the names, and the Crown and initials the court printed are all that is published.

## What it adds up to

About 47,000 JDO decisions the MCP does not hold (52,700 listed less its 5,702 JDO files), about 15,000
from the finder (17,000 listed less about 1,750 held), about 21,000 ERA determinations, and up to 206
Waitangi reports once `forms.justice.govt.nz` answers: some 83,000 decisions, against the 14,528 the
lane holds today. The figures from the finder are its page count times 25, so they are within 25 of
the true number.

## Ranked capture plan

Each source is a separate job of one lane (`registers/courts`, a new `own.py` beside `capture.py`), at
one request every 5 s to a host, 22:00 to 06:00 NZ time: 5,760 requests a night a host. Hosts are paced
apart by the gate, so two hosts may run the same night.

1. **JDO, the High Court and Court of Appeal back catalogue** (`www.justice.govt.nz`). The listing by
   court and year (about 1,000 pages of 50 across all ten courts) gives every PDF address; a PDF whose
   address the MCP has already landed (`mcpsource.files.url`) is not fetched. About 48,000 requests:
   about 9 nights on this host. Then nightly: page one of each court sorted newest first, until a
   page holds nothing new.
2. **The Ministry's decisions finder** (same host, so after JDO or interleaved on the same pacer). 26
   jurisdictions, about 700 listing pages and about 15,000 files: about 3 nights. Nightly: page one of
   each jurisdiction.
3. **The Employment Relations Authority** (`determinations.era.govt.nz`, its own pacer, so the same
   nights as 1). The year search pages (10 a page, about 2,200 pages) give the PDF addresses; about
   23,000 requests: about 4 nights. Nightly: the recent list. The view number range gives a check
   that no year was missed.
4. **The Waitangi Tribunal's 206 reports**, when `forms.justice.govt.nz` answers: one listing page,
   206 PDFs, one night. The same host's Immigration and Protection Tribunal and ARLA databases are
   surveyed then (their listing service is likely the same Solr proxy the tenancy lane uses).
5. **The Teachers Disciplinary Tribunal**: one page and its PDFs, once the position names the CDN path.
6. **Not sources**: NZLII (the Environment Court's and MVDT's own pages send there; ARLA before 2014),
   the HPDT's login page, courtsofnz.govt.nz `/search/`, Court Martial (no official listing found).

So JDO, the finder and the ERA together are about 10 nights on the two hosts, and 83,000 decisions in
the store; then the reader's backlog grows by the same number.

## How a captured file joins the MCP's

The courts load lists one entry per MCP record (`capture.records`: record id, url, kind, court hint,
the file's sha256, state, `source`, `note`) and builds every table from those entries. The narrowest
change:

- a ledger table `courts.own_files` (url, listing it came from, court as the listing names it, the
  listing's citation and date, sha256, fetched_at, status), written by the new capture and never
  dropped (a captured document is never deleted);
- `capture.own_records(conn)` returning the same entry dict for each landed file, with
  `record_id = "own/<sha256>"`, `source = "courts-own"` and its own `note`;
- `load.job` takes `capture.records(...) + capture.own_records(...)`, and drops an own entry whose
  sha256 equals an MCP entry's `capture` sha256 (the MCP stays first, ruling 140): one document by
  its hash, whichever arrived first;
- before fetching, the capture skips any address the MCP has already landed, so the two only meet
  where the MCP re-captures something later, and the hash settles it.

The profiles already cover JDO files (`courts-nzhc-*`, `courts-nzca-judgment`, `courts-nzdc-judgment`)
and the finder's tribunal PDFs (`courts-tribunal-decision`, `courts-hrrt-decision`); the ERA's PDFs
are `courts-era-determination`. A JDO listing row carries the case name and the PDF address only, so
dates and citations come from the document's own caption, as for the MCP's files today.

## Found on the way

- The tenancy lane's capture failed on 31 October, 1 and 2 November; `forms.justice.govt.nz` reset two
  survey requests the same day. For the tenancy lane.
- The gate holds one class per host (`fetchgate.positions` keeps the last file's), so a host shared by
  two classes (here `www.justice.govt.nz`, under `agency-contract-disclosures.md`) is recorded under
  one of them. This page's class is named in `court-judgments.md`'s body for those paths.
