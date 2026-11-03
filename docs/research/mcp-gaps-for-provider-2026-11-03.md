# What the ingest MCP is missing: an outline for the provider (3 November 2026)

Measured on 3 November 2026 against the MCP's own `corpora` and `gaps` tools, samples of `records`, and our copy of
every corpus. Each item says what is missing and what we are asking for. The numbers are from your `gaps` tool
where it has one; elsewhere they are ours. Courts come first: they matter most to us.

## 1. Courts (`courts`, 15,143 records)

Almost everything arrived after 29 October, and for the High Court and the Court of Appeal it is nearly all from
2025 and 2026.

**Missing, by court (your `gaps` tool's comparison index, lacking / indexed):**

| Court or tribunal | Missing | Indexed | Held now |
| --- | ---: | ---: | --- |
| High Court (NZHC) | 31,554 | 31,982 | 2,704, mostly 2025 to 2026 |
| Court of Appeal (NZCA) | 10,326 | 10,609 | 851, mostly 2025 to 2026 |
| District Court (NZDC) | 5,029 | 5,029 | 321, from 2020 and 2025 to 2026 |
| Family Court | 1,102 | 1,102 | 75 |
| Environment Court | 817 | 1,070 | 231 |
| Legal Complaints Review Officer | 779 | 779 | 44 |
| Employment Court | 708 | 2,077 | 484 |
| Supreme Court (NZSC) | 603 | 2,366 | 3,940; the 603 are not on the official site either |
| Coroners | 578 | 578 | 167 PDFs from coronerscourt.govt.nz |
| Human Rights Review Tribunal | 312 | 533 | 701 |
| Lawyers and Conveyancers Disciplinary Tribunal | 210 | 317 | 47 |
| Youth Court | 177 | 177 | 2 |
| Disputes Tribunal | 75 | 75 | 2 |
| Real Estate Agents Disciplinary Tribunal | 62 | 429 | 793 |

**Not held at all:**
- Tenancy Tribunal;
- Immigration and Protection Tribunal;
- Waitangi Tribunal reports;
- Māori Land Court and Māori Appellate Court;
- Court Martial;
- Motor Vehicles Disputes Tribunal;
- Teachers Disciplinary Tribunal;
- Alcohol Regulatory and Licensing Authority.

**Other faults:**
- **Date.** The record's `date` is the day the record arrived. We need the judgment's own date as a field.
- **Unknown tribunal.** Some tribunal PDFs arrive filed as `tribunals/unknown`. We need each record to carry its
  court or tribunal.
- **Hashes.** 107 files no longer match the sha256 their record gives. The file was fetched again but its record
  was not updated.
- **Suppression.** We need to know how a judgment that is later suppressed or taken down is marked, and whether the
  change feed carries it.

**What we ask:** the High Court and Court of Appeal back catalogue as far back as the courts publish it; the
District, Family, Youth and Coroners courts; every body in the "not held" list; and the four faults fixed. From
today we also fetch the missing decisions ourselves from the courts' own sites. Anything you add, we match to ours
by sha256, so nothing is held twice.

## 2. GETS (`gets`, 929 records)

The corpus so far is a single day's crawl, 2 November.

| Held | Records | Missing |
| --- | ---: | --- |
| Open tenders | 398 | |
| Closed tenders | 525 | Only those closing 29 July 2014 to 9 September 2015; the rest of the closed list |
| Awarded | 6 | The rest of the awarded list |
| Future opportunities | 0 | The whole list |
| Late tenders | 0 | The whole list |

Each record carries only the RFx id, title, type, buyer, reference and close date. These fields are on the page but
not in the record: open date, coverage, categories, regions, exemption reason, prequalification, the overview,
and, on an award, the supplier and the award date. There are no amounts and no tender documents.

**What we ask:** every list in full and kept current, including the whole awarded list; the page's own fields in
the record; re-fetching a tender when it changes; and your basis for reading GETS, whose terms (clause 3.2(i)(e))
bar "any spider or robot".

## 3. Parliament

| Corpus | What is missing |
| --- | --- |
| Bills (`parliament-bills`, `parliament-bills-historical`) | Every bill's text, at each version (introduced, reported, passed); a publication date; bills before the 43rd Parliament |
| Supplementary order papers (`parliament-sops`) | The text of each SOP; every SOP before the 54th Parliament |
| Select committee reports (`parliament-sc-reports`) | Everything before 15 November 2024 (exactly 1,000 held, which looks like a cap); the text of each report |
| Submissions (`parliament-sc-submissions`) | The submissions themselves, each submitter's document with who made it; the committees' evidence and advice papers. Only the 1,335 calls for submissions are held |
| Written questions (`parliament-written-questions`) | The 44,584 attachments the questions name; 56 question numbers (27 in 2019, 1 in 2020, 28 in 2026); anything before 2003; anything after 1 October 2026. Also, 17,619 questions changed text on 27 October without their `updated_at` moving |
| Hansard (`parliament-hansard-debates`) | Everything before 11 February 2003; the corrected version of 35 days from 28 April 2026, held only as drafts; the per-speech HTML with Parliament's member ids; the PDF files themselves; any sitting after 23 September 2026 |
| Ministers' diaries (`parliament-diaries`) | The release PDFs; a list of every release Beehive published, to show which ministers and months are missing; 119 releases with no PDF address; September and October 2026 |
| Wayback (`parliament-wayback`) | Archive dates thin out after 2016; what the new `kind: doc` records are (no snapshot, no text) |

## 4. Every corpus

- **Original files.** Five corpora are captured from files, but `download` serves the bytes only for `courts` and
  `gets`: Hansard PDFs, diary PDFs, archived pages, sitemap pages and Beehive pages. We ask for the original bytes
  and response headers for all of them.
- **Dates.** `date` means something different in each corpus (arrival day, last modified, publication, or nothing),
  so the date ranges `corpora` shows mislead. We ask that each record carry the document's own date.
- **Refresh.** Nine corpora have had nothing new since 17 to 26 October. We ask for each corpus's refresh cadence,
  and whether it is still running.
- **Method.** For each corpus, we ask how it is acquired (crawl, the site's API, a bulk download, or an archive),
  and what happens at a block, a CAPTCHA or a login. We do not take content obtained by getting past one.
- **Change feed.** We ask whether every change to a record moves its `updated_at`, and whether a removal is shown.

## 5. The questions

Forty questions: eight general, then by corpus.

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
