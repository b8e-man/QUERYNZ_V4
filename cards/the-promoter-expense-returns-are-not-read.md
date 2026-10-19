# The registered promoters' expense returns are not read
kind: finding
state: open
use-case: 1
session: party-finance
opened: 2026-10-20

`pub.promoter_expenses` carries the Commission's own figure for each
promoter's return (21 rows, 2020 and 2023) and links the return; the lane
holds 20 of the 21 returns (The Better NZ Trust 2023, `Better-NZ-Trust-01.pdf`,
is linked by the Commission and not held: a capture for the old job, not
this lane) and reads none of them. Reading their own totals would check
the Commission's table the way the party returns check theirs. One row
asks for it: Family First New Zealand 2020 prints $141,224.34 in all three
columns (election, cannabis referendum, end-of-life referendum).

The profile exists (`ec-promoter-expenses-return` v2, GLM-OCR at 200 dots);
the page reader's stored readings cover 18 of the 20 (79 pages, at 200
dots only). Next: a reader in the shape of `expenses.py` (Part totals and
the return's own total, checked against its parts), then against the table.
