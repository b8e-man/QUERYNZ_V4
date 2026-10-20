# Part A rows are read on a minority of the returns held
kind: finding
state: open
use-case: 1
session: comparison
opened: 2026-10-20

The party-returns lane has read the Part A (named donor) rows on 38 of the
152 returns it holds; the other party-years publish their declared total
and no rows (`named_by_year` is null). The frozen site has rows for those
years. So for 50 party-years every named figure, over-the-line figure,
size-band placing and per-donor year is short on the rebuilt side, and the
window and race figures that sum them follow. Today: 1,909 differences
(pickers 966, donor 775, home 76, party pages 65, size-bands 27); for ACT
alone 2017, 2018 and 2020 are unread, $832,810 of named rows.

Which side is right: the frozen one, for the rows; the rebuilt declared
totals agree with it. Clears as the lane reads the rest of the returns
(the scans need the page reader; see the lane's own cards). Owner:
party-returns.
