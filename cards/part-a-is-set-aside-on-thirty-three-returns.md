# Part A is set aside on forty-five read returns (was thirty-three)
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-19
updated: 2026-10-20 (party-returns session 3)

A return's donors are published only when its Part A rows add, to the
cent, to the declaration's Part A and to `TOTAL FOR PART A` where read.
Once `qv4-read-pages` had read the 41 returns' pages, the live load held
137 rows: Part A published on 25 (580 donor rows), nil on 62, set aside on
50. Session 3 added the page reader's in-line rows (`schedule._inline`: a
row whose figure ends its line, or a cell and then `Yes $ x` on the next
line) and three guards, measured over all 152 landed returns, replay
only: **published on 30 (679 rows), nil on 62, set aside on 45.** Five
returns came off the list (Green 2017, NZ First 2024 and its replaced
copy, Opportunity 2025, National 2022's unlisted copy); no name already
published changed except two that lost an address word ("…, Floor",
"…, Shed"). Of the 45, 31 are current in-window returns. By cause:

- **22 (19 in window), the cells and the figures do not pair.** The page
  reader went down the page column by column (all names, then all
  amounts: Advance NZ 2020, ONE Party 2020, Te Pāti Māori 2023 and 2025,
  NewZeal 2023, Freedoms NZ 2023 p2), or a text-layer row runs over a page
  break (ACT 2019; Labour 2020, 2023, 2024; NZ First 2023), or a numbered
  list whose numbers may be the reader's own, or a page where the reader
  lost a donor's name so the next line's date column stood in its place
  (Labour 2018; refused by the new row-number guard). Pairing these by order is
  what the lesson `a-shifted-name-still-adds-up` forbids. Fix: a re-read
  of the table at cell scale (the page reader on each row's crop), which
  is a job for the scheduler's page reader, then the lane replays it; the
  page-break carry is lane code and comes after.
- **14 (7 in window), no rows found.** The donors are on an attachment
  the region does not reach ("See attachment for full listing", National
  2024; NZ First 2021 and 2022), or the table page came back with no
  figures. Fix: find the schedule by its own heading or total.
- **4 (2 in window), a cell with no name before its address** (Green 2019,
  2020; National 2025; ACT 2018): the name sits on the line above.
- **4 (2 in window), the rows add to something else.** National 2023: 182
  rows add to $4,015,899.35 against a printed $4,015,899.34; Labour 2017's
  figures are corrected by hand (card
  `labour-2017-the-page-reader-drops-a-handwritten-correction`).
- **1, nothing to reconcile against** (NZ Outdoors and Freedom 2022).

`select * from party_returns.set_aside where stage = 'part-a'` lists them.
