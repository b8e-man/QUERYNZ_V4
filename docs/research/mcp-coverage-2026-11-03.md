# The ingest MCP's coverage, and the questions for its provider (3 November 2026, ruling 138)

The "ingest MCP" is the server on Arthur's provider's box that the estate pulls documents from
(`support/mcpsource`, job `qv4-mcp-pull`). A "corpus" is one of its collections. This note measures
what each corpus holds against what its source publishes, names the gaps, and ends with the questions
for the provider. Arthur sends them himself.

How it was measured: the MCP's own `corpora` and `gaps` tools; pages of `records` without text (the
whole of `gets`, 929 records; three small samples of every other corpus); two `download` calls for
two GETS pages; and the estate's tables, read-only (`mcpsource.*`, the lanes' `pub.*` views, schema
`tenders`). No source website was fetched. A figure for "what the source publishes" that is not in
the repository or the MCP is marked **unknown** and becomes a question. Courts and diaries records
are referred to by number, never by name.

## The gaps, in order of value to the estate

1. **Courts back-catalogue and missing courts.** The High Court and Court of Appeal are held almost
   only for 2025 and 2026: the MCP's own `gaps` tool counts 31,554 High Court and 10,326 Court of
   Appeal judgments in its comparison index that the corpus lacks, and 5,029 District Court, 1,102
   Family Court and 779 Legal Complaints Review Officer decisions with none held. Several bodies are
   absent altogether (below). Courts documents name companies and people with their roles, which
   is what the links are built from.
2. **GETS is a first crawl, not yet a register.** One day's crawl (2 November): 398 open tenders,
   525 closed tenders from 29 July 2014 to 9 September 2015 (a backfill walking forward), and 6
   awarded. No tender documents, no amounts. It does not overlap our award files at all (below).
3. **Parliament's papers are metadata without the papers.** Bills, supplementary order papers,
   select committee reports and calls for submissions carry no text of the paper itself; select
   committee reports stop at exactly 1,000 (a cap, by its look); SOPs cover only the 54th
   Parliament; the submissions people and companies made are not held at all; 44,584 written
   questions point at an attachment the MCP does not serve.
4. **Original files not served.** Five corpora were captured from files (Hansard daily PDFs, diary
   PDFs, archived pages, sitemap pages, Beehive pages), but only `courts` and `gets` declare
   `has_files: true`. For the rest the estate holds the provider's extracted text, not the bytes.
5. **Hansard before 2003**, and 35 days held only as the draft (uncorrected) version.
6. **The corpus `date` means different things** (arrival day for courts and gets, last-modified for
   written questions, none for historical bills), so `corpora`'s date ranges mislead: written
   questions "start 2024-10-11" but hold every question from 2003.

## Inventory on 3 November 2026

| Corpus | Records | `corpora` dates | What the dates are | Estate holds | New in 24 h |
| --- | ---: | --- | --- | ---: | ---: |
| beehive | 66,578 | 1995-07-14 to 2026-11-02 | publication | 66,578 | 5 |
| parliament-wayback | 31,692 | 2006-09-02 to 2026-11-02 | archive stamp / capture | 31,530 | 1,205 |
| parliament-written-questions | 683,524 | 2024-10-11 to 2026-10-06 | API last-modified | 683,524 | 0 |
| parliament-bills | 92 | 2016-05-25 to 2026-09-23 | | 92 | 0 |
| parliament-diaries | 208,464 | 2017-10-01 to 2026-08-31 | meeting day | 208,464 | 0 |
| parliament-hansard-index | 596 | 2016-04-13 to 2026-11-02 | sitemap lastmod | 591 | 52 |
| parliament-hansard-debates | 1,862 | 2003-02-11 to 2026-09-23 | sitting day | 1,862 | 0 |
| parliament-bills-historical | 3,542 | none | | 3,542 | 0 |
| parliament-sops | 783 | 2023-12-13 to 2026-09-23 | publication | 783 | 0 |
| parliament-sc-reports | 1,000 | 2024-11-15 to 2026-09-25 | publication | 1,000 | 0 |
| parliament-sc-submissions | 1,335 | 2006-08-11 to 2026-09-24 | publication | 1,335 | 0 |
| courts | 15,143 | 2026-10-29 to 2026-11-02 | **arrival day** | 14,528 | 3,036 |
| gets | 929 | 2026-11-02 | **arrival day** | not yet pulled | 929 |

