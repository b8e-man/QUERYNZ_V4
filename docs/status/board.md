# board: where it stands

**Date:** 2026-10-26. **Step:** 4.9 second version, ruling 92 items 2, 4,
5 and 6 (80 to 91 kept), `products/board/`. **Session:** board-6.
**Merge request:** `board-6` (raised). board-5 builds item 1 (the graph's
layout) beside it in `graph.py`; this branch leaves `graph.py` and the SVG
styles untouched.

## Done

- Item 2, names not keys. A field that holds another row's key (a
  director's company, an officer's charity, an NZBN of a body) shows that
  row's name as a link, the key on hover. A row not held shows the key and
  "(row not held)". One query per far view per page.
- Item 4, near names. A "near names" button beside the search box. Its
  pane lists, for each given name typed, the given names filed with the
  same surname: common forms from a table of English and Māori names
  (`given_names.py`), plus names sharing the first three letters or one
  letter apart, each with a count of rows. A click adds the name to the
  search as an alternative (`garry|gary payinda`). The pane says a variant
  is a candidate, never a link.
- Item 5, a register as a table. Each register's name in the left pane
  opens a table: the count of all rows, 100 one-line rows, "more" for the
  next 100 (1,000 at most), a chooser for the register's other views. A
  search with the table open puts the results between search and table.
- Item 6, all or any. Two choices in "narrow by field": all fields must
  match (the default, as before) or any field may match. Under "any" each
  result says which field it matched.
- The check has four new cases (16 to 19). Against live data it is green.
  Each was shown red with its rule broken.

## Known limits

- The graph tab always combines fields with "all": it is board-5's file.
- Near names reads the name fields when first and last are filled, else
  the box when it reads as a person's name (two to four words).
- A table cell is cut at 40 characters; the whole value is on hover.
- Earlier limits stand: one name as filed drawn as one donor; lines under
  node labels; `SHAPE_OWN`; family-given names with no comma; card
  `an-address-search-on-the-board-cannot-also-name-the-company`.

## Next

1. The integrator merges `board-6` (after or beside board-5) and restarts
   `qv4-board` at the release. No table, unit or setting changes.
