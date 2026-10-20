# Recruitment board screen: known limits

Template `recruitment` 0.1, use case 8. What the screen cannot see, stated to
the reader. Checked on 2026-10-20 against twelve real subjects on
`querynz_v4` (the checkpoint, below). Each line is a limit accepted for now;
the card that would lift it is named.

## What it cannot see

- **A bankruptcy.** The Gazette's 65,299 bankruptcy notices are published,
  but no link rule joins one to a person yet. The bankruptcy check is
  always "blocked", never clear: a blank there is not a clear.
  (`bankruptcies-and-appointments-are-not-in-pub-names`)
- **A public appointment in the Gazette, or a candidate's own return.** Not
  joined to a person by any link rule, so the template does not read
  appointments, and a candidate's return of donations received is not
  listed. (same card)
- **Charities.** The Charities Register is not published yet: no charity
  role, and no check of its banned-director and undischarged-bankrupt
  marks (that flag is blocked). Incorporated societies are read.
- **The Commerce Commission's cases and the FMA's warnings.** Held but not
  published (step 5.3); that flag is blocked.
- **An MP's declared interests and expenses.** The interests are published
  but the shape does not walk to them from a person
  (`an-mps-declared-interests-are-not-walked-from-a-person-start`); the
  expenses are published but the shape cannot read them
  (`expenses-views-are-not-in-the-report-catalogue`). A screen of an MP
  shows the seats and candidacies and says nothing of interests.
- **Court judgments, the Insolvency Register, the securities register,
  financial service providers, sanctions lists, limited partnerships.** Not
  held. Listed in the screen's last section.
- **When a role really ended.** A directorship that has left the latest
  monthly file carries no end date, because the file states none. The
  official interface check (step 5.5) will date it.
- **GST age.** The old young-company rule read GST registration; it is not
  held, so the company's own registration date stands in.

## How to read it

- **The subject** is the row the screen starts from and the rows a rule
  confirms are the same person. Every other row under the same name is a
  **namesake**, listed first and apart, with the reason it is only near. A
  namesake's notices are amber and say so; only the subject's own are red.
- **A contested group** (the watch saw a sign that one "person" is two)
  turns every other row of it near. Four of the twelve checkpoint subjects
  were contested, a common name among them; the screen then reads mostly
  amber, which is the honest answer.
- **Two facts with dates sit side by side.** A company's liquidation is
  listed beside the subject's dates on that company; the screen never says
  one followed from the other. A removal from the register is not an
  insolvency and is flagged apart, as information.
- **A holding is a holding of record.** A nominee or trustee holder is
  flagged as a hub and never called an owner.
- **Hubs:** a professional director (50 or more directorships), a nominee,
  the Crown, an address shared by 50 or 1,000 companies. A shared board or
  address through a hub means little on its own.
- **Absence is not a finding.** "None found in …" is the most it says.
- **Start from a person row** (a director, shareholder, society officer,
  seat or candidacy). A screen started from a donation row cannot walk the
  person's companies, and says so (`a-donation-row-start-has-no-group`).
- **A Gazette company notice shows one date,** which for a winding-up
  application is the day it is to be heard, not the day it was filed or
  published (`a-gazette-company-notice-date-does-not-say-what-it-dates`).
- Companies register rows come from the old estate's tables; the original
  monthly file is not held, so they cite the row.

## Refused reports

The shape refuses to print a report that seems to break a presentation
rule. Two of its checks refuse true reports today: a person surnamed Lane
(or Place, Drive, Street) with a dated row
(`a-surname-lane-trips-the-home-address-check`), and any report reaching a
company with "CONTROL" in its name
(`a-company-name-with-control-trips-the-cause-check`). The screen for
those subjects cannot be printed until the report lane fixes the checks.

## The checkpoint, 2026-10-20

Twelve real subjects, chosen from the tables to cover the cases: a
director confirmed to a prohibition and a winding-up; a professional
director (139-row group, contested); a common name with 129 namesakes; a
donor; a society officer; a nominee holder; a promoter; a director with a
namesake's prohibition; a sitting MP; a director of a company under two
years old; an MP's interests return; a "John Smith". Ten printed with no
breach of the presentation rules; two were refused (above). Built in 0.2
to 4.6 seconds each (the old requirement: under 5). Read against the
source documents: the prohibition of the first subject (four years from 22
September 2022, ended), the near prohibition of the eighth (a different
middle name, two years from 6 September 2013), and the winding-up notice
(dated by its hearing day, carded). The old requirements of section 2.1:
one screen with no tab-hopping (one memo); namesakes visibly separate (the
first section); a namesake count that degrades to a declared partial (the
walk's limits and the namesake-exposure flag); charities and ComCom
declared not held.
