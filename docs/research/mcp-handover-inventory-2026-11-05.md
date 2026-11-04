# Handover inventory for the ingest MCP's provider: the sources we gathered ourselves (5 November 2026)

On 5 November 2026 Arthur agreed that every website crawl and document download the estate runs moves to the
ingest MCP. This note hands each of those sources over: where it lives, how we walked it, how much we hold, what
went wrong, what we learned, and what is still missing.

**What stays with us.** The keyed APIs: business.govt.nz (NZBN, the Companies Office registers, insolvency),
LINZ, DigitalNZ (our Gazette source), data.govt.nz, the sanctions lists, and LINZ's overseas-investment decisions.
They are not described here.

**What moves.** Sixteen lanes and the courts lane's own captures, listed in the table below. A "lane" is our
pipeline for one source; its code is under `registers/<lane>/`. For the sources the MCP already gathers for us
(Parliament, Hansard, Beehive, ministers' diaries, the courts corpus, GETS), the last section lists only what we
learned about those sites.

**How to read the figures.** Counts were taken on 5 November 2026 from our document store and the lanes' tables.
"Docs" are distinct files by their bytes (sha256); one file is often seen under several URLs or names, and we
count it once. "Names" are the URLs and file names it was seen under. Dates in the "content" column are the
documents' own dates (decision, meeting, election), not the day we fetched them. Nothing here names a person;
figures are counts only. No credential or key appears anywhere in this note; where a source needs one, the
provider needs its own.

**State on 5 November** is each source's light on our board at 05:30 NZDT: green (updates working), orange
(working but not whole), red (the last run failed, or a host it reads is held), off (no job running).

## Summary

| Source | Lane (capture) | Main hosts | What we capture | Docs held | Main rows | Content dates | Cadence | State on 5 Nov | Main gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Charities Register | `charities` | www.odata.charities.govt.nz; www.charities.govt.nz | OData JSON pages of 1,000 by key; feed metadata, terms, data dictionary | 1,201 (5,109 MB) | 46,139 charities; 589,366 officers; 430,739 returns | registered Feb 2007 to Oct 2026 | nightly 23:30; changes by ModifiedOn; full pass every 28 days | red at 05:30 (one DNS failure 4 Nov 23:31); green again 05:38 | charity rules and return PDFs (not in the feed); data dictionary refused (403) since 27 Oct |
| Class 4 gaming and Lottery grants | `grants` | catalogue.data.govt.nz; www.communitymatters.govt.nz; ~10 society sites | DIA national CSV; society grant lists (PDF); Community Matters pages | 504 (122 MB) | 196,494 grants | 2017 to Sep 2026 | nightly 22:45; 30-day re-asks | green; Community Matters 403 every night since 22 Oct | every Lottery record of grants; 118 society files in unread layouts |
| Commerce Commission case register | `commerce_commission` | www.comcom.govt.nz | listing and entry pages (HTML) | 1,726 (159 MB) | 1,684 cases | 1986 to Oct 2026 | weekly full pass | green; listing never yields its stated total | ~44 entries the paged listing never reaches |
| FMA warnings and enforcement | `fma` | www.fma.govt.nz (Cloudflare) | two listings and item pages (HTML) | 913 (112 MB) | 802 actions | 2010 to Oct 2026 | weekly full pass | green; new robots content signals | ~26 enforcement cases beyond page 5 |
| WorkSafe court summaries and undertakings | `worksafe` | www.worksafe.govt.nz | two listings and item pages (HTML) | 737 (328 MB) | 665 actions | 2013 to Jun 2026 | weekly full pass | green | 5 undertaking pages of an odd shape |
| Building Practitioners Board decisions and the LBP register | `building_practitioners` | www.lbp.govt.nz; kete-lbp.mbie.govt.nz | decision list pages; 26 register searches; practitioner pages | 13,403 (7,762 MB) | 790 decisions; 8,792 practitioners | decisions 2018 to Sep 2026 | decisions weekly; register nightly, ~4,400 pages | green; register copy half done (13,213 of 26,978) | ~13,765 practitioner pages; decision PDFs; sub-tables behind a POST |
| Real Estate Authority decisions | `real_estate_authority` | decisions.dotnous.com; www.rea.govt.nz | year listings, abstracts, decision PDFs | 8,110 (2,145 MB) | 3,063 decisions | 2010 to Sep 2026 | nightly 23:00 | green | 27 abstracts that showed no decision; decisions dropped before 18 Oct |
| Te Kāhui Māngai (iwi directory) | `iwi_directory` | www.tkm.govt.nz | whole-site HTML walk (~229 pages) | 251 (3.6 MB) | 2,697 entities | undated | weekly walk | green | nothing wanted is missing |
| Te Haeata (settlement commitments) | `settlement_commitments` | tehaeata.govt.nz | the login page, watched; 4 about-pages | 7 (0.1 MB) | none | none | nightly watch (1 request) | green; the login wall stands | the whole record (behind a login) |
| Council minutes on InfoCouncil | `council_minutes` | 20 `*.infocouncil.biz` + 4 `infocouncil.<council>.govt.nz` | listing pages; minutes PDFs | 1,005 (287 MB) | 1,388 meetings (21 councils) | 2024 to Nov 2026, nearly all 2026 | listings weekly; PDFs nightly | green | earlier years; Christchurch, Kāpiti, Hawke's Bay Regional; 57 councils not on InfoCouncil |
| Councillors' registers of interests | `councillor_interests` | 78 council sites (88 hosts) + 3 document stores | landing pages; register PDFs | 447 (193 MB) | 78 registers; 8,991 interests (42 councils) | 2014 to 2026 | landing pages monthly; each document once | red: Dunedin, Gisborne, Kaipara held since 4 Nov | 11 councils blocked, 3 barred by terms, 13 not found |
| Local election candidates' returns | `local_elections` | 43 council sites, 45 file hosts | listing pages; return PDFs, Word files, scans | 2,055 (2,085 MB) | 2,147 returns (43 councils) | 2017 to 2026 | listings weekly; files nightly | red: Dunedin, Gisborne, Kaipara 403 since 23 Oct, held since 4 Nov | 97 returns behind holds; 177 corrected addresses not yet asked; 35 councils |
| Council procurement off GETS | `council_procurement` | 3 council terms pages; vendorpanel.nz | terms pages only | 3 (1.1 MB) | none | none | switched off (ruling 136) | off | council award and tender lists, by decision |
| Electoral Commission candidate returns | `candidate_returns` | elections.nz (Incapsula) | return PDFs and amendments; listing pages; summary spreadsheets | 1,165 (2,466 MB) | 1,105 return files | 2020 and 2023 elections, 2022 by-election | old estate's headed browser, nightly retry; full walk by hand | green | 2026 returns (due after 7 Nov); 175 scans unread; ~19 listed returns not held |
| Electoral Commission donation disclosures | `disclosures` | elections.nz (Incapsula) | the two listing pages; scanned declarations | 322 (170 MB) | 530 declarations | gifts Apr 2008 to Oct 2026 | old estate's headed browser, daily 03:30 | green; one declaration refused 3–4 Nov | scans for the 244 rows from 2008 to 2022 |
| Tenancy Tribunal orders | `tenancy_tribunal` | forms.justice.govt.nz | monthly Solr listing (JSON); order PDFs | 20,838 (2,956 MB) | 33,847 orders listed, 20,778 held | Oct 2023 to Oct 2026 | nightly 22:30 | red: PDFs reset since 25 Oct; host held since 4 Nov | 13,069 order PDFs (published Jun 2025 to Oct 2026) |
| Judicial Decisions Online | `courts` (`courts-jdo`) | www.justice.govt.nz | listing JSON; decision PDFs the MCP lacks | 6,142 (1,847 MB) | 5,932 files landed | High Court 2020 to 2026 | nightly 22:00–06:00 | walking; host never refused | High Court 2005 to 2019; every other court (~40,000) |
| Employment Relations Authority | `courts` (`courts-era`) | determinations.era.govt.nz | search pages; determination PDFs | 40 (10 MB) | 36 files | Dec 2014 (trial) | nightly 22:00–06:00 | failed 3 and 4 Nov (our date bug, fixed 5 Nov) | ~21,700 determinations, 2000 to 2026 |
| Ministry decisions finder | `courts` (`courts-finder`) | www.justice.govt.nz | finder pages; decision PDFs | 30 (7.3 MB) | 28 files | 2014 to 2022 (one tribunal, trial) | after the JDO walk each night | trial only | ~15,000 decisions across 21 jurisdictions |
| Courts survey | `courts` (`courts-survey`) | 11 court and tribunal hosts | reference pages, robots files | 45 (5.4 MB) | none | as at 3 Nov | once | done | none |
| courtsofnz.govt.nz and the old estate's court copies | `courts` (`courts`) | www.courtsofnz.govt.nz; forms.justice.govt.nz | RSS feeds, case pages, judgment PDFs | 379 (1,289 MB) | none | 2023 to 2026 | retired 30 Oct | retired | 206 Waitangi Tribunal reports (host held); 79 judgments the MCP lacks |

Docs held are distinct files by sha256, with megabytes in brackets. Times are NZDT.

## How we fetched, for every source

Every request went through one fetch gate (`support/fetchgate`). Its rules are the terms we hand over with the
sources, and we ask the provider to keep to them for anything it gathers for us:

- **Open pages only.** Nothing behind a login, a paywall or a challenge. We never solve a challenge or CAPTCHA,
  never use a login that is not ours and never get around a block. A headed browser that is shown no challenge
  may read a page; shown one, it stops. A challenged read is a failed read.
- **A refused host stops gathering** (Arthur's ruling 141, 3 November 2026). A 403, 429 or 503, or a challenge
  page, holds the host at once; three transport failures in a row on one host (a reset, a refusal, a timeout, a
  500, 502 or 504) hold it too. A held host is sent nothing more by anyone until a person clears it. A hold is a
  prompt to find another way (the MCP, a bulk release, an arrangement with the publisher), not to retry. The
  gate also treats a small page (under 64 KB) carrying a challenge mark (`cf-chl`, "just a moment", "captcha",
  "access denied", Imperva's `x-spa-interstitial` header and similar) as a block.
- **Robots files** are read for one thing: a stated crawl delay, which is honoured. They are archived with their
  hash. A crawl delay above 120 s is honoured at 120 s.
- **Pacing.** One request at a time per host, never in parallel on a host. The gap between requests to one host is
  the slowest of 1.5 s (default), the host's stated delay, its robots crawl delay, and 5 s where we judged the host
  small or fragile. Off-peak: 284 of 323 capture runs started between 21:00 and 02:00 NZDT. Nothing fetched twice: every file is
  kept by its sha256, and a URL already held is not fetched again unless the lane is checking for change.
- **One User-Agent** for the whole estate, naming the project and a contact address. No rotation of exits or
  agents; the pacer is keyed by host, so a second exit would never buy speed.
- **Redirects are not followed unasked.** A 3xx is recorded with its Location; following it is a new request,
  judged and paced as one.
- **Out by name:** fyi.org.nz and every NZME masthead (the NZ Herald, BusinessDesk, Newstalk ZB, the Gisborne
  Herald, OneRoof, Driven). Neither is captured, indexed or read.
- **A legal position per class of source.** Before a class of source was captured we wrote a one-page legal
  position: is the page open without getting past a lock; is storing it lawful copying; what terms did we accept;
  what does privacy law or the register's own statute limit. Each section below names its position file
  (`docs/legal/positions/<name>.md`) and gives its gist.

**A document is its bytes.** We identify every file by sha256, never by its file name or URL. Several publishers
put one file under several names (the Electoral Commission publishes one return under several file names and
every amendment as a separate file; councils link one PDF from several pages). Anything the provider sends us is
matched to what we hold by sha256, so nothing is held twice.

**What we ask of the provider for each source** (as in our note of 3 November): the original bytes and response
headers of every file; the document's own date as a field, separate from the day it arrived; a change feed in
which every change moves `updated_at` and a removal is shown; a re-fetch when a document changes, with a new
record (or an updated sha256) when its bytes change; and a record, per source, of any host that refused or
challenged you.

# The sources moving to the MCP

## Charities Register (lane `charities`)

**Hosts and entry points.** `www.odata.charities.govt.nz`: an OData version 2 service, no login, no key. The service publishes itself on http; https answers the same. Every request takes `$format=json`. Ten keyed sets: Groups, Activities, Beneficiaries, Sectors, SourceOfFunds, Organisations, vOrganisations, Officers, AnnualReturn, AnnualReturnCloseRelationshipTransaction. Each is paged as `/<Set>?$format=json&$orderby=<Key>&$top=1000&$filter=<Key> gt <last key>[ and ModifiedOn ge datetime'<UTC>']&$inlinecount=allpages`. The keys are GroupId, OrganisationId, OfficerId, AnnualReturnId and so on. Ten code lists are fetched whole, one request each: AreaOfOperations, AuditModifiedOpinionReceived, LegalStructure, ReportingCurrency, ReportingTier, MainActivity, MainBeneficiary, MainSector, OfficerStatus, RegistrationStatus. `/$metadata` is fetched too. A count probe asks for one row with `$top=1&$select=<key>&$inlinecount=allpages`, for example `$filter=RegistrationStatus eq 'Registered'`. Documents about the feed come from `www.charities.govt.nz`: the open-data page (`/charities-in-new-zealand/the-charities-register/open-data/`), `/terms-of-use`, `/copyright`, `/im-a-registered-charity/restricting-information`, the data dictionary (`/__data/assets/excel_doc/…/Data-Dictionary-17.09.2025.xlsx`) and the entity diagram (`/__data/assets/pdf_file/…/Charities-OData-ERD.pdf`). The register's own search (`register.charities.govt.nz`) is not used.

**What we capture.** The feed's JSON pages, verbatim, each stored by its sha256. We also land the `$metadata` XML, the HTML pages about the feed, the data dictionary (xlsx) and the diagram (PDF). Nothing is parsed at capture time.

**Held.** 1,201 documents, 5,108.6 MB in all. Of these, 1,190 are JSON pages (5,107.5 MB, about 4.3 MB each). The rest are 9 web pages, 1 PDF and 1 spreadsheet. They sit under 1,211 distinct names. One sha256 was seen under more than one name. Four names have held more than one sha256. Fetched 20 October 2026 to 5 November 2026. Published rows: `pub.charities` 46,139 (29,278 Registered, 16,593 Deregistered, 268 Removed), `pub.charity_officers` 589,366, `pub.charity_returns` 430,739, and 357 groups. Registration dates in the content run from 8 February 2007 to 23 October 2026. Return periods end between 1 March 2007 and 30 September 2026. The newest registration is 23 October 2026 because the 403s from 27 October to 3 November stopped the captures, and the published copy has not yet taken in the 5 November capture.

**How we walk it.** The order of a run changed on 5 November 2026 (commit 7c05544): the keyed sets first, then the code lists, then the documents about the feed. Paging goes by key: each request asks for "key greater than the last held", 1,000 rows a page, which is the feed's own cap. We never use `$skip`, because it shifts when rows are added mid-copy, and we never use `$returnall`. The first page of each pass asks for `$inlinecount`, and the pass reconciles to that figure. A full pass of every set runs every 28 days. In between, a changes pass asks for `ModifiedOn ge` one day before the last pass began. The feed compares that literal in UTC, not NZ local time. Sets with no ModifiedOn are copied whole weekly: Activities, Beneficiaries, Sectors and SourceOfFunds, which hold 12,728, 7,540, 6,361 and 2,772 rows. The code lists and documents are also asked for weekly. A pass that stops part-way resumes from its last key on the next run. The first full copy took two nights (20–21 October 2026, 1,146 requests, 7,115 s). The register's count of Registered charities is landed with each full pass of Organisations. A page whose bytes are already held adds a name, not a document. Job `qv4-charities-capture` runs nightly at 23:30 NZDT. Its budget is 4 hours and its hard deadline 5 hours, with 0.5 GB of memory. It runs only in off-peak hours, 22:00 to 06:00 NZ. One request is in flight at a time, with 5 s of rest after each answer (the gate floor for the odata host is 5 s). The gate's floor for `www.charities.govt.nz` is 1.5 s. Every request carries the estate's single User-Agent, which names the project and a contact address. A redirect to another host stops the run unfetched. A 403, 429, 5xx or challenge stops the run. Since 5 November 2026, a single transport failure on a keyed set's page leaves that pass open and the run moves to the next set. Three transport failures in a row stop the run. Our load (`qv4-charities-load`) runs at 06:30 NZDT.

**Legal position.** `docs/legal/positions/charities-register.md` (a draft under ruling 61). The data is Crown copyright, licensed CC BY 3.0 NZ on the open-data page, with attribution owed to Charities Services. The site's general copyright page is narrower ("personal or in-house use"); a lawyer is to confirm that the data licence governs the feed. No terms were accepted by click. The open-data page says the feed is for developers, caps every query at 1,000 rows, and says email addresses on the register must not be harvested for marketing (Unsolicited Electronic Messages Act 2007). Charities Act 2005, s 24, sets what the register shows. Section 25 lets Charities Services restrict information, and restricted data is already withheld from the feed. Both hosts answer 404 for robots.txt, so no crawl delay is stated.

**What went wrong and what we learned.**
- 20 October 2026: Activities, Beneficiaries, Sectors and SourceOfFunds look like code lists but hit the 1,000-row cap. They hold every "Other – …" entry a charity typed, so they are now paged as keyed sets.
- 21 October 2026: the feed's `datetime` literal is read as UTC. A local-time literal returned the wrong change set (228 rows, against a last change at 06:02 UTC).
- 22 October 2026: the lane now stops on a redirect whose Location is on another host.
- 27 October to 3 November 2026: every night `www.charities.govt.nz` answered HTTP 403 for the data dictionary xlsx (27–30 October), then for the diagram PDF (31 October to 3 November). The documents were then asked for first, so the 403 stopped the whole run each night and no register pages were captured for eight nights. The odata host itself never refused. The fix (5 November 2026, commit 7c05544): the register is fetched first and the documents last, and a refusal on the documents ends only their part. The gate log shows no hold recorded for that host. Those two document passes are still open.
- 4 November 2026, 23:31: one DNS name lookup failed on the odata host, on the Groups changes pass's first page ("No address associated with hostname"), between good answers. It stopped every set after it. Fixed in commit 1cd04be: a single transport failure leaves that set's pass open to resume, and the run continues. The re-run at 05:38 on 5 November 2026 was green (40 requests, 35,895 rows).
- The old estate's weekly job reads the same feed outside any gate (card `two-fetchers-on-the-charities-feed`, open). The publisher may see two readers from us.
- AnnualReturnCloseRelationshipTransaction reports 0 rows on every pass.

**Still missing.** The data dictionary and diagram have not been re-fetched since 27 October 2026 because of the 403s; earlier copies are held. We hold no document from the register itself: charity rules, annual-return PDFs and financial statements are not in the feed, and `register.charities.govt.nz` is not used. The register's count of Registered charities lands only at the next full Organisations pass (about 17 November 2026; not verified).

## Class 4 gaming grants and Lottery grants (lane `grants`)

**Hosts and entry points.**
- `catalogue.data.govt.nz`: the package page `/dataset/class-4-grants-data` links the national CSV "Grants from Gaming Machine Profits" (`/dataset/<id>/resource/<id>/download/…`).
- `www.communitymatters.govt.nz`: walked whole from `/`, because its Lottery "record of grants" pages (for example `/lottery-community/<year>-round-two-lottery-community-national-record-of-grants`) hang off no index.
- `www.dia.govt.nz` (`/Copyright`, `/Terms-of-use`, a statistics page).
- `granted.govt.nz`: a script application whose JavaScript bundle carries the Department's list of 31 societies and their websites.
- Class 4 societies' own sites. The walk starts at each society's grants page: `www.nzct.org.nz/grants`, `www.airrescueservices.co.nz/grant-distributions/`, `www.pelorustrust.net.nz/grants`, `www.agt.nz/resources/funding-distributions`, `onefoundation.nz/grants`, `trustaoraki.co.nz/grants-list/`, `www.newhorizoncommunitytrust.co.nz/approved-grants/`, `www.milestonefoundation.co.nz/grant-recipients.html` and `wecare.org.nz/historical-grants.html`. It follows links two deep and lands every file whose address or link words speak of grants. About 20 more society hosts were surveyed on 21 October 2026, home page and grants pages only.

**What we capture.** The national CSV, verbatim. Community Matters pages, verbatim HTML. Society grants pages (HTML) and their grants files (mostly PDF), verbatim. The pages about the sources (copyright, terms, privacy).

**Held.** 504 documents, 122.0 MB: 414 PDFs (78.3 MB), 83 other (5.7 MB), 5 web pages, 1 CSV (37.7 MB) and 1 spreadsheet. They sit under 504 distinct names. No sha256 has more than one name. Fetched 22 October 2026 to 4 November 2026; the survey requests were on 21 October 2026. By list: 415 society files (151 recognised by a profile; 118 lines in `unprofiled.list`; 7 are scans with no text layer), 56 society pages, 27 Community Matters pages, 1 national CSV, 1 catalogue page and 5 about-pages. Published rows: `pub.grants` 196,494 (126,747 Accepted, 69,739 Declined, 8 Refunded), `pub.grant_recipients` 97,618 and `pub.grant_publishers` 39. The national file gives 178,729 grants decided from 1 January 2021 to 31 December 2025. The society lists give 17,765 grants for periods from July 2017 to September 2026. No Lottery grant is held.

**How we walk it.**
- The catalogue's package page is asked at most every 30 days; the CSV only when the page or its link changed. The Department updates the file about once a year.
- Community Matters is a resumable whole-site walk (frontier table, maximum depth 8). Each page is asked again after 30 days. A page that blocked is marked asked, so the next night does not open on it.
- Each society's grants pages are asked again after 30 days. Each grants file is landed once and never asked again: a society publishes a new list as a new file. A file whose name dates it wholly before 2017 is not asked.
- Job `qv4-grants-capture` runs nightly at 22:45 NZDT, off-peak only. Budget 4 hours, deadline 5 hours, 0.3 GB.
- One request at a time, 5 s apart. The catalogue gets 10 s, its own robots Crawl-Delay, and so do `mainlandfoundation.co.nz` and `www.mainlandfoundation.co.nz`, whose robots files set 10 s for every agent. After a 5xx the run rests 60 s, and three failures in a row stop that host.
- A 403, 429 or challenge stops that host for the night and the run moves to the next list.
- Redirects are never followed blind. The lane asks the gate about each hop and leaves a page that points off the publisher's host unasked.
- Every request carries the estate's single User-Agent, which names the project and a contact address.
- Our load (`qv4-grants-load`) runs at 06:35 NZDT.

**Legal position.** Two files.
- `docs/legal/positions/dia-gambling-and-lottery-grants.md`: the national file is CC BY 4.0, per the catalogue and the Department's copyright statement, attributed to Te Tari Taiwhenua Department of Internal Affairs. No terms were accepted by click. The Department's terms are a disclaimer only. Community Matters' own copyright page has never been read, because the host refused before the walk reached it. Gambling Act 2003, s 110(4) requires each society to publish its grants, approved and declined. Recipients may be individuals, and declined applications are published. Crawl delay: the catalogue states 10 s; the Department and Community Matters state none.
- `docs/legal/positions/class-4-society-grant-publications.md`: the societies' lists are published under s 110(4). No licence is stated; footers carry plain copyright lines. Facts are read and cited. A lawyer is to confirm society by society before anything is sold. No society terms page was found. Crawl delay: none stated where read, except Mainland Foundation's 10 s.

**What went wrong and what we learned.**
- 21 October 2026 (session grants-1): a catalogue search page (`catalogue.data.govt.nz/dataset?q=…`) answered HTTP 200 with Imperva's interstitial ("Pardon Our Interruption", a `reese84` script, an `X-SPA-INTERSTITIAL` header). The gate did not recognise it at first and landed it as a document; it is held and never read. The gate now treats that title, header and script as a block (fix-support-fetchgate-1, 22 October 2026). The package page and the CSV, asked directly, answered normally. `www.data.govt.nz` showed the same wall to another lane.
- 21 October 2026: urllib followed a redirect from `www.trillian.nz` to `www.trillian.co.nz`, a host no position named. The gate now returns redirects to another host unfetched.
- 22 October 2026 to 4 November 2026: Community Matters answered HTTP 403 every night. The first walk landed 15 pages, then got a 403 on the 16th. Since then each night lands 0 to 4 pages before a 403 on the next. The capture job is logged as failed on 24, 27, 29 and 30 October and on 1, 2 and 3 November 2026 (nothing landed), and as OK on the other nights. It is unknown whether the 403 is tied to particular pages or to request rate; the card suggests raising the floor to 10 s, then 30 s. No Lottery record of grants has ever been landed live.
- 22 October 2026: NZ Community Trust's lists redirect to `static1.squarespace.com`, a shared host no position names, so they are not followed. One Foundation's lists are built by script: 156 frontier addresses are unasked. A Trust Aoraki file returned 404. New Horizon has 10 frontier pages with non-200 statuses.
- Quirks in the society files: Pelorus's declined list for 28 April 2026 serves the approved list again; Milestone's February 2019 file is titled February 2018; We Care's 2022 lists differ from the national file (52 grants against 55). Seven files are scans with no text layer.
- `youthtowntrust.org.nz` was refused by the gate (no legal position names it).

**Still missing.** Every Lottery Grants Board record of grants: Community Matters blocks the walk. The older Lottery recipient CSVs on the data catalogue (to 2017/18) were not tried. 118 society files are in layouts no profile reads (Milestone 2020–2026, Trust Aoraki 2016–2022 and 2024–2025, We Care's declined lists and 2023–2025). Not reached: NZ Community Trust (Squarespace host), One Foundation (script-built), about 20 other societies whose lists were not found among the first pages, and two dead addresses. Also not landed: Kānoa regional funding (CC BY-NC file) and TEC (challenged).

## Commerce Commission case register (lane `commerce_commission`)

**Hosts and entry points.** `www.comcom.govt.nz`. Listing: `/case-register/?q=&size=100&page=N`, newest first, 100 a page, 18 pages. The page carries the register's own count in a `:total="N"` attribute (1,727 on 21 October 2026; 1,728 on 29 October 2026). Entries: `/case-register/case-register-entries/<slug>`; some slugs are `withheld-N` or `withheldN`. About-pages: `/using-our-website/copyright/`, `/using-our-website/disclaimer/`, `/using-our-website/privacy/` and `/case-register/about-our-case-register/`. `comcom.govt.nz` (the bare domain) was asked once.

**What we capture.** Listing pages and entry pages, verbatim HTML. We do not follow or fetch the documents an entry links.

**Held.** 1,726 documents, 159.0 MB, all web pages, under 1,706 distinct names. No sha256 has more than one name. 20 names have held more than one sha256 (re-fetched after the entry changed). Fetched 21 October 2026 to 29 October 2026. Published rows: `pub.commerce_commission_cases` 1,684 and `pub.commerce_commission_parties` 2,446. Cases opened from 23 June 1986 to 20 October 2026. 335 cases carry `taken_down_on` (see below).

**How we walk it.** A full listing pass at most weekly (`FULL_EVERY_DAYS` = 7), resuming from its next page. Each listed entry gets a fingerprint made from its card's status, outcome, date closed and tag. An entry is fetched once, and again only when its fingerprint changes. About-pages are fetched every 30 days. Job `qv4-commerce-commission-capture` runs nightly at 22:30 NZDT; on nights with no pass due it makes 0 requests. Budget 4 hours, deadline 5 hours, 0.3 GB, off-peak 22:00–06:00. One request at a time, 5 s floor (gate). After a 5xx it rests 60 s. A 403, 429 or challenge stops the run, as does a redirect to another host or three failures in a row. Every request carries the estate's single User-Agent, which names the project and a contact address. First pass: 21 October 2026, 1,216 requests in 6,084 s. Second: 29 October 2026, 510 requests. Our load runs at 06:20 NZDT.

**Legal position.** `docs/legal/positions/commerce-commission-case-register.md`. Crown copyright, licensed CC BY 4.0, attributed to the Commerce Commission; logos and images are excluded. The disclaimer says project dates "are not official" and a link must not imply endorsement. Neither bars reuse. The Commission writes "Withheld" for parties it does not name. Some pages state a suppression (Criminal Procedure Act 2011, ss 200–211). The existence of an investigation is not a finding of breach. robots.txt disallows only `/admin`, `/dev` and error pages, and states no crawl delay.

**What went wrong and what we learned.** The listing does not enumerate the whole register. On 21 October 2026, 18 pages of 100 gave 1,194 distinct entries against a stated 1,727. On 29 October 2026 they gave 1,349 against 1,728. Both passes together reach 1,684. The cause is not verified; the listing's order may not be stable from page to page. The lane check has been red since then (difference −379). The load marks an entry `taken_down_on` when the newest pass did not list it, so the 335 such rows are probably artefacts of the paging, not real take-downs (not verified). No 403, block or transport failure was met. No captures ran between the two weekly passes.

**Still missing.** About 44 entries never listed, by the stated count against the union held. Re-fetches of entries the 29 October 2026 pass did not list. Any document an entry links, such as determinations and media releases.

## Financial Markets Authority warnings and enforcement cases (lane `fma`)

**Hosts and entry points.** `www.fma.govt.nz`, behind Cloudflare. Two lists, 15 items a page, newest first, each stating "N results found": warnings and alerts at `/library/warnings-and-alerts/` (`?start=15`, `?start=30`, …), and enforcement cases at `/about-us/enforcement/cases/` (`?start=15`, …). Item pages: `/library/warnings-and-alerts/<slug>` and `/about-us/enforcement/cases/<slug>`. About-pages: `/copyright/` and `/privacy/`. A warnings CSV download exists. It was fetched once on 21 October 2026 while the page shapes were surveyed, and is held but never read: it carries address fields and no page address.

**What we capture.** Listing pages and item pages, verbatim HTML.

**Held.** 913 documents, 111.9 MB, all web pages, under 858 distinct names. No sha256 has more than one name. 55 names have held more than one sha256 (re-dated items and re-walked listing pages). Fetched 21 October 2026 to 29 October 2026. Published rows: `pub.fma_actions` 802 (727 warnings, 75 enforcement cases) and `pub.fma_parties` 612. Actions dated from 27 January 2010 to 23 October 2026. One row carries `taken_down_on`.

**How we walk it.** A full pass of both lists at most weekly, resuming from its next page. Each item's fingerprint is its date and title as listed. An item is fetched again only when the list shows it re-dated or retitled; the FMA re-dates a case it updates. About-pages are fetched every 30 days. Job `qv4-fma-capture` runs nightly at 23:00 NZDT; on nights with no pass due it makes 0 requests. Budget 4 hours, deadline 5 hours, off-peak only. One request at a time, 5 s floor; after a 5xx it rests 60 s. A 403, 429 or challenge page (recognised by its title) stops the run, as does a redirect to another host. Every request carries the estate's single User-Agent, which names the project and a contact address. First pass: 21 October 2026, 856 requests in 4,275 s. Second: 29 October 2026, 57 requests (54 listing pages, 3 items). Our load runs at 06:25 NZDT.

**Legal position.** `docs/legal/positions/fma-warnings-and-enforcement.md`. FMA copyright, licensed CC BY 4.0, attributed to the FMA; logos and images are excluded. The privacy statement covers only visitors' data. The site's "AI search – terms of use" governs its own search assistant, which we never use. A warning is a caution, not a finding. Warnings print labelled fields (address, telephone, email, bank). On 21 October 2026 there was no robots file (404), so no crawl delay was stated.

**What went wrong and what we learned.**
- The enforcement list states 99 results (21 October 2026) and 100 (29 October 2026), but paging reaches only 5 pages, 74 distinct items. The cause is not verified. The lane check is red on that list (difference −26). The warnings list reconciles exactly (727 of 727).
- By 29 October 2026 the host was serving a robots.txt. It is a Cloudflare-managed file whose preamble says that accessing the site means agreeing to its "content signals". For all agents it sets `Content-Signal: search=yes, ai-train=no, use=reference` and `Allow: /`, with no crawl delay. This was not in the position written on 21 October 2026 and has not yet been assessed in it.
- No block or challenge was met. Cloudflare's email obfuscation appears in the page markup.
- Older warnings headed by a person's name alone are read as naming nobody (a reading limit).

**Still missing.** About 26 enforcement cases the listing does not reach. The warnings CSV is held but not read.

## WorkSafe New Zealand court summaries and enforceable undertakings (lane `worksafe`)

**Hosts and entry points.** `www.worksafe.govt.nz`. Two lists, 20 items a page (`?start=20`, `?start=40`, …), each stating "Found N results": court summaries at `/laws-and-regulations/prosecutions/court-summaries/` (31 pages), and accepted enforceable undertakings at `/laws-and-regulations/enforceable-undertakings/accepted-enforceable-undertakings/` (4 pages). Item pages sit under those paths. About-pages: `/about-us/about-this-site/copyright/` and `/about-us/about-this-site/privacy-statement-and-policy/`.

**What we capture.** Listing pages and item pages, verbatim HTML.

**Held.** 737 documents, 328.2 MB, all web pages, under 702 distinct names. No sha256 has more than one name. 35 names have held more than one sha256. Fetched 22 October 2026 to 29 October 2026; the first pass began 21 October 2026, 21:02. Published rows: `pub.worksafe_actions` 665 (608 prosecutions, 57 undertakings) and `pub.worksafe_parties` 668. Actions dated from 13 June 2013 to 8 June 2026. None is marked taken down.

**How we walk it.** A full pass of both lists at most weekly, resuming from its next page. Each item's fingerprint is its date, title and status as listed; an undertaking moving from "In progress" to "Complete" triggers a re-fetch. About-pages are fetched every 30 days. Job `qv4-worksafe-capture` runs nightly at 23:30 NZDT. Budget 4 hours, deadline 5 hours, off-peak only. One request at a time, 5 s floor; after a 5xx it rests 60 s. A 403, 429, challenge or redirect to another host stops the run. Every request carries the estate's single User-Agent, which names the project and a contact address. First pass: 21–22 October 2026, 707 requests in 3,701 s. Second: 29 October 2026, 40 requests. Our load runs at 06:30 NZDT.

**Legal position.** `docs/legal/positions/worksafe-prosecutions-and-undertakings.md`. WorkSafe's copyright statement: material may be reproduced free of charge without specific permission, accurately, not in a derogatory or misleading context, with the source and copyright acknowledged. Third-party material is excluded. WorkSafe publishes a code such as "2019-A" in place of an unnamed defendant. An undertaking is not a conviction. robots.txt disallows `/admin/`, `/security/`, `/search` and error pages, and sets a 10 s crawl delay for Bingbot only, so none applies to us.

**What went wrong and what we learned.** Five undertaking pages listed on the undertakings list do not have an undertaking's shape (no date and intro). They are set aside and not landed. Because they are never held, the capture asks for the same five pages every night: 75 set-aside lines from 22 October 2026 to 4 November 2026. That is wasted traffic, and a newcomer would trip on it. On the board run of 4 November 2026 the lane check was red, showing 0 items read on the newest passes; the cause is not verified (the load may not have re-read the 29 October passes). No block or challenge was met.

**Still missing.** The five undertakings whose pages do not match the expected shape. Media releases and full court decisions linked from summaries are not captured.

## Building Practitioners Board decisions and the register of licensed building practitioners (lane `building_practitioners`)

**Hosts and entry points.**
- `www.lbp.govt.nz`: the Board's past complaint decisions list at `/complaints-and-past-decisions/past-complaint-decisions/`, 20 a page (`?start=20`, `?start=40`, …). The first page states "Displaying 20 of N results" (1,600 on 21 October 2026; 1,602 on 29 October 2026). About-pages: `/about-us/copyright/` and `/about-us/privacy/`.
- `kete-lbp.mbie.govt.nz`: the register's own GET search, `/advanced-building-practitioner-search/`, asked once per licence class (7, parameter `lclass`) and once per area of practice (19, parameter `aop`): 26 searches. Each search returns every match on one page with no paging; the largest, Carpentry, has 21,372 rows and is 18 MB. Each result links a practitioner page, `/practitioner/?id=<guid>`. A search with no criterion did not answer within 60 s on 2 November 2026 and is never asked.

**What we capture.** Decisions list pages, verbatim HTML; the decision PDFs they link are not fetched. The register's 26 search result pages and each practitioner's page, verbatim HTML.

**Held.** 13,403 documents, 7,762.0 MB, all web pages, under 13,323 distinct names. No sha256 has more than one name. 80 names have held more than one sha256 (the decisions list pages re-walked). Fetched 21 October 2026 to 5 November 2026. Register: 26 search pages and 13,213 practitioner pages (fetched 2 to 5 November 2026) out of 26,978 practitioners listed. Published rows: `pub.building_practitioner_decisions` 790 (decided 28 February 2018 to 23 September 2026; 2 carry `taken_down_on`) and `pub.building_practitioners` 8,792 (as of the load on 4 November 2026; classes first granted from 26 March 2008 to 30 October 2026).

**How we walk it.**
- Decisions: job `qv4-building-practitioners-capture`, nightly at 23:00 NZDT, 45-minute deadline. The spec wants a weekly pass on Sunday, but the catalogue has no weekday field, so the lane keeps the weekly cadence itself. A full pass is about 80–84 requests and 10 minutes. It resumes from its next page. A 403, 429, 5xx or challenge stops the run.
- Register: job `qv4-building-practitioners-register-capture`, nightly at 22:05 NZDT. It stops at 06:00 NZDT (about 27,000 s a night) or on a block. The 26 searches run weekly. Each listed practitioner's page is fetched once, about 4,400 a night, and again after 90 days. A page the store already holds under its address is never asked. It runs only while the legal position carries its `authorised: register` line.
- One request at a time, 5 s apart (the lane's own floor). The gate's floor for `kete-lbp.mbie.govt.nz` is the 1.5 s default. The gate log attributes these requests to a different position that also names an mbie.govt.nz host; the cause is not verified.
- Redirects to another host stop the run. Every request carries the estate's single User-Agent, which names the project and a contact address.
- Our load runs at 06:40 NZDT.

**Legal position.** `docs/legal/positions/building-practitioners-register.md`. Crown copyright on lbp.govt.nz, "This includes the Public Register": it may be used, copied and re-distributed free of charge, with the source acknowledged. Board decisions may carry no copyright at all (Copyright Act 1994, s 27; for a lawyer). Statutory limit: Building Act 2004, s 299 lists the register's purposes. Section 307 says a search may be carried out only for those purposes. Section 308 makes a search for personal information outside them an interference with privacy under the Privacy Act 2020. The register's search page repeats this. The register is copied on Arthur's ruling 132 (2 November 2026); a lawyer is to say how s 299 applies. The Board shows discipline for three years. robots.txt for `www.lbp.govt.nz` sets a 5 s crawl delay for Bingbot only. `kete-lbp.mbie.govt.nz` has no robots file (404).

**What went wrong and what we learned.**
- 21 October 2026: the first capture run fell outside off-peak hours and did nothing. The first pass came that night, 80 pages, 1,600 decisions.
- The register's search lists only current licence holders; ticking "include not currently licensed" changes nothing. Lapsed practitioners are therefore never reached.
- A practitioner page's five sub-tables (companies, qualifications, classes with dates, suspensions, discipline) load by a POST to `/_services/entity-subgrid-data.json` with an anti-forgery token. The gate makes only GETs, so none is read.
- The reading sets aside 765 of the 1,602 listed decision items: their title is not of the form "<name> [YYYY] BPB <number>". The lane check is red (difference −49 after set-asides). This is a reading gap, not a fetch gap.
- The register copy started on 2 November 2026: 4,406, 4,427 and 4,429 requests on three nights, each ending on its budget, with 7–8 pages set aside a night. About 13,765 pages were still due after the night of 4 November 2026.
- No block or challenge was met on either host.

**Still missing.** About 13,765 practitioner pages, at about 4,400 a night, so about three more nights (not verified). The decision PDFs. The practitioner pages' sub-tables, which need a POST. Lapsed or unlicensed practitioners. Reading of the 765 set-aside decision titles.

## Real Estate Authority decisions (lane `real_estate_authority`)

**Hosts and entry points.**
- `decisions.dotnous.com/reaa/v2/`: the Authority's decisions database, run by a contractor; plain ASP.NET pages. Year listings: `default.aspx?qd3=during&qd1=<year>&Go=Submit+Search…&pagesel=<n>`, 10 a page, stating "Search Results (N)" and "Page X of Y", for every year from 2010. Abstracts: `abstract.aspx?case=<n>`. Decision PDFs: `/reaa/pdfs/<name>.pdf`, with names such as `C<n>_Determination.pdf`, `C<n>_Orders_Determination.pdf` and `CAN_Determination.pdf`.
- `www.rea.govt.nz`: `/complaints-and-decisions/complaint-decisions/` (links the database) and `/terms-of-use-and-privacy-statement/`, read once on 18 October 2026, together with the sitemap and robots file.

**What we capture.** Listing pages, abstract pages and every PDF an abstract links, all verbatim.

**Held.** 8,110 documents, 2,145.4 MB: 4,407 PDFs (2,013.9 MB) and 3,703 web pages (131.5 MB), under 7,892 distinct names. 100 sha256s have been seen under more than one name: one decision PDF published under several file names. 21 names have held more than one sha256. Fetched 18 October 2026 to 4 November 2026. 3,090 cases listed across 2010–2026, 3,063 held: 2,912 Complaints Assessment Committee, 169 Disciplinary Tribunal, 9 with no body stated. Published rows: `pub.rea_decisions` 3,063 and `pub.rea_parties` 1,573. Decisions dated 27 February 2010 to 16 September 2026.

**How we walk it.** Every year not yet fully listed is listed, oldest first, and the current and previous years are always re-listed. A year is marked listed only when every page of it was read. The run then fetches listed cases not yet held, Committee decisions oldest first (they leave the database after three years), then the rest: the abstract, then each PDF it links that is not already held. Job `qv4-real-estate-authority-capture` runs nightly at 23:00 NZDT, budget 4 hours, deadline 5 hours, off-peak only. The first capture ran by day on 19 October 2026 on Arthur's word (`--anytime`). One request at a time, 5 s floor; the gate log shows 1.5 s on the first day's requests. A 500, 502, 503 or 504 without a challenge is one failed read, after which the run rests 60 s. Three failures in a row stop the run. A 403, 429 or challenge stops it. A run that stops early after landing anything is recorded green. A session advisory lock allows only one run of the lane at a time. An answer from another host, or a redirect to one, stops the run. Every request carries the estate's single User-Agent, which names the project and a contact address. Our load runs at 06:35 NZDT.

**Legal position.** `docs/legal/positions/real-estate-authority-decisions.md`. The Authority's terms say its information "may be reproduced, free of charge, for personal or in-house use only", with the source and date; other use needs its permission. Capture is held as in-house use; showing or selling waits on a lawyer (Copyright Act 1994, s 27, for tribunal decisions) or on permission (ruling 59: no letter to the Authority yet). The contractor's host shows no terms of its own. The Authority says decisions stay on the public register for 3 years; the database reaches back to 2010. `decisions.dotnous.com/robots.txt` says `Disallow: /` for every agent. Under the estate's ruling 10 a robots file is read only for a crawl delay, and none is stated. `www.rea.govt.nz` states no crawl delay. Its feedback form carries a reCAPTCHA, which we never use.

**What went wrong and what we learned.**
- 19 October 2026: 2016 stopped at page 1 of 22 on a connection reset. Fixed the same day: a year cut short is listed again.
- 20 October 2026: an HTTP 500 ended the run as "a block or a challenge" (292 PDFs landed, 28 set aside). Fixed 21 October 2026: a 5xx without a challenge is one failed read.
- 20 October 2026: 27 abstract pages answered with "no decision on the page" (11 in 2019, 14 in 2020, 2 in 2022). They were set aside and never asked again, so the lane check is red: "short 3 years, source 288, held 261".
- Six connection resets (19 October to 2 November 2026). Failed listing reads on 27 October, 1 November and 2 November 2026: those nights listed 10, 17 and 14 pages instead of 20.
- The Committee's older decisions are leaving the database: 2015 lists 292 decisions, 2023 only 84. We keep what we hold after the database drops it.
- A newcomer should expect one PDF under several names: 100 sha256s are each held under more than one name.

**Still missing.** 27 abstracts (2019, 2020 and 2022) and their PDFs. Any Committee decision already dropped from the database before 18 October 2026, which cannot be recovered from this source.

## Te Kāhui Māngai, the Directory of Iwi and Māori Organisations (lane `iwi_directory`)

**Hosts and entry points.** One host: `www.tkm.govt.nz` (Te Puni Kōkiri). The walk starts from these seeds: `/`, `/map/`, `/browse/`, `/omo/`, `/marae/`, `/NonTribalMarae/`, `/glossary/`, `/disclaimer/`, `/about/`, plus the copyright and privacy pages. URL families on the frontier: `/iwi/<slug>/`, `/region/<slug>/`, `/localauthority/<slug>/`, `/regionalauthority/<slug>/`, `/rmagroups/`, `/omo/`, `/marae/`. The government data catalogue record (`catalogue.data.govt.nz`, package `directory-of-iwi-and-maori-organisations-te-kahui-mangai`) was read once for the licence. That host has a 10 s floor.

**What we capture.** HTML pages only: the 13 region maps, 117 iwi pages, the authority lists, other organisations, non-tribal marae, and site pages (about, copyright, disclaimer, privacy, glossary). It never asks for files (rohe map PDFs, images), the search and contact forms, `/rohe`, `/images`, `/search`, `/Bin`, or any URL with a query string.

**Held.** 251 documents, 3.6 MB, all web pages. 251 names, and no sha256 is held under more than one name. Fetched 22 October 2026 to 30 October 2026. Two finished walks: 22 October (229 requests, 229 landed, 5,133 links found) and 30 October (229 requests, 22 new, 207 unchanged). Main tables (`pub.*`):
- `iwi_directory_entities`: 2,697 rows (117 iwi, 1,381 hapū, 1,013 marae, 98 organisations, 88 governance entities).
- `iwi_directory_relations`: 4,080 rows.
- `iwi_directory_settlements`: 110 rows naming 96 distinct settlements.

The content has no date range. The site says organisations supply their details and the directory is checked twice a year.

**How we walk it.** The whole site is walked from the home page in the order links are found. The frontier of every address is stored with its state, so a stopped walk resumes on the next run. A new walk starts only when the last finished walk is at least 7 days old, and is capped at 1,500 pages. Each page is landed once per walk, and an unchanged page is recognised by its hash. Job `qv4-iwi-directory-capture` is due daily at 22:30 NZDT, so it walks weekly. Budget 2 h, deadline 3 h, about 20 minutes per walk. Requests go one at a time, 5 s apart (gate floor for `www.tkm.govt.nz`). Robots states no crawl delay. A 403, 429 or challenge stops the run. A 5xx with no challenge is set aside, followed by a 60 s rest. Three failures in a row stop the run. Redirects to another host are not followed. The load (`qv4-iwi-directory-load`) runs daily at 06:35 NZDT and publishes only when a new walk is held.

**Legal position.** `docs/legal/positions/iwi-and-hapu-directory.md`.
- Basis: every page is open (200, no login or challenge).
- Licence: the site's copyright page says Crown copyright, reproducible for "personal, not-for-profit or in-house use". The data.govt.nz catalogue lists the same directory as CC BY 3.0 NZ. Which of the two governs is an open queue item (`whether-te-kahui-mangai-is-cc-by`).
- Terms: none accepted by click. The disclaimer bars nothing.
- Privacy: entries name people with phones and emails, and organisations' postal and physical addresses. Pages are captured whole. Only organisational fields are published. Contact fields are kept in a private table that no view reads (ruling 142).
- Attribution: "Source: Te Kāhui Māngai, Te Puni Kōkiri, CC BY 3.0 NZ as catalogued".
- Robots states no crawl delay.

**What went wrong and what we learned.**
- 22 October 2026: the first load was red because no walk had finished yet.
- 23 October 2026: the load published nothing because 8 entities carried a role flag no rule named. It was the Taranaki Maunga collective-redress flag. Fixed the same day.
- 23 October 2026: one organisation key covered pages that print the name with different macrons. Rows are now split by the name each page prints, and macrons are kept.
- The scheduler's first slot (08:35) fell outside off-peak, so that run asked nothing.
- No blocks or holds have been seen on this host.

**Still missing.** Nothing the lane wants. Rohe map files and images are left out by design. The licence question is open.

## Te Haeata, Treaty settlement commitments (lane `settlement_commitments`)

**Hosts and entry points.** `tehaeata.govt.nz` (Te Puni Kōkiri). The records address `/commitments` is watched. The home page, `/settlements` and `/resources` all return the same login page. The open pages are `/about-us`, `/copyright`, `/terms-use` and `/privacy`. The position also names `www.whakatau.govt.nz` and `tearawhiti.govt.nz` (Te Tari Whakatau). Their settlement pages are open, but their terms bar data collection. Only one settlement page was read, in the survey.

**What we capture.** No records. The lane lands the login page that `/commitments` returns, plus the four open "about the source" pages.

**Held.** 7 documents, 0.1 MB, all web pages, all from `tehaeata.govt.nz`. Fetched 22 October 2026 to 4 November 2026. No sha256 is held under more than one name. No register rows: no settlement or commitment is held. `settlement_commitments.capture_watch` holds 18 rows: `/commitments` answered 14 times with status 200 and the login wall, from 22 October to 4 November; each of the four open pages answered once, on 22 October. Settlement Acts named on governance entities' directory pages come from `iwi_directory` instead (110 rows).

**How we walk it.** Job `qv4-settlement-commitments-watch` runs daily at 23:15 NZDT. It makes one request to `/commitments` and checks whether the login wall is still there. The four open pages are re-read every 30 days. Requests are 5 s apart (gate floor). Robots states no crawl delay. No account is ever made. The job goes red the day `/commitments` answers without the wall. No load job.

**Legal position.** `docs/legal/positions/treaty-settlement-commitments.md`.
- Basis: the records sit behind a login (email and password, "Create new account"). Hard limit 6 treats a login as a lock, so the lane holds nothing.
- Te Haeata: Crown copyright, no licence. Its terms bar nothing; the wall does.
- Te Tari Whakatau: Crown copyright under CC BY 4.0, but its terms of use say "You must not carry out any data collection activities (including data mining, data extraction and data harvesting)". Not captured.
- Privacy: commitments name agencies and governance entities, not people.
- Robots: Te Haeata states no crawl delay; Te Tari Whakatau gave no readable robots file.
- The only ways in are letters, which are Arthur's (queue `whether-to-ask-for-the-settlement-commitments`).

**What went wrong and what we learned.** 22 October 2026: the job's first weekly slot fell on Thursday 13:00 NZDT, outside off-peak. The capture refused, and every weekly slot failed. The job was moved to daily 23:15. The wall has stood on every watch since.

**Still missing.** The whole commitments record: every commitment by settlement, agency and type. Also Te Tari Whakatau's per-settlement pages, which its terms bar.

## Council meeting listings and minutes on InfoCouncil (lane `council_minutes`)

**Hosts and entry points.** 24 InfoCouncil instances.
- 20 are on `<council>.infocouncil.biz`: carterton, centralotago, christchurch, hastings, hawkesbay, horowhenua, huttcity, kapiticoast, mackenzie, napier, northland, palmerstonnorth, southland, tararua, tasman, taupo, waimate, wairoa, waitaki, westernbayofplenty.
- 4 are on the council's own domain: `infocouncil.fndc.govt.nz`, `infocouncil.tauranga.govt.nz`, `infocouncil.dunedin.govt.nz`, `infocouncil.boprc.govt.nz`.
- Entry point: each instance's default page (`https://<instance>/`), a grid of the current year's meetings.
- Documents use the pattern `https://<instance>/RedirectToDoc.aspx?URL=Open/<YYYY>/<MM>/<BODYCODE>_<YYYYMMDD>_MIN_<n>.PDF`. This answers with a same-host redirect to the file.
- The instance list came from the old estate's verified list (July 2026).

**What we capture.** The listing page (HTML), and every minutes PDF the listing names, once. Agendas and attachments are listed but not fetched.

**Held.** 1,005 documents, 287.2 MB: 963 minutes PDFs, 20 listing pages, 22 other (repeat listing captures with no file extension, plus one pinned JSONL of the old estate's listing). No sha256 is held under more than one name. Fetched 22 October 2026 to 2 November 2026.
- `pub.council_meetings`: 1,388 meetings from 21 councils. Minutes landed for 963, 1 failed, and 424 meetings list no minutes.
- Meeting dates run from 22 January 2024 to 25 November 2026. All but 6 are in 2026; future meetings are listed.
- Reading tables built from the minutes: 13,012 attendance rows, 6,163 resolutions, 398 declarations.
- Coverage: 21 of the 24 instances, which is 21 of the 78 councils. The other councils do not use InfoCouncil and are not in this lane.
- Minutes held per instance range from 82 (Far North) to 1 (Waitaki).

**How we walk it.** Job `qv4-council-minutes-capture` is due nightly at 22:15 NZDT. Budget 2 h, deadline 3 h, and it stops at 06:00. Each listing is asked at most weekly; the last listing pass was 29 October 2026. Each minutes PDF is asked once ever. A failed PDF is never asked again. Requests go one at a time, 5 s apart (gate floor for `infocouncil.biz` and the four council domains). The four council-domain instances serve a robots file with no crawl delay; the `*.infocouncil.biz` instances serve none. A 403, 429, 5xx, a challenge, or a 404 on a listing holds that instance in the lane's `capture_held_hosts` until a session clears it. The run then moves to the next instance. A redirect off the host is not followed.

Change detection: the listing grid's own row count is checked against the meetings read, and a document already held is recognised by its hash. Load `qv4-council-minutes-load` runs daily at 06:45. Reader jobs (`qv4-council-minutes-read`, `-pages`) run on the estate's own models and fetch nothing.

**Legal position.** `docs/legal/positions/council-meeting-platform-infocouncil.md`.
- Basis: the Local Government Official Information and Meetings Act 1987 requires councils to publish these papers: agendas and reports available to the public (s 46A), minutes open to inspection (s 51). Copyright is the council's, and no instance states a licence.
- Terms: none accepted by click, and instance pages carry no terms. 17 of the 24 councils' own site terms were read. None bars automated access. Hastings, Napier, Tasman, Mackenzie and Southland District license their sites CC BY. Christchurch, Horowhenua, Hawke's Bay Regional and Tararua ask permission for commercial use.
- Privacy: the venue is kept privately. Public-excluded and public-forum lines are kept privately and flagged (ruling 142).
- Robots: no crawl delay stated. Floor 5 s.

**What went wrong and what we learned.**
- 22 October 2026: Kāpiti (`kapiticoast.infocouncil.biz`) and Hawke's Bay Regional (`hawkesbay.infocouncil.biz`) answered 404. The instances have moved, and both are held until someone finds the new address.
- 22 October 2026: Christchurch's listing (about 796 KB, 237 minutes links) contains the word "captcha" in a script, so the gate's challenge check called it a challenge. The gate now treats this page as content. On 23 October the lane held Christchurch again because the page "is not an InfoCouncil meeting listing" (no `bpsGridDate` cell, year selector or BusinessPapers style), and it remains held.
- The old estate's 347 minutes PDFs could not be copied because its other box did not answer. On 2 November 2026 all 347 were fetched once from the councils. 53 of them were not the same bytes as the old estate's listed hash.
- One Tasman minutes PDF answered 404.
- No 403 has been seen on any InfoCouncil host.

**Still missing.**
- Christchurch, Kāpiti Coast and Hawke's Bay Regional: no listings.
- Every year before the current one: the capture only asks for each instance's default page, never the year selector.
- Agendas and attachments.
- The 57 councils not on InfoCouncil, which need other platforms.

## Councillors' registers of pecuniary interests (lane `councillor_interests`)

**Hosts and entry points.** The 78 councils' own sites. The council list comes from DIA's council contact list on data.govt.nz. Registers were requested from 88 hosts, all named in the position's hosts line. Six councils have moved host: `cdc.govt.nz`, `hamilton.govt.nz`, `nelson.govt.nz`, `npdc.govt.nz`, `southtaranaki.com`, `upperhutt.govt.nz`.

Three councils' document stores are followed from their sites:
- Hutt City: `hccpublicdocs.azurewebsites.net`
- Porirua: `storage.googleapis.com`
- Tasman: `tasmandc-publicdocs.azurewebsites.net`

Each council's landing page and register document address are hard-coded in `registers/councillor_interests/capture.py` (`REGISTERS`, from the survey of 22 October 2026). Common file patterns are Squiz-style `/__data/assets/pdf_file/<n>/<n>/<file>.pdf`, `/assets/...`, `/media/...` and `/documents/...`.

**What we capture.** Each council's landing page (HTML), and every register document it links: mostly PDFs, a few HTML registers, and one file per member at seven councils (Christchurch, Hastings, Mackenzie, Matamata-Piako, Tauranga, Wairoa, Auckland).

**Held.** 447 documents, 192.7 MB: 381 PDFs, 61 other (files whose URL has no extension), 5 web pages. 448 names, and 1 sha256 is held under two names. Fetched 23 October 2026 to 3 November 2026; the 22 October survey bytes were adopted into the store on 23 October.

`pub.councillor_interest_registers` has 78 rows, one per council:

| Form | Councils | Notes |
| --- | --- | --- |
| PDF register | 37 | 51 documents |
| Per-member files | 7 | 340 documents (Christchurch 255) |
| HTML register | 3 | |
| HTML register waiting for the reader | 2 | |
| Linked but not found | 9 | |
| Not found | 4 | |
| Not reached (blocked) | 11 | |
| Held on terms | 3 | |
| Redirect not followed | 2 | |

`pub.councillor_interests` has 8,991 rows from 42 councils. The registers' own dates run from 2014 to 2026, mostly the 2025 to 2028 triennium. The 2014 to 2022 rows come from Christchurch's archive of per-member files.

**How we walk it.** Job `qv4-councillor-interests-capture` runs nightly at 00:30 NZDT (catalogue `at_utc = 11:30`; the spec said 23:30), with a 1 h budget and a 2 h deadline. Each landing page is re-read monthly (`EVERY_DAYS = 30`); the next is due about 22 November 2026. Each register document is asked once. A document that failed is asked again monthly. Links are resolved against the page's `<base href>`. A same-site redirect is followed once.

Requests go one at a time, at least 5 s apart, or the site's crawl delay. Stated crawl delays: Christchurch (`ccc.govt.nz`) 10 s, Kawerau 10 s, Ōtorohanga (`otodc.govt.nz`) 30 s. These sites state 7 s: Central Otago, Clutha, Gore, Grey, Hauraki, Hurunui, Invercargill, Kaikōura, Marlborough, Masterton, Nelson, Ōpōtiki, Rotorua Lakes, Ruapehu, South Taranaki, South Waikato, Southland Regional (`es.govt.nz`), Stratford, Taupō, Waimate, Waipā, West Coast Regional, Western Bay of Plenty. Tauranga and Hamilton are 5 s. A block holds the host in the lane's `capture_held_hosts`.

The load `qv4-councillor-interests-load` runs at 06:50. The reader `qv4-councillor-interests-read` uses the estate's own model and fetches nothing.

**Legal position.** `docs/legal/positions/councillors-registers-of-interests.md`; terms evidence is in `councillors-registers-of-interests-terms.md`.
- Basis: the Local Government Act 2002, Part 4 subpart 3 (in force 20 November 2022), requires each council to publish a summary of its register on its website. No department collects them. The summary is the council's copyright.
- Terms: 47 terms pages were read and cited by sha256. Most allow non-commercial reuse with attribution. Five license CC BY: Hastings, Mackenzie, Napier, Southland District, Tasman. Five ask permission for commercial use: Christchurch, Horowhenua, Hawke's Bay Regional, Tararua, Upper Hutt.
- Three councils' terms bar automated access, and they are not captured: Auckland ("must not use automated tools, such as bots or web scrapers"), South Waikato ("spider, crawl, or scrape") and Waimakariri ("harvesting bot, robot, spider, scraper"). The setting is `TERMS_BAR`; queue item `whether-to-capture-councils-whose-terms-bar-automated-access`, no default.
- Privacy: rulings 142 and 143 apply. Every category is kept, with flags for real property and for a partner's interests. Entries shaped like an address or a contact are kept in a private table.
- Robots: crawl delays as listed above.

**What went wrong and what we learned.**
- 22 October 2026: the survey met a 403 or an Imperva/Incapsula challenge at ten sites: Ashburton, Environment Canterbury, Chatham Islands, Dunedin, Far North, Gisborne, Carterton, Matamata-Piako, Waikato Regional, Wellington City. Six requests went to an already-blocked site before the survey carried the block list forward between passes.
- 22 October: relative links resolved wrongly until `<base href>` was honoured.
- Ōtorohanga's and Whakatāne's register addresses now answer 301. The lane does not follow redirects to a new path, so both show as "address failed".
- 3 November 2026: Timaru (`www.timaru.govt.nz`) answered 403 to its landing page and was held by the lane. That was before the gate's own holds began, so it is not in the gate's `refusals.jsonl`.
- 4 November 2026, 22:20: the gate held Dunedin, Gisborne and Kaipara. The holds were triggered by the elections lane, but they apply to this lane too. Kaipara's register, held since 22 October, is not re-read.
- 5 November 2026: the lane was changed so that a gate-held host is skipped with nothing written.
- 17 PDFs have no text layer and are waiting for the page reader.

**Still missing.**
- Not reached because of blocks (11 councils): Ashburton, Environment Canterbury, Carterton, Chatham Islands, Dunedin, Far North, Gisborne, Matamata-Piako, Timaru, Waikato Regional, Wellington City.
- Held on terms: Auckland, South Waikato, Waimakariri.
- Linked but not found: Gore, Hurunui, Hutt City, Mackenzie, Porirua, Selwyn, Tasman, Taupō, Waikato District.
- No register found: Clutha, Grey, Kawerau, Ōpōtiki.
- Redirect not followed: Ōtorohanga, Whakatāne.
- Rotorua publishes only an old register released on request.
- Registers for years before the current triennium, except Christchurch's archive.

## Local election candidates' returns of donations and expenses (lane `local_elections`)

**Hosts and entry points.**
- Each council's own page listing its candidates' returns. `registers/local_elections/listings.tsv` seeds 66 pages at 43 councils, and the capture follows sub-listings up to two levels deep on the same host. 89 listing pages are held.
- Returns files come from 45 hosts. Most are council sites. Others are Hutt City's document host `hccpublicdocs.azurewebsites.net`, Thames-Coromandel's `docs.tcdc.govt.nz`, and `hamilton.govt.nz`. Auckland's `voteauckland.co.nz` is named in the position but not captured.
- File URL families across the 2,147 listed returns: `/assets/...` (686 returns, 15 councils), `/repository/libraries/...` (390, 10 councils; the Hawke's Bay councils use this platform), `/media/...` (379, 7), Squiz `/__data/assets/pdf_file/<n>/<n>/<file>.pdf` (171, 4), the Azure blob host (162, 1), `/uploads/...` (137, 2), `/documents/...` (137, 2), other (85, 3).
- File names often carry the candidate's name, for example `<Prefix>_<Ward>-<SURNAME>,-<Given>.pdf` or `<surname>-<given>-expense-return.pdf`.
- These places were checked for a collected copy and hold none in the window: `electionz.com` (2010 and 2013 only), `electionservices.co.nz`, `lgnz.co.nz`, `votelocal.co.nz`.

**What we capture.** Listing pages (HTML), and every return file they link (PDF, Word, scanned images), each asked once ever. The files are held. The lane itself reads only the listing's facts.

**Held.** 2,055 documents, 2,085.4 MB: 1,687 PDFs, 249 other (no file extension, one `.docx`), 112 web pages, 7 images. 2,061 names; 6 sha256s are held under two names. Fetched 23 October 2026 to 4 November 2026.

`pub.local_election_returns` has 2,147 rows from 43 councils: 1,944 single-candidate returns and 203 combined files. File states: 1,856 landed, 85 wanted, 27 blocked, 177 "not asked", 1 not found, 1 too large (over 60 MB). `pub.local_election_returns_coverage` has 96 rows.

| Election year | Rows | Councils |
| --- | --- | --- |
| 2019 | 447 | 22 |
| 2022 | 744 | 31 |
| 2025 | 819 | 29 |

The rest are by-elections and other years: 2017 (13 rows, 1 council), 2020, 2021, 2023, 2024 (89 rows, 3 councils) and 2026 (8 rows). Coverage is 43 of 78 councils. The largest file hosts by count are New Plymouth (203), Hamilton (169), Hutt City's Azure host (161) and Thames-Coromandel (127).

**How we walk it.**
- `qv4-local-elections-listings`: due daily at 22:10 NZDT. It refuses to start less than a week after the last finished pass or outside off-peak, so it runs weekly. About 150 requests, about 20 minutes. Passes on 23 October (87 requests) and 29 October (86); the next is due 5 November.
- `qv4-local-elections-files`: nightly at 22:20. Each wanted return is asked once ever, oldest election first. Budget 7 h, and it stops at 06:00. The first files pass on 23 October made 230 requests and landed 226. Later nights made 3 to 14 requests.
- `qv4-local-elections-load`: 06:40.
- One request at a time, at least 5 s apart, or the robots crawl delay.
- Stated crawl delays: Ōtorohanga 30 s, Christchurch 10 s, Kawerau 10 s. These sites state 7 s: West Coast Regional, Southland Regional, Nelson, Marlborough, Hauraki, Waipā, South Waikato, Taupō, Rotorua Lakes, Western Bay of Plenty, Ōpōtiki, Stratford, South Taranaki, Ruapehu, Masterton, Grey, Kaikōura, Hurunui, Waimate, Central Otago, Clutha, Gore, Invercargill.
- A 403, 429, 5xx or challenge is a failed read, and the host is not asked again that run.
- A redirect to a bot manager (for example Queenstown-Lakes to Radware's `validate.perfdrive.com`) counts as a challenge. A redirect to another host is not followed.
- Files are capped at 60 MB.

**Legal position.** `docs/legal/positions/local-election-candidate-returns.md`.
- Basis: under the Local Electoral Act 2001 s 112A, every candidate files a return within 55 days of the result. Under s 112F, the electoral officer must publish returns electronically or otherwise, keep them open to inspection for seven years after the election, and give anyone a copy on request (s 112F(2)(c)). The seven-year limit means each election's returns may come down after seven years. The window is 2017 onward (ruling 71).
- Copyright in a return belongs to the candidate. Several councils' terms exclude third-party material.
- Terms fall into four classes:
  - (a) Open licence: Greater Wellington, CC BY 4.0.
  - (b) Personal or non-commercial reuse: most councils.
  - (c) Automated access barred, so not seeded: Auckland, Christchurch, South Waikato, Waimakariri. Queue item `whether-to-ask-the-councils-whose-terms-bar-automated-access`, no default.
  - (d) No terms found: Clutha, Far North, Hutt City, Kaipara. Captured under the statute.
- Privacy: returns print the candidate's address and the names and addresses of donors over $1,500 (s 112A(4)). The listings carry only name and seat.
- Robots: crawl delays as listed above.

**What went wrong and what we learned.**
- 22 October 2026 survey: nine councils gave failed reads. Waikato Regional, Environment Canterbury, Chatham Islands and Matamata-Piako returned an Incapsula challenge. Southland District returned a CAPTCHA. Wellington City, Carterton and Mackenzie returned 403. Queenstown-Lakes redirected to a Radware challenge.
- An early blind sitemap walk was stopped: 60 requests to four hosts found nothing a search did not.
- From 23 October 2026, Dunedin (`www.dunedin.govt.nz`), Gisborne (`www.gdc.govt.nz`) and Kaipara (`www.kaipara.govt.nz`) answered 403 to return files. Dunedin and Gisborne alternate between 200 and 403 on the same URL shapes, often 403 on the first request of a night. The files job failed 3 requests every night from 23 October to 4 November (14 blocked rows per host).
- 4 November 2026, 22:20: the gate held all three hosts. They stay held until a person clears them.
- 3 November 2026: the listing reader had joined relative links to the page's folder instead of the page's `<base href>`. This produced wrong addresses for Kaipara and for six Hawke's Bay pages (Central Hawke's Bay, Hawke's Bay Regional, Wairoa, Hastings, Napier): 184 of the 185 "not found" (404) rows. 242 addresses were corrected, and the 177 "not asked" rows are those corrected addresses, waiting for the next listings pass. The URL that triggered Kaipara's hold on 4 November appears to be one of the old wrong folder-joined addresses (not verified).
- 5 November 2026: changed so that a gate-held host is skipped before the gate and its files stay "wanted".
- One Hutt City combined file exceeded the 60 MB cap and was not landed.
- One Northland Regional file returned 403 on 23 October.

**Still missing.**
- Returns waiting behind the holds: Dunedin 76, Gisborne 6, Kaipara 15 (declared gap in `checks/source_gaps.toml`).
- Hawke's Bay councils' corrected addresses not yet asked: Napier 69, Hawke's Bay Regional 35, Kaipara 29, Central Hawke's Bay 24, Hastings 16, Wairoa 4.
- Four councils held on terms: Auckland, Christchurch, South Waikato, Waimakariri.
- Nine councils with failed reads, listed above.
- 21 councils where no listing page was found, including Whangārei, Hauraki, Waikato District, Western Bay of Plenty, Ōpōtiki, Stratford, South Taranaki, Ruapehu, Tararua, Porirua, Upper Hutt, Masterton, Buller, Grey, Westland, Hurunui, Ashburton, Timaru, Central Otago, Invercargill, Environment Southland.
- Tasman: re-ask pending after a URL-encoding fix.
- 2017 is nearly empty (1 council). Returns from before 2017 are out of scope.

## Council procurement off GETS (lane `council_procurement`) — switched off

**Hosts and entry points.** The watch asked four pages:
- `https://www.cluthadc.govt.nz/terms-and-conditions`
- `https://www.tauranga.govt.nz/terms-of-use`
- `https://www.dunedin.govt.nz/about-this-site`
- `https://www.vendorpanel.nz/marketplace` (VendorPanel's supplier sign-up)

The survey of 22 October 2026 asked 45 councils' home pages and the tender links on them (88 requests, 49 hosts), plus the platforms they name: TenderLink (`tenderlink.com`, `portal.tenderlink.com`) and VendorPanel.

**What we capture.** Only the three councils' terms pages. No tender or award page was ever landed. Pages read in the survey were kept in a session scratch folder and then removed.

**Held.** 3 documents, 1.1 MB, web pages, all fetched 22 October 2026, one name each. No rows: no reading table exists. `council_procurement.capture_watch` has 4 rows from 22 October 2026: three pages "bars" (status 200), and VendorPanel set aside on a 302 redirect.

**How we walk it.** Job `qv4-council-procurement-watch` was due daily at 22:50 NZDT and asked nothing unless 30 days had passed since the last watch. It made four requests: Clutha's at 7 s (Clutha's own crawl delay), Tauranga's at 5 s, one per host. **Disabled** in `jobs.toml` (`enabled = false`) by ruling 136 on 3 November 2026. Its last run was 2 November 2026 (not due).

**Legal position.** `docs/legal/positions/council-procurement-platforms.md`.
- Clutha's terms, accepted "By entering this website": "The Data may not be distributed or copied for any commercial purpose."
- Tauranga's terms allow "personal, informational and non-commercial purposes only".
- Dunedin's site: "Upon request, information ... may be used free of charge". That means asking first.
- TenderLink shows a login or an Incapsula challenge, and VendorPanel needs registration. Both are locks under hard limit 6.
- Wellington City (403), Environment Canterbury and Waikato Regional (Incapsula) gave failed reads. Queenstown Lakes redirected to Radware.
- Crawl delays: Clutha 7 s, Tauranga 5 s.

**Why it is off.** Ruling 136 (Arthur, 3 November 2026): "forget it. store these but take them off any work schedule they are lowest priority." No letter is sent and nothing is captured. The survey and the terms pages stay stored. The lane is taken up again only on Arthur's word. Councils' awards on GETS stay held in the `tenders` lane: 6,545 notices from 76 councils at the survey.

**What went wrong and what we learned.** 22 October 2026: the first watch run was red because VendorPanel's page redirected (302) and was set aside. TenderLink's Hutt Valley portal and Queenstown Lakes' "Awarded Council Contracts" page sent challenges and are never to be asked again.

**Still missing (by decision).**
- Dunedin's quarterly contract-award PDFs (2021 to September 2026).
- Clutha's 17 awards with supplier and price.
- Tauranga's current tenders (none of its awards are on GETS).
- Queenstown Lakes' awarded contracts.
- 17 councils' sites where the home page had no tender link (class F in `survey.md`); a full walk might find lists.

## Electoral Commission candidate returns (lane `candidate_returns`)

**Hosts and entry points.** Host: `elections.nz` (behind an Incapsula bot wall). The new estate fetches nothing from it. The lane copies, by sha256, files the old estate already holds. The old estate got them three ways:
- The Commission's per-election listing pages, a plain GET form paged 20 rows at a time: `https://elections.nz/democracy-in-nz/historical-events/2023-general-election/candidate-expenses-donations-and-loans?Year=2023&start=<n>` and `https://elections.nz/democracy-in-nz/historical-events/2020-general-election-and-referendums/candidate-expenses-and-donations-for-the-2020-general-election?Year=2020&start=<n>`. The Commission renamed these pages between elections, so the URLs are written out, never derived.
- Return PDFs at `https://elections.nz/assets/candidate-returns/<year>/<party-or-electorate>/<file>.pdf`. An amended return is filed at `https://elections.nz/assets/Uploads/<file>-amended-<ddmmyy>.pdf`, with no year or party in the path.
- The Commission's summary spreadsheets: `2020-Candidate-Returns.xlsx`, and for 2023 dated versions named `2023-candidate-returns-updated-<DDMMYYYY>[-vN].(csv|xlsx)`.
- An Internet Archive (Wayback) replay of the asset tree, plus one manual browser download of the 2020 returns.

**What we capture.** Return PDFs: one per candidate, plus amendments. The Commission's listing pages, kept as rendered HTML. The summary spreadsheets.

**Held.**
- Documents: 1,165 (2,466 MB). That is 1,105 PDFs (2,456 MB), 58 listing pages (9 MB) and 2 spreadsheets (0.1 MB).
- Fetch dates as the old estate records them: 19 August to 12 October 2026. All landed in the new estate on 20 October 2026.
- Names: 3,548 in `docs.names`, which is 1,774 file names plus 1,774 old-folder paths.
- Same bytes under more than one name: 609 documents. In every case the archive replay and the browser download hold the same return under two names. 472 returns are held under one archive name, 26 under an `Uploads` (amendment) name, and 58 are listing pages.
- Return files by status: 2020 general election 609 (576 current, 15 replaced by a linked amendment, 18 unlisted); 2022 Tauranga by-election 12 (unlisted); 2023 general election 484 (473 current, 11 unlisted).
- Returns read into `candidate_returns.returns`: 930 (351 from a text layer, 579 from stored page images, i.e. scans). 175 are set aside.
- Commission spreadsheet rows: 2,151 (2020: 1,184; 2023: 967).
- Published: 1,103 rows in `pub.candidate_return_totals`. 930 are read returns; 173 are Commission spreadsheet rows standing where no return is read. There are 482 Part A donor rows.
- Content dates: the 2020 and 2023 general elections and the 2022 Tauranga by-election. The old estate also holds the 2011, 2014 and 2017 returns; the lane leaves them where they are.

**How we walk it.** The old estate's walk ran inside the old `ec-disclosures` job, which fires at 03:30 NZ time (`ops/ec_disclosures_feed.py --candidate-returns`):
- A real headed Chromium runs on the desktop display. It uses the browser's own User-Agent, with nothing patched and no spoofing. It waits on the challenge shell and does one plain reload after the shell sets its cookie, as a person's browser would.
- It walks `start` in steps of 20 and stops at the first page that adds no new asset.
- It works one request at a time, at least 2 s apart plus 0 to 1 s of jitter (the Commission's crawl delay as read in a browser in July 2026).
- Downloads go through the same browser session. Each is recorded in a manifest (file, sha256, bytes, source URL, fetched_at).
- A challenged or refused file counts as a failed read. It is retried on a later firing by a "missing returns" pass (`--candidate-missing`, nightly). The full per-candidate walk is not scheduled; it was run by hand on 25 September and 12 October 2026.
- A new file is downloaded only if its Commission file name is not already held. The new lane compares by sha256.
- The new estate's job, `qv4-candidate-returns-load`, runs nightly at 02:40 NZ time. It copies and reads only and makes no network request.

**Legal position.** No one-page position for elections.nz is on file in the new estate's `docs/legal/positions/` (`local-election-candidate-returns.md` covers council returns on other hosts, not this). The basis used is the old estate's ruling 242 (7 September 2026): a government body's proactively released information may be collected, politely, even where robots.txt says no. Old ruling 243 adds the headed browser. Old ruling 241 closes the Wayback route for the live disclosure page. No terms were accepted (not verified). Statutory limits: these are returns filed under the Electoral Act 1993 and published by the Commission. Donor street addresses are held privately and never published. robots.txt answers 403 behind the wall, which the old estate treats as absent (old ruling 168). Crawl delay honoured: 2 s.

**What went wrong and what we learned.**
- 25 September 2026: the listing is paged, not a single list. One render showed 20 rows, and the Wayback bulk pull had stopped at 237 of the 274 2023 assets. The missing 37 were 11 ordinary returns and 26 amendments. The walk by `start` fixed this.
- Amendments are published separately under `/assets/Uploads/`, with a different name pattern and no year or party in the path. Only the Commission's listing link says which return an amendment replaces. 15 of the 2020 returns are replaced.
- A document is its bytes (sha256): the same return turns up under several names (archive replay plus browser download), counted once.
- 7 September 2026: the Wayback pull had cut 16 of the 2020 files at exactly 1 MiB. Files of exactly 1,048,576 bytes are treated as cut and not counted as held.
- Two kept listing pages (2020 `start=620`, 2023 `start=500`) have no table rows, probably a challenge page the browser kept.
- Most returns are scans, or typed forms with image pages. 579 were read from stored page images, not a text layer. 30 are set aside because no text page carries the declaration and no stored reading exists. About 668 typed returns have their Part A on image pages (21 October 2026).
- One single return was refused by the wall on 25 September 2026 (once a 403, once a challenge page served with a 200). It stayed missing until the nightly retry pass was added on 12 October 2026.

**Still missing.**
- Commission spreadsheet lines with no matching return: 10 have "no held return answers", and 9 listing rows link no return. Another 9 are marked by the Commission as "no return received", which is not a capture gap.
- 175 held returns are not read, mostly scans waiting for a page reading.
- Any 2026 general election returns: the election is 7 November 2026 and returns come later.
- Only 2 spreadsheets are landed, while the old folder holds 12 versions (2 for 2020, 10 for 2023) (not verified why).

## Electoral Commission large-donation disclosures (lane `disclosures`)

**Hosts and entry points.** Host: `elections.nz`, behind the Incapsula wall. The new estate fetches nothing; ruling 70 (21 October 2026) says no nightly capture of the Commission's table is added before the public site is switched. The lane copies, by sha256, from the old `ec-disclosures` job's folder. Entry points:
- Listing, 2023 regime onward (over $20,000): `https://elections.nz/democracy-in-nz/political-parties-in-new-zealand/donations-exceeding-20000/`
- Listing, earlier regimes (2008–2010 over $20,000; 2011–2022 over $30,000): `…/donations-exceeding-20000/donations-exceeding-30000`
- Scanned declarations linked from the listing: `https://elections.nz/assets/2026-20k+-donations/<file>.(pdf|jpg|png)` and `https://elections.nz/assets/Donation-returns/<year>/<file>.pdf` (2023–2025), plus a few bare `/assets/<file>`.

**What we capture.** The two listing pages, kept as rendered HTML; the Commission's own table is the register. The scanned declaration for each row: PDFs and a few JPEG/PNG images.

**Held.**
- Documents: 322 (170 MB). That is 279 PDFs (138 MB), 11 images (27 MB) and 32 listing-page versions (5 MB).
- Fetch dates: declarations 19 August to 31 October 2026. Listing versions landed 19 October to 4 November 2026.
- Names: 586. Each declaration has a file name and an old-folder path. The 32 listing versions share only 4 names: the old job overwrites the same two listing files every night, and each version whose bytes changed is a new document under the same name.
- Same bytes under more than one file name: 1 declaration.
- Rows: 530 declarations (`pub.disclosures`) and 913 itemised gifts (`pub.disclosure_items`). By regime: over $20,000 from 2023, 286 rows (285 with the scan held); over $30,000 2011–2022, 220 rows; over $20,000 2008–2010, 24 rows (neither earlier regime has any scan held). 26 are amendments.
- Content dates: gifts received from 9 April 2008 to 29 October 2026. Declarations received by the Commission up to 2 November 2026.
- Checks: 291 declaration files sit in the old folder. 285 are linked by the table and 6 are not.

**How we walk it.** The old estate's `ec-disclosures` job does the walk, daily at 03:30 NZ time with up to 10 minutes of random delay:
- A real headed Chromium on a desktop display (X11). A fresh browser profile is made per run, because a profile left by a killed run crashed Chromium.
- The browser keeps its own User-Agent, with no stealth patches and no identity rotation.
- It loads a page and, while the Incapsula shell shows, waits 2 s at a time, reloading at most twice after the shell sets its cookie. If the page is still challenged, the read has failed and the run exits 2, to be tried again at the next firing. No challenge is solved.
- It collects every `/assets/` link from both listing pages and downloads only files whose Commission file name is not already held, through the same browser session. One request at a time, at least 2 s plus 0 to 1 s of jitter apart.
- Each download is a manifest row (file, sha256, bytes, source URL, fetched_at, robots status).
- robots.txt is read every run under the old estate's own User-Agent (which names the project and a contact address); it answers 403.
- The same firing then runs the party annual-returns page, the 2026 candidate lists, the retry pass for missing candidate returns, and the party register (see the note below).
- Run record: 210 runs from 7 September to 4 November 2026. 589 assets seen across the newest night's runs. Every page rendered without a challenge since 8 September; the last challenged page was on 7 September 2026.
- New estate: `qv4-disclosures-load` runs daily at 07:40 NZ time. It copies by hash and publishes only when its check against the frozen site is green. `qv4-disclosures-read` reads, on a local model, scans that have no stored page reading.

**Legal position.** No one-page position for elections.nz is on file in the new estate (not verified whether one exists in the old estate). The basis is old ruling 242: a government body's proactive release, collected politely even where robots says no. Old ruling 243 allows the headed browser shown no challenge. Old ruling 241 closes the Wayback route for this page. Statutory basis: party donation declarations under the Electoral Act 1993, which the Commission publishes. The donor cell's address lines are kept in a private table and never published. robots.txt answers 403 (treated as absent, old ruling 168). Crawl delay used: 2 s.

**What went wrong and what we learned.**
- 7 September 2026: the earlier Wayback pull had saved the wall's challenge page (about 212 bytes of HTML) under 35 of the 71 asset names for 2026 declarations. It also cut files at exactly 1 MiB. Both are tested for and never counted as held.
- 7 September 2026: headless Chromium, old or new, gets only the challenge shell. A headed browser renders the page.
- Under Wayland, Playwright's launch hangs unless `--ozone-platform=x11` is passed.
- Single asset downloads are refused now and then: 50 refusals over the run record, 28 of them a challenge page served with HTTP 200 and 22 with HTTP 403. On 3 and 4 November 2026 one newly listed declaration was refused each night, so 1 row from 2023 onward has no scan held.
- The table is the register. An amendment is the Commission's own statement and appears in place. The page is overwritten nightly, so every changed version is kept by its bytes.
- A declaration belongs to the year the party received the gift, not the date the Commission received it. 8 of 520 differ.
- Scans: 6 have no text layer and no page reading. 27 have no total read under the form's label.

**Still missing.** The scanned declarations for the 244 rows from 2008 to 2022: none is held, and it is not verified whether the Commission links them. The 1 declaration refused on 3–4 November 2026. Page readings for 6 scans.

**Note: other lanes on the same host (not in the moving list).** The same old browser job and old folder also feed two more lanes:
- `party_returns`: the parties' annual donations-and-loans returns. Nightly mode `--annual-returns` over `…/political-parties-in-new-zealand/party-donations-and-loans-by-year/`, with assets at `/assets/Party-donations-and-loans/<year>-returns/…`. Calendar 2017 onward. 154 documents, 671 MB.
- `party_finance`: party election expense returns (2020, 2023), annual financial statements, broadcasting-allocation pages and decisions, the register of promoters and promoter expense returns (2020, 2023). These were by-hand modes in September 2026. 116 documents, 270 MB.

Neither new lane fetches anything itself.

## Tenancy Tribunal orders (lane `tenancy_tribunal`)

**Hosts and entry points.** Host: `forms.justice.govt.nz` (Ministry of Justice).
- Search page: `https://forms.justice.govt.nz/search/TT/`. It is a script over a Solr listing service.
- Listing, JSON, gzip-compressed whether asked or not: `https://forms.justice.govt.nz/forms/publicSolrProxy/solr/TTV2/select?q=publishedDate_dt:[<YYYY-MM-01>T00:00:00Z TO <next month>T00:00:00Z}&fq=jurisdictionCode_s:TT&sort=publishedDate_dt asc,id asc&start=<n>&rows=1000&wt=json`
- Order PDF: `https://forms.justice.govt.nz/search/Documents/TTV2/<orderId>.pdf`, or for an order flagged as an MBIE order, `…/TTV2/PDF/<publishedOrderPdfName>`. This is how the page's own `abstract.theme.tt.js` builds them.
- Each listing row carries `unpublishedDate`: an order is taken down three years after publication.

**What we capture.** One listing response per published month, kept as JSON, which is the citation for its rows. Then each order's PDF.

**Held.**
- Documents: 20,838 (2,956 MB). That is 20,777 order PDFs (2,937 MB) and 61 listing responses (19 MB). Each is held under its URL, so there are 20,839 names. The one extra is a single PDF that two order ids point to.
- Orders listed: 33,847 (one per case). Orders held: 20,778. Waiting: 13,069.
- Held orders were published 19 October 2023 to 16 September 2025. The orders waiting were published 23 June 2025 to 5 October 2026.
- No order leaves the source within 14 days that is not held. The earliest takedown among the waiting orders is June 2028; most fall from September 2028.
- PDFs were fetched 18 to 24 October 2026.
- Months listed: 38 (October 2023 to November 2026), 69 listing reads in all. The source's own count is 33,841 across the newest read of each month.
- The source listed only 155 orders for October 2026 and 0 for November 2026 on 3 November 2026 (not verified whether publishing has slowed).

**How we walk it.** Job `qv4-tenancy-tribunal-capture`, nightly at 22:30 NZ time, enabled.
- Budget 4.5 hours, off-peak only (22:00 to 06:00 NZ time), deadline 6 hours.
- Each run lists every month of the 37-month window not yet listed, oldest first, and always relists the current and previous month. It pages by `start` with 1,000 rows per request.
- It then fetches orders not yet held, soonest takedown first. Nothing is fetched twice; an order already held is never asked for again.
- One request at a time, at least 5 s apart. That is the floor in the legal position, and the gate's polite floor because robots.txt cannot be read. This gives about 3,240 PDFs a night.
- One run at a time, enforced by a database advisory lock.
- Everything goes through the estate's fetch gate with the estate's single User-Agent (which names the project and a contact address). No browser is used.
- A 403, 429, 5xx, challenge page or off-host redirect is a failed read: logged, and the run stops. Three transport failures in a row also stop it.
- While the gate holds the host, a run asks nothing at all.
- Fetch gate: 20,928 requests to this host from 18 October to 4 November 2026.

**Legal position.** `docs/legal/positions/tenancy-tribunal-decisions.md` (written 18 October 2026):
- Open: no login, key, challenge or CAPTCHA.
- Copying: Copyright Act 1994 s 27, no copyright in the judgments of a court or tribunal (lawyer to confirm it covers this Tribunal).
- Terms: none accepted. The search tool's "Important Information" page says orders older than three years are not available, names are as given by the applicant and not verified, and it is not an authoritative background check.
- Statute: Residential Tenancies Act 1986. The Tribunal may suppress names or not publish an order; a suppressed order is simply not listed.
- Privacy: the three-year window is the Ministry's choice; orders leave the search after it, so anything not fetched before then is gone from this source.
- robots.txt: the host reset the connection, so it is treated as unreadable and the 5 s polite floor applies. No crawl delay is stated.
- Floor: 5 s, one at a time, off-peak.
- The position covers only `/search/TT/`, the TTV2 listing service and `/search/Documents/TTV2/`.

**What went wrong and what we learned.**
- August 2026: the old estate found this host dropping it on every path. It never captured these orders.
- Run records: 18 runs, 7 successful and 11 failed.
  - 19 October 2026, 07:58: asked nothing (off-peak was over).
  - 19 October 2026, a hand run from 08:36: 46 listings, 32,193 orders listed, 3,152 landed.
  - Nightly 19 to 23 October 2026: about 3,228 to 3,238 landed each night, budget spent.
  - 23 October 2026: 11 transport failures set aside.
  - 24 October 2026: 991 landed, then the run stopped on three transport failures in a row (connection reset by peer).
  - 25 October to 3 November 2026 (10 nights): every run listed its two months, landed 0, and stopped after three connection resets on the first three PDFs.
  - 53 PDF requests were set aside as connection resets (24 October to 3 November) and 1 as a remote disconnect (19 October).
- The listing service kept answering throughout; only the order PDFs reset.
- 4 November 2026, 00:24: the gate held the host under ruling 141. A host that refuses, throttles, or resets three times in a row is sent nothing until a person clears it, and a hold prompts a search for another way, not a retry. One listing request was refused by the gate that day.
- 5 November 2026: a run on a held host now ends quietly, asking nothing.
- 4 November 2026 (ruling 143): the listing is to be asked for each row whole, not with a field list. No month has yet been relisted whole because the host is held.
- The ingest MCP holds no Tenancy Tribunal decisions (survey of 3 November 2026).

**Still missing.**
- 13,069 listed order PDFs (published 23 June 2025 to 5 October 2026).
- Every month relisted whole (all 38 months).
- Orders published after 5 October 2026.
- Orders already taken down before 18 October 2026 (published before about 19 October 2023): gone from the source.

# The courts lane's own captures

## Judicial Decisions Online (lane `courts`, capture `courts-jdo`)

**Hosts and entry points.**
- Host: `www.justice.govt.nz` (Ministry of Justice).
- The page `/courts/decisions/jdo/` is a script over two open JSON endpoints:
  - `/jdo-taxonomy-api/courts`: the list of courts. It answers a same-host redirect to `/jdo-taxonomy-api/courts/`.
  - `/jdo-search-api`: the listing.
- The listing takes the parameters `court`, `location`, `judge`, `counsel`, `caseName`, `fileNumber`,
  `citation`, `judgmentDate=['Y-M-DT00:00:00Z','Y-M-DT23:59:59Z']`, `minuteReference`, `searchTerms`, `page`
  and `sort=judgmentdate desc`. Every field is sent, empty where unused, as the site's own script sends them.
- `/jdo-search-api?…` answers a same-host redirect to `/jdo-search-api/?…`, so each listing page costs two
  logged requests.
- Each decision is a PDF at an opaque address, `/jdo_documents/workspace___SpacesStore_<id>.pdf`.
- The listing covers ten courts: Supreme Court, Court of Appeal, High Court, Employment, Environment, District,
  Family, Youth, Māori Land and Māori Appellate.

**What we capture.**
- Every listing page (the JSON, stored by hash).
- The court list.
- Every listed PDF whose address the MCP has not already landed. Each PDF is checked to start with `%PDF`.

**Held.**
- **Documents:** 6,142 (1,846.5 MB). Of these, 5,927 are PDFs (1,844.7 MB) and 215 are listing or court-list
  JSON pages. Landed between 3 November 15:08 and 5 November 05:24 NZDT.
- **Ledger:** `courts.own_files` has 5,932 landed rows, 0 absent (404) and 5,995 distinct hashes across all
  own sources. One PDF hash sits under two addresses.
- **By court and listing year:**

  | Court | Year | Files landed | Listing total | Note |
  | --- | --- | ---: | ---: | --- |
  | High Court | 2020 | 1,073 | 2,038 | in progress, page 21 |
  | High Court | 2021 | 2,189 | 2,200 | done |
  | High Court | 2022 | 1,362 | 2,014 | done |
  | High Court | 2023 | 0 | 2,396 | done, see below |
  | High Court | 2024 | 1,285 | 2,433 | done |
  | High Court | 2025 | 0 | 2,550 | |
  | High Court | 2026 | 15 | 1,583 | |
  | Māori Appellate Court | 2024 and 2025 | 8 | | |
  | Māori Land Court | 2025 | 0 | | page 1 only; trial |

- **Why High Court 2023 and 2025 are zero.** Every listed address was already in the MCP's courts files. A
  sample of 100 addresses from the 2023 listing: all 100 were held by the MCP. The MCP's courts corpus now
  carries 16,318 JDO addresses, against 5,702 on 3 November.
- **Content dates:**
  - By listing year: 2020 to 2026.
  - Read so far: only 8 JDO files are in the lane's last published reading (4 November 09:47), dated
    23 July 2025 to 23 October 2026. The nights' 5,900-odd files wait for the next load.
- **What the listing gives.** Each result is only `caseName` and `url`. No date, citation or court is given per
  row, so those come from the document's own caption.

**How we walk it.**
- One court at a time, in this order:
  1. High Court
  2. Court of Appeal
  3. District Court
  4. Family Court
  5. Youth Court
  6. Employment Court
  7. Environment Court
  8. Māori Land Court
  9. Māori Appellate Court
  10. Supreme Court, last, because the MCP holds more of it
- Within each court, one judgment-date year at a time, from this year back to 1990, 50 results a page, newest
  first.
- A query answers at most 10,000 results (page 201 is empty). A year at the cap would be asked a month at a
  time; no court is near the cap today.
- **Resuming.** The cursor (`courts.own_cursor`: source, court, year, total, pages done, done) is never wiped.
  - A past year resumes at the page after the last one walked, and is never asked again once walked to its end.
  - This year and last year are walked again each night from page 1, until a page holds nothing new.
- **Skips.** A PDF whose address the MCP has landed, or that the ledger already holds, is not fetched.
- **Status codes.**
  - A 404 is recorded as `absent` and the walk goes on.
  - A 403, 429, 5xx, challenge page, reset, timeout, a listing that is not JSON, or a "PDF" that is not one
    stops the run. Nothing is retried in the same run.
- **Job.** `qv4-courts-jdo-capture`, nightly at 22:00 NZDT. Time budget 27,600 s, deadline 27,900 s, nice 10,
  one request at a time with a 5 s floor.
- **Throughput.** About 640 PDFs an hour. The average PDF is about 311 KB.
- **Robots.** robots.txt disallows `/*/jdo`, `/jdo_documents/` and `/assets/`, and states no crawl delay. Taken
  under hard limit 5: this is the Ministry's own proactive publication.
- The Ministry's pages say decisions go up no earlier than three days after delivery, and restricted decisions
  are not published.

**Legal position.** `docs/legal/positions/court-judgments.md`, section "Added 3 November 2026 (ruling 140)":
- Open: no login, key, challenge or CAPTCHA.
- No copyright, per the Ministry's own statement citing Copyright Act 1994 s 27(1)(g).
- No terms shown before a decision.
- Family and Youth Court decisions are anonymised by statute before publication.
- The page was written before capture (ruling 61). A lawyer's review is owed before anything is sold.

**What went wrong and what we learned.**
- **Night of 3 to 4 November.** The walk ran 22:00 to 00:02 and landed about 1,290 files (High Court 2024 and
  2026). The job then exited 1 at 00:07 with no run record. A re-run at 01:16 landed one PDF and exited 1 at
  01:22. Both show the same pattern: about 5 minutes of silence, then the database's 300 s query limit ends the
  run. The cause was not recorded (not verified).
- **Night of 4 to 5 November.** The walk ran 22:00 to 05:24 and landed about 4,640 files. At 05:24 its insert
  into the ledger waited behind the courts load, whose `CREATE INDEX IF NOT EXISTS` held a lock on
  `courts.own_files`. The insert was cancelled at 05:29. Fixed in commit 52fb008: the load now creates its
  tables and commits at once. The failure was ours, not the host's.
- **Daytime run on 4 November, 09:46.** Refused by the job's own off-peak rule, as designed.
- **Load and pull overlap** (commit be0bdaf). The courts load now reads arrivals up to its own start time, so a
  pull landing during a load is no longer counted against it.
- **The host itself.** It never refused, throttled or challenged us: no 403, 429, 5xx or reset in about 6,500
  requests.

**Still missing.**
- High Court 2005 to 2019 and the rest of 2020: about 20,000 to 25,000 decisions by the survey's yearly counts
  (not verified exactly).
- Every other court, none walked yet. Totals from the survey, 3 November:

  | Court | Decisions listed |
  | --- | ---: |
  | Court of Appeal | 6,995 |
  | Supreme Court (the MCP holds more than JDO) | 3,014 |
  | District Court | 2,015 |
  | Family Court | 1,143 |
  | Employment Court | 466 |
  | Māori Land Court | 408 |
  | Environment Court | 390 |
  | Youth Court | 233 |
  | Māori Appellate Court | 47 |

- At the planned pace, the back catalogue was about nine nights from 3 November.

---

## Employment Relations Authority (lane `courts`, capture `courts-era`)

**Hosts and entry points.**
- Host: `determinations.era.govt.nz`.
- **Search form:** `/determinations/DeterminationSearchForm?Parties=&JurisdictionTitle=&Keywords=&JurisdictionIdentifier=&DateFrom=YYYY-01-01&DateTo=YYYY-12-31&StatutoryOfficer=&action_doSearch=Search`,
  plus `&start=10n` from page 2. The older form path `/determination-search-page/DeterminationSearchForm?…`
  redirects to it.
- **Pages:** 10 results a page. The pager reads "N of M".
- **Records:** each record is an `<li class="search-results__record">` with a PDF link under
  `/assets/elawpdf/<year>/`.
- **Other pages:** each determination also has a page `/determination/view/<n>` (n from 1 to about 21,764),
  and there is `/determinations/recent`.

**What we capture.**
- Each year's search result pages (HTML, stored by hash).
- Every listed PDF the MCP has not landed.
- A record with no PDF is passed. The Authority publishes no PDF where a restriction applies.

**Held.**
- 40 documents (10.0 MB): 36 PDFs (8.8 MB) and 4 search pages (1.3 MB). All landed on 3 November, 15:50 to
  15:53, in a daytime trial capped at 40 requests.
- Ledger: 36 landed. No hash sits under more than one name.
- Content: 2014 only, pages 1 to 3 (and part of 4) of 89. 35 read, dated 16 to 24 December 2014; 1 waits on the
  page reader.

**How we walk it.**
- One year at a time, from this year back to 2000, newest first, 10 a page.
- The same floor, stops, skips, ledger and cursor as JDO. The cursor's `total` here is the year's page count.
- This year and last year are re-walked each night from page 1 until a page holds nothing new.
- **Job.** `qv4-courts-era-capture`, nightly at 22:00 NZDT beside the JDO job, its own pacer. Budget
  27,600 s, 5 s floor.
- **Robots.** robots.txt disallows `/search`, `/determination/`, `/determinations/`, `/determinations/recent`,
  the search form and `/assets/elawpdf/` (its comment says this is to keep the determinations out of search
  engines). It states **`Crawl-delay: 5`**, which the gate honoured from the first request on 3 November.
  - **Correction.** Our survey note and our position both say this host states no crawl delay. That is wrong:
    the gate log shows "crawl delay 5s honoured" from 14:42 on 3 November.

**Legal position.** `docs/legal/positions/specialist-court-and-authority-decisions.md`:
- Open.
- No copyright (s 27(1)(g)). The lawyer is to confirm this for the Authority's determinations.
- No terms found.
- Non-publication orders exist under the Employment Relations Act 2000, Schedule 2 cl 10.
- The site's terms page is to be read at the first run. A bar on robots found there would stop the host.

**What went wrong and what we learned.**
- **Two failed nights, 3 and 4 November, both at the first request.** The run asked for 2026 with
  `DateTo=2026-12-31`. The form refuses a date in the future: it answered a same-host redirect to `/`, then to
  `/determinations`, the landing page. Our parser saw no `search-results` and stopped with "a search page that
  is not the Authority's results page". Each night lasted about 11 seconds and made 1 to 3 requests. 2014's
  search answered normally the same afternoon.
- **Fix** (commit 8234b55, 5 November). The current year's search ends at today's date. Two checks that
  morning:
  - At 05:34, the old form of the request reproduced the redirect.
  - At 05:47, `DateTo=2026-11-05` answered results and one 2026 PDF was asked.

  That 05:47 PDF is not in the main store (not verified why). The job has not yet run a night with the fix.
- **For anyone walking this site.**
  - Any year range whose end is in the future fails silently: you get a redirect to the landing page with
    status 200, not an error.
  - The view numbers (1 to about 21,764) give a check that no year was missed.

**Still missing.**
- Almost everything: about 21,700 determinations, 2000 to 2026 (2015 alone about 740).
- The MCP holds 581 ERA PDFs, citations 2019 to 2026.
- The plan was about four nights at 5 s.

---

## The Ministry's decisions finder (lane `courts`, capture `courts-finder`)

**What it is.** One search page, shared by the Ministry of Justice's tribunal and court pages on
`www.justice.govt.nz`, that lists decisions for 26 jurisdictions. The Employment Court, Māori Land Court and
Coroners sites send their readers to it.

**Hosts and entry points.**
- Host: `www.justice.govt.nz` (the same host as JDO).
- **Listing:** `/tribunals/human-rights/hrrt-decisions/?Filter_Jurisdiction=<id>[&start=25n]`, 25 a page. The
  same finder also appears under `/courts/decisions/`.
- **Count:** in the `resultsHeader` block.
- **Links:** in `<ol id="SearchResults">`. The page also carries commented-out copies of each link, which must
  be dropped.
- **Files:** under `/assets/Documents/Decisions/`. The Weathertight Homes Tribunal's files sit directly under
  `/assets/<file>.pdf`, and their file names carry party names.
- **Redactions:** a file name carrying `REDACTED` marks a redacted version.

**What we capture.**
- Each finder page (HTML).
- Every listed PDF the MCP has not landed.
- A listed file that is not a PDF is counted and never asked.

**Held.**
- 30 documents (7.3 MB): 28 PDFs (7.1 MB) and 2 finder pages. Landed 3 November, 16:21 to 16:24, in a daytime
  trial capped at 30 requests on one jurisdiction, the Weathertight Homes Tribunal (419 listed).
- No hash sits under more than one name.
- Reading:
  - 15 set aside, because there is no Weathertight profile yet.
  - 12 wait on the text reader, dated April 2014 to March 2022.
  - 1 waits on the page reader.

**How we walk it.**
- Jurisdictions are walked in a fixed order, those the MCP lacks most first:

  | Order | Jurisdiction | Id |
  | ---: | --- | ---: |
  | 1 | Employment Court | 17 |
  | 2 | Disputes Tribunal | 26 |
  | 3 | Māori Land Court | 24 |
  | 4 | Legal Complaints Review Officer | 29 |
  | 5 | ACC appeals registry | 795 |
  | 6 | Real Estate Agents Disciplinary Tribunal | 32 |
  | 7 | Lawyers and Conveyancers Disciplinary Tribunal | 279 |
  | 8 | Human Rights Review Tribunal | 27 |
  | 9 | Private Security Personnel Licensing Authority | 745 |
  | 10 | Social Security Appeal Authority | 275 |
  | 11 | Māori Appellate Court | 468 |
  | 12 | Weathertight Homes Tribunal | 35 |
  | 13 | Land Valuation Tribunal | 636 |
  | 14 | Environment Court | 19 |
  | 15 | Canterbury Earthquakes Insurance Tribunal | 768 |
  | 16 | Accident Compensation Appeal Authority | 23 |
  | 17 | Review Authority | 277 |
  | 18 | Customs Appeal Authority | 792 |
  | 19 | Immigration Advisers Complaints and Disciplinary Tribunal | 28 |
  | 20 | Student Allowance Appeal Authority | 33 |
  | 21 | Secondhand Dealers and Pawnbrokers | 777 |
  | 22 | Coroners | 18 |

- **Not walked:**
  - The Tenancy Tribunal (618), which has its own lane.
  - Five jurisdictions that answer nothing in the finder: Taxation and Charities Review (902), Copyright (25),
    Victims' Special Claims (412), Waitangi (22), and Secondhand Dealers and Pawnbrokers Licensing (30).
- **Resuming.** Each jurisdiction is one cursor row. Once walked to its end, only its newest pages are asked each
  night, until a page holds nothing new.
- **Schedule.** It runs inside `qv4-courts-jdo-capture`, after the JDO walk reaches its end for the night,
  because it shares JDO's host and must not run beside it. So it has not run a real night yet.
- **Robots.** As for JDO: `/assets/` is disallowed and no crawl delay is stated.

**Legal position.** `court-judgments.md` (ruling 140 section) covers the finder. The tribunals in it are also
covered by `professional-disciplinary-tribunal-decisions.md` and `specialist-court-and-authority-decisions.md`.

**What went wrong and what we learned.**
- No failures on the host.
- The "count" in the results header is the only total the page gives. The survey's per-jurisdiction figures
  are page counts × 25, so each may be up to 25 too high.

**Still missing.** About 15,000 decisions the MCP does not hold (about 17,000 listed, less about 1,750 held).
The largest are:

| Jurisdiction | About |
| --- | ---: |
| Employment Court (finder) | 4,100 |
| Disputes Tribunal | 3,550 |
| Māori Land Court | 2,225 |
| Legal Complaints Review Officer | 1,450 |
| ACC appeals | 1,275 |
| Real Estate Agents Disciplinary Tribunal (the MCP holds 793) | 975 |
| Lawyers and Conveyancers Disciplinary Tribunal | 600 |
| Private Security Personnel Licensing Authority | 575 |
| Social Security Appeal Authority | 450 |
| Māori Appellate Court | 425 |
| Weathertight Homes Tribunal | 410 |

---

## The courts survey (lane `courts`, capture `courts-survey`)

**What it is.** Tranche 0 of ruling 140, 3 November 2026, 14:33 to 14:45 NZDT. A one-off look at where each
court and tribunal publishes and how it can be listed. About 60 gated requests, at least 5 s apart per host.
Nothing was fetched in bulk. Written up in `docs/research/courts-sources-2026-11-03.md`.

**Hosts and entry points read.**

| Host | Names held |
| --- | ---: |
| `www.justice.govt.nz` (JDO page and script bundle, the court list, the finder's page 1 for each of 26 jurisdictions, tribunal pages) | 19 |
| `www.courtsofnz.govt.nz` (robots, sitemap, `/judgments/<court>`, 3 PDFs) | 4 |
| `coronerscourt.govt.nz` | 4 |
| `determinations.era.govt.nz` | 4 |
| `www.hpdt.org.nz` | 4 |
| `www.māorilandcourt.govt.nz` | 3 |
| `www.employmentcourt.govt.nz` | 2 |
| `www.districtcourts.govt.nz` | 2 |
| `waitangitribunal.govt.nz` | 2 |
| `www.teachersdisciplinarytribunal.nz` | 2 |
| `teachingcouncil.nz` | 2 |

Two requests to `forms.justice.govt.nz` `/search/IPT` were reset, so nothing from that host is held.

**Held.**
- 45 documents (5.4 MB): 32 web pages, 10 text files (robots files), 2 JSON and 1 PDF.
- 2 hashes sit under more than one name.
- The store holds them for reference. None is a row in the lane's tables.

**What it found** (not repeated in the sections above):
- **courtsofnz.govt.nz.**
  - `/judgments/<court>` lists only the last 90 days of public-interest judgments, with an RSS feed at
    `/judgments/<court>/RSS`.
  - PDFs are under `/assets/cases/<year>/`.
  - Old files are removed: 3 old addresses answered 404.
  - `/search/` drops automated requests and is out of bounds.
  - robots.txt disallows only `/search/` and a few admin paths, with no crawl delay.
  - The MCP already covers this site.
- **Coroners.** `coronerscourt.govt.nz` publishes selected findings only, as files under the Ministry's
  `/assets/Documents/Decisions/`. The MCP holds 166 to 167 Coroners PDFs.
- **Māori Land Court.** Its own site sends readers to the finder (jurisdictions 24 and 468).
- **Environment Court and Motor Vehicle Disputes Tribunal.** Their own pages send readers to NZLII only. NZLII
  is not a source for us.
- **Health Practitioners Disciplinary Tribunal.** The search page is open, but its decisions-documents page
  sends readers to a login, so it is out (hard limit 6). The MCP holds 790 of its pages and PDFs.
- **Teachers Disciplinary Tribunal.** One page lists PDFs hosted on a shared CDN (`res.cloudinary.com`). 30
  were seen on the page read, with decision years 2021 to 2026 named. Not captured: our position must first
  name the tribunal's account path on the CDN.
- **Waitangi Tribunal.** `/tribunal-reports/by-wai-number` lists 206 report PDFs, which live on
  `forms.justice.govt.nz/search/Documents/WT/`.
- **`forms.justice.govt.nz`** hosts the Waitangi Tribunal reports, the Immigration and Protection Tribunal's
  three databases, the alcohol licensing authority's decisions after 2014, and the Tenancy Tribunal.
  - It reset the connection on 3 November.
  - The Tenancy Tribunal's order PDFs had reset every request since 25 October.
  - The gate has **held** the host since 4 November 00:24 (ruling 141), so nothing more is asked of it.
- **Court Martial and Court Martial Appeal Court.** No official listing found.

**Legal position.** Three new pages, written for the survey: `specialist-court-and-authority-decisions.md`,
`waitangi-tribunal-reports.md` and `professional-disciplinary-tribunal-decisions.md`. `court-judgments.md` was
extended.

**Still missing.** Not a capture; nothing is owed from it.

---

## Old-estate copy and the retired courtsofnz RSS capture (lane `courts`, capture `courts`)

**What it is.** Two things stored under the source name `courts`:
1. **The old estate's own captures, copied by hash on 21 October 2026.** These were listed in a once-only
   export of 359 documents (pinned listing, sha256 `8285d006…`) and include 148 courtsofnz judgments and about
   205 Waitangi Tribunal documents. The old estate fetched them between 13 July and 14 October 2026. Each kept
   its original fetch time.
2. **The job `qv4-courts-capture`, now retired.** It ran nightly at 03:30 NZDT from 22 to 30 October 2026. It
   read the three RSS feeds on `www.courtsofnz.govt.nz` (Supreme Court, Court of Appeal, High Court), each
   item's case page, and the judgment PDF on that page. It never took `MR-` media releases or `/search/`.

**Hosts and entry points.**
- `www.courtsofnz.govt.nz`: `/judgments/<court>/RSS`, `/cases/<slug>` and `/assets/cases/<year>/`.
- Old copies only: `forms.justice.govt.nz/search/Documents/WT/<doc-id>/` and a few `www.justice.govt.nz/jdo_documents/`.

**Held.**
- 379 documents (1,289.3 MB): 372 PDFs and 7 other (the listing and feed files).
- Names: 354 file names, 202 `forms.justice.govt.nz` addresses (Waitangi Tribunal), 94 `www.courtsofnz.govt.nz`
  addresses and 3 JDO addresses. 272 hashes sit under more than one name (a file name plus its address).
- Arrivals by date: 113 on 13 July and 203 on 25 July (old-estate captures), a trickle through October, and 19
  on 22 October (the first RSS night).
- Content: the courtsofnz PDFs' addresses carry years 2023 to 2026. The Waitangi reports' dates were not
  measured (not verified).
- **None of these is a row in the lane's tables.** Since ruling 127 (30 October), the lane rebuilds only from
  the MCP plus its own captures. The 79 old-listing judgments that the MCP's corpus lacks are logged as catch
  lines (stage `listing`) to report to the provider.

**How we walked it** (retired).
- Each night: three RSS feeds, then each item's case page, then the PDF if it was new.
- One request at a time, 5 s floor, off-peak.
- A redirect to another host stopped the run (commit 5b84f9b).
- The job's run records:

  | Night | Items found | New files landed | Already held | Set aside |
  | --- | ---: | ---: | ---: | ---: |
  | 22 October | 86 | 16 | 69 | 3 |
  | 23 to 30 October, each night | 1 to 2 | 0 to 1 | | |

**Legal position.** `docs/legal/positions/court-judgments.md`:
- No copyright in judgments (s 27).
- No click-through terms.
- The court's suppression marking was read, and is now kept as a flag (ruling 142).
- robots.txt disallows `/search/` only, with no crawl delay. Floor 5 s, off-peak, feeds once a day.

**What went wrong and what we learned.**
- **Repeated case pages.** Of the 992 gate requests to `www.courtsofnz.govt.nz`, about 860 were the same
  95 to 98 case pages asked again every night from 22 to 30 October, although the feeds named only 1 or 2 new
  items a night. "Fetched once" was enforced for PDFs, not for case pages (not verified why the case pages were
  re-asked; the retired code is in git history before commit ab2a3b8). A provider walking this site needs only
  each new feed item's case page once.
- **The rest of the 992:** 88 PDFs on the first night and 1 on some later nights, about 30 RSS reads, and
  about 10 survey requests on 3 November.
- **The host itself.** It never refused or challenged us.
- **Retired.** Ruling 127 made the MCP the lane's only source; ruling 140 then reopened capture only for what
  the MCP lacks.

**Still missing.**
- The Waitangi Tribunal's 206 reports: `forms.justice.govt.nz` is held.
- The 79 old-listing judgments the MCP lacks.

# What we learned about sites the MCP already gathers

These are facts about the sites, and about what reached us. The MCP's corpora themselves are not described again.

- **Hansard (`hansard.parliament.nz`) and `parliament.nz`.**
  - The estate's own Hansard reader met a challenge (held on our side from 23 September). From about 5 October
    2026 the site has answered automated reads with a challenge.
  - We never pass one (hard limit 6). The fetch gate holds both hosts by name.
  - Ruling 78 (21 October): Hansard and Beehive are not captured by the estate; Arthur supplies a third-party
    source. Rulings 94 and 96 (26 October): the MCP is that source, and every corpus is taken.
  - The old estate read the transcripts from 17 July to 2 October 2026 (sitting days 20 November 2024 to
    23 September 2026) with no challenge on record.
  - The robots file is behind the challenge and was never read.
  - 10 of the archived parliament.nz pages (`parliament-wayback`) are the site's own refusal page ("Unauthorized
    Request Blocked"). We set them aside as blocked.
  - Gaps we measured (5 November):
    - Hansard: nothing before 11 February 2003.
    - Hansard: 35 days from 28 April 2026 held only as the uncorrected draft.
    - Hansard: no sitting after 23 September 2026.
    - No per-speech HTML (with Parliament's member ids) and no daily PDF bytes.
- **Parliament's written questions** (the Parliament API).
  - On 27 October, 17,619 questions came back with changed text and an unmoved `updated_at`. A change feed
    keyed on `updated_at` alone misses silent edits.
  - Records removed from the feed have later come back at a lower position.
  - 44,584 questions name an attachment that is not served.
  - 56 question numbers are missing (27 in 2019, 1 in 2020, 28 in 2026). Nothing after 1 October 2026 and
    nothing before 2003.
  - Bills, SOPs and select committee reports arrive as metadata without the paper's text.
  - Select committee reports stopped at exactly 1,000 on 3 November, which looks like a cap. By 5 November we
    hold 2,500 of the 10,970 the source lists, and 16,931 of its 1.1 million evidence and submission rows.
- **Beehive (`www.beehive.govt.nz`).**
  - On 21 October our robots read got an Imperva/Incapsula challenge page, not a robots file. Our
    ministers'-diaries reader was refused by the same wall. We neither passed it nor asked to (ruling 78
    closed the question).
  - The site's copyright page could not be read behind the wall; we rely on NZGOAL / CC BY as published
    elsewhere (to confirm).
  - `www.data.govt.nz` returns the same Incapsula page (identical bytes).
- **Ministers' diaries** (monthly release PDFs on `www.beehive.govt.nz/sites/default/files/`).
  - 119 of 2,560 releases reach us with a file name but no PDF address.
  - The MCP's download serves the release PDFs without the hash it captured them by
    (`captured_sha256` null), so we take none of them.
  - September and October 2026 are not held.
- **Courts corpus** (the MCP's own).
  - 107 files whose bytes differ from the sha256 their record promises. The site re-served a changed file and
    the record was not updated. We keep these as catch lines, not rows.
  - The record's `date` is the arrival day, not the judgment's. Since 3 November `doc_date` and `citation`
    arrive; we use them only where the document itself gives none.
  - Some justice.govt.nz tribunal PDFs arrive filed as `tribunals/unknown`.
  - On 4 November 716 records were re-filed under another court (`court_reclassified_at`). We record both.
  - What JDO, the finder and the ERA look like to a crawler: see Part 1. In short:
    - Open JSON listings and open PDFs, no challenge in about 6,500 requests.
    - Same-host trailing-slash redirects on JDO's two APIs.
    - The ERA form refuses a future `DateTo`.
    - The ERA states `Crawl-delay: 5`.
    - `forms.justice.govt.nz` resets connections and is held.
- **GETS (`www.gets.govt.nz`) and MBIE's award data.**
  - **GETS terms.** The terms (`GetsTermsAndConditions.htm`, last updated 7 March 2024; we store a copy by
    hash) say in clause 3.2(i)(e) that a user agrees not to "use any software or other method (whether
    automatic or manual), including any spider or robot, to monitor, copy, collect or index any data,
    Information or content found on GETS". Clause 1.1 deems use to be acceptance. Clause 4.6(ii) defines "you"
    as a registered person: whether a visitor who never registers is bound is a question for the lawyer. Until
    it is answered we read the bar as binding.
  - **What we asked of GETS.** One survey on 22 October: the home page, the terms page and the robots file
    (3 requests). Nothing since.
  - **GETS robots and content.**
    - robots.txt bars only SEMrush and states no crawl delay.
    - Tender documents need a supplier login (never used).
    - Each tender page names the buyer's contact person, with a phone and an email.
    - Clause 3.5(v) allows tender documents to be republished only if "non-commercial or … not to create a
      competing product", with the purchaser's contact details left out.
  - **MBIE's award CSVs** (`www.mbie.govt.nz/assets/Data-Files/NZGPP-GETS-Open-Data/`).
    - They answer HTTP 403 to the estate's User-Agent: on 21 October and again on 2 November.
    - The old estate's notes say the files answer a browser-like User-Agent and challenge a plain one. We do
      not change our User-Agent.
    - The data catalogue (`catalogue.data.govt.nz`) is open, states a 10 s crawl delay (honoured), and gives
      the licence as CC BY 3.0 NZ.
    - Arthur wrote to the ministry on 22 October. The award refresh waits on its answer (ruling 133).
  - **The MCP's GETS gaps** (5 November):
    - Awards for only 1,102 tenders (closing August to November 2026), none with its supplier or award date.
    - No future-opportunities or late lists.
    - No amounts and no documents.
    - None of the MCP's first 929 RFx ids is among our 29,874 award notices. The two sources join by buyer,
      reference and title, not by id.
- **A note on our gate log for MBIE hosts.** The log tags requests by parent domain. So
  `kete-lbp.mbie.govt.nz` (the building practitioners register: 13,347 requests, a different lane, copied
  under ruling 132) appears under the procurement position. It has nothing to do with GETS. That host answers
  404 for robots.txt.

# Notes on reading our records

- **Our fetch gate's log names a legal position by host, not by the job that made the request.** Where two
  positions name the same host (or the same parent domain), the request is logged under one of them. So every
  www.justice.govt.nz request (Judicial Decisions Online and the finder) is logged under the agency
  contract-disclosures position, kete-lbp.mbie.govt.nz (the building practitioners register) under the
  procurement position, and many councillor-interests requests under the local-election position. Per-lane
  counts in this note come from the lanes' own tables and the document store, not from the gate log.
- **Every hold and clearing is a line in the gate's refusals ledger, never edited.** On 5 November 2026 four hosts
  were held: forms.justice.govt.nz (since 4 November 00:24, resets on the Tenancy Tribunal's order PDFs since
  25 October), www.dunedin.govt.nz, www.gdc.govt.nz and www.kaipara.govt.nz (since 4 November 22:20, HTTP 403 on
  candidates' return PDFs; 403s seen from 23 October). Timaru (www.timaru.govt.nz) is held by the councillor
  interests lane itself after a 403 on 3 November, before the gate kept holds. api.business.govt.nz (a keyed
  API, staying with us) was held and cleared on 4 November.
- **We will match whatever you send to what we hold by sha256.** Where you re-fetch one of these sources from
  its start, the documents we already hold need not be sent again; their hashes can be listed for you.
