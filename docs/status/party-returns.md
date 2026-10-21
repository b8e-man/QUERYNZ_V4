# party-returns: where it stands

**Date:** 2026-10-21. **Step:** 4.1, the party donation and loan returns
lane, `registers/party_returns/`. **Merge request:** `reconcile-1` (after
`party-returns-5`, merged).

## Done

- Tranches 1 to 5 merged (`party-returns-1` to `-5`).
- Ruling 66 (Arthur, 21 October 13:00), session `reconcile-1`:
  `reconcile.py` holds `RECONCILE_TOLERANCE_CENTS = 10000`. Wherever the
  lane holds parts to a printed total (the declaration's parts to its
  total; Part H + Part I to Total (H + I); Part A's rows to the
  declaration's Part A and `TOTAL FOR PART A`; a donor's dated rows to its
  aggregated total; Part H's loans to Part H and `TOTAL FOR PART H`), a
  difference below $100 is reconciled and the row carries `issue` (signed,
  parts minus printed, and which parts); $100 or more is set aside as
  before. The printed total is published. `issue` is the last column of
  `pub.party_return_totals`, `_donors` and `_loans`; `check.py` counts the
  issue rows. Pairing heuristics (a page subtotal, a misread total mended)
  stay to the cent.
- Replayed on all 152 landed returns, no fetch, no model: 34 set-aside
  lines carried a sum before; **1 became reconciled with an issue**
  (National 2023 Part A, `765c53fbeb28`: +0.01 against both printed
  totals; 182 rows published, Part A now 53 returns, 1,315 rows, set
  aside 24). 1 more is within $100 on its sum but stays aside for another
  fault (`78441dc2a23e` Part H: $50 read against a nil Part H, no lender
  read). **32 stay unreconciled**: 31 at $100 or more, and one $1.00
  declaration (`6c6292569369`) whose parts were not read. Largest
  difference admitted: $0.01. Nothing at or above $100 moved.
- Sample: National 2023 and Heartland 2022 ($5,000, set aside) renamed
  for their cases; Legalise Cannabis 2019 added. Tests either side of
  $100 and at exactly $100 for each sum (`tests/test_reconcile.py`).

## Set aside, carded

- Part A on 24: as `part-a-is-set-aside-on-thirty-three-returns`, less
  National 2023.
- Declarations on 4 (`seven-pixel-…`); Heartland 2022 ($5,000); loans and
  Part H as before.

## Next

1. The integrator queues the re-reads (`replay rereads`); the lane replays.
2. Conservative 2017 and ACT 2018: one donor's numbered dated rows.
