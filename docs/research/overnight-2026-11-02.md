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
