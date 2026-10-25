# board: where it stands

**Date:** 2026-10-26. **Step:** 4.9 second version, rulings 86 and 87
(80 to 85 kept), `products/board/`. **Merge request:** `board-4`
(raised).

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
- Source links. `/doc/<sha256>` serves the captured document, read only.
  It opens only for sources whose form has no address field: house and
  expenses, 270 documents. Every other held document is cited and not
  opened (hard limit 15). Queued with no default:
  `which-captured-documents-the-board-may-open-whole`.
- The store is read only through `support.docstore`, because of the
  one-way test. Its new reader `landing.documents_of` comes as the patch
  `board-4-docstore-read.patch` beside the request. Until it is applied,
  nothing opens and the check says so.
- The use cases tab, `/uses`. It shows the plan's 17 rows at render time,
  with templates built (3 use cases have one) and registers held or not.
- The check covers each of the above. Against live data it is green with
  the patch applied, and has one problem (nothing opens) without it.

## Known limits

- Two rows filed under one name are drawn as one donor. Identical filing
  is all that groups them; the page says so.
- Lines still pass under node labels. Only text boxes are kept apart.
- Scan templates carry no `use_case` field. The tab reads "(use case N)"
  from the owner line, and reads the `use_case` field once a template has one.
- Earlier limits stand: family-given names with no comma; lanes' pane.md
  name orders; card `an-address-search-on-the-board-cannot-also-name-the-company`.

## Next

1. The integrator applies the patch, merges `board-4` and restarts `qv4-board`.
2. Arthur rules which further sources may open whole.
