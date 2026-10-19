# party-returns: where it stands

**Date:** 2026-10-20. **Step:** 4.1, the party donation and loan returns
lane, `registers/party_returns/`. **Merge request:** `party-returns-3`.

## Done

- Tranches 1 and 2 merged (`party-returns-1`, `-2`).
- Session 3 (`party-returns-3`), on the live load of 20 October after
  `qv4-read-pages` (queue rows 110, 111): 137 rows, none at stage `read`.
  - **Frozen site, re-measured:** 71 party-years equal (was 49), 1 differs
    (Labour 2017: the lane is wrong, a handwritten correction the page
    reader drops), 56 returns of parties not on the frozen site, 3 replaced
    originals beside an equal amendment.
  - **The Commission's by-year table** (`commission.py`, new): 117
    party-years equal to the cent, 5 differ (Labour 2017 the lane's; four
    the table's, each page read by eye), loans 0 differ; 11 rows whose
    returns are set aside at the declaration, 1 not tied.
  - **Part A's refused pages**, replay over all 152: published on 30
    returns (679 rows; was 25, 580), nil 62, set aside 45 (was 50). New
    route `schedule._inline`; guards: row numbers must climb, a cell's name
    is its first line, "see attachment" is a pointer, floor/shed/building
    open an address.

## Set aside, carded

- Part A on 45 (`cards/part-a-is-set-aside-…`, updated): 22 column-order or
  page-break pages (a cell-scale re-read is the scheduler's job), 14 with
  no rows found (attachments), 4 name-above cells, 4 sums, 1 nothing.
- Labour 2017 (`cards/labour-2017-…`); the Commission's four
  (`cards/the-commission-s-table-differs-…`).
- Loans on 4 and Part H on 6 (`cards/loans-are-set-aside-…`, not re-counted);
  ALCP 2025's amendment not held; 15 returns at the declaration; party labels.
- Queued for Arthur: National 2022, two returns, one listed (default:
  neither replaced).

## Next

1. Part A rows across a page break (text layer: ACT 2019, Labour 2020,
   2023, 2024, NZ First 2023), lane code.
2. Schedules outside the Part A heading: find an attachment by its own
   heading or total (National 2024, NZ First 2021, 2022).
3. Ask the scheduler for a cell-scale re-read of the column-order pages and
   of Labour 2017's declaration cells; the lane replays it.
