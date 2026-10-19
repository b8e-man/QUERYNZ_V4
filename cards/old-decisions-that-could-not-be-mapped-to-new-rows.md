# Old decisions that could not be mapped to new rows
kind: finding
state: open
use-case: 1
session: links
opened: 2026-10-20
closed:

Every row of the old estate's three ledgers is copied exactly into
`links.old_decisions` (folds 5,479; anchors 71,319; verdicts 381) and
mapped by content to the new stable keys (`links/old.py`). Only the old
estate's last word is applied: live rows at `donor-anchor-2.2`, live folds,
live verdicts. The old row numbers changed nightly, so a row is found by
its name, company and appointment date (directors), or by its donor, the
return's file hash or year, and the amount (donations). What did not map,
and why (nothing was guessed):

| Ledger (last word) | Pairs | Mapped | Not mapped | Why |
| --- | --- | --- | --- | --- |
| roster folds | 5,154 | 5,153 | 1 | the folded record's company carries two rows of that name on that day |
| anchors, accept + corroborated | 654 | 161 | 248 | the return is not yet read by the party-returns lane (Part A set aside on 45 returns; years the lane does not hold, e.g. 2003) |
| | | | 167 | a candidate donation: the candidate-returns lane is not built |
| | | | 36 | several rows of one donor in one return at one amount: the old row is one of them and nothing says which |
| | | | 32 | the donor name is on several or no published rows and the old row number no longer resolves |
| review verdicts (hold → contested) | 127 | 42 | 85 | the anchor each hold read is among the unmapped above |

The 248 and the 167 map themselves when those lanes publish: re-run
`python -m links.old --map --promote` after each. The 36 are one decision
about a donor name applied to one of several identical rows; applying it to
every row of that donor in that return would be faithful to what the old
estate judged, but it is a choice, so it waits here. The 32 and the 1 are
read by eye when the party-returns lane's Part A is complete. Superseded
versions (`donor-anchor-1.0` to `-2.1`) and withdrawn rows are copied and
mapped where they can be, and never applied.
