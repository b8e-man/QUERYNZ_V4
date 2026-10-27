# board: where it stands

**Date:** 2026-10-28. **Step:** 4.9 second version, rulings 80 to 105,
`products/board/`. **Session:** board-8 (ruling 105, the graph's people
state). **Merge request:** `board-8`.

## Done

- Rulings 80 to 102: as before (fix-products-board-2).
- Ruling 105, the people state: "show: rows · people" above the graph,
  the state in the address (`g=people`). One node per `pub.groups` group,
  labelled by the fullest filed name with "n rows, n registers"; lone rows
  dotted; edges lifted to group ends; near links one hop from the matched
  rows, dashed, reason on the line; contested dashed border; decisions on
  their lines. Tap an entity to open its rows inside it (40 at most),
  again to close. Double-tap opens the entity pane (`entity:<group_id>`).
- Suppressed rows are never gathered: own node, no near link, no count.
- Cost, live: the fold adds 20 to 28 ms and drops the rows state's own
  links step (130 to 155 ms), so a people graph costs about 0.1 s less
  than the rows graph of the same search (smith 1.98 s against 2.06 s).
  Opening the largest group (1,220 rows) costs 80 to 150 ms.
- Check item 22; `tests/test_people.py`; fast tier green in 57 s.

## Known limits

- 32 registers share 14 colours, by family (queue item
  `graph-node-colours-by-family`).
- No published suppressed row sits in a group today, so the live check
  centres an ungrouped one; the grouped case is held on a fixture.
- An entity's rows of one register read alike in its pane (a director's
  title is the name alone).
- A donor folded by filed name (ruling 86 (3)) is folded by its first row.

## Next

1. The integrator merges `session/board-8` and restarts `qv4-board` at
   the release. No table or unit changes.
