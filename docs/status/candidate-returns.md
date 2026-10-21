# candidate-returns: where it stands

**Date:** 2026-10-21. **Step:** 4.1, the candidate donation and expense
returns lane, `registers/candidate_returns/`. **Merge requests:**
`candidate-returns-1` and `-2` merged; `reconcile-1` raised (ruling 66).

## Done

Measured on all 1,105 in-window returns (2020, 2022 Tauranga, 2023),
replay only (`python -m registers.candidate_returns.replay
run|compare|shape|rereads`), with the 60 scans read on 20 October as the
sample (ruling 62):

- **Totals:** 412 rows, 693 set aside; the catch log reconciles. Against
  the spreadsheet: 391 equal to the cent, 13 differ, each judged with
  evidence (card closed): 5 amendments the listing agrees with us on, 5
  the Commission's typing, 2 its own unexplained figure, 1 return that
  contradicts itself.
- **A scanner's text layer** (a page under a full-width picture) stands
  only on its printed total: two misreads the Commission had right are set
  aside for a page reading.
- **Part A:** 221 donor rows on 100 returns (88 typed, 12 from pixels),
  each part adding to its printed total and the declaration; 26 parts set
  aside (carded). A candidate copy without the part's heading is known by
  `TOTAL FOR PART A`; a scan's Part A comes from its stored page reading
  (`pixels.py`) and is refused when read column by column; a Part A the
  declaration left blank is no longer taken for nil.
- **Part D and H:** one return declares Part D ($140), none a loan: no
  reader built.
- **Re-reads:** `replay rereads` lists 668 returns, 6,287 pages (hash,
  stage, pages), the queue for when the build is done.

## Ruling 66 (reconcile-1)

Parts within $100 of a printed total are published on the printed total
with `issue` (the signed difference and which parts); $100 or more stays
set aside. One constant, `reconcile.RECONCILE_TOLERANCE_CENTS = 10000`;
the declaration's pairing is sought to the cent first, the tolerance only
where none holds. Replayed on all 1,105 (no fetch, no model):

- 1 set-aside became reconciled with an issue (`13e5f25572ae`, expenses
  F + G $0.03 over the printed $337.23; the Commission's spreadsheet has
  the parts' $337.26, so the outside check now shows 14 differ, not 13).
- 5 published returns had a 1-cent difference passed silently by the old
  rule (`<= 0.011`); each now carries its issue.
- Stay unreconciled for a sum: 6 declarations (nearest `fde6a63114d2`,
  $117.30) and 16 Part A parts (nearest $1,650). Largest admitted: $0.03.
  No Part A was admitted.
- `check.py` prints the issue rows; two sample cases; 41 tests green.

## Set aside, carded

- 668 returns wait on page readings (`the-candidate-return-scans-…`).
- 26 Part A sets aside; the 2022 Tauranga by-election has no Commission
  figure held.

## Next

1. When the build is done and the readings land: `replay run`, `compare`,
   rebuild.
2. Part A scans read column by column want a cell-scale re-read.
