# Property developer due diligence: known limits

Template `property` 0.1, use case 12. What the report cannot see, stated to
the reader. Checked on 2026-10-21 against twelve real subjects on
`querynz_v4` (the checkpoint, below). Each line is a limit accepted for now;
the card that would lift it is named.

## What the serial pattern is here

The old estate's SPV-serial rule (USE_CASE_REQUIREMENTS.md 2.6, MC-P1):
the same principals, sequential special-purpose companies, a liquidation
after settlement. Here, for each **principal** (from a company, each of its
current directors; from a person, the person), the companies under them,
two or more of which **failed**: a liquidator, receiver or administrator
appointed, a winding-up application, a creditors' notice, a deed of company
arrangement, each dated from its Gazette notice; or a removal from the
register where the company has in fact ended, which is not an insolvency.
`serial-pattern` sets them out in the order registered, each with its life
from registration to failure, beside the principal's going companies with
the gap in days. `earlier-failure` sets each failure beside the entity's
own start.

- **The window is the reader's** (ruling 65, as the construction template
  reads it): `window_days`, a parameter the template declares, days
  either side of the failure (`--set window_days=365`,
  `?window_days=365`). With none set no cut is applied and every gap is
  shown, nearest first, with how many fall within 90 and 365 days.
- **Severity.** Red only on a person's own confirmed companies with two or
  more insolvencies and the person no hub. Through a director (from a
  company) a director's other company is the director's connection, near,
  so amber at most; start a report from the director for red. Every
  failure a removal: info.
- **An intention to remove is not a removal.** A Gazette "intention to
  remove" on a company the file still calls Registered lapsed (the company
  filed, or someone objected), and is no failure. The checkpoint found
  this: BROOKS HOMES LIMITED had notices in 2008 and 2011 and is
  registered today; the first version counted it, and two subjects'
  first results (5 and 9) rested on such notices.
- **Two facts side by side.** A failure and a later company's start are
  set beside each other with the gap; nothing here says one followed from
  the other.

## What it cannot see

- **Land titles, overseas investment, consents, courts.** Land titles and
  their company side (LINZ), the Overseas Investment Office's decisions,
  building consents and council minutes, court judgments, the Personal
  Property Securities Register, the Insolvency Register, the Real Estate
  Authority's decisions and the licensed building practitioners register
  are not held. Nothing here says what land a developer holds, what it was
  consented to build, or whether a buyer or a body corporate sued it. Each
  has a blocked flag, never clear. Three have no key in the shape's
  not-held list (`the-not-held-list-has-no-key-for-the-property-registers`).
- **Past roles and removed companies.** The companies file lists current
  roles only, and a removed company carries no directors in it: of 4,960
  director rows on removed companies, 4,941 are not in the latest file
  (measured 2026-10-21). A principal's special-purpose company that was
  liquidated and then removed, the end of the SPV pattern, is not seen
  from the principal. So `serial-pattern`, `earlier-failure`,
  `possession` and `insolvency-notices` fire on what they see and are
  otherwise **blocked, never clear**; `past-roles` says so on every report.
  A blank in the project history is not a clear.
- **A director the links lane joins by name alone.** The officers reach
  follows each director's confirmed group. Of 12,719 current directors of
  registered companies named "develop…", 4,602 have no confirmed link to
  another director row and 1,956 of those have a near one: for them the
  project history is empty, and `history-reach` blocks and says to start
  a report from the director. Checkpoint subject 3 (GORING DEVELOPMENT
  LIMITED) is one: its director's two liquidated development companies are
  not shown. (`the-officers-reach-does-not-list-an-officers-near-links`)
- **Twelve directors, forty rows each.** Past the walk's limits the history
  and the notices are partial, and the checks say so.
- **Holders are listed, not followed.** A holder of record is never called
  an owner, and for whom a nominee or a trustee holds is in no register.
- **The companies above.** The chain is followed two up; the directors of a
  company above and the Gazette on it are not read
  (`the-chain-reach-reads-nothing-on-the-companies-above`).
