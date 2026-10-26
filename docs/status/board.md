# board: where it stands

**Date:** 2026-10-26. **Step:** 4.9 second version, rulings 80 to 93 and
100, `products/board/`. **Session:** board-7 (ruling 100). **Merge
request:** `board-7`.

## Done

- Ruling 100, the graph canvas. The graph tab's picture is a Cytoscape
  canvas with the cola layout, as the old estate's graph page had it:
  round nodes coloured by register family, label beneath, centre ringed,
  soft curved edges in the key's colours, near verdicts dashed. Tap a
  node to grow its one hop, tap again to fold it; double-tap opens its
  pane; drag, zoom, pan; "spread" and "tree" controls; hover for words
  and causes.
- The libraries (Cytoscape 3.34.0, cytoscape-cola 2.5.1, WebCola 3.4.0,
  MIT) are vendored in `static/` with their licences and sha256, served by
  the board under `/static/` only. Every page now carries a content
  security policy: it can ask nothing of any other address.
- `/graph.json` gives the same graph as data from the same `graph.build`.
- The SVG stays inside `<noscript>`; the key and the edge list are
  unchanged.
- Live, 26 October: the check's new case 21 ("hart": JSON and SVG have
  the same 28 nodes and 27 lines) is green, and red with the answer
  broken. Headless Chrome: grow 28 to 68 nodes, fold back to 28, spread,
  tree, hover, double-tap all work; no console error, no request off
  the box.

## Known limits

- 28 registers share 14 colours, by family (queue item
  `graph-node-colours-by-family`).
- The canvas carries only what one tap's answer gives: one hop, capped
  as the SVG is.
- Earlier limits stand (see `docs/merges/` for board-5, board-6 and
  fix-products-board-1g).

## Open

- Card `the-board-has-no-entry-for-the-hansard-views`: the check is red
  on three lines for the Hansard views. This was red on main before
  board-7.

## Next

1. The integrator merges `session/board-7` and restarts `qv4-board` at
   the release. No table or unit changes.
