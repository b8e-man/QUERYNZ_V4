# Part A is set aside on 26 published candidate returns
kind: finding
state: open
use-case: 1
session: candidate-returns
opened: 2026-10-20

`donors.py` (text layer) and `pixels.py` (the page reader's stored
readings) publish a return's Part A only when its rows add to the page's
`TOTAL FOR PART A` and to the declaration's Part A, and only when the cut
leaves names with no figure, street word or comma tail. Measured on 21
October (candidate-returns-2) on all 1,105 returns: 221 donor rows on 100
returns (88 typed, 12 from pixels). Stage `part-a` (the row stands), 26:

- 15 scans whose stored reading of the Part A page does not pair: 9 put
  rows among the column headings, 4 give a figure with no cell (read
  column by column), 2 leave a cell with no figure or a cell and figure on
  one line after waiting lines. Refused by design: a shifted name still
  adds up. They want a cell-scale re-read, not a looser parser.
- 4 scans with nothing to reconcile, or rows short of the total
  (`02e7fb6587a3`: rows run on to a page the reader did not join; `1348a1ec2972`:
  the declaration says 13,750, the Part A page 5,400).
- 3 with no stored reading of the Part A pages: in `replay rereads`.
- 6 typed: 3 cells the cut cannot vouch for (`405025782059`,
  `46b9dbe30bcf`, `8cc3c5beb63e`; set aside is the safe outcome), 1 row
  with no donor (`5aa66f7c54b1`), 2 tables whose columns are not where the
  header says (`16f8069f7c7f`, `98161ad95f6d`, the latter now set aside
  whole as a scanner layer).

Closed from the first list: the 8 candidate copies without the part's
heading are known by their printed total (7 publish, 26 rows); the 6
scans' Part A is read from pixels where it pairs. Part D is declared on one
return ($140) and no return read declares a loan, so neither has a reader.
