# board: where it stands

**Date:** 2026-10-26. **Step:** 4.9 second version, rulings 86 to 88
(80 to 85 kept), `products/board/`. **Merge request:** `board-4`
(merged); `fix-products-board-1e` (raised, ruling 88).

## Done

- Night mode. One dark stylesheet. Every text colour reads at 4.5:1 or
  more on every background, and the edge colours are re-chosen for dark.
  A test and the check read the colour pairs from the stylesheet itself.
- No edge numbers. An edge's words are drawn only where they touch no
  other text. The list under the key is grouped by the row each edge
  reaches.
- Donations summed. A donor's rows filed under one name are one node,
  with one edge per party or candidate. The edge shows the total and the
  count. Every addend is listed under it. A disclosure is listed and never
  added to a return.
- Source links. `/doc/<sha256>` serves the captured document, read only,
  whole. Ruling 88: every document the store holds opens, whatever its
  source, the addresses it prints included: 54,875 documents from 31
  sources, none withdrawn. The board listens on the local network only
  (hard limit 13) and publishes no table and no export. A suppressed row
  or withheld text still offers no link. The setting `SERVED_SOURCES`
  and the 403 are gone.
- The store is read only through `support.docstore`, because of the
  one-way test. Its new reader `landing.documents_of` comes as the patch
  `board-4-docstore-read.patch` beside the request. Until it is applied,
  nothing opens and the check says so.
- The use cases tab, `/uses`. It shows the plan's 17 rows at render time,
  with templates built (3 use cases have one) and registers held or not.
- The check covers each of the above. Against live data it is green. It
  opens a party return and one cited document of each of the 27 sources a
  published row cites; with a refusal put back for party returns it is red.

## Known limits

- Two rows filed under one name are drawn as one donor. Identical filing
  is all that groups them; the page says so.
- Lines still pass under node labels. Only text boxes are kept apart.
- Scan templates carry no `use_case` field. The tab reads "(use case N)"
  from the owner line, and reads the `use_case` field once a template has one.
- Earlier limits stand: family-given names with no comma; lanes' pane.md
  name orders; card `an-address-search-on-the-board-cannot-also-name-the-company`.

## Next

1. The integrator merges `fix-products-board-1e` and restarts `qv4-board`.
