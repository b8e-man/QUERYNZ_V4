# board-9: ruling 108, the search tab's results pane
branch: session/board-9 (pushed, 37a3593; one commit on 69fe1a8)
session: board-9 (Opus, build, scope products/board/)
raised: 2026-10-28
claims: products/board/ (search.py, panes.py, people.py, graph.py, server.py, check.py, catalogue.py, fold.py,
static/graph.js, static/README.md, spec.md; tests/test_results.py new, test_canvas.py, test_real.py);
lessons/read-a-result-dict-s-registers-by-type-not-by-skipping-the-known-extra-keys.md,
lessons/a-board-red-during-a-links-rebuild-is-the-rebuild-until-its-counts-say-otherwise.md; docs/status/board.md.

Note: ruling 108 was in the main checkout's rulings.md, uncommitted, when this session read it; the brief carried it too.

## What it does

1. **The switch on the results pane.** "show: rows · entities" sits above the results as well as the graph, using the
   same `g=entities`. In entities, the pane lists the entities the shown rows fall in first (`people.gather`). Each
   entity shows its fullest filed name, "n rows, n registers", contested where flagged, the registers named and the
   rows of this search it holds. At most 50 are listed and the rest counted. Then "Rows in no group", as rows. A
   suppressed row is never gathered.
2. **Tabs by matching field.** These apply to the search box alone and to the fields under "any field may match". There
   is one tab per field matched: first, middle and last name, address, organisation and year (from the columns
   `FIELDS_OF` declares, each word read the way the box reads it), number, and "elsewhere in the row". Each tab carries
   the count of rows under it. Under a tab, each register is a closed details element showing its name and count. A row
   that matches several fields appears under each. "All fields must match" keeps the one list. It is one query per view
   (`search.tab_sql`): flags, whole counts per tab, and the first 50 rows under each tab. Above the tabs, each
   register's total and its removed-hidden count (ruling 93).
3. **Entity search.** The box, or the name fields, are read against `pub.names` by equality on `fl_key`, `full_key` and
   `name_key` (all indexed), then folded into `pub.groups` by `groups_pkey`. Only the registers searched are read, and a
   suppressed row never finds its group. A group found this way is listed under the tab of the key it matched, after the
   groups in hand. Nothing else is read for this, and no link is made.
4. **The graph beside the results.** Every result carries `data-graph` (`/graph.json?c=…` with the boxes and the
   state). A click opens ruling 100's canvas in a pane to the right, centred on that row, or on its entity in the
   entity state. A click with a key held opens the pane as before. Below 75rem the graph stacks under the results. The
   content security policy is unchanged and the graph tab stays.
5. Also: the per-view scans are queued longest first, using each view's last time. Words for links-3's three new
   rules: without them the graph printed "links rule …" and the check was red.

## Cost (live, 28 October, load average 5 to 9)

- **Search** (plain, then with tabs): hart 1.95 s and 1.93 s; smith 2.10 s and 2.11 s; "Graeme Hart" 1.7 to 1.8 s.
  The tabs add about 13% of the scans' serial work. Queuing the scans longest first absorbs it.
- **Entity state:** gathering takes 0.17 to 0.19 s. The entity search's lookup takes 1 to 48 ms ("John Smith": 37
  groups).
- **Whole page,** against main's code: hart 2.07 s becomes 2.18 s (2.34 s in entities); smith 2.21 s becomes 2.72 s
  (2.46 s in entities).
- **Page size:** 0.9 MB becomes 1.5 MB, and 1.8 MB becomes 2.8 MB, because a row appears under each tab it matched.
- Every new query goes by row key or group id, or by equality on an indexed key.

## Verified

- `python -m products.board check`: green in 74 s. New item 23 went red on three planted faults: whole-word tabs, a
  wrong key fold, and a suppressed row shown. It also caught a real mismatch while it was being written (the removed
  rows). Item 22 was red on main's own code during the links-3 rebuild. Its near arm now takes a director of a near
  pair across two groups when the "smith" rows have none.
- `tests/test_real.py`, `test_night` and `test_canvas`: green together. The first run straight after the check was red
  on two timings, then green alone and on the full re-run (the same as board-8).
- `QV4_INTEGRATOR=1 bin/fast products/board`: green in 69.2 s. The sample fill took 67.7 s of that. Root
  `test_imports_one_way`, `test_reading_limits` and `test_lessons_search` pass.
- Headless Chrome against a scratch server on 127.0.0.1:
  - "smith": six tabs. The first tab shows, a click on another switches, and the registers start closed.
  - A real click on a result opened the graph to the right, centred on that row.
  - In entities: 8 entities listed first. A click centred the graph on the entity.
  - At 1000 px wide the graph stacks under the results.
  - Two name fields under any field show tabs first and last; under all fields, none.
  - No console error. 27 requests, none to any address but the board's own. The one 404 is the browser's
    `/favicon.ico`, which the board has never served.

## The integrator must

1. Merge `session/board-9`.
2. **Restart `qv4-board` at the release:** new `graph.js` hash, new page layout. No table, unit or setting changes.
3. Regenerate `lessons/INDEX.md` for the two new lessons.

## Result (integrator, 28 October 13:26 NZDT)
Merged d0b700f, gate green at the first run; the lessons index rebuilt. Released; `qv4-board` restarted 13:26. Branch and the working copy retired. Next on the board, not yet carded: the lineage frame for the links lane's "related" grade (links-3's request says how).
