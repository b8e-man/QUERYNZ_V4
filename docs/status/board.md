# board: where it stands

**Date:** 2026-10-27. **Step:** 4.9 second version, rulings 80 to 93 and
100, `products/board/`. **Session:** fix-products-board-1 (the Hansard
views), carrying board-7. **Merge request:** `fix-products-board-1h`.

## Done

- Ruling 100 (board-7, carried here): the graph tab's picture is a
  Cytoscape canvas with the cola layout, the libraries vendored in
  `static/`, `/graph.json` from the same `graph.build`, the SVG inside
  `<noscript>`, every page under a content security policy.
- Hansard (ruling 96, `registers/hansard/pane.md`): the register "Hansard:
  who spoke in Parliament" after MPs' interests, in the House's family.
  Sitting days (the table's main view) titled with Parliament and volume,
  citing the transcript's address; sections with their text whole in
  their own pane only, "no text held" for the 262 captured empty; speech
  turns titled with the old roster's name and the label as read, a
  role-only turn its role and never a person, each member's other turns
  by member id. `hansard` leaves the not-held list.
- Live, 27 October: `python -m products.board check` green,
  `tests/test_real.py` green, the contrast tests green, the fast tier
  green in 43 s.

## Known limits

- 29 registers share 14 colours, by family (queue item
  `graph-node-colours-by-family`).
- No pointer and no graph edge from a turn to the House's member row:
  `pub.members` carries no member id; a name match would be a link made
  by looking (plan 4.9).
- Section text is not searched; a search finds a section by subject,
  proceeding or bill.
- The lane's "a suppressed name is suppressed in the text" has nothing to
  read: no published suppressed-name list or flag covers these rows.
- The index fields (last modified, fetched) read "not stated" until
  hansard-2 joins them.

## Next

1. The integrator merges `fix/products-board-1` (board-7 with it) and
   restarts `qv4-board` at the release. No table or unit changes.
