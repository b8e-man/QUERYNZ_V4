# The registered promoters' expense returns are not read
kind: finding
state: closed
use-case: 1
session: party-finance
opened: 2026-10-20
closed: 2026-10-20

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

**Closed, 2026-10-20 (party-finance session 2).** `promoter_returns.py`
reads each part of the 20 held returns: the declaration's box and the
schedule's `TOTAL FOR PART <X>`, checked against each other, never added
across parts. On every real file, 44 of the Commission's 49 figures equal
the part the return states (28 confirmed by both statements, 15 by the
declaration alone, 1 by the schedule alone), 0 differ, 5 unread (card
`four-promoter-return-parts-are-unread`; the fifth is The Better NZ
Trust's return, not held). Family First 2020 is the return's own
statement: it declares $141,224.34 in all three parts, and the form says
a cost that is both election and referendum advertising counts in full
in each. Published as `pub.promoter_expense_returns`, and beside each
column of `pub.promoter_expenses`.
