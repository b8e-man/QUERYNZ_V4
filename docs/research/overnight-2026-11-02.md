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
