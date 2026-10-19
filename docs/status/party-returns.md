# party-returns: where it stands

**Date:** 2026-10-19. **Step:** 4.1, the party donation and loan returns
lane, `registers/party_returns/`. **Merge request:** `party-returns-2`.

## Done

- Tranche 1: the declaration from pixels (`party-returns-1`, merged).
- Tranche 2 (`party-returns-2`), measured over the 152 landed returns,
  replay only: Part A donors published whole on 22 returns (476 rows), nil
  on 44, set aside on 33; Part H loans on 6 (9 rows), nil on 87, set aside
  on 6; 14 returns replaced by amendments, as the Commission's listing
  states them. Addresses only in `party_returns_private.addresses`.
  New: `schedule.py`, `donors.py`, `loans.py`, `amendments.py`,
  `private.sql`; tables `donors`, `loans`, `amendments`; views
  `pub.party_return_donors`, `pub.party_return_loans`; `returns` gains
  five columns, the totals view gains them and `replaced_by` at its end.

## Set aside, carded

- 41 returns at stage `read`: rows 95/96 read page 1 only; 645 image
  pages still owed (`cards/forty-one-party-returns-…`, updated).
- Part A on 33 returns (`cards/part-a-is-set-aside-…`); loans on 6
  (`cards/loans-are-set-aside-…`); ALCP 2025's amendment not held.
- 7 pixel returns at the declaration; 27 unresolved party labels.
- Queued for Arthur: National 2022, two returns, one listed (default:
  neither replaced).

## Next

1. The page-reader job over all image pages of the 41 (scheduler module).
2. Part A's refused pages: a cell-scale re-read of column-by-column pages,
   rows across a page break, schedules outside the Part A heading.
3. The outside check against the Commission's by-year table: the listing
   is now landed by hash and carries each party-year's totals.
