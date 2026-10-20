# A struck-out total on a declaration is read as the total
kind: finding
state: closed
use-case: 1
session: disclosures
opened: 2026-10-20
closed: 2026-10-20

`form_check` differs on `ec-listing/2023-11-22/3a6748fb63ae` (Freedoms New
Zealand, received 22 November 2023, amended return received 22 April
2024): the table says $19,250.22, the form check took $26,066.66.

The total box was looked at (a crop of that box alone): $26,066.66 is
struck through by hand and $19,250.22 written beside it. The page reader
gives both figures and drops the strike, and `form.total` takes the first
figure under the label. The table is right.

The Commission's link is to the `-v4` file; `-v3` is held and no row
links it. A reading cannot see a strike, so the fix belongs in the check,
not the reader: where the box holds two figures and one equals the table,
say "equal, a second figure in the box" rather than "differs". Not worked
here; the table's amount stands. The amount is under the $20,000 floor
(`at_or_under_threshold`), as the Commission lists it.

Closed 2026-10-20 (disclosures-3). `form.total` now keeps every figure in
the box (`figures`, the label's line and the lines under it up to the next
label), and `read.form_check` says "equal, a second figure in the box" where
the box holds two figures and one equals the table, keeping that figure as
`form_total`. Measured on all 276 linked scans: this row is the only one
held so; `differs` falls from 3 to 2 on that account. A second struck-out
box is known (`ec-listing/2026-10-07/2d24e90d7db2`: $25,000 struck, $44,000
written, the table $44,000), but its page reading dropped the box, so it is
set aside for a reading (ruling 62) and the rule will meet it then.
