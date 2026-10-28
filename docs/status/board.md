# board: where it stands

**Date:** 2026-10-29. **Step:** 4.9 second version, rulings 80 to 117,
`products/board/`. **Session:** board-13 (ruling 117, four tranches).
**Merge request:** `board-13` (raised at the last tranche).

## Done

- Rulings 80 to 116: as before (board-8 to board-12, fix-products-board-1).
- Ruling 117 tranche 1 (`facts.py`): the dossier folds the rows that say
  the same thing into one entry, by what the row says (body, role, event,
  where), never by view. Lloyd Budd: "Director and shareholder of BUDD
  CONSULTANCY LIMITED since 4 December 2025"; "Trustee of Keystone New
  Zealand Property Education Trust since 11 March 2025"; near: "Lloyd
  Budd: marriage celebrant, listed 2020 to 2025" (five Gazette lists),
  "Lloyd Sam BUDD: candidate, Whangārei, 2026 General Election". Each
  row as filed stays closed under its fact. The many-rows dossier keeps
  its shape; each view's heading is its fact with its years (SQL).
  Largest group 0.56 s before, 0.8 s after.
- Tranche 2: the dossier head and the result cards say what the entity
  is ("director and shareholder, charity trustee"), never row counts,
  register counts or view names; a single-row card says its row's fact.

## Half-done

- Tranche 3 (table sort and resize), tranche 4 (the entity graph
  fault): not started.

## Known limits

- No claims section: no claims lane publishes yet.
- A written question in a minister's group reads "named on written
  questions": pub.names holds the asker alone, so asker and answering
  minister are not told apart.
- 32 registers share 14 colours (queue item `graph-node-colours-by-family`).
- A minister's name searched takes the page past two seconds (card).

## Next

1. Tranches 2 to 4, then the merge request; the integrator restarts
   `qv4-board` at the release. No table, unit or setting changes.
