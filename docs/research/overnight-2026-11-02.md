# Overnight 1 to 2 November 2026: company history, the templates, the held lanes

Arthur's six approvals, 1 November about 21:25: commit and release after each verified step; rebuildable tables and views;
a sample of the business-number interface and a polite capture; what the templates' checks conclude; node2's memory;
findings to the inbox and this report. Off: the old estate, the public site, the frozen donations feed, credentials, the
readers' settings, deleting anything that cannot be regenerated.

## 1. The change history held since 16 August: nothing new in it

The old companies database's history tables (`nzbn_canonical`, read only) are the July file's rows, written aside when
the August file replaced them: `director_role_history` 1,194,878 rows, one per role, recorded 14 July to 16 August,
9,071 with an end date, the same 9,071 the current rows carry. The companies lane already holds both files, each row
windowed by the files that list it. The sixteen small `bulk.*` history tables (trading names 2,678, industry 4,467,
addresses about 30,000) are left; nothing reads them.

## 2. Past roles come from the business-number interface: the backfill

The five proof answers of 21 October list ended directorships with the register's own dates, back to 2007 (one company:
four directors, three ended 2017 to 2022). The monthly files drop every role of a removed company: 1,052,208 removed
companies hold no director at all.

`qv4-companies-history` (ad7febe), nightly from 22:05 NZDT: the entity detail of each wanted entity in rank order, one
call at least 5 s apart (the gate's floor for the host), off-peak 22:00 to 01:00, at most 2,000 calls a day, each answer
landed by hash and read into `companies.lookup_roles` with its start and end dates. Its own limit and its own line in
the lane's check; the monitor's 300 a day counts the monitor's calls only. Stops at a failed read (hard limit 6).

| Tier | Wanted | Entities |
| --- | --- | --- |
| 1 | Removed companies the Gazette names in a liquidation notice, newest removal first | 52,615 |
| 2 | Other companies removed since 2019, newest first | 290,450 |
| 3 | Registered companies, for their earlier directors | 759,464 |

At 2,000 a night tier 1 takes about 26 nights; tier 2 about 145 more. A wider window or a shorter floor is Arthur's.

## 3. The credit template reads status and name changes (STATES on)

3720b62. `pub.company_states` (5,629 earlier states) was already in the report's catalogue; the credit template now
reads it. A status a later file turned to liquidation, receivership, administration or removal is red in
status-name-changes and recent-adverse-change and listed in monthly-changes; a name change is amber; the change checks
clear where no later file changed anything. Verified on the real rows: a company Registered in July and In Liquidation
in August renders red. The report server was restarted on the release.

## 4. WorkSafe, the Commerce Commission and the FMA are read by the templates

82c4418. The catalogue knows the six views of the three lanes (actions or cases, and their parties, each party dated by
its listing); the three leave the not-held list. Legal, banking and recruitment: `comcom-coverage` fires amber on a
listing naming the subject or a namesake, and clears on none, as the regulators list them today. Insurance:
`safety-record` fires red on a WorkSafe listing and stays blocked on none, because Fire and Emergency's notices are not
held; `regulator-actions` fires or clears. Healthcare shows the three in a regulators section. A name the regulator
withheld (24 WorkSafe, 80 Commission, 3 FMA) is never shown or counted.

Verified on the real rows: Pacific Edge Limited's FMA warning renders in insurance and legal as near. A party row
carries a company number 3 times in 3,258, so every match is by name and near; a confirmed listing needs a link rule,
which is Arthur's.

The history backfill began at 22:05:08: 23 answers by 22:07, every one 200, about 5.6 s apart.

## 5. The Building Practitioners Board's decisions; namesakes in the regulators' listings

29a5a70. `pub.building_practitioner_decisions` (264 decisions, November 2023 to September 2026, the Board's three-year
window) is read by construction and property. `building-practitioners` fires on an upheld decision against a confirmed
person (amber in construction, info in property), fires info on a namesake's, and stays blocked on none: the licence
register itself (`pub.building_practitioners`) is held empty until Arthur's decision, so whether a person holds a licence
is never cleared.

A fault in section 4, mended here: a person start found no regulator listing, because nothing looked a person's name up
in a view no link reaches. The walk's name join now reads the Board's decisions and the three regulators' parties, near
by name; and the new sections had `own = false`, which dropped every row reached through the subject. Verified on the
real rows: a current director who shares an upheld decision's name renders the decision near and the flag info.

## 6. A timeout stopped the backfill; mended and restarted

At 22:32 one call to the business-number host timed out, and the run crashed with a traceback after 273 answers. The
history run and the monitor's run share one fetch, so a call that gets no answer now records a failed read (status 0)
and stops the run cleanly, as a block does (39848ea, with a test that raises a timeout). The job was queued again at
22:39 and runs to 01:00 or the day's 2,000.

## 7. Limited partnerships: the general partners are read

ddb4d83. 4,114 partnerships and 4,468 general-partner rows (4,304 bodies, 164 people; limited partners are not public).
The walk joins a company to its partnership row by business number, and the partnership to its general partners.
`officers-of-record` in legal, banking, agriculture, construction and ownership lists the general partners: clear when
one is current, amber when none is, blocked when the walk reached none. Insurance's `officer-churn` stays blocked for a
partnership: few start dates are stated. Verified on the real rows: a farming partnership's count of current general
partners is the register's.

Sanctions stay not held: `pub.sanctions_listings` is published empty, and reading it would print blanks that look
like a clear. Not yet: ownership's chain still names a holder that is a partnership as filed, and does not follow its
partners. A company that is a general partner lists its partnerships since c2 (see section 10).

## 8. The Overseas Investment Office's decision summaries in property

bd3d5e8. 1,295 decision summaries and 2,911 parties (applicants, vendors, consent holders). `overseas-investment` fires
info on a party naming the subject or a namesake, and clears on none, as the Office lists its summaries, not every
application. A name the Office withheld is never shown. Verified on the real rows: a company the Office names as a
vendor in a 2017 sensitive-land decision renders it near and the flag info.

Every held lane the templates did not read is now read, apart from sanctions (published empty) and the licence
register of building practitioners (held empty until Arthur's decision).

## 9. Past roles from the business-number register in the report

49a203b, 6086cfc. `pub.company_lookup_roles` is a company's people in the report: its roles as the business-number
register states them, with the register's own start and end dates, confirmed by the company. A role the monthly file
already holds (`held_key`) is listed once, from the file. A person's name finds a register role no file held, near.
Ten templates list them beside the directors; `officers-of-record` in five counts them. Verified on the real rows: a
removed company the files hold no director for lists four directors, two ended 14 November 2016.

`HISTORY` stays off in every template, so no check clears on past roles: 525 of 1.1 million wanted companies are
answered. Arthur's question, not done: should a namesake's past role at a failed company count in the firing checks
(earlier failure, serial pattern, phoenix), near and amber, the way current roles already do?

## 10. A company that is a general partner lists its partnerships

The walk joins a company to the partner rows that carry its business number, each titled by its own partnership; a
partnership's own `officers-of-record` counts only the partners reached through its row. Verified on the real rows: a
fund's general-partner company lists its two partnerships, confirmed.

## 11. Two real-data tests red, not the night's

`products/board` outside check (pub.name_sightings published, no board entry) and `products/scan`'s procurement
read-back (five pinned donor-director pairs no longer joined by a link): both red at 8c7db4e too. A note is in the
inbox (`cards/2026-11-01-two-real-tests-red-on-live-data.md`). `products/scan/tests/test_real.py` needs the integrator
mark to run and was not run.

## 12. A partnership up the ownership chain lists its general partners

The chain reads a partnership's current general partners above it, as it reads a company's current directors, and
`partnership-holders` in ownership finds a partnership by name or by the register's entity type, once. Verified on the
real rows: a company held by a partnership lists the partnership's general partner.

Arthur's question: the chain joins a holder to a company by exact name. 1,397 holder rows match a partnership's name
case-folded; only 290 match exactly, so 1,107 are "not followed; no company of this name". A case fold would follow
them all (still near); it changes how every holder is joined, so it is his. Ruled 2 November: ignore case; done.

## 13. The night's backfill ended at a second timeout

At 00:18 a call timed out again; the mended run recorded it as a failed read and stopped cleanly after 1,019 calls
(1,018 answered). The night's total: 1,292 calls, all but the two timeouts answered. Not restarted: two timeouts in two
hours reads as a strained host, and politeness comes first. The next run is 22:05 tonight, from where it stopped.

## 14. Arthur's rulings of 2 November, done

Case ignored when a holder of record is joined to its company by name (8b51850). Option (b): a namesake's past role
at a failed company is an amber warning in eight failure checks across seven templates; a repeat check needs two
failed companies; never red; listed in a past-roles section. Verified on the real rows.
Correction to 0164ed4's message: on the real director (one failed company under the name) legal's repeat-insolvency
stays blocked, as a repeat needs two; property's earlier-failure fires amber. The message's legal example predates the
two-company rule.

## 15. Courts into the report (2 November, daytime)

Arthur: "keep building out the missing use case parts". The courts corpus held (4,975 judgments, 13,801 heading
parties, 45,098 people the text reader found) was published and linked but no template read it. Now the catalogue
carries the three views, every template and the shape have a courts section, and court-judgments in six templates
reads them: confirmed party amber; an officer's case or a namesake's info; judges, counsel, witnesses, withheld and
suppressed names never count; none is blocked, as the corpus is partial. The not-held key `courts` is now
`court_coverage`, the judgments the corpus does not carry. Five mutants of the check, each caught (dfc55d3).
Transient: two ownership real tests hit the 30 s statement timeout on an indexed pub.names lookup once; passed on rerun.

## 16. Government contract awards into the report

GETS award notices (29,874 notices, 31,264 supplier rows, 2014 on) were published and linked (16,470 supplier rows
confirmed to a company) but not read. Now in the catalogue; construction and the shape list them; construction's new
public-contracts check is info only: a track record, never a finding (b730a6d). Not-held `tenders` is now
`tender_coverage`, the contracts with no GETS notice.

Fault seen, not mine: each `qv4-names-*` job holds pub.names for about a minute (06:50:15–06:51:23 today). Every
report's first query waits on it and fails at the 30 s statement timeout; the real-data tests that ran then went red,
and green on rerun. A live report opened in that minute fails the same way.

## 17. Tribunal checks read the courts corpus

Four checks called held decisions not held. Now: employment-determinations (construction) and tribunals (insurance)
read the ERA and the Employment Court; disciplinary-findings (legal) the Lawyers and Conveyancers Disciplinary
Tribunal and the Legal Complaints Review Officer; real-estate-authority (property) the Real Estate Agents Disciplinary
Tribunal. Confirmed party: the check's severity; near: info; none: blocked (4507eca). Property's abstains on real rows:
no company or director is linked to a real-estate tribunal party yet.

## 18. Mortgagee possessions in four more templates

Legal, credit, insurance and construction blocked mortgagee-possession on "the catalogue does not know the view";
it has known it since property read it. Now each reads pub.gazette_possessions: the entity as mortgagor red (credit)
or amber; as lender, or near, info; from a company none is clear, from a person blocked (6885054). Still stale:
insurance's status-history says the same of pub.company_states, which credit reads; next.

## 19. Insurance status-history

Reads pub.company_states: an earlier insolvent or removed state amber, another change info, none blocked (the files
held begin July 2026) (88ebbb7). Real row: a company In Liquidation in the July file and Registered in August, amber.

## 20. Past holdings

pub.company_lookup_holdings in the catalogue and the walk, listed beside the past roles in every template that has
them; current holdings left to the monthly file (aaab674). No check reads them yet: whether a namesake's past holding in
a failed company counts like a past role (option b) is Arthur's to say.

## 21. Arthur's ruling: past holdings, amber on a namesake

A namesake's past holding at a failed company now counts as a past role does (option b): amber, never red, a repeat
needing two companies (44e1653). Found while verifying: the register writes a person holder surname first, so the name
join could never meet a director; it now turns the name, never a body's.

## 22. Name orders: one reading, not a turn per view

Arthur asked whether surname-first names were a known problem. They are solved: keys.names reads every order and
the links and the board use it. The report's own name joins did not; 44e1653's per-view turn was a local copy. Now
both joins read by keys.names and the turn is gone; the board declares the holdings FAMILY_GIVEN (84ba2f1).
Board real check red, not from this: pub.name_sightings (carded 1 November) and 7 Hansard people rows whose name
carries a residence word.

## 23. The board's two reds, closed

pub.name_sightings is on the board (register `links`, keyed by document, lane and offset). The six Hansard
"residence" rows were bill and Act titles the reader filed among the people; the check now reads a law's title as no
person's name (617036e). The board's outside check is green. The 1 November card's first item is done; its second
(the scan's procurement read-back) stands.

## 24. The day of 2 November: registers brought current, and step 8

- Past roles (744298d): the backfill at the approval's one request a second, a second window 06:00 to 07:00, 15,000 a day,
  a call with no answer skipped; about 14,000 a night against 2,000 (52,615 liquidated companies in about four nights).
- The October 2026 companies package (d706458, 2c4443d, published 82bb7f2): cut 30 September; 1,930,745 entities,
  1,206,299 directors, 17,715 state changes since August; 26,791 directors and 42,200 holdings gone between the files;
  pub.company_insolvencies 109,586 appointments; pub.retirement_villages 514. The outside check leaves overseas companies
  out from the 30 September quarter (the Office's count does; Arthur: "alright do it"): 752,307 against 752,292.
- The Gazette (f9300ae, 6446f16, published 58e545e): gazette.govt.nz challenges, so notices after the 20 October export come
  from DigitalNZ (Arthur: "na digitalnz is fine"), nightly; 300 notices 16 to 30 October; the bankruptcy lists ended in
  December 2018 (the readers miss nothing); the office families read: appointments 3,156 to 9,591 and
  pub.gazette_board_interventions 1,345.
- The Real Estate Authority (75c55ad, 95ec600): 3,062 decisions, 1,571 parties, 7 suppressed naming no one.
- The councils' registers (fa8e930, queued row 1159): the PDFs read by the text reader; a sample of 685 rows across eleven
  councils against 56 at one; the full read about 474 pieces.
- The templates (2cc05c9, 366e097): a company start reads what the walk followed through each officer in eight templates;
  grants, society states, councillors' interests and the REA read.
- A red of the morning (84ba2f1) closed: products import only support/, so the report's name reading is its own copy held
  equal to keys/ (3be7171). Three jobs had taken priority 124 and the scheduler kept its last good catalogue from 10:46 to
  11:16 (2fef5d0).
- Two samples printed one address-like detail into an agent's session (a councillor's property row, a JP's road); neither
  was repeated or committed; the published rows pass the lanes' address checks.
- Step 8 planned (ec4f17f, docs/plan/step-8.md) and its parts 8.1 to 8.6 running in parallel; 8.7 (council minutes) in flight.

## 25. Step 8's merges, afternoon of 2 November

- 8.1 (ca8c000): the ten templates read pub.company_insolvencies on the company and on each director's other companies
  (a solvent winding-up listed, never a failure), the retirement villages (healthcare: one operator, 38 villages), the
  Gazette's appointments by name (legal, recruitment), and the beside step answers in legal and banking.
- 8.2 (4fe1536, docs/research/links-2026-11-02.md): link rules 1a to 2b measured; Arthur's to rule.
- 8.3 (007df21): registers/linz; 54,735 place names published and on the board; titles (2.46 M) and owners (5.75 M) pull
  from 22:30 (qv4-linz-capture).
- 8.4 (484f2d7, 68216b5): the Insolvency Register lane built on fakes, nightly at 21:00 once Arthur places its key file;
  a whole first copy about three weeks at one call per 5 s. The PPSR needs an account and a fee per search: carded.
- 8.5 (879a828, 0f0db3a): the scans re-run after the links and companies loads (the 11 stale scans cleared, qv4-scan-rerun
  row 1163). Two lobbying scans: meetings to GETS suppliers, 26,958 lines (run 570, 0 problems). Their first runs were
  red for applying hard limit 15: the outside check counted the address flags filtered to false as address reads; it no
  longer does, and a flag filtered to true or carried as a column is still refused (test, two mutants caught). The
  donors scan then hit the 10-minute statement limit: its named cursor planned for the first tenth of the rows and took a
  fast-start plan; the reader now plans for the whole result (2eb3804), 45 lines in 18 s (run 577). products.scan check:
  0 problems over 13 scans.
- 8.6 (e641666, 453ff4c): the search-only rule live with its test; batch 1 9,031 of 10,000 landed in staging. Arthur
  (2 November): "use the 4tb HDD": the text goes as compressed files on /mnt/hdd2 with the catalogue only in the
  database (option 1); built (2af5315, merged 5b61ce7). The 1-million sample (every 90th row, 1840 to 2001, 188 papers):
  956,344 landed, 1,046 disk bytes and 255 catalogue bytes an item; 4.4% have no text, so about 86.7 M land: 91 GB of
  files on /mnt/hdd2 and 22 GB of catalogue. Keyword index sized on the sample: tantivy 92 GB, 0.03 to 4 ms warm;
  SQLite FTS5 153 GB, 2 to 105 ms; equal hit counts. Arthur: "for papers past use tantivity and go". The load now
  streams, committing every 1 M rows with a resumable checkpoint (43d30c5; peak 0.95 GB, about 7.5 h for the dump, then
  the tantivy index 1.7 to 3.5 h, about 95 GB). qv4-papers-past-ingest queued as row 1169, into staging; published after
  the outside check on the whole.
- 8.7 council minutes (b304e41, 80cf246, merged 8454484): two profiles (the standard template, 175 documents, read by
  rules; other text layouts, 403, by the text reader); public-excluded sections and the public forum cut before any
  reader. qv4-council-minutes-read queued as row 1170 (745 pieces, about 1.75 h).
- The model server stalled at 15:48 in a driver wait (11 requests held, readers timing out at 900 s); restarted 16:21,
  answering again.

## 26. Evening of 2 November: Arthur's answers, and the gaps

- Rulings 132 to 135 (03592ab): the building practitioners register and the sanctions lists copied; HDC and OpenLaw
  stay carded; GETS awards stay carded; the PPSR account requested; keys rotate once the lanes are set up.
- Building practitioners (2d397c7, merged 790eeec): the hold lifted; the register enumerated by its own 26 option
  searches (26,978 current practitioners); each practitioner's page once, then every 90 days, 5 s apart, off-peak:
  qv4-building-practitioners-register-capture nightly from 22:05, about 4,000 pages a night, six nights. A new card: the
  page's five sub-tables load by POST, which the fetch gate does not do, and lapsed practitioners are not listed.
- Council minutes gaps (499ffaf, merged 05e9d73): no scans among the 616 minutes held; the page-reader route is built
  for the first; the 347 the old estate read are fetched once from the councils at tonight's capture.
- Diary attendees (bd982f9, merged eb712d7, published by row 1173): pub.minister_diary_attendees, 287,599 rows from
  191,597 entries, 46 set aside for unbalanced brackets, every split rejoins its text. Two scans start from them:
  lobbying-attendees-suppliers 31,969 lines and lobbying-attendees-donors 118 (5,631 entries reach a company that the
  whole-text join does not). On the board (c549cb9). products.scan check: 0 problems over 15 scans.
- The Papers Past ingest (row 1169) waited because the worker, started on 1 November, did not know `gzip` and `ionice`;
  the worker was restarted after the diaries load and the ingest leased.
- The Insolvency Register: Arthur placed the key file. The first live calls all answered 404, which the lane reads as an
  empty month: the API's version belongs in its path (`/v5`), as the NZBN API's does (44949bb, the fake server pins it).
  The search cursor reset; 18 calls then saw 1,180 estates from 1990 and 1991. Nightly from 21:00. The schema had not
  been made on the live database; made with the standard grants.
- The model server's watchdog (f01fb1c, Arthur: "make the gpu watchdog too"): qv4-radiance-watchdog.timer every two
  minutes; a warm, active server with requests in flight and no token for ten minutes is restarted and alarmed; a
  stopped unit is never started (the night window); three restarts in six hours, then an alarm only.
- For the morning: the owner login's limit is 20 connections and the worker holds about ten, so test runs in a session
  meet "too many connections" (two worker tests failed on it at 21:00). Raising the limit is a superuser's change.

## 27. Midnight, 2 to 3 November

- The sanctions lists (ruling 132) merged and released (e015726): the hold lifted; a weekly capture by its own record,
  nothing fetched twice, a block fails that one list only; qv4-sanctions-capture (141, 23:30 NZDT) and
  qv4-sanctions-load (142, 06:35 NZDT). In the sample database: MFAT Russia 1,918 listings, UN 1,007, Police 494
  current and 317 ended; 10 requests, none challenged. MFAT's workbook profile at version 2 (its Total row tallies one
  column, not listings); identity-document phrases cut from every value. Police's check is red by design: its page says
  22 current designations, its workbook holds 21 (as on 21 October). Template 13's sanctions rule still says no list is
  held: its own session.
- Papers Past: the ingest finished at 21:25 (1h42m); the index failed at once, tantivy missing from the release's venv.
  Installed there; queued again as row 1208, running since 00:00. Lesson filed.
- Insolvency (42bd833): the first removals run listed 1,511 estates back to the API's start and re-asked each at 5 s,
  so it hit its 30-minute deadline and the night's search never ran. It now re-asks only an estate we hold; none is
  left, so the 21:00 run on 3 November goes straight through to the search. A test, and its mutant caught.
- Failed reads tonight, source side, no change made: grants (the lottery page answered 403: a block, a failed read),
  tenancy tribunal (three transport failures in a row), local elections files (3 failed); tenders and charities
  both answered 403 (a block, a failed read).

## 28. Morning of 3 November: the plan, in parallel

Published overnight: building practitioners (4,372 practitioners, 788 decisions; 42,091 on the register, about nine
more nights at tonight's budget), council minutes (1,388 meetings, 963 minutes: 13,012 attendees, 5,883 resolutions,
396 declarations), the Gazette (207,548 notices). Fixed (3edb6a7): the insolvency and papers_past sample lists had no
loader, which stopped the shared sample and errored 118 tests in the 05:00 full tier; a fast test now finds it.

Tracks, each a fix session in its own worktree, merged and released by the integrator:

| Track | Module | What |
| --- | --- | --- |
| 1 | registers/papers_past | The index's memory: PSS grew about 260 MB per million documents to 9.6 GB at 35M; file-mapped segments or real growth. Retry row 1212 (19 GB) cancelled until then |
| 2 | registers/courts | The load's red: four judgments whose counsel lines name a role no party holds (tolerated 2); the cause, not the tolerance |
| 3 | products/board, templates/13 | The three council views and the building practitioners' new fields catalogued; template 13's sanctions rule reads the lists |
| 4 | tenancy_tribunal, local_elections | Ours or the source's: every order fetch failed in transport; three files failed |
| 5 | (after row 1268) | The full tier's four failures, named by its rerun |

The integrator's own: merges and releases; the alarm channel (ntfy.sh's free daily quota is spent, nothing has reached
Arthur since 1 November 08:45: his decision); the owner login's 20-connection limit (a superuser's change).
