# Banking director history: known limits

Template `banking` 0.1, use case 3. What the report cannot see, stated to
the reader. Checked on 2026-10-20 against twelve real subjects on
`querynz_v4` (the checkpoint, below). Each line is a limit accepted for now;
the card that would lift it is named.

## What it cannot see

- **Past directorships and holdings.** The companies file lists current
  roles only. Measured 2026-10-20: none of 1,185,805 director rows carries
  an end date; 9,056 left the file since July 2026 with none; the 1,066,680
  removed companies keep 4,888 director and 6,300 holder rows between them.
  A company the person left, or that was struck off with them on it, is not
  seen, nor its liquidation. So the history checks (company-endings,
  insolvency-notices, repeat-insolvency, left-before-notice,
  register-removals) fire on what they see and are otherwise **blocked,
  never clear**; the flag `past-roles` says so on every report. This is the
  heart of use case 3 and the largest limit here. When a view publishes
  past roles with end dates, `HISTORY = True` in `rules.py` turns the clears
  back on. (`the-companies-file-holds-no-past-directorships`)
- **Who has lent against the companies.** The Personal Property Securities
  Register is not held (the interface has waited on approval since 19
  September); the flag `securities-register` is blocked, never clear.
- **The people behind a company, from the company.** Started from a
  company, the report lists its directors and holders of record and the
  Gazette notices on it, and does not follow the people: their other
  companies, their prohibitions, the people they sat beside and their
  society roles are not read. Those checks are blocked, and the sections
  for the person print "none found", which is not a clear. Start a report
  from each person listed. (`a-company-start-does-not-follow-its-officers`)
- **Every company of a busy director.** The walk lists 40 companies and
  reads the notices and officers of 12; past those, a status shows and the
  rest is unread. The flag `walk-coverage` fires and the clears that need
  them block. (`the-walk-reads-twelve-companies-and-lists-forty`)
- **A bankruptcy.** Gazette bankruptcy notices are published but no link
  rule joins one to a person; the check is always blocked: a blank there
  is not a clear. (`bankruptcies-and-appointments-are-not-in-pub-names`)
- **When a role ended.** No role carries a filed end date, so
  left-before-notice (a role that ends in the year before an insolvency
  notice on the same company) cannot fire on today's data; it is kept for
  when end dates are published.
- **Whether two people beside the person are one.** A name seen on two of
  the person's companies is two rows that share a name; shared-boards
  counts names, never people.
- **A Crown entity by its own name** (Health New Zealand) is not flagged as
  the Crown. (`a-crown-entity-holder-is-not-flagged-as-the-crown`)
- **The start row's own company in a contested group** can be graded near,
  and the flags then call it a namesake's. Seen once in twelve.
  (`a-contested-groups-near-row-can-make-the-start-rows-own-company-near`)
- **Current roles first.** A section lists newest first; it cannot put
  current roles first. (`a-section-cannot-put-current-roles-first`)
- **The Insolvency Register, court judgments, the Charities Register, the
  limited partnerships register (a partnership's partners), financial
  service providers, sanctions lists, land titles, the Commerce
  Commission's cases.** Not held; named in the last section and in the
  flags that would read them.
- **GST age.** The old young-entity rule read GST registration; it is not
  held, so a company's own registration date stands in.

## How to read it

- **The person** is the row the report starts from and the rows a rule
  confirms are the same person. Every other row under the name is a
  **namesake**, listed first and apart with the reason it is only near.
  Past fifty namesakes the report says it is partial. A namesake's
  companies and notices are amber at most; only the person's own are red.
- **How each company ended** is the companies file's own status (in
  liquidation, in receivership, removed, deregistered, dissolved), and
  beneath each company the Gazette's notices on it with their own dates: a
  liquidator's appointment, a receiver's, administrators', a winding-up
  application's hearing day, a creditors' meeting, a removal's last day for
  objections, a restoration, an overseas company ceasing (Companies Act
  s 341), a society dissolved, a partnership deregistered. A removal is not
  an insolvency.
- **Two facts with dates sit side by side.** A notice is listed with its
  date and the person's role with theirs; the report never says one
  followed from the other.
- **The people beside** are the other directors and holders of record on
  the person's companies, always near.
- **A holding is a holding of record.** A nominee, trustee or company
  holder is flagged and shown as the register states it.
- **Hubs:** a professional director (50 or more directorships), a nominee,
  the Crown, a registered office shared by 50 or 1,000 companies.
- **Absence is not a finding.** "None found in …" is the most it says.
- **Start from a person row** (a director or shareholder), or from the
  company. A donation or a society row walks the person's group when a link
  confirms one, and the company checks block.
- Companies register rows come from the old estate's tables; the original
  monthly file is not held, so they cite the row.

## The checkpoint, 2026-10-20

Twelve real subjects (`checkpoint.list`), chosen from the tables to cover
the cases: a director of two companies both in liquidation (CRANELAB); a
director in a contested group with five failed companies around him and a
near prohibition; a professional director of 60 companies (walk short);
a director confirmed to a prohibition that ended in 2023; the most shared
first and last name among directors (61 namesakes, a contested group of
337 rows, declared partial); a director whose role left the file on a
company in liquidation; a shareholder of a company in liquidation in a
contested group; a company in receivership and liquidation; an Australian
company removed under s 341; a deregistered limited partnership; a society
officer who is also a company director; a party donor row confirmed to a
director's group. All twelve printed; none was refused by the shape's
presentation rules; built in 0.3 to 5.5 seconds each, and 0.6 to 8.4 on a second run while the box was busier. Read against the
Gazette source file: CRANELAB PROPERTY VALUATION SOLUTIONS LIMITED's
liquidators appointed 15 March 2024 (published 18 March); CRANELAB
LIMITED's appointed 26 March 2024 (published the same day); the
prohibition under s 385(3) for two years six months, 9 November 2020 to 9
May 2023. Against the old requirements (MC-B1 to MC-B4 in
`data-layer/docs/USE_CASE_PROGRAMME.md`): occurrences with confirmed and
near apart, over fifty namesakes declared partial (B1); insolvency events
on companies the person has a role on, confirmed and near visibly apart
(B2, current roles only); prohibitions with namesakes labelled (B3); company
age by registration date, not GST (B4). Failures carded: five on the report
lane, one on the companies lane (above).
