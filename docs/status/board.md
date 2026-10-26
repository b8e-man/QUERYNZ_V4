# board: where it stands

**Date:** 2026-10-26. **Step:** 4.9 second version, rulings 80 to 93,
`products/board/`. **Session:** fix-products-board-1 (ruling 93). **Merge
request:** `fix-products-board-1g`.

## Done

- Ruling 92 items 1, 2, 4, 5 and 6 (board-5, board-6, merged): the graph
  as a family tree; names not keys; near names; a register as a table;
  all or any fields.
- Ruling 93, removed companies hidden by default. A check box "show
  removed companies" sits under the register ticks on both tabs,
  unticked on the first view; ticked, every link carries `removed=1`.
  Unticked, a company whose status reads removed, deregistered,
  dissolved, closed or "Removed & In Liquidation" (any case) is left out
  of the search results, the near matches, the companies table and the
  graph's matched rows, and the count line says "n removed hidden".
  The status words are data (`catalogue.REMOVED_STATUS`). A row opened by
  its own link, and a removed company reached as a far row (a director's
  company, a graph node's far end), still shows.
- Live, 26 October: "fletcher" in the companies register, 2,196 rows
  unticked with 240 removed hidden, 2,436 ticked. The companies table:
  820,706 shown, 1,099,762 hidden.
- The check has case 20 (ruling 93); green against live data, and red
  with the rule broken.

## Known limits

- Statuses not counted as removed: liquidation, receivership and
  administration (still on the register), CANCELLED (5), SUSPENDED (1),
  inactive (1).
- Only `pub.companies` is filtered; `company_lookups` and the earlier
  states keep every status.
- The graph tab always combines fields with "all".
- A table cell is cut at 40 characters; the whole value is on hover.
- Earlier limits stand: one name as filed drawn as one donor; lines under
  node labels; `SHAPE_OWN`; family-given names with no comma; card
  `an-address-search-on-the-board-cannot-also-name-the-company`.

## Next

1. The integrator merges `fix/products-board-1` and restarts `qv4-board`
   at the release. No table, unit or setting changes.
