# Business credit and monitoring: known limits

Template `credit` 0.1, use case 5. What the report cannot see, stated to
the reader. Checked on 2026-10-21 against twelve real subjects on
`querynz_v4` (the checkpoint, below). Each line is a limit accepted for now;
the card that would lift it is named.

## What a change is here

The grain is the companies register's **monthly file**. Two are held,
`companies-2026-07` and `companies-2026-08`. A director, holder of record or
registered office first shown in the August file arrived between the two
files; one last shown in the July file left between them. That dates a
change to a **month, not a day**, and every flag that lists one says so.
Where the register files a day beside the row (a director's appointment, an
office's start), it is printed with it as the register's own date. A
holding whose share count changed shows in the file as one holding leaving
and one arriving under the same name; the template pairs them and says the
holding changed. A Gazette notice is dated to the day from the notice.

Measured 2026-10-21 between the two files: 9,056 director rows left and
11,782 arrived; 17,236 holdings left and 20,582 arrived; 11,788 registered
offices left the file; 5,830 companies are first shown in August (5,827 of
them registered in 2026; three older ones reappear) and 2 are gone from it.

The flag `monthly-changes` lists every change it sees on the entity (or, from
a person, on the person's confirmed companies), newest file first, up to
twelve in its text and the rest in the changes section, each cited.
`recent-adverse-change` is red on a Gazette insolvency notice published in the
last 90 days (`RECENT_DAYS`) or the entity gone from the latest file, amber
on a removal notice in that window, a director leaving in the latest file, or
an office moving in it to an address fifty or more companies share.
`officer-churn` counts directors arriving and leaving between the files and
current directors appointed in the last 365 days as filed (`CHURN_DAYS`), a
founding director (appointed within 31 days of registration) not counted;
amber at three with a departure.

## What it cannot see

- **A status or name change between the files.** `pub.company_states` holds
  the earlier state of each entity the August file changed (5,629 rows: 3,979
  status changes, 1,346 name changes), but the report's catalogue does not
  know the view, so no template can read it. The status today is shown; how
  it stood in July is not. So `monthly-changes` and `recent-adverse-change`
  never clear (`STATES = False`), and `status-name-changes` is blocked on
  every report. This is the largest limit for use case 5.
  (`the-catalogue-does-not-know-company-states`)
- **Anything after the August file.** Nothing filed with the register since
  is seen until the next monthly file is loaded, or until step 5.5 checks the
  entity against the business-number interface on each lookup;
  `interface-freshness` is blocked. (step 5.5, the companies lane's work)
- **A "since" date, and a watched list.** The report takes no date to
  report changes from, and keeps no list of entities to re-run when a file
  loads: it lists every change it can see, dated, and what is new to the
  reader is theirs to pick out. `since-date` says so on every report.
  Monitoring is the report re-run by hand.
  (`a-report-takes-no-since-date`, `the-report-keeps-no-watched-list`)
- **The change list as a section.** A section cannot select only the rows
  that changed between files, so the changes section lists every director,
  holder and office of the entity with the files that show it, and the
  dated list itself is the flag `monthly-changes`.
  (`a-section-cannot-select-the-rows-that-changed-between-files`)
- **Which files exist.** The lane publishes no list of its files or their
  cut dates, so `rules.py` carries the two measured (`FILES_MEASURED`) and
  adds any file a row names; a change cannot be dated between two days.
  (`the-companies-lane-publishes-no-list-of-its-monthly-files`)
- **The people behind a company, from the company.** Started from a
  company, the report lists its directors and holders of record and does not
  follow them: their other companies and those companies' states, their
  prohibitions and bankruptcies are not read. `people-failed-companies`,
  `other-current-companies`, `prohibition` and `bankruptcy` are **blocked,
  never clear**, and say to start a report from each director listed; the
  people sections print "none found", which is not a clear, and their text
  says so. From a director the same checks read across the person's
  companies. (`a-company-start-does-not-follow-its-officers`)
- **Past roles.** The companies file lists current roles only, and the
  roles that left it since July 2026 with no end date; a director who left
  before the July file is not seen. `past-roles` is blocked on every report;
  a check over a person's companies fires on what it sees and never clears
  (`HISTORY = False`). (`the-companies-file-holds-no-past-directorships`)
- **Earlier names before 16 August 2026.** The companies change history is
  not held before then, and is held and unread since. `change-history` is
  blocked. (`the-not-held-list-lacks-credit-bureau-and-the-business-number-interface`)
- **Who holds security over the company.** The Personal Property
  Securities Register is not held (its interface has waited on approval
  since 19 September); `securities-register` is blocked, red.
- **The Insolvency Register, court judgments, credit-bureau defaults.**
  Each is blocked: a bankruptcy's discharge, a creditor's judgment, a
  payment default cannot be seen. A bankruptcy notice dated more than five
  years before the report is amber, not red: most are discharged after three
  years, and the discharge is in the Insolvency Register.
- **A lender's entry into possession.** Published (`pub.gazette_possessions`)
  and not in the report's catalogue; `mortgagee-possession` is blocked.
  (`the-catalogue-does-not-know-gazette-possessions`)
- **Every company of a busy director.** The walk lists 40 companies and
  reads the notices and officers of 12; past those the checks that need them
  block and `walk-coverage` fires.
- **Same-name companies.** Started from a company, a company that only
  shares its name is listed in the standing section, near, after the
  entity's own rows; a section cannot set them apart in a section of their
  own. (`a-section-cannot-set-the-starts-own-rows-apart-from-its-peoples`,
  raised by construction-1)

## The checkpoint, 2026-10-21

Twelve subjects (`checkpoint.list`), rendered through `python -m
products.report render REF --template credit` and as HTML: all twelve print,
**none refused** by the shape's presentation rules, 0.2 to 4.9 s each (the
professional director's walk is the slow one). The first run found five
faults in the rules, fixed before the second:

1. The files held were read from the report's own rows: a company new in
   the August file showed one file and no change; a removed company showed
   July as the latest file. Now the measured files are added (`FILES_MEASURED`).
2. `recent-adverse-change`'s clear text said "the entity is in the latest
   file" for a person and for a removed company.
3. A new company's founding director counted as officer churn.
4. A prohibition that ended in 2006 was red; one ended is now amber.
5. A company under a year old read "0 year(s)".

And a sixth on the second run: a company removed in May 2026 and gone from
the August file was red as a recent change; the drop is the file catching up
with a removal the row dates, and it is listed and not raised.

What the twelve show, by subject:

| Subject | Start | What fired |
| --- | --- | --- |
| a horticulture company | company | in liquidation (red); liquidator appointed 23 July 2026, a director and two holders left and one arrived in the August file, the office moved to an address 67 companies share (recent, red); two earlier removal notices (amber) |
| its new director | person | the same company's liquidation on the person's one company (red); every person beside, near |
| a company registered 2 July 2026 | company | young (amber); first shown in the August file with its directors |
| a logging company | company | a winding-up application to be heard 2 November 2026, published 16 October (recent, red); still Registered in the August file |
| a company in liquidation after receivership | company | two receiverships and a winding-up application (red), all before the 90-day window, so not recent |
| a test company removed in May 2026 | company | removed (red); gone from the August file, listed, not recent |
| an electrical company | company | a holding of 100 shares became 80, a new holder: two changes, info |
| a company whose five directors left | company | five directors left and one arrived in the August file: churn amber, recent amber |
| a company renamed between the files | company | nothing it can show: the rename is in `pub.company_states`, not reachable; every change check blocked |
| a professional director (75 directorships) | person | a hub (amber); the group contested; 65 companies not read; a namesake's bankruptcy (amber) |
| a director with a 2003 prohibition | person | the prohibition, ended 2006 (amber); a bankruptcy notice of 2002 (amber) |
| a director with a 2005 bankruptcy | person | the bankruptcy (amber, older than five years) |

Read against the Gazette source file (fields only, never the text), on each
notice's own line in the file: the horticulture company's liquidation,
notice 2026-al4099, names the company and holds 23 July 2026 and 27 July
2026, the row's appointment and publication days; its removal notice
2024-ds4495 names the company and holds 15 October 2024 and 12 September
2024, the row's objections and publication days. The companies register
rows cite the old estate's export (the original monthly file is not held).

Against use case 5's checklist ("has anything changed for the companies I am
exposed to"): status today, type, age, latest file: built. Changes at the
monthly grain (directors, holders, offices, the entity itself): built,
status and name changes blocked. The Gazette on the entity: built. Its
people's other companies and their notices: built from a person, blocked
from a company. A since-date, a watched list, the interface's freshness,
the securities and insolvency registers, judgments, credit-bureau data: not
held, each named.
