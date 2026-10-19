# Part A is set aside on thirty-seven read returns (was forty-five)
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-19
updated: 2026-10-20 (party-returns session 4)

A return's donors are published only when its Part A rows add, to the
cent, to the declaration's Part A and to `TOTAL FOR PART A` where read.
Session 4, measured over all 152 landed returns, replay only
(`python -m registers.party_returns.replay`): **published on 38 (843
rows; was 30, 679), nil 62, set aside 37 (was 45).** Eight returns came
off the list: ACT 2019 (a row carried over the page break), NZ First 2023
and its replaced original (figures printed with no cents), NZ First 2021
and its amendment and NZ First 2022 (the same, and `No 35000` on one
line), DemocracyNZ 2023 (no cents), Labour 2025 (the page reader's HTML
table). No name or amount already published changed. Of the 37, 28 are
in-window returns (2019 on). By cause:

- **17 (15 in window), the cells and the figures do not pair.** The page
  reader went down the page column by column (Advance NZ 2020, NewZeal
  2020 and 2023, Te Pāti Māori 2023 and 2025, Freedoms NZ 2023 p2, Leighton
  Baker 2023, Social Credit 2021, TOP 2017 and 2024, NZ First 2020, National
  2020 and 2025, ACT 2020, Green 2023 p4, Labour 2018), or Labour 2023: a
  row runs over the page-4 break, but page 5 opens on another row's name
  (its row number is misread, `6B`) above the first figure, so the carried
  row has no figure the lane can be sure is its own. Fix: a cell-scale
  re-read of these pages (the page reader on each row's crop), the
  scheduler's job; the lane replays it.
- **9 (5 in window), no rows found** (Conservative 2017, DemocracyNZ 2022
  both copies, Green 2018, National 2018, NewZeal 2024, TOP 2018 and 2023,
  Vision 2023). Not yet looked at page by page.
- **5 (4 in window), the rows add to something else.** Labour 2024: the
  scanner's own text layer garbles one figure (row 31, page 3), so the part is
  $7,030.16 short; National 2024: the attachment (pages 3 to 5) is now
  read, 90 rows, but the page reader looped on page 3's last row (one date
  repeated for 4,000 characters) and its figure is lost, $69,241.49 short;
  NZ First 2024's amendment, 9 rows against $338,907.24; National 2023 one
  cent over; Labour 2017 (card `labour-2017-the-page-reader-drops-a-
  handwritten-correction`). Labour 2024 and National 2024 need the page
  reader on one page each (re-read job, step 2.14).
- **5 (3 in window), a cell with no name before its address** (ACT 2017,
  2018; Green 2019, 2020; Labour 2020). Labour 2020's page 2 has no
  figures at all in its text layer (a scanner's OCR layer that dropped the
  amount column): it needs the page reader on page 2.
- **1, nothing to reconcile against** (NZ Outdoors and Freedom 2022).

`select * from party_returns.set_aside where stage = 'part-a'` lists them.
