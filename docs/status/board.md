# board: where it stands

**Date:** 2026-10-28. **Step:** 4.9 second version, rulings 80 to 108,
`products/board/`. **Session:** board-10 (ruling 106 (2), the lineage
frame). **Merge request:** `board-10`.

## Done

- Rulings 80 to 105 and 108: as before (board-8, board-9).
- Ruling 106 (2), `lineage.py`: `pub.links`' related grade is drawn in
  both graph states as a lineage frame: a compound node (lime, double
  border) labelled "succeeded by · 1987 → 2011, 2013", the companies in
  date order left to right, each its own node, the people on both drawn
  once beneath, joined to each company. A chain is one frame. A suppressed
  person is counted, never named. Near keeps its colour and dash alone.
- Panes: "Related companies" on a row's links and on an entity, with the
  relation, years and people on both. The results pane says "related" on
  an entity or a company row that has one.
- Words for ruling 107's rule (`organisation-one-live-company@1`).
- Cost: one query by key for the rows in hand, one more per round of a
  chain (at most 3): 13 to 16 ms a graph; the two-second floor holds.
- Check item 24; `tests/test_lineage.py`; two live tests in `test_real.py`
  (one a planted merge that turns item 24 red).

## Known limits

- Without script the frame is the lineage line between the companies; the
  SVG draws no frame.
- Live `pub.links` has no `relation` column after the 14:09 rebuild; the
  board reads the evidence's copy until the lane republishes it.
- Live succession companies sit in no group, so the entity state shows
  them as lone rows inside the frame.
- `products/report/walk.py` still treats `related` as near (not the
  board's folder).
- 32 registers share 14 colours (queue item `graph-node-colours-by-family`).

## Next

1. The integrator merges `session/board-10` and restarts `qv4-board` at
   the release. No table, unit or setting changes.
