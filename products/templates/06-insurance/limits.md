# Insurance underwriting: known limits

Template `insurance` 0.1, use case 6. What the report cannot see, stated to
the reader. Checked on 2026-10-21 against twelve real subjects on
`querynz_v4` (the checkpoint, below). Each line is a limit accepted for now;
the card that would lift it is named.

## What it cannot see

- **The safety record.** WorkSafe's prosecutions and enforceable
  undertakings, the Commerce Commission's cases, the Financial Markets
  Authority's warnings and actions, court judgments, the Employment
  Relations Authority's determinations, the Disputes Tribunal's decisions
  and Fire and Emergency New Zealand's notices are in no published
  register. This is the heart of use case 6 ("the real safety and solvency
  record behind a proposal") and the largest limit here: the flag
  `safety-record` is **blocked, never clear**, red, on every report, and so
  are `regulator-actions`, `court-judgments` and `tribunals`. No
  prosecution, undertaking, judgment or determination in a report is a
  finding of none. The old estate holds 143 WorkSafe release documents read
  into 83 prosecutions and 62 enforceable undertakings (76 with a business
  number); no lane of the new estate reads them yet.
  (`worksafe-and-regulator-actions-have-no-lane`)
- **The safety registers by name in the memo's not-held line.** A section
  may name only the catalogue's not-held keys, and there is none for
  WorkSafe, the regulators, the employment bodies, the Disputes Tribunal,
  the fire service or the change history; the safety section's text and
  the flags name them, and the line under the section names only court
  judgments, the Insolvency Register, the securities register and financial
  service providers. (`the-not-held-list-has-no-key-for-the-safety-registers`)
- **The people behind a company, from the company.** Started from a
  company, the report lists its directors and holders of record and the
  Gazette on it, and does not follow the people: their other companies, a
  sister company that failed, their prohibitions and bankruptcies are not
  read. Those checks are blocked, and the sections for the people print
  "none found", which is not a clear. Start a report from each director
  listed. An underwriter's first question is about the business, so this
  is the second-largest limit. (`a-company-start-does-not-follow-its-officers`)
- **Past directorships and holdings.** The companies file lists current
  roles only. A sister company the person left before it failed, or that
  was struck off with them on it, is not seen; a director who left the
  board before July 2026 is not seen either. So `sister-company-failure`,
  `register-events` and `other-current-companies` fire on what they see
  and otherwise block, and `officer-churn` counts arrivals only and never
  clears; `past-roles` says so on every report. `HISTORY = False` in
  `rules.py` turns the clears back on when a view publishes past roles.
- **When a holder of record took its shares.** A holding carries no start
  date, so a sister company's failure beside a holding is "no start filed"
  and never red.
- **The status history and a lender's entry into possession.**
  `pub.company_states` (each file's status for a company) and
  `pub.gazette_possessions` (3,002 mortgagee entries into possession) are
  published and the brief names them, but the report's catalogue knows
  neither, and a template naming a view the catalogue does not know is
  refused when loaded. The template does not read them; `status-history`
  and `mortgagee-possession` are blocked.
  (`the-catalogue-does-not-know-gazette-possessions`)
- **The change history.** Former names, trading names, industry
  classification (the old estate's change-of-trade flag), earlier
  directors and offices: not held before 16 August 2026, held and not
  published since. `change-history` is blocked.
- **The Insolvency Register, the securities register, financial service
  providers.** The interfaces have waited on approval since 19 September
  2026: a bankruptcy's discharge, who has lent against the firm, a
  provider's registration are not seen. A Gazette bankruptcy is shown with
  its own date and nothing about its discharge.
- **A contested group.** The watch's contested groups make every other row
  near, and a prohibition joined by a confirmed full-name link then shows
  amber, a namesake's until confirmed (seen on checkpoint subject 3). The
  start row's own company is read as the person's whatever grade the walk
  gives it (seen on subject 6; the shape's side is
  `a-contested-groups-near-row-can-make-the-start-rows-own-company-near`).
- **Every company of a busy director.** The walk lists 40 companies and
  reads the notices and officers of 12; past those `walk-coverage` fires
  and the clears that need them block.
- **A winding-up application is not a failure.** An application may be
  dismissed. A failure is dated from the first appointment a notice dates
  (a liquidator, a receiver, an administrator), and from an application
  only where no appointment is held.
- **Two facts side by side.** A failure's date and the person's role on
  the company are shown together; the report never says one followed from
  the other.
- Companies register rows come from the old estate's tables; the original
  monthly file is not held, so those rows cite the row, not a document.

## Settings, not findings

`YOUNG_DAYS = 730` (under 24 months registered); `CHURN_DAYS = 365` and
`CHURN_AT = 2` (two or more current directors appointed in the last year);
`AT_START_DAYS = 30` (directors appointed within 30 days of registration are
the first board and not churn). Arthur may rule other figures.

## The checkpoint, 2026-10-21

Twelve real subjects (`checkpoint.list`) through `python -m products.report
render REF --template insurance`: seven person starts (a director appointed
before a liquidation; one appointed after it; a director with a Gazette
prohibition; one with a Gazette bankruptcy; a professional director, 75
directorships; a shareholder of record; a society officer) and five company
starts (in liquidation; in receivership and liquidation; going with three
directors appointed this year; registered June 2025; restored to the
register). All twelve printed, none refused, no rule broke; built in 0.3 to
5.5 seconds each. What fired, as an underwriter would want it: the
director on the board when the liquidator was appointed, red; the director
appointed three years after, amber with both dates; the liquidated and the
receivership companies red on their status and their own Gazette notices;
the churning board amber (three of four directors from November 2025); the
young company amber; the restored company amber on its register events.
Every report blocked the safety record.

Two faults the checkpoint found, fixed before the close: a 2019 winding-up
application dated a company's failure three years before its liquidator
was appointed (fixed: an appointment dates a failure first); and a
contested group filed the shareholder's own company near, so its
liquidation read as a namesake's (fixed in the template, as above).

Read against the Gazette source file (the lane's export, fields only, never
the text): notice 2026-al3431, published 22 June 2026, names the company,
says the shareholders appointed, and holds 16 June 2026, the row's
appointment day; notice 2022-al2162, published 2 June 2022, names the
company, says the court appointed, and holds 31 May 2022; prohibition
2019-ot857, published 25 February 2019, holds 8 January 2019, the row's
start (its end, 8 January 2023, is the lane's reading of the period, not a
date the text holds).

## Against the old estate's requirements (2.7)

MC-I2, the Gazette events on the company: built (insolvency-event,
register-events). The sister-company receivership through the Gazette and
shared directors: built from a person (sister-company-failure, dated),
blocked from a company. WorkSafe's prosecution facts, derived from the
release texts at a reported tier: not built, no lane (carded). The
change-of-trade flag: blocked, the change history unpublished. MC-I1 (a
company's dated press timeline) and MC-I3 (semantic incident recall): the
press graph is parked; the "articles mentioning" section comes with step 7.6.
