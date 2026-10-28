# board: where it stands

**Date:** 2026-10-28. **Step:** 4.9 second version, rulings 80 to 112,
`products/board/`. **Session:** board-12 (rulings 111, 112).
**Merge request:** `board-12`.

## Done

- Rulings 80 to 110: as before (board-8 to board-11).
- Ruling 111: the results pane lists entities alone, in every state.
  Groups first, then each row in no group as a single-row entity. No
  row's card is in the pane; a row is read in its dossier. Tabs hold
  entities and count them ("+" where rows past the 50 read matched).
- The rows and entities switch sits on the graph's pane alone.
- The graph tab left the bar. `/graph?…` and `/?tab=graph` answer 303 to
  the search page with `gv=1`: the graph drawn beside the results by the
  server, centred on `c`/`d`. A saved path still opens (live test).
- Ruling 112, `collapse.py`: a closed "collapse" section above the
  entities. Criteria: groups (always on), shared first and last name,
  full name with middle names, registered address (a company's office),
  official number (an organisation's own). `cl=` rides every href. A
  folded entry says "collapsed here by …; not a link"; its dossier lists
  its members; the graph folds the same way. Reads only.
- The dossier names a pointed row (a director's company), never its key.
- Check items 26 and 27; items 6, 9, 16, 19, 21, 23, 25 moved to
  entities. `tests/test_collapse.py`; live tests in `test_real.py`.

## Known limits

- No claims section: no claims lane publishes yet.
- `panes.hit` (a row's card) is used by no surface now; its tests stay.
- A folded entry's keys are read once per page; an entity under two tabs
  keeps the number keys of the rows its first tab held.
- 32 registers share 14 colours (queue item `graph-node-colours-by-family`).

## Next

1. The integrator merges `session/board-12` and restarts `qv4-board` at
   the release. No table, unit or setting changes.
