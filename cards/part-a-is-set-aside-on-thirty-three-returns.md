# Part A is set aside on twenty-five read returns (was thirty-seven)
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-19
updated: 2026-10-20 (party-returns session 5)

A return's donors are published only when its Part A rows add, to the
cent, to the declaration's Part A and to `TOTAL FOR PART A` where read.
Session 5, measured over all 152 landed returns, replay only: **published
on 52 (1,133 rows; was 38, 843), nil 63, set aside 25 (was 37).** Fourteen
came off: Labour 2020 and 2024 and Green 2019 (Part A read again over the
page reader's stored readings of the text pages), National 2018,
DemocracyNZ 2022 both copies, NZ First 2024's amendment and TOP 2023 (a
numbered name with its row on the lines below), NewZeal 2023 (bare row
numbers), NewZeal 2024 (a figure with no cents after `NO`), TOP 2024 (one
figure on the page), National 2025 (a pointer page, and `22 E.A.W
Limited`), NZ First 2019 (each donor's `Aggregated total` line), ACT 2017
(a donor's dated rows over the page break). TEA Party 2020 joined the list
when its declaration was mended. `python -m registers.party_returns.replay
rereads RUN.json` lists each with its hash and the pages to ask for.

- **17, a page whose cells and figures do not pair**, nearly all read
  column by column (cell-scale re-read of the page named; Conservative
  2017 and ACT 2018 are instead one donor's numbered dated rows, which
  the lane does not yet give to the donor above): Social Credit 2021 p2, Conservative 2017 p2, TOP 2017 p2, ACT
  2018 p3, Labour 2018 p2, ACT 2020 p4, Advance NZ 2020 p2, NZ First 2020
  p2, National 2020 p4, NewZeal 2020 p2, TEA 2020 p2, Freedoms NZ 2023 p2,
  Green 2023 p4, Leighton Baker 2023 p2, Te Pāti Māori 2023 p2 and 2025
  p2. Vision NZ 2023's page 2 reading carries the names and no figures
  (the same re-read).
- **2, text pages with no stored reading:** Labour 2023 pages 4, 5, 7
  (the carried row), Green 2020 page 4.
- **2, text layers too garbled to find the table** (Green 2018 pages 2–3,
  TOP 2018): a re-read of the Part A pages, which the lane cannot name
  until it finds the heading.
- **3, the rows add to something else:** National 2023 one cent over
  (card `national-2023-the-rows-add-to-one-cent-more-than-the-printed-total`,
  a rule for Arthur); National 2024 $69,241.49 short (the page reader
  looped on page 3: re-read page 3); Labour 2017 (its own card).
- **1, nothing to reconcile against** (NZ Outdoors and Freedom 2022).

reconcile-1 (21 October, ruling 66): 24 set aside; National 2023 leaves the "add to something else" list (reconciled, issue `+0.01`). The rest differ by $100 or more and stay.