- **Charities.** Where a trust behind a developer is a registered charity,
  its officers are not reachable: the catalogue knows no charities view yet
  (the same ask as healthcare-1's `the-report-cannot-reach-the-charities-register`).
- **Offices.** A registered office fifty or more companies share, or whose
  lines name an accountant, a lawyer or a formation agent, or that the
  file says is kept care of another, is a hub: a company met there means
  nothing on its own, and `shared-office` does not compare it. Only 5,551
  of 855,489 registered offices in the latest file name such a firm; most
  professional offices are hubs by count instead. A liquidated company's
  office is usually its liquidator's, so from a company a failed company
  at the entity's office is amber and says it cannot tell whether that was
  its office before it failed (the change history is not held).
- **Mortgagee possessions** are read where the Gazette names a company as
  mortgagor and the gazette lane matched it to the register: 306 of 339
  company mortgagors, of 3,002 notices (2,441 print no mortgagor the lane
  can read, 136 name a person, held privately). A person mortgagor is
  never shown. Where a company here is the lender, the flag is info.
- **The Gazette is daily and the file monthly.** A liquidation the Gazette
  published after the latest file is shown red with the file's status
  beside it (subject 3: liquidator appointed 12 August 2026, the August
  file still Registered).
- The entity is the row the report starts from and the rows a rule
  confirms are the same; a namesake is set apart with its reason. No
  residential address is held in any view read. Companies register rows
  come from the old estate's tables and cite the row, not a document.

## The checkpoint, 2026-10-21

Twelve subjects in `checkpoint.list`, each rendered with `python -m
products.report render REF --template property` (0 to 5 seconds each), none
refused, no rule broken. Read against the source rows (a liquidation's
appointment day and appointer, a director's current companies and their
statuses).

| # | Subject | What fired |
| --- | --- | --- |
| 1 | TREEBIRD PROPERTY LIMITED, two directors, trustee-company holders | serial-pattern amber (a director with 12 insolvent companies of 34), earlier-failure, insolvency-notices on 12 of the directors' companies; holding-chain two companies up; office a hub (79 companies) |
| 2 | RIF DEVELOPMENT LIMITED, one of the same directors | the same pattern; history-reach info (33 other companies reached) |
| 3 | GORING DEVELOPMENT LIMITED, one director with no middle name | entity-status red (Gazette liquidation newer than the file); history-reach blocked: the director's liquidated predecessors are not reached |
| 4 | KERVIL DEVELOPMENT LIMITED, the same director's earlier company, in liquidation | entity-status red, insolvency-notices red |
| 5 | VOLKAN DEVELOPMENTS LIMITED, mortgagor in two possessions | possession red (entered 7 and 15 July 2026); sole-vehicle; office kept care of an accounting firm, a hub |
| 6 | COLLABORATION DEVELOPMENTS (6 KAWAKA STREET) LIMITED, an address-shaped name | young-entity, serial-pattern amber; the name is shown in the sections and masked in the flags; 511 rows past the walk's limit, history-reach blocked |
| 7 | WOLFBROOK DEVELOPMENT LIMITED | serial-pattern amber; a liquidation 74 days before its start |
| 8 | MCCONNELL PROPERTY LIMITED | serial-pattern amber (a director with 6 insolvent companies of 37: receiverships of May 2018 across one group) |
| 9 | JCSB DEVELOPMENT GP LIMITED, young, one person director and holder | earlier-failure (a liquidation 206 days before its start), young-entity, sole-vehicle |
| 10 | GORING's director, from the person | insolvency-notices red on the one company reached; history-reach blocked |
| 11, 12 | TREEBIRD's two directors, from the person (groups contested) | group-standing amber; every other row near; serial-pattern amber |

Fixed at the checkpoint: the lapsed intention to remove (above); a stale
count in the serial text; a person whose group reaches one company read as
a full history; an office kept care of another named apart from a
firm-named one. Carded: the three cards named above.
