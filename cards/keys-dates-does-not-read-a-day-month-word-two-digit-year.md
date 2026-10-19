# keys.dates does not read a date printed as 31-Dec-25
kind: finding
state: open
use-case: 1
session: party-finance
opened: 2026-10-20

The Commission's roster of party financial statements prints its 2026
table's dates as `31-Dec-25`, `30-Sept-26`, `2-Jun-26`. `keys.dates.filed_date`
(the one reading of a filed date) returns None for that shape: its numeric
pattern needs digits for the month and its printed pattern needs a
four-digit year. So the 14 rows of the 2026 table carry no balance date,
deadline or date filed; the printed text stands beside each.

Fix in `keys/dates.py` (a fix session on `keys`): read `d-Mon-yy` and
`d-Month-yy` (and the Commission's `Sept`) day first, with the two-digit
year rule `_year` already applies. The lane needs no change: its next load
fills the dates.

Blocks: nothing. The roster's 2024 and 2025 tables read.
