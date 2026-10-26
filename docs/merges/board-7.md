# board-7: ruling 100, the graph tab's picture becomes a Cytoscape canvas (rulings 80 to 93 kept)
branch: session/board-7 (pushed, 8ad1a29; one commit on 0bf98c9)
session: board-7 (Opus, build, scope products/board/)
raised: 2026-10-26 (written to the session's scratch folder: the fence refused the inbox link; move it to
inbox/merge-requests/)
claims: products/board/ (graph.py, panes.py, server.py, catalogue.py, check.py, spec.md; new assets.py, static/,
tests/test_canvas.py); cards/the-board-has-no-entry-for-the-hansard-views.md (opened);
docs/decisions/queue/graph-node-colours-by-family.md; lessons/check-a-colour-floor-against-the-number-of-colours-before-promising-it.md;
docs/status/board.md.

## What it does

1. **The library.** Cytoscape 3.34.0, cytoscape-cola 2.5.1 and WebCola 3.4.0, the versions the old estate locked, all
   MIT, in `products/board/static/`, each licence file beside it. `static/README.md` records the package, version,
   registry tarball, its sha512 and each file's sha256; `tests/test_canvas.py` holds the sha256. **Where they came
   from:** the session's command list refuses `curl`, so nothing was fetched from jsdelivr. The three registry tarballs
   were in this box's npm cache, stored under their sha512. Each sha512 was checked against the registry integrity in
   the old lock file before the tarball was opened. The README says so. If the integrator wants a jsdelivr fetch on
   record, fetch the three addresses in the README and compare the sha256.
   `GET /static/<name>` serves only the names in `assets.FILES`, with their content type, `nosniff` and an immutable
   one-year cache; each address carries the file's hash; any other name is a 404. **Every HTML page now sends a
   content security policy** (`server.POLICY`: scripts, fetches and images from the board only, no frames, no
   objects), so the browser itself refuses any request off the box.
2. **`/graph.json?c=<view:key>&<boxes>`** (`server.graph_answer` → `graph.answer`) builds from the same
   `graph.build` on the product reader. Nodes carry view, key, title (suppression and withholding as
   `panes.shown`), register, family, colour, matched, centre, their layered position (ruling 92 (1)), and the hrefs
   of their pane and their one hop. Edges are one per line: the kind's colour, dashed only for a near verdict, the
   words, and every cause with its kind, words, rule and the asserting row's href; money edges carry their addends
   (ruling 86 (3)). No address edge.
3. **The canvas** (`static/graph.js`) starts from the inline JSON, then calls `/graph.json` as the reader taps. Tap a
   node to grow its one hop; tap it again to fold it (whatever only that tap brought leaves, recursively).
   Double-tap opens the row's pane. Drag, zoom and pan work. "Spread" runs cola; "tree" returns every node to its
   layered place. Hovering shows an edge's words and causes, or a node's register. The legend lists the families on
   the canvas. Text goes in by `textContent` only. The SVG stays inside `<noscript>`. The key and the edge list are
   byte-identical with and without the canvas (a test holds this).
4. **Node colours.** 28 registers cannot each have a colour 3:1 on the picture and 15 apart in OKLab (a search found
   13.5 at best). So 14 families share a colour each (`catalogue.FAMILIES`), 17.5 or more apart and 3.2:1 or more,
   the way the two same-person kinds share a hue. `panes.contrast_problems` covers them on the SVG's and the canvas's
   surfaces. Queue item `graph-node-colours-by-family` has the default and the alternative.
5. **The check, case 21.** The canvas, the inline data and the `<noscript>` SVG are on the graph tab. No page and no
   static file names an address off the box outside a licence comment. For "hart", `/graph.json` has the SVG's nodes
   at its places and its lines with their causes and colours, and the inline data is that answer. A suppressed row,
   centred, keeps its name out of the answer. Case 7's "no script" condition is replaced by "SVG in `<noscript>`".

## Verified

- `QV4_INTEGRATOR=1 bin/fast products/board`: green in 44.7 s. Root `test_imports_one_way`, `test_reading_limits`
  and the spec test pass. The whole-repository fast tier was stopped at 590 s, unfinished, and was not re-run.
- `python -m products.board check` against live data: 3 problems, all `pub.hansard_*` views with no catalogue entry.
  These were red on main before this branch (card opened; `tests/test_real.py` is red on them too). Case 21 is
  green, and it goes red when the answer drops an edge or moves a node.
- **Headless Chrome on the box** (google-chrome, driven over DevTools by node's own WebSocket; nothing installed),
  on a scratch server bound to 127.0.0.1. "hart" drew 28 nodes and 27 edges, curved, 6 near edges dashed. A real tap
  on a party node grew it to 68 nodes; a second tap folded it back to 28. Spread moved all 28 nodes; tree put every
  node back on its layered position. Hover showed the tip. Double-tap opened the row's pane. There were no console
  errors and no requests off the box (only /favicon.ico 404).

## The integrator must

1. Merge `session/board-7`.
2. **Restart `qv4-board` at the release** (new routes, new files, `graph.js`'s hash is read at start). No table,
   unit or setting changes.
3. Pick up card `the-board-has-no-entry-for-the-hansard-views` for a board fix after the Hansard lane's merge: three
   `View` entries from its `pane.md`.

Lesson: `check-a-colour-floor-against-the-number-of-colours-before-promising-it`.

## Result (integrator, 27 October 07:10 NZDT)
Merged inside fix-products-board-1h (ae6120a, gate green at 07:06): the first gate run of board-7 alone was refused by `tests/test_real.py` on the three Hansard views the board did not catalogue (the card this session opened), so the fix session fix-products-board-1 was given a copy carrying board-7 and the two went through one gate. The three library files were fetched from jsdelivr by the integrator and their sha256 equal the vendored copies (npm cache) byte for byte. The lesson's rule line was shortened under 240 characters at the merge. Released; `qv4-board` restarted; `/graph?q=hart` answers 200 and `/graph.json` answers. The colour queue item stands on its default. Branches and the working copy retired.
