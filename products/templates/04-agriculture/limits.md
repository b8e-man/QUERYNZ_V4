# Agriculture counterparty: known limits

Template `agriculture` 0.1, use case 4. What the report cannot see, stated
to the reader. Checked on 2026-10-20 against twelve real subjects on
`querynz_v4` (the checkpoint, below). Each line is a limit accepted for now;
the card that would lift it is named.

## What it cannot see

- **The people behind a company, from the company.** Started from a
  company, the report lists every director and holder of record with the
  dates the register files, but does not follow them: their other
  companies and what became of them, a prohibition on a director, their
  society roles and donations are not read. Those five checks are
  "blocked", never clear, and the "people's other companies" section's
  "none found" is not a clear. Start a second report from each person
  listed. (`a-company-start-does-not-follow-its-officers`)
- **Companies that share the counterparty's name.** No link rule joins
  company to company by name, so a same-name or "(2025) LIMITED" company is
  not set apart as a namesake. (`a-companys-same-name-companies-are-not-set-apart`)
- **Who stands behind a company holder.** The companies file gives a
  shareholder that is a company no business number, so the report flags
  it and does not follow it. (`a-company-holder-carries-no-business-number`)
- **A practitioner who recurs across a group's failures.** The notices
  count their liquidators and receivers but the report does not reach the
  names; that check is blocked. (`insolvency-practitioners-are-not-reached-from-a-notice`)
- **A bankruptcy.** The Gazette's bankruptcy notices are published, but no
  link rule joins one to a person yet; the check is always blocked, never
  clear: a blank there is not a clear. (`bankruptcies-and-appointments-are-not-in-pub-names`)
- **Sole traders, general partnerships and trusts.** Not in the companies
  file and not held; a person start has no register status, and that check
  is blocked. A limited partnership's own row (status, dates) is held; its
  general and limited partners are not, so it shows no officers and says
  why. (`not-held-lacks-unincorporated-entities-and-mpi`)
- **A charity officer row is matched by name.** No link joins the
  Charities Register's officers to any other row yet, so a row carrying
  the counterparty's name is near, a namesake's until a rule confirms it,
  and the register's disqualified mark on one is amber, never red. From a
  company, its charity by business number is confirmed (an A&P
  association, a society on the companies register) with its officers and
  returns, and a mark on one of those officers is red; its directors' own
  charity rows are not read, so the mark check blocks. A holder of
  record's row is not looked up by name.
  (`charity-officers-are-in-no-link-and-no-name-row`, the links lane's)
- **Security over stock, crops and plant (the PPSR), land titles, the
  Insolvency Register, court judgments, MPI
  prosecutions and NAIT enforcement.** Not held; listed in the report's last
  section and in the flags that would read them.
- **When a role really ended.** A directorship that has left the latest
  monthly file carries no end date, because the file states none; a
  holding of record is undated and shows the files it was seen in. The
  interface check of step 5.5 will date them.
- **GST age.** The old young-entity rule read GST registration; it is not
  held, so the company's own registration date stands in.

## How to read it

- **The counterparty** is the row the report starts from: a company is its
  NZBN; a person is the rows a rule confirms are the same person. Every
  other row under the same name is a **namesake**, listed first and apart,
  with the reason it is only near. A namesake's notices are amber and say
  so; only the counterparty's own are red.
- **Register status** is the companies file's own word: in receivership,
  in liquidation, removed, deregistered are red; not in the latest file is
  amber.
- **Two facts with dates sit side by side.** A receivership is listed with
  its own date and the officers with theirs; the report never says one
  followed from the other. A removal from the register is not an
  insolvency and is flagged apart.
- **A holding is a holding of record.** A nominee or trustee holder and a
  company holder are flagged and never called an owner.
- **Hubs:** a professional director (50 or more directorships), a nominee,
  the Crown, a registered office shared by 50 or 1,000 companies (an
  accountant's office often is). What a hub joins means little on its own.
- **Absence is not a finding.** "None found in …" is the most it says.
- **Start from the company or from a person row** (a director or
  shareholder). A society or a donation row is not a counterparty start,
  and the checks say so.
- **A Gazette company notice shows one date,** which for a winding-up
  application is the hearing day, and a removal notice may be undated
  (`a-gazette-company-notice-date-does-not-say-what-it-dates`).
- Companies register rows come from the old estate's tables; the original
  monthly file is not held, so they cite the row.

## The checkpoint, 2026-10-20

Twelve real subjects, chosen from the tables to cover the cases: a farm
company in receivership (NIRVANA FARM LIMITED); a removed farm company with
a 2000 liquidation; a farming limited partnership under two years old; a
dairy co-operative with nominee custodians and nine company holders; a farm
company with two near donations under its name; a young farm company at an
accountant's office with a trustee company holder; an irrigation company
with 151 officers and holders (75 of them companies); a Federated Farmers
district society (not a counterparty start); a director with a prohibition
in force and a company registered this year; a director of five companies,
four in liquidation, 17 insolvency notices; a contested group (seven rows,
amber throughout); a director with 25 namesakes and a namesake's ended
prohibition. All twelve printed; none was refused by the shape's
presentation rules; built in 0.1 to 1.3 seconds each (the old requirement
MC-A2: under 2). Read against the Gazette source file: NIRVANA FARM
LIMITED's receiver appointed 23 July 2025; HALL BLOCK FARM LIMITED's
liquidator appointed 7 February 2000; the prohibition from 16 June 2025 for
eight years (to 16 June 2033). The old requirements of section 2.2: the
controlling mind through the register's directors and a hand-off to a
person's report (MC-A1: the officers section, then a report per person,
until the walk follows them); flags and the memo in one build under 2 s
(MC-A2); a partnership's empty officers said so; NAIT and MPI declared not
held, never adjudicated from news.

## Re-rendered, 2026-10-21 (fix-templates-1, the Charities Register)

The 2026-10-20 checkpoint kept no keys, so `checkpoint.list` now holds six:
NIRVANA FARM LIMITED and HALL BLOCK FARM LIMITED from it, NIRVANA's
director, a Federated Farmers district society, and two societies on the
companies register that are registered charities. Rendered before and
after the template read the Charities Register; none refused. The two farm
companies and the society start are unchanged (no charity by business
number; a society start's officers are that society's). The director:
`charity-integrity-marks` from blocked to clear, `charity-officer-roles`
from clear to fired with three charity officer rows of the same name, near.
RAI VALLEY AGRICULTURAL AND PASTORAL ASSOCIATION and the Institute of
Agricultural and Horticultural Science: `charity-officer-roles` from blocked
to fired, each reaching its charity by business number, confirmed, with 11
and 21 officer rows and the returns beneath it (28 and 40
rows in the section); the mark check still blocks (their directors are not
followed) and says the charity's own officer rows carry no mark.