"Estate holds" is the pull's cursor (`mcpsource.cursors`); the gaps there are the next night's pull.
Nine of the thirteen corpora have had no arrival since 17 to 26 October.

## Per corpus

### beehive (government releases, speeches)

Held 1995 to 2026, 66,578 records: releases 54,498, speeches 9,510, pages 1,969, features 607.
Per year 1,000 to 3,400; 2019 to 2023 are lower (1,006 to 1,685) than 2006 to 2017. Against the old
estate's own Beehive copy the MCP lacks only 17 pages. What beehive.govt.nz publishes in total:
**unknown**. The change feed is busy: 109,340 versions landed for 66,578 records, so 42,762 were
re-served changed.

### parliament-written-questions

Every question from 2003 to 1 October 2026 (Parliaments 47 to 54). Each year's count equals its
highest question number except 2019 (27 numbers missing), 2020 (1) and 2026 (28). 683,517 of
683,524 have a reply. Gaps: questions before 2003 (**unknown** whether Parliament publishes them);
nothing released after 1 October 2026 (Parliament's dissolution before the 7 November election
may explain it: **unknown**); the 44,584 attachments the records name (`attachmentId`) are not
served. 1,365,944 versions landed for 683,524 records; a re-walk on 27 October found 17,619
questions re-rendered without their `updated_at` moving, which the change feed cannot show.

### parliament-bills and parliament-bills-historical

Together 3,634 records for 1,394 bill numbers across Parliaments 43 to 54 (about 1990 to 2026):
`parliament-bills` is the 92 bills now before the House (all 92 also in the historical corpus);
the historical corpus has 2,913 Government, 510 Member's, 66 Local and 53 Private bill records. So
"92 against hundreds" is answered: the two corpora cover hundreds per Parliament. The gap is the
bill itself: no record carries a bill's text or an attachment, and no publication date is set.
Bills before the 43rd Parliament: **unknown**.

### parliament-sops (supplementary order papers)

