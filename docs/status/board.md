# board: where it stands

**Date:** 2026-10-25. **Step:** 4.9 second version, ruling 84 (80 to 83
kept), `products/board/`. **Merge request:** `fix-products-board-1c`
(raised).

## Done

- Ruling 84, graph tab. No rule id on the picture: `catalogue.RULE_WORDS`
  gives each of the links' 14 rules plain words (name-only@1 reads "same
  name, nothing else"); an id the table lacks reads "links rule <id>". The
  id and version show as "(links rule name-only, version 1)" only in an
  edge's tooltip and the list. A slow test holds every rule in `pub.links`
  to the table (14 of 14).
- Two rows joined more than once get one line (`graph.lines`), its colour
  the first cause in the key's order, its tooltip every cause.
- Each line carries a number, an href to the asserting row, placed along
  the line clear of every label, number and circle (`graph.place`,
  deterministic); with no room it is left off and kept in the list. Node
  labels are shortened, set beside, or dropped to the tooltip so none meets
  another. Under the key: the edges by number, each cause with kind, words
  and the asserting row. The key keeps its counts.
- The row pane's links read the same words.
- Near matches: none found from two or more words in the plain box says
  the box already matches reversed names exactly; use the name fields.
- `python -m products.board check` adds the picture case (known donor, a
  name-only donor, the "smith" search); each new test and case shown to
  fail with its rule broken.

## Known limits

- On a crowded name search ("smith": 87 nodes, 76 lines) about a quarter
  of the numbers and a tenth of the node labels have no room and live in
  the list and the tooltips.
- Text widths are estimated, not measured (no script on the page).
- Card `an-address-search-on-the-board-cannot-also-name-the-company` open.

## Next

1. The integrator merges `fix-products-board-1c` and restarts `qv4-board`.
