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