783 from 13 December 2023 (the 54th Parliament's start) to 23 September 2026. Earlier Parliaments'
SOPs are not held. Metadata only, no text of the amendment.

### parliament-sc-reports (select committee reports)

Exactly 1,000, from 15 November 2024 to 25 September 2026. The round number and the late start
look like a page or query cap: everything before November 2024 is missing. Metadata only.

### parliament-sc-submissions

1,335 calls for submissions, 2006 to 2026. These are the committees' invitations, not the
submissions. The submissions (a document per person, company or body, with who made it) are not
held, nor the committees' evidence and advice papers.

### parliament-hansard-debates and parliament-hansard-index

1,862 daily PDFs, 11 February 2003 to 23 September 2026, 55 to 95 days a year; no year looks thin,
and every day the old estate held (2024-11-20 to 2026-09-23) is present. The PDF is the whole day's
transcript, so the transcripts are there as text. What is missing:

- Hansard before 2003 (Parliament's debates go back to 1854; what it publishes online: **unknown**);
- the corrected version of 35 days from 28 April 2026 held only as the draft;
- the per-speech HTML (each speech with Parliament's member id), which the old estate had for 137
  days and the estate now rebuilds by splitting the PDF;
- the PDF bytes themselves: the corpus declares no files, so the estate holds the provider's
  `pdftotext -layout` text;
- sittings after 23 September 2026, if any (**unknown**).

The index corpus is 596 parliament.nz sitemap pages (order papers, committee pages, rules); by its
own label, not transcripts.

### parliament-diaries (ministers' diaries)

208,464 meetings, October 2017 to August 2026, every month present, about 1,300 to 3,100 a month (fewer in January and around elections).
August 2026 has 587 (release lag). 2,560 releases; 119 have no PDF address in the records. Gaps: the
release PDFs are not served (only the provider's rows); which ministers and which months Beehive
published that are not held: **unknown** (a list of releases would answer it). 231,131 versions
landed for 208,464 records.

### parliament-wayback (archived parliament.nz pages)

31,692 pages from the Internet Archive. Their archive dates cluster 2008 to 2016 (8,549 in 2016,
then 57 to 409 a year to 2024, 3 in 2025). Biggest paths: debates (about 7,100), legislation (about
5,400), business (about 3,450), select committees (about 4,960). 10 archived copies are
parliament.nz's own refusal page and are set aside (hard limit 6). The corpus grew 1,205 in 24 hours
(archived oral-question lists of 2018 and 2019 among them), and 19 records are of a new kind
(`kind: doc`: current parliament.nz addresses, dated 23 October to 2 November, no snapshot address,
no text). What the provider is adding there: **unknown**.

### courts

15,143 records (case pages, judgment PDFs, media releases, transcripts, submissions), nearly all
since 29 October. The `date` field is the arrival day, not the judgment's.

What the estate holds, by citation series (`pub.court_documents`, 14,528 records):

| Series | Documents | Years | MCP `gaps`: comparison index | lacking |
| --- | ---: | --- | ---: | ---: |
| Supreme Court (NZSC) | 3,940 | 2005 to 2026 | 2,366 | 603, all checked absent from the official site |
| High Court (NZHC) | 2,704 | 2013 to 2026; 2,535 of them 2025 to 2026 | 31,982 | 31,554 |
| Court of Appeal (NZCA) | 851 | 2007 to 2026; 370 of them 2025 to 2026 | 10,609 | 10,326 |
| Real Estate Agents Disciplinary Tribunal | 793 | 2013 to 2026 | 429 | 62 |
| Human Rights Review Tribunal | 701 | 2012 to 2026 | 533 | 312 |
| Employment Relations Authority | 566 | 2019 to 2026 | none | |
| Employment Court | 484 | 2010 to 2026 | 2,077 | 708 |
| District Court | 321 | 2020, 2025 to 2026 | 5,029 | 5,029 |
| Environment Court | 231 | 2018 to 2026 | 1,070 | 817 |
| Family Court | 75 | 2025 to 2026 | 1,102 | 1,102 |
| Lawyers and Conveyancers Disciplinary Tribunal | 47 | 2022 to 2026 | 317 | 210 |
| Legal Complaints Review Officer | 44 | 2024 to 2026 | 779 | 779 |
| Youth Court | 2 | 2025 to 2026 | 177 | 177 |
| Disputes Tribunal | 2 | 2024 | 75 | 75 |
| Coroners | 2 by citation; 167 PDFs from coronerscourt.govt.nz | 2013 to 2026 | 578 | 578 |

Also held: the Health Practitioners Disciplinary Tribunal (790 pages and PDFs from hpdt.org.nz),
ACC appeals (30), Social Security Appeal Authority (13), Land Valuation Tribunal (64), Immigration
Advisers Complaints and Disciplinary Tribunal (85), and handfuls of others. The `gaps` tool counts
its "lacking" against its comparison index (NZLII case numbers via the Internet Archive), so these
are measurements with that index's own holes; the High Court figure is from the tool's last index,
older than the newest arrivals.

No document carries a citation from the Tenancy Tribunal, the Immigration and Protection Tribunal,
the Waitangi Tribunal, the Māori Land Court or Māori Appellate Court, the Court Martial, the Motor
Vehicles Disputes Tribunal, the Teachers Disciplinary Tribunal or the liquor licensing authority.
Some justice.govt.nz tribunal PDFs arrive filed as `tribunals/unknown`, so a few of these may be
present unclassified. Case pages (2,695) are almost all the Supreme Court's.

The pull's catch log: 107 courts files whose bytes differ from the hash the record promises (the
provider re-fetched a file without updating its record); 607 files were duplicates already held.

### gets (Government Electronic Tenders Service)

929 records, all fetched 2 November 2026 between 18:29 and 21:17 UTC, all `kind: tender_notice`,
each a GETS detail page (`ExternalTenderDetails.htm?id=…`, 27 to 42 KB of HTML).

| | MCP `gets` | Our tenders lane (`registers/tenders`) |
| --- | --- | --- |
| Source | GETS public web pages, crawled by the provider | MBIE's open-data CSVs of award notices, copied 14 August 2026 |
| Notice types | Tender notices: RFT 302, RFP 298, ROI 182, NOI 67, RFI 42, RFQ 23, other 13; one Award Notice (AN), one Future Procurement Opportunity (FPO) | Awards only: RFP 13,239, RFT 12,286, RFQ 3,521, Award Notice 828 |
| Lists walked | open 398, closed 525, awarded 6; not the future-opportunities or late lists | every award notice |
| History | closed tenders closing 29 Jul 2014 to 9 Sep 2015 so far; open ones closing to 2029 | closing 29 Apr 2013 to 6 Dec 2026, awards Jul 2014 to Dec 2026 |
| Buyers | 157 | 308 |
| Fields in the record | RFx id, title, tender type, buyer, reference (691 of 929), close date as text | RFx id, agency, department, type, competition type, coverage, prequalification, title, reference, opened, closed, awarded, award type, amount (4,613 of 29,874), regions, categories, suppliers |
| Fields only in the page | open date, coverage, categories, regions, exemption reason, prequalification, overview text; on an award page, the supplier and its business address and the award date; the buyer's contact person, email and phone (never read) | |
| Amounts | none on the two pages read | where the agency gave one |
| Attachments | none: tender documents need a supplier login | none |
| Refresh | one crawl so far; cadence **unknown** | quarterly; MBIE's host answers 403 since 21 October |

**Overlap: none.** Not one of the 929 RFx ids is in our 29,874 award notices; 31 share a reference
number and 14 a title, and those are generic. An award is often its own notice with its own id, so
the two join by buyer, reference and title, not by id. The MCP corpus is therefore new information
(the tender as advertised), and its awarded list could carry the awards our own refresh cannot reach
while MBIE's host refuses us.

The estate's own position on the GETS listing (`docs/legal/positions/government-electronic-tenders-listing.md`)
records that GETS's terms (clause 3.2(i)(e)) bar "any spider or robot", which is why the estate never
crawled it. The provider's basis for crawling it is the first GETS question below.

## Questions for the provider

40 questions: 8 general, then by corpus.

### General

1. For each corpus, how is it acquired: a crawl of the site, the site's own API, a bulk download, or
   an archive (the Internet Archive or another)?
2. What is each corpus's refresh cadence, and is it still running? Nine corpora have had no
   arrival since 17 to 26 October.
3. What backfill is planned, per corpus, and to what start date?
4. How do you handle a block, a CAPTCHA or other challenge, or a login page? Do you ever pass one,
   or is a challenged read logged as a failure? Which hosts have refused you?
5. Do you keep the original bytes and the HTTP response headers of everything you fetch? Can
   `download` serve them for the corpora that declare `has_files: false` (Hansard PDFs, diary
   PDFs, archived pages, sitemap pages, Beehive pages)?
6. What does `date` mean in each corpus? For courts and gets it is the arrival day; could each
   record carry the document's own date (judgment, publication, close) as a separate field?
7. The change feed (`changes`): does every change to a record move its `updated_at`? On 27
   October 17,619 written questions came back with new text and an unmoved `updated_at`. When a
   record is removed, does the feed say so, and why do records sometimes come back at a lower
   position after a removal?
8. When you re-fetch a file and its bytes change, will the record's `sha256` be updated, or a new
   record made? 107 courts files today differ from the hash their record promises.

### Courts

9. Which sources does the courts crawl walk (Judicial Decisions Online, courtsofnz.govt.nz,
   justice.govt.nz tribunal pages, each tribunal's own site), and from what start date for each?
10. Is a High Court and Court of Appeal back-catalogue planned? Your `gaps` tool counts 31,554 and
    10,326 missing; how many of those are on the official sites at all?
11. Can you add the District Court (5,029 missing), Family Court (1,102), Youth Court (177),
    Legal Complaints Review Officer (779), Coroners (578) and Disputes Tribunal (75)?
12. Can you add bodies not held at all: the Tenancy Tribunal, the Immigration and Protection
    Tribunal, the Waitangi Tribunal, the Māori Land Court and Māori Appellate Court, the Court
    Martial, the Motor Vehicles Disputes Tribunal, the Teachers Disciplinary Tribunal and the
    liquor licensing authority?
13. Some tribunal PDFs arrive as `tribunals/unknown`; can each record carry its court or tribunal?
14. How do you handle suppression: do you remove or mark a record when a court later suppresses
    or takes down a judgment, and does the change feed carry it?

### GETS

15. On what terms do you read GETS? Its terms (clause 3.2(i)(e), version of 7 March 2024) bar
    "any spider or robot"; do you have MBIE's permission, an account, or another basis?
16. Which lists do you walk (current, closed, awarded/completed, late, future opportunities), and
    how far back does each go on GETS?
17. Is the closed-tender backfill (now at September 2015) going forward to today, and how many
    closed and completed tenders does GETS list in all?
18. Will you crawl the awarded/completed list in full? It is the one way to see current awards
    (supplier and award date) while MBIE's open-data host refuses us.
19. Can the record carry the page's own fields: open date, coverage, categories, regions,
    exemption reason, and on an award the supplier and award date?
20. Do you re-fetch a tender when it changes (notices, extensions, cancellation, award)? How often?
21. Do you hold any tender documents or attachments? (We expect none, as they need a login.)
22. Do you hold MBIE's open-data award CSVs, or can you read them? Our reads get HTTP 403.

### Parliament: bills, SOPs, select committee reports and submissions

23. Can you capture the bill texts (each version as introduced, reported and passed), and the
    text of each SOP and select committee report, as files?
24. Select committee reports stop at exactly 1,000 from 15 November 2024: is that a cap? Can you
    take every report back to the start of the API's history?
25. Can you take SOPs before the 54th Parliament?
26. Can you capture the submissions themselves (each submitter's document), and the committees'
    evidence and advice papers?
27. Bills before the 43rd Parliament: does the API hold them?

### Parliament: written questions

28. Can `download` serve the 44,584 attachments the questions name?
29. Does the API hold questions before 2003?
30. 56 question numbers are missing (27 in 2019, 1 in 2020, 28 in 2026): withdrawn, or not
    captured?

### Hansard

31. Can you add Hansard before 2003, and from what source?
32. 35 days from 28 April 2026 are held only as the draft; will the corrected version replace or
    join them?
33. Can you add the per-speech HTML transcript (with Parliament's member ids), beside the PDF?
34. Were there sittings after 23 September 2026?

### Ministers' diaries

35. How are the diaries acquired (Beehive's PDFs read by you?) and can `download` serve each PDF?
36. Can you give a list of every diary release Beehive has published, so we can see which
    ministers and months are missing? 119 releases have no PDF address in the records.
37. What is the release lag, and when will September and October 2026 arrive?

### Beehive

38. How many items does beehive.govt.nz publish in all, and is everything since 1995 taken?

### Wayback and the sitemap pages

39. What are the new `kind: doc` records in `parliament-wayback` (no snapshot address, no text),
    and what are the 1,205 records of the last 24 hours? Archive dates thin out after 2016; is a later backfill planned?
40. What decides which parliament.nz sitemap pages enter `parliament-hansard-index`?
