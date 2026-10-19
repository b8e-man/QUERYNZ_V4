# candidate-returns: where it stands

**Date:** 2026-10-20. **Step:** 4.1, the candidate donation and expense
returns lane, `registers/candidate_returns/`. **Merge request:**
`candidate-returns-1`.

## Done

Measured on all 1,105 in-window returns (2020, 2022 Tauranga, 2023),
replay only (`python -m registers.candidate_returns.replay run|compare|shape`):

- **Capture by hash** from the old folder, read-only, fetching nothing;
  the Commission's 58 listing pages and newest summary spreadsheet per
  election landed beside them (a challenge page kept as a .csv refused).
- **Four profiles proposed** (`profile-proposed.jsonl`): the return with a
  text-layer declaration, the scanned return, the listing, the summary.
- **The join:** 1,105 placed (1,049 by the listing's own link), none left
  abstaining; 15 originals replaced by the amendment the listing links.
- **Totals:** 372 rows, 733 set aside; the catch log reconciles. Against
  the spreadsheet: 353 equal to the cent, 11 differ (carded).
- **Part A:** 175 donor rows on 81 returns, each part adding to its own
  printed totals; the form's example row dropped (336); addresses only in
  `candidate_returns_private`. 20 parts set aside beside their rows.
- 22 tests; module and whole-repository fast tiers green.

## Set aside, carded

- 713 returns wait on a page reading of the declaration page (a scheduler
  job, `cards/the-candidate-return-scans-need-their-page-readings.md`).
- The 11 differences; the 20 Part A sets aside; the 2022 Tauranga
  by-election has no Commission figure held.

## Next

1. After the page readings land: rebuild, measure, then Part A from pixels.
2. Part A of the nine candidate-made copies (no form table).
3. Part D (overseas donors) and Part H's lenders, if the product needs them.
