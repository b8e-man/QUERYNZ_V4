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
- **The Charities Register, by number and by name.** The template reads
  `pub.charities`, `pub.charity_officers` and `pub.charity_returns`. A
  company's charity is reached by its business number, confirmed, with
  the officers and annual returns the register files on it (the figures as
  filed, newest first, never added across returns). A charity officer row
  that carries a person's name is listed near: no link joins the
  register's officers to any other row yet, so each is a namesake's until
  a rule confirms it, and a rule over such a row is amber at most. A
  charity met only by such a row is named, not walked: its returns are not
  read. (`charity-officers-are-in-no-link-and-no-name-row`, the links
  lane's)
- **A charitable trust board's trustees.** The companies register lists no
  officer on any of its 35,599 charitable trust board rows; the trustees
  are filed with the Charities Register. Started from a trust board whose
  charity carries its business number, the trustees are listed from the
  charity and the register's disqualified mark on each is read (red on one
  with no end filed); they are not followed to their other roles, so the
  overlap and Gazette checks over them block and say so. A board with no
  charity by its number blocks every officer check. The same holds for an
  incorporated society's companies-register row: its officers are under
  its row in the societies register, and the flags say to start there.
- **The health regulators' registers.** The Health and Disability
  Commissioner's decisions, certification audits of rest homes and
  hospitals, the Ministry of Health's provider registers and the Aged Care
  Commissioner's reports are not held; nor are court judgments, the
  tribunals, WorkSafe's prosecutions or the Commerce Commission's cases.
  `hdc-decisions`, `certification-audits`, `provider-registers`,
  `aged-care-commissioner` and `court-judgments` are **blocked, never
  clear**, each naming its register as the catalogue's not-held key does;
  the last section cites the five keys, so the memo's not-held line
  carries them, and the standing section cites the villages file's. Nothing in a report says anything about care quality, a
  complaint, a breach of the Code of Rights or a certification: no such
  finding is a finding of none.
- **An officer's near links.** A row the link rules join to an officer by
  name alone (a namesake's directorship, its company, the notices on it) is
  listed in the overlap and Gazette sections with the officer's reason and
  then the link's, rule the link's. `officer-overlap` and
  `officer-company-notices` count such rows apart, never as the officer's
  own, and never raise amber on them; a prohibition or bankruptcy reached by
  one is never red. A namesake's row alone gives info, never a clear.
- **The companies above.** The governance section lists the current
  directors of each company up the holding chain (two up) and the Gazette
  section the notices on it, each with the company's grade and its place up
  the chain. `insolvency-notice` sets an insolvency notice on a company
  above beside the entity's own and never counts it as one; no officer
  check reads the directors above.
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
not held. MC-H2, the charity's financial claims: read since 2026-10-21
from the charity's returns, as filed. MC-H3, officer overlap
across the web: built from a company and a society (`officer-overlap`,
dated, hubs flagged) and from a person. MC-H4, adverse-coverage recall: the
press is parked; the "articles mentioning" section comes with step 7.6.
Statutory-supervisor churn: not held, as the old estate found. The
Health and Disability Commissioner's decisions: to acquire (plan 5.3).

## The checkpoint re-rendered, 2026-10-21 (fix-templates-1, the Charities Register)

The same twelve subjects, before and after the template read the Charities
Register. None refused. The two charitable trust boards (Ryman Healthcare
Charitable Trust, Presbyterian Support (Northern)) now reach their charity
by business number, confirmed: 14 and 37 officer rows and 18 and 17 annual
returns. On both, `charity-arm` and `charity-returns` went from blocked to
fired (info), `charity-audit-opinion` and `charity-return-filed` from
blocked to clear (no modified opinion; a return held for the last period);
the officer checks still block, now saying the trustees are listed from
the charity, their disqualified mark read (none carried one), and not
followed. The director (subject 12): `charity-arm` from blocked to fired,
three charity officer rows of the same name, near; `disqualified-officer`
stays clear and now names the charity officer rows it read by name. The
operators, the society and the village row are unchanged: no charity by
business number.

## The checkpoint re-rendered, 2026-10-22 (fix-products-templates-1, the reaches)

The same twelve subjects, before (a clean copy of 2748790) and after. None
refused; no flag changed status or severity. The five health registers
now stand in every memo's not-held line, and the villages file under the
standing section; the five blocked flags name them as the catalogue does.
`officer-overlap` on eight subjects (the seven operators and the society)
now counts apart the roles an officer's near link
reaches (one to eight each, all `name-only`): a namesake's, never the
officer's own; before, they were listed and the flag did not say so.
Summerset's Gazette section gained one notice on a company two up its
holding chain (a removal, near by name, a nominee holder): the holder's,
not an insolvency, so `insolvency-notice` is unchanged.
