# Healthcare operator governance: known limits

Template `healthcare` 0.1, use case 11. What the report cannot see, stated
to the reader. Checked on 2026-10-21 against twelve real subjects on
`querynz_v4` (the checkpoint, below), on the shape's third tranche
(`session/report-3`, raised, not yet merged: this template names its
`officers` and `chain` reaches, its `own` filter, `company_states` and its
not-held keys, so it loads only on that shape). Each line is a limit
accepted for now; the card that would lift it is named.

## What it cannot see

- **The retirement villages file.** Which company operates a village, the
  village's statutory supervisor and when the supervisor changed are in no
  published register. The companies lane carries 512 village rows in
  `pub.companies` (register `retirement_village`: name, number, status,
  registration day, from the old estate's tables) and nothing joins a
  village to an operator: no officer, holder or office sits on a village,
  and the only links are 164 near `company-name@1` pairs. A village row
  reached by a name it shares is listed with the namesakes; a report
  started from a village row lists no officer and every officer check
  blocks. The flag `retirement-villages` is **blocked, never clear**, red.
  (`the-retirement-villages-file-holds-no-operator-or-supervisor`)
- **The charities register.** The lane's reading (`session/charities-3`)
  publishes `pub.charities`, `pub.charity_officers` and
  `pub.charity_returns`, with the financial fields under the ruling of
  14 August 2026, and has not merged: the views are not on the database,
  and the report's catalogue knows none of them, so a template naming them
  is refused when loaded. The template names the register as not held in
  its governance and charity-returns sections; `charity-arm`,
  `charity-returns`, `charity-audit-opinion` and `charity-return-filed`
  are **blocked, never clear**, and `disqualified-officer` names the
  register's own disqualification marker as not held. The rules already
  read the three views by name (period, tier, income, expenditure,
  surplus, assets, liabilities, equity, audit and opinion, newest first;
  the officer's `disqualified`); they run the day the template reads them.
  Even then a charity is reached only where the links lane joins its
  officers by name and its number to its companies-register row: neither
  join exists yet. (`the-report-cannot-reach-the-charities-register`)
- **A charitable trust board's trustees.** The companies register lists no
  officer on any of its 35,599 charitable trust board rows; the trustees
  are filed with the Charities Register. Started from a trust board (an
  operator's charity arm, such as Ryman Healthcare Charitable Trust), every
  officer check blocks and says why. The same holds for an incorporated
  society's companies-register row: its officers are under its row in the
  societies register, and the flags say to start there.
- **The health regulators' registers.** The Health and Disability
  Commissioner's decisions, certification audits of rest homes and
  hospitals, the Ministry of Health's provider registers and the Aged Care
  Commissioner's reports are not held; nor are court judgments, the
  tribunals, WorkSafe's prosecutions or the Commerce Commission's cases.
  `hdc-decisions`, `certification-audits`, `provider-registers`,
  `aged-care-commissioner` and `court-judgments` are **blocked, never
  clear**. Nothing in a report says anything about care quality, a
  complaint, a breach of the Code of Rights or a certification: no such
  finding is a finding of none.
- **Those registers by name in the memo's not-held line.** A section may
  name only the catalogue's not-held keys, and there is none for the
  villages file, the Commissioner, certification, the provider registers
  or the Aged Care Commissioner; the last section's text and the flags name
  them. (`the-not-held-list-has-no-key-for-the-health-registers`)
- **What an organisation does.** The registers carry no industry. A company
  is called care or retirement living only because its registered name
  carries such a word (care, lifecare, health, hospital, rest home,
  retirement, village, aged, senior, nursing, living, lifestyle,
  residential): a sign to read, never a finding. A rest home named for a
  street or a family is not counted; a "village" of shops is.
- **Whose subsidiary a company is.** An officer's other care-named company
  that carries the entity's own leading name word ("BUPA RETIREMENT
  VILLAGES" beside "BUPA CARE SERVICES NZ") is counted apart and does not
  raise the overlap amber; the register does not say it is a subsidiary,
  and a subsidiary under another name ("KARINA REST HOME LIMITED" under
  Heritage Lifecare) is counted as another operator.
- **Officers past the walk's limit.** From a company or a society its first
  twelve officers are followed one step to their other current roles. A
  board of thirteen leaves one unread, and every officer check
  (`disqualified-officer`, `officer-bankruptcy`, `officer-overlap`,
  `officer-company-notices`) blocks; the limit counts past officers too.
  (`the-officers-reach-counts-past-officers-against-its-limit`)
- **Through an officer, near.** An officer's other role is the officer's
  connection, not the entity's: every row in the overlap section is near.
  A prohibition or bankruptcy on an officer's record is red only where the
  officer's group is not contested, the officer is current on the entity,
  is not a hub, and the prohibition is in force; at the checkpoint every
  officer followed from Arvida sat in a contested group, so such a notice
  there would show amber.
- **Past roles.** The companies file lists current roles only: an overlap
  that ended, a board that turned over, or a company an officer left
  before it failed, is not seen. `past-roles` is blocked and
  `officer-company-notices` never clears.
- **A blank is not a clear.** "None found" in a section is the most a report
  says of the registers it read; it is not a clear of the registers it did
  not, and a flag blocked for want of a register is never shown as clear.
- **A society's Gazette notices.** They are filed under the society's
  companies-register row, which the societies register's row does not
  join; from a societies start `insolvency-notice` blocks.
- **The companies change history** before 16 August 2026 (former names,
  earlier directors) is not held, and held but unread since.

## Settings, not findings

`YOUNG_DAYS = 730` (under 24 months registered). `FILE_WITHIN_DAYS = 183`
(a charity files within six months of its balance date) and
`PERIOD_SLACK_DAYS = 31` (a return is the period's when its period end is
within a month of the balance date). `CARE_NAME`, the words above, and
`LEAD_SKIP`, the words a leading name word skips. Arthur may rule others.

## The checkpoint, 2026-10-21

Twelve real subjects (`checkpoint.list`) through `python -m products.report
render REF --template healthcare` on the report-3 shape: seven operators of
aged care and retirement living (Arvida, Ryman, Summerset, Oceania,
Metlifecare, Bupa Care Services, Heritage Lifecare), two charitable trust
boards (Ryman Healthcare Charitable Trust, the charity arm; Presbyterian
Support (Northern), which runs Enliven), a society (Presbyterian Support
New Zealand Incorporated), a retirement village developer in receivership
(Shundi Tamaki Village Limited) and a director who sits on two operators'
boards (from her row on Arvida). All twelve printed, none refused, no rule
broke; built in 0.1 to 6.7 seconds each.

What fired, as an investor would want it: officer overlap amber on six
operators. Arvida's director Norah Barlow, on its board from 1 February
2025, is a director of Heritage Lifecare from 13 December 2018 and of its
rest-home companies; Bupa's director Julie Sellar is an officer of the Aged
Care Association from 6 August 2022; every Metlifecare director followed
sits on another care-named company. Summerset's overlap is info, and one of
its directors' other companies, Wynyard Group, had a liquidator appointed
8 February 2017, amber, with her role there dated beside it. Shundi Tamaki
Village red on its status (In Receivership) and on six Gazette notices
(a winding-up application to be heard 27 February 2026; administrators and
receivers appointed 4 March 2026). From the director's own row, the overlap
counts 25 organisations through her contested group's rows, 16 care-named,
near. Both trust boards and the society blocked every officer check (no
trustee listed; one officer past the limit), and none cleared. Every
report blocked the charity checks and every register not held.

Three faults the checkpoint found, fixed before the close: three officer
checks cleared a charitable trust board and a village row on zero officers
(fixed: no officer listed blocks, and says where they are filed); a
contested group dropped the director's other roles from the overlap
(fixed: counted near, apart); and an operator's own subsidiaries counted as
other operators (fixed: counted apart by the entity's leading name word).

Read against the source record (fields only, never the text): Gazette
notice 2026-aa1210, family "insolvency: administration", published
5 March 2026, two records, as the memo dates it.

## Against the old estate's requirements (2.5)

MC-H1, the operator web with its roll-up: the officers reach and the
holding chain two up (Arvida's holder of record Stonepeak Alps Bidco, and
its holder Stonepeak Alps Holdco, near by name); the villages it runs are
not held. MC-H2, the charity's financial claims: written in the rules,
blocked until the charities register is reachable. MC-H3, officer overlap
across the web: built from a company and a society (`officer-overlap`,
dated, hubs flagged) and from a person. MC-H4, adverse-coverage recall: the
press is parked; the "articles mentioning" section comes with step 7.6.
Statutory-supervisor churn: not held, as the old estate found. The
Health and Disability Commissioner's decisions: to acquire (plan 5.3).
