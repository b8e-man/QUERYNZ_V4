# Part A is set aside on thirty-three read returns
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-19

Tranche 2 publishes a return's donors only when its Part A rows add, to
the cent, to the part's figure on the declaration page and to `TOTAL FOR
PART A` where read. Of the 99 returns with a row: 22 published (476
donor rows), 44 nil, 33 set aside at stage `part-a`, each with its
reason. Measured over all 152 landed returns, replay only. Of the 56
current in-window party returns, 38 have Part A published or nil and 18
are set aside. By cause:

- **16, the cells and figures do not pair.** The page reader went down a
  page column by column (every name, then every amount), which the lane
  refuses to pair by order: on ADVANCE NZ 2020 an address line paired as
  a donor shifted every amount below it by one row and the sum still
  matched. Or a text-layer row runs over a page break with its amount on
  the next page (ACT 2019; Labour 2023 and 2024). Fix: a cell-scale
  re-read of the refused pages (the page reader on the table's crop),
  and carrying an unfinished row across a page break.
- **9, no rows found under the Part A heading.** The donors are on an
  attached schedule the reader's region does not reach (NZ First 2021 and
  2022 print "see attached"; National 2024's table page came back with
  no figures). Fix: find the schedule by its own heading or its total.
- **5, the rows add to something else.** National 2023: 182 clean rows
  add to $4,015,899.35 against a printed $4,015,899.34 (one cent; read
  the rows against the page to find which). National 2022 (the unlisted
  copy), Green 2023, Freedoms NZ 2023, NZ First 2024 (replaced): rows on
  pages the region misses.
- **2, a cell with no name before its address** (Green 2019, 2020): the
  name sits on the line above.
- **1, nothing to reconcile against** (NZ Outdoors and Freedom 2022).

`select * from party_returns.set_aside where stage = 'part-a'` lists them.
