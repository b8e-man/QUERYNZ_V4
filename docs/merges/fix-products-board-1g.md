# fix-products-board-1g: ruling 93, removed companies hidden by default (rulings 80 to 92 kept)
branch: fix/products-board-1 (pushed, 434b945; one commit on 8ce2d33)
session: fix-products-board-1 (Opus, fix, scope products/board/)
raised: 2026-10-26 (written to the session's scratch folder: the fence refused the inbox link; move it to
inbox/merge-requests/)
claims: products/board/ (catalogue.py, search.py, near.py, panes.py, server.py, graph.py, check.py, spec.md; tests:
new test_removed.py, test_real.py extended); lessons/a-count-carried-on-the-rows-vanishes-when-every-row-is-filtered-out.md;
docs/status/board.md. No card opened or closed.

## What it does

1. **The box.** "show removed companies" under the register ticks on both tabs (`panes.removed_box`), unticked on the
   first view. `search.Boxes.removed`; `removed=1` in the form and every href (and the pin and save forms) only when
   ticked; `boxes_of` reads it.
2. **The status words, as data.** `catalogue.REMOVED_STATUS`, trimmed and case folded, and `catalogue.REMOVED_OF =
   {"companies": "status"}`. From pub.companies' status values, 26 October:
   included: Removed 1,066,680, removed 1,931, dissolved 28,534, deregistered 2,550, closed 65, "Removed & In
   Liquidation" 2 (1,099,762 rows in all; the last is a fifth word beyond the ruling's four, since the company is off the
   register). Left out: liquidation, receivership, statutory management and voluntary administration in their spellings
   (still on the register), CANCELLED 5, SUSPENDED 1, inactive 1 (not stated as off the register; a ruling can add them
   by editing the set).
3. **Left out in the SQL, before the limit.** `search.removed_expr` / `removed_sql`. Search results: `view_sql` with
   `removed=False` is one scan in a CTE, the counts in a one-row CTE left-joined to the limited rows, so "n removed
   hidden" is said even when every match was removed (`search()` drops the counts' own row; `res["hidden"]`). Near
   matches (`near._read`), the register table (`search.table`, its count and hidden count in one query) and the graph's
   matched nodes (`graph.build(removed=)`). The count line of the register and of the table reads "n removed hidden".
   Ticked, the SQL is byte for byte what it was (the report's copy test still green; `guard_sql` untouched).
4. **What still opens.** `search.row`, `far_rows`, `children`, `same_name` and a graph centre take no status clause: a
   row pane by its own link, a director's company, a graph node's far end open whatever their status.
5. **Check case 20** (live): "fletcher" in companies, box off vs on; shown red with `REMOVED_OF` emptied. Check case 18
   (the table) now counts what the first view shows.

## Checked

- `QV4_INTEGRATOR=1 bin/fast products/board`: green (42.2 s).
- `python -m products.board check` against live data: green (39 s).
- Root `tests/` and `products/report/tests/test_search.py` (fast): green.
- Slow: `test_real.py::test_removed_companies_against_fixture_rows_under_both_settings` (five fixture rows in a temporary
  table of pub.companies' shape, limit two): passed.
- Live "fletcher", companies register: 2,196 rows unticked with 240 removed hidden; 2,436 ticked (2,436 - 2,196 = 240).
  The companies view alone: 119 vs 359. The companies table: 820,706 shown, 1,099,762 hidden.

## For the integrator

1. Move this file into `inbox/merge-requests/`.
2. Merge, **rebuild `lessons/INDEX.md`** (`bin/lessons-index`; the new lesson is not in the committed index, the fence
   refuses generated files), then **restart `qv4-board`** at the release. No table, unit, setting or other module
   changes.
3. The report's copy of the board's search needs nothing: the copied pieces and the no-fields SQL are unchanged.

## Result (integrator, 26 October 16:10 NZDT)

Gate green; merged as 3ef8fc4 (integrate commit 2960b4e: board, lessons index, decisions regenerated). Released and `qv4-board` restarted 16:05. Live: "fletcher" in companies with the box off says "240 removed hidden"; with `removed=1` it says nothing and the box is on the page. The removed set as data: removed (any case), dissolved, deregistered, closed, "Removed & In Liquidation"; liquidation, receivership, administration, CANCELLED, SUSPENDED and inactive stay visible, reported to Arthur. Branch and working copy retired.
