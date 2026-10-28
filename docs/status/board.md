# board: where it stands

**Date:** 2026-10-29. **Step:** 4.9 second version, rulings 80 to 117,
`products/board/`. **Session:** board-13 (ruling 117, four tranches).
**Merge request:** `board-13` (inbox).

## Done

- Rulings 80 to 116: as before (board-8 to board-12, fix-products-board-1).
- Ruling 117 (1), `facts.py`: the dossier folds rows that say the same
  thing into one entry, by what they say, never by view. Lloyd Budd:
  "Director and shareholder of BUDD CONSULTANCY LIMITED since 4 December
  2025"; "Trustee of Keystone New Zealand Property Education Trust since
  11 March 2025"; near: "Lloyd Budd: marriage celebrant, listed 2020 to
  2025" (five Gazette lists), "Lloyd Sam BUDD: candidate, Whangārei, 2026
  General Election". Rows as filed stay closed under each fact. The
  many-rows dossier keeps its shape, each view's heading its fact.
- (2): the dossier head and the result cards say what the entity is
  ("director and shareholder, charity trustee"), no row or register
  counts, view names or "single-row entity".
- (3): the register table sorts every column both ways from its heading,
  in SQL, the sort in the address (`ts=`); one line, three lines or whole
  values, and dragged column widths, kept for the browser session.
- (4): the entity graph is one drawing from every row of a group and in
  both states of the name fold (group rows by a shared order; the stand-in
  row by ref; a fold named by its member).
- Measured live: largest dossier 0.70 s → 0.88 s; Lloyd Budd's dossier
  0.06 s, his entity graph 0.04 s → 0.05 s; a minister's centred graph
  0.62 s; a sorted companies page 0.4 s.

## Known limits

- No claims section: no claims lane publishes yet.
- A written question in a minister's group reads "named on written
  questions": pub.names holds the asker alone.
- A group past 40 rows is drawn from its first 40 (connections first).
- 32 registers share 14 colours (queue item `graph-node-colours-by-family`).
- A minister's name searched takes the page past two seconds (card).

## Next

1. The integrator merges `session/board-13` and restarts `qv4-board` at
   the release. No table, unit or setting changes.
2. The integrator merges `fix/products-board-5` (a fold's dossier shows each
   member's records under its name, 29 October) and restarts `qv4-board`.
