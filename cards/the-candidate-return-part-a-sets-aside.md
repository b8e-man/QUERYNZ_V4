# Part A is set aside on 20 published candidate returns
kind: finding
state: open
use-case: 1
session: candidate-returns
opened: 2026-10-20

`donors.py` publishes a return's Part A only when its rows add to the
page's TOTAL FOR PART A and to the declaration's Part A, and only when the
cut leaves names with no figure, street word or comma tail. 81 of 94
text-layer returns with donations publish (175 donor rows; the form's
example row dropped on 336). Stage `part-a` (the row stands):

- 9: no rows found against a declared Part A: candidate-made copies of
  the form (Word, Excel) with no form table, and no `TOTAL FOR PART A`.
  Their tables need their own look (`replay shape <hash> 2`).
- 6: Part A is on image pages; not read from pixels yet (after the
  page-reading card).
- 2: the table's columns are not where its header says.
- 2: the cut cannot vouch for a name (a street word, no name before the
  address): set aside, which is the safe outcome; look at the cells'
  shape before loosening anything.
- 1: the rows add short, and later pages are images (a continuation).

Part D (overseas donors) is not read.
