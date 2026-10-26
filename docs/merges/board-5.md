# board-5: the graph laid out like a family tree, right-angled edges (ruling 92 item 1)
branch: session/board-5 (pushed; one commit, 40cd120, on da00cf7)
session: board-5 (Opus, build, scope products/board/)
raised: 2026-10-26 (written to /home/user/querynzv4-work/scratch/board-5/board-5.md: the fence refused the inbox link)
claims: products/board/ (graph.py; check.py's graph checks; panes.py's SVG stylesheet lines only, three; spec.md;
tests test_graph.py, test_night.py's one edge regex); lessons/a-crossing-count-cannot-see-two-runs-laid-on-one-another.md;
docs/status/board.md. No card opened or closed. No table, unit or setting changed.

## What it does

1. **One line for the matched rows.** `graph.layout` (pure, deterministic) puts the search's hits on one horizontal
   line in the middle, by register (the catalogue's order) then title, evenly spaced.
2. **Layers above and below.** A row a matched row names (company, party, return, electorate, recipient) sits above.
   A row naming a matched row (directors, shareholders, officers, donors, declared interests) sits below. A links
   same-person row sits beside its match, one each side, when the line fits 2,000 px at three slots a row; else it
   goes below. A row joined to several matched rows is drawn once, centred at their mean x where the layer has room,
   its edges fanning 4 px apart. A full layer wraps into tiers; only the matched line widens the picture (16 rows:
   1,880 px, and the pane scrolls sideways).
3. **Right angles.** Every edge is an SVG `<path>` of M, H and V: vertical from the matched row, a run on a channel,
   vertical to the far row. One matched row's edges on one side share one run. Runs whose spans overlap take
   different channels, ordered by counting each overlapping pair's crossings both ways. A line between two matched
   rows runs straight between neighbours, else on the side with fewer drops. `graph.crossings` counts crossings.
4. **Labels.** Outward from their layer, under or above on the middle line, never on a channel band, no wider than
   the gap to their row's nearest node. All SVG text has a halo of the picture's surface (stylesheet). Ruling 86's
   rules stand: no edge numbers, words only where they touch nothing, one line per pair, the list under the key,
   donations summed. The key and the list are unchanged.
5. The old sector layout is deleted. Its crossing counts on the two test fixtures are kept as constants in the test.

## Verified

- `QV4_INTEGRATOR=1 bin/fast products/board`: green (43 s with the sample fill). `pytest -m slow products/board`:
  green. `python -m products.board check` against live pub: green (27 s).
- Tests: matched rows share one y, organisations above, people below, same-person beside, the shared node once at
  the mean x with its edges fanning; every path only H and V; no two runs on one channel share an x span unless they
  are one bar; labels off the channels; a fixture shaped like the live "hart" graph (invented names) crosses 2 times,
  against 7 for the sector layout.
- Each was broken in memory and went red: layers swapped, matched order unsorted, every bar on one channel, the
  crossing count inflated. Check: a diagonal edge and a matched row moved 1 px each turned it red. Every bar on one
  channel first passed both tests (the lesson); the overlap test now reads the busier fixture.
- Live crossings, sector to layered: "hart" 7 to 2, "smith" 6 to 11, "fletcher" 33 to 63, the known donor 0 to 0,
  the busiest company (centred) 0. The rise comes from a party or same-name row joined to matched rows far apart,
  whose long run the drops between must cross. The sector layout's straight lines crossed less but ran through nodes
  and names. Every node keeps a name on the four searches measured.
- Scratch screenshots looked at: the "smith" search and the busiest company, centred.

## For the integrator

1. Copy this file into merge-requests/ (the fence refused it). Merge after `fix-products-board-1e` and `-1f`. Then
   **restart `qv4-board`** at the release (graph.py and the stylesheet changed). No table, no unit, no setting.
2. board-6 works on search.py, the results pane and server.py's search handling from the same main. This branch
   touches panes.py only in the CSS string (three lines near `svg rect.bg`), so a conflict there is a CSS-line merge.

## Result (integrator, 26 October 11:30 NZDT)

Gate green; merged as d2d47a7 (integrate branch a1779e0 on main da00cf7: the board, lessons index and decisions regenerated). Released and `qv4-board` restarted 11:28; `/graph?q=hart` answers 200. board-6, built in parallel from the same main, conflicted only in `products/board/spec.md` and `docs/status/board.md` (both sessions rewrote the prose); the integrator folded board-5's three spec sentences and its status bullet into board-6's versions. The crossing rise on busy searches ("smith" 6 to 11, "fletcher" 33 to 63) is reported to Arthur as the layout's known cost. Branch and working copy retired.
