# candidate-returns: where it stands

**Date:** 2026-10-30 (candidate-returns-3). **Step:** 4.1, the candidate
returns lane, `registers/candidate_returns/`. **Merge requests:** `-1`,
`-2`, `reconcile-1` merged; `candidate-returns-3` raised.

## Done

- Read returns as before: 413 rows published (2020 236, 2022 3, 2023
  174; 5 of them replaced), the catch log reconciling; the outside check unchanged.
- **The Commission's rows where no return is read** (this tranche):
  `pub.candidate_return_totals` gains one row per row of the newest
  summary spreadsheet with figures that no read current or unlisted
  return is placed on: 675 (2020 363, 2023 312). `read_from`
  'commission'; the Commission's figures in `commission_*`; the return's
  columns NULL; key `<spreadsheet sha256>/<row>`; cited by hash, `sheet`,
  `sheet_row`. The replacement rule is the view's (`publish.sql`). The 15
  "Return not received" rows are not published. No candidate has both.
- Measured against the frozen 2026-10-29T0616 (base and branch built in
  scratch from the same listing): the not-held cause 5,133 → 3,189:
  electorate 776 → 3, electorates 206 → 2, home 627 → 311, subject
  1,570 → 919, donor 1,412 and pickers 542 unchanged. Rebuilt-side-wrong
  7,216 → 5,280.

## Remains

- Donor pages, pickers, person pages' donations received: Part A from
  the scans' readings, held under ruling 79. Not read here.
- Home race totals: 2017 in the frozen side, and party labels (site).
- Christchurch Central 2020: two Webbs; the template's join refuses.
- 9 published 2023 rows where the listing's figure differs from the
  spreadsheet's (the listing may carry an amendment; lesson
  `the-commission-s-spreadsheet-can-carry-...`): published as the
  spreadsheet says; worth a look when those returns are read.
- Site: the cite label and "$0.00" evidence text on a Commission row (card).

## Next

1. Integrator: merge; the load adds `commission.sheet`; install the
   proposed `qv4-candidate-returns-load` (spec).
2. When readings land: `replay run`, `compare`, rebuild.
