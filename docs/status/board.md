# board: where it stands

**Date:** 2026-10-20. **Step:** 4.9, the board, `products/board/`. **Merge
request:** `board-1` (raised).

## Done

- The page: one search across the 35 published views (every word a word
  start, macrons folded, a number exact; a suppressed, revoked or withheld
  name never matched), results by register with counts, "none found" and
  "not held" said; a pane per row (fields, dates as filed, the same
  register's rows, links, namesakes by name apart, the document cited not
  opened); panes chain left to right; a person pane; pin and save path
  (`board.pins`, `board.paths`, only ever added to). Stdlib HTTP server,
  no script, no npm. Port 8420 on the local network; unit
  `units/qv4-board.service`; launcher `qv4-board.desktop` + `open`.
- Scans run on the product reader (pub only, 3 connections), one session
  reader connection per page, one page at a time (lesson filed).
- Outside check green against the real tables (`python -m products.board
  check`): a donor found with its count, not-held said, every shown column
  present, no address column outside the registered office, the walk
  donor → company → director rendered with citations. Search 0.75 s;
  five panes 1.5 s. Fast tier 25 tests, slow 3, one-way test green.
- Real state tried in `querynz_v4_sample.scratch_board` (one pin, one path).

## Carded

- `the-installer-does-not-reach-a-product-s-unit-folder` (blocker, integrator).
- `expense-release-totals-has-no-stable-key` (expenses lane).
- `how-links-names-a-register-row` (links session; the board assumes
  `<register>:<key>`).

## Next

1. The integrator merges `board-1`, adds the installer globs, enables
   `qv4-board`, runs `python -m products.board state`.
2. Arthur copies the launcher to his desktop (one line in the closing note).
3. When links/ publishes `pub.links`, `pub.groups`, `pub.decisions`: the
   panes fill on their own; settle the row-ref form (card).
4. Step 5: "report from here" on a pane.
