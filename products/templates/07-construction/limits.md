# Subcontractor vetting and phoenix detection: known limits

Template `construction` 0.1, use case 7. What the report cannot see, stated
to the reader. Checked on 2026-10-21 against twelve real subjects on
`querynz_v4` (the checkpoint, below). Each line is a limit accepted for now;
the card that would lift it is named.

## What the phoenix signature is here

A company that failed (a liquidator, receiver or administrator appointed, a
winding-up application, a creditors' notice, a deed of company arrangement;
or a removal from the register, which is not an insolvency) dated from its
Gazette notice, beside every going company that shares a person or an
office with it, **whatever the gap in time**. Each pair shows the gap in
days from the failure to the going company's registration, signed ("50
days after", "134 days before"), and the pairs are ordered by that gap,
nearest first. The **window is the reader's setting, not the template's**
(Arthur's ruling 65, 21 October 2026): until then the template cut at 365
days either side (`WINDOW_DAYS`, now gone). The flag says how many of its
pairs fall within 90 days (the old estate's MC-C1) and within 365 days
(construction-1's cut), so a reader sees the old defaults without losing
the rest. A window cuts only when the reader sets one, as `window_days` on
the report; the shape does not carry it yet, so today every gap is shown
(`the-report-carries-no-template-parameters`). Measured on the confirmed
groups, 2026-10-21: 476 going companies at 90 days, 1,191 at 365, 1,858 at
730, of 784,993 registered. A removal is thirty times as common (38,059 at
365 days) and is never red. With no cut, a confirmed insolvency beside a
going company is red however far apart they are: a director whose one
company failed in 2024 and whose other was registered in 2001 is raised,
and the gap, last in the order, is the reader's to weigh.

The flag `phoenix-signature` is raised only on a **shared person** (from a
person: two of the person's own confirmed companies) or a **shared
registered office** (from a company: a company of the same name that had,
before its failure, the office the entity has now) together with a dated
failure. **A name is never the signature.** The old estate's probe found a
same-name join within ninety days yields 14.2 million pairs; here, of 183
going companies that share a name with a company liquidated within a year
of their start, 2 share a director's name and 1 a confirmed person. A
company that only shares the name is listed near and flagged
`same-name-failed`, info, or amber when an officer's name is on both, and
never red.

## What it cannot see

- **The people behind a company, from the company.** Started from a
  company, the report lists its directors and holders of record and the
  Gazette notices on it, and does not follow the people: their other
  companies and how those failed, their prohibitions, bankruptcies and
  society roles are not read. So from the firm a procurement lead names,
  the phoenix signature through a person is **blocked, never clear**, and
  says to start a report from each director listed; from a director it is
  read across all the person's companies. This is the largest limit here.
  (`a-company-start-does-not-follow-its-officers`)
- **A shared office alone.** The walk counts the companies at a registered
  office and lists none, so a failed company at the entity's office that
  shares neither its name nor a person is not seen.
  (`the-walk-counts-the-companies-at-an-office-and-does-not-list-them`)
- **The office a failed firm traded from.** On liquidation a company's
  registered office moves to its liquidator's: 4,735 of 4,945 companies in
  liquidation have an office dated from their liquidation. The template
  never compares that office, and compares an office from before the
  failure only where the file still holds one, which is seldom; the office
  check is otherwise blocked.
  (`a-liquidated-companys-office-before-its-liquidation-is-not-published`)
- **Past roles.** The companies file lists current roles only: a director
  who left the failed company before it failed, or one struck off with it,
  is not seen, nor that failure. The checks over a person's companies fire
  on what they see and are otherwise blocked; `past-roles` says so on every
  report. (`the-companies-file-holds-no-past-directorships`)
- **Earlier names.** The companies change history (former names, trading
  names, earlier directors and offices) is not held before 16 August 2026
  and is held but not published since: a firm that failed under one name
  and trades under another is seen only through a person or an office.
  `change-history` is blocked. (`the-companies-file-holds-no-past-directorships`,
  `the-not-held-list-lacks-employment-determinations-and-the-change-history`)
- **The registers a subcontractor check needs most.** The licensed building
  practitioners register (licence, class, discipline), the Official
  Assignee's Insolvency Register (discharge, no-asset procedures, summary
  instalment orders), court judgments, the Employment Relations
  Authority's determinations (unpaid wages), the Personal Property
  Securities Register. Each has a flag that is always blocked, and the last
  section names them.
- **A lender's entry into possession, and the dated status rows.** Both are
  published (`pub.gazette_possessions`, `pub.company_states`) and unknown to
  the report's catalogue, so a template cannot name them.
  (`the-catalogue-does-not-know-gazette-possessions`)
- **One liquidator across a group's failures.** A liquidation notice
  publishes a count of its liquidators; a liquidator's row names its
  notice, not its company. `practitioner-repeat` is blocked.
  (`a-liquidator-row-does-not-name-its-company`)
- **Every company of a busy director.** The walk lists 40 companies and
  reads the notices, offices and officers of 12; past those the checks that
  need them block and `walk-coverage` fires. A professional director's
  signature is shown and never red. (`the-walk-reads-twelve-companies-and-lists-forty`)
- **A company named like a street address.** The shape refuses any report
  whose walk meets one (2,914 such names, 1,454 registered).
  (`a-company-named-like-a-street-address-refuses-every-report-that-meets-it`)
- **The entity's own notices apart.** A section cannot set the start's own
  rows apart from its people's: every company reached is in the phoenix
  section with its status, and every Gazette notice in the Gazette section
  under its company's name; the flags make the split.
  (`a-section-cannot-set-the-starts-own-rows-apart-from-its-peoples`)
- **A reader's window.** The template reads `window_days` from the
  report and cuts there, saying how many pairs it left out; the shape
  takes no such parameter from the page or the command line yet, so a
  reader cannot narrow the list and every gap is shown.
  (`the-report-carries-no-template-parameters`)
- **A status and a notice that disagree.** 739 companies with a Gazette
  liquidation notice are registered today (restored, or the liquidation
  ended). The notice still dates a failure, and the company's status is
  shown beside it.

## How to read it

- **The entity** is the row the report starts from and the rows a rule
  confirms are the same. Every other row under the name is a **namesake**,
  listed first and apart with the reason it is only near; past fifty
  namesakes the report says it is partial. A namesake's companies and
  notices are amber at most.
- **A failure's date is the Gazette's.** A liquidator's or receiver's
  appointment where the notice states one; otherwise the day the notice was
  published (a winding-up application's own date is its hearing, a
  removal's the last day for objections, and neither is the day it
  failed). The earliest failure notice on a company dates it. A receiver
  ceasing to act ends a receivership and dates nothing.
- **Two facts sit side by side**: "FAILED LIMITED: liquidation (liquidator
  appointed by the court), appointed 11 March 2024 | NEW LIMITED: registered
  7 August 2024, 149 days after". The report never says one followed from
  the other, and a flag never prints an address (the office section shows
  a company's registered office).
- **Blocked is not clear.** A check the walk could not have seen says why;
  absence is never a finding. A section that prints "none found" from a
  company start (the phoenix section, the people's notices) is not a clear
  either: its text says the people are not followed.

## The checkpoint, 2026-10-21

Twelve real subjects (`checkpoint.list`), chosen from the tables to cover
the cases: three directors each on a construction-trade company in
liquidation and on a going one registered 4, 7 and 34 days after its first
failure notice (roofing, scaffolding, framing), all three raised red; the
going roofing and scaffolding companies themselves, from which the
signature blocks and names the director to start from; the liquidated
roofing company itself (entity-status and insolvency-notices red); a
director in a 56-row group whose walk met a company named like an address;
a director in a contested group (the pair raised amber, a namesake's until
confirmed); a professional director of 69 companies (walk short, the
signature blocked); a going company that shares its name with one
liquidated 263 days before its start and no officer's name (info, not
raised); a director confirmed to a 2002 bankruptcy (the first roofing
director is confirmed to one of 2006); one confirmed to a director
prohibition published in 2023 and since ended. Whether a confirmed
bankruptcy or prohibition is the same person is the links lane's rule
(`full-name@1`); the report shows the notice's date beside the person's
roles and says nothing of a discharge, which the Insolvency Register holds. Eleven printed and one was refused by the shape
(carded); none broke a rule; built in 0.3 to 6.0 seconds each.

Read against the Gazette source file (fields only, never the text): the
roofing company's liquidation, notice 2024-al1200, published 18 March
2024, names the company, and its entry holds 12 March 2024, the row's
appointment day; the winding-up application on it, 2024-aw205, published
24 January 2024, names the company and the High Court, and holds 6 October
2023 and 1 February 2024, the row's filing and hearing days; the
scaffolding company's liquidation, 2025-al7327, published 17 December 2025,
names the company, says the shareholders appointed, and holds 11 December
2025, the row's appointment day. The registration dates beside them are
the companies register's rows (the original file is not held).

Against the old estate's requirements (2.4): MC-C1 the phoenix signature,
deterministic, a failure and a re-registration within a window: built, on a
shared person from a person start and a shared pre-failure office from a
company start, never on a name; from a company the person half is blocked
(carded). MC-C2 the subcontractor officer web: the officers of record and,
from a person, the people beside them, near. MC-C3 liquidation history:
`insolvency-notices` and `repeat-failure`. Its "ERA claims" (employee
proceedings) are declared not held; "address reuse (same yard)" is the
office check, thin until the past offices are published; its precomputed
nightly signature table is not built (a report reads the walk).

What the checkpoint changed: the office comparison now uses the failed
company's office from before its failure, never its liquidator's (the
measurement above); `same-name-failed` words its subject by the start. The
fixtures had already caught a crash in the office pair's text that no real
row reached. Cards: four on the report lane, one on the companies lane, one
on the earlier templates' bankruptcy check.

## The checkpoint re-rendered, 2026-10-21 (construction-2, ruling 65)

The same twelve subjects, rendered with the template before and after the
window became the reader's. Ten printed and changed only in their phoenix
flags; one (subject 7, the address-named company) is still refused by the
shape; one (subject 9, the professional director) is unchanged, its walk
short. No flag changed status or severity.

- **Pairs the 365-day cut hid now show, after the near ones.** The
  scaffolding director (subject 4): the liquidation beside the new
  company 4 days after, as before, and now beside a going company
  registered 765 days before it. The director in the contested group
  (subject 8): 6 pairs instead of 1 (0 within 90 days, 1 within 365), the
  rest from 2,806 days apart. The director of 28 going companies (subject
  7's walk, refused) counts 28 pairs, 2 within 90 days and 4 within 365.
- **Every fired flag counts its pairs** ("of 1 pair(s), nearest first, 1
  within 90 days and 1 within 365 days; no window is set, so every gap is
  shown"); the three red signatures (subjects 1, 4, 6) still name the same
  failure and the same new company first, at 34, 4 and 7 days.
- **`same-name-failed`** (subject 10) drops "within the window" and counts
  its one pair, 263 days, within 365 and not within 90.
- **A person with no failure** (subjects 11, 12) says so plainly ("no dated
  failure has a going company to set beside it") instead of naming a
  window, and still gives no clear.
