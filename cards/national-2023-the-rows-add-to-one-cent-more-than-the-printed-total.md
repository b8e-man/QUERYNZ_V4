# National 2023: the rows add to one cent more than the printed total
kind: finding
state: closed
use-case: 1
session: party-returns
opened: 2026-10-20
closed: 2026-10-21

National's 2023 return
(`765c53fbeb2801555b8b01d8ee280412dcf79444518b23911377f96560433ba2`) is a
spreadsheet exported to PDF (embedded fonts, a true text layer). Its 182
Part A rows add to $4,015,899.35; the declaration and `TOTAL FOR PART A`
both print $4,015,899.34. The old estate read the same 182 rows to the same
$4,015,899.35, and page 3's rows read by the page reader agree with the
text layer. So no row is misread: the spreadsheet holds fractions of a
cent and printed each row and the total rounded.

The lane reconciles to the cent, so the part is set aside and every named
National 2023 row is missing from the rebuilt pages (the comparison's
"Kelly, Andrew", $25,000, is one). Whether a rounding difference under
half a cent a row may pass is a rule for Arthur: `docs/decisions/queue/
may-part-a-pass-a-rounding-cent.md`. Default: no; the part stays set aside.

Closed by ruling 66 (21 October) and `reconcile-1`: a difference under $100 is reconciled and the row carries an issue; National 2023's Part A publishes (182 rows, `+0.01`). The queue item `may-part-a-pass-a-rounding-cent` closed with it.
