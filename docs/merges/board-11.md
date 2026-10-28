# board-11: ruling 110, the dossier under the graph; the matching-here line goes
branch: session/board-11 (pushed, 0381178; two commits on 6041a50)
session: board-11 (Opus, build, scope products/board/)
raised: 2026-10-28
claims: products/board/ (dossier.py new, server.py, panes.py, graph.py, people.py, check.py, static/graph.js, spec.md;
tests/test_dossier.py new, test_canvas.py, test_real.py, test_results.py);
lessons/scroll-and-resize-cytoscape-before-measuring-a-node-for-a-real-tap.md; docs/status/board.md.

Note: the fence refused the inbox link `merge-requests/`, so this request was written to the session's scratch
folder, `/home/user/querynzv4-work/scratch/board-11/board-11.md`.

## What it does

1. **Ruling 110 (1).** An entity result in the results pane no longer lists "matching here: …". Its count and
   registers stay. `test_results` asserts the line is absent, and check item 25 asserts it on a live page.
2. **The dossier (`dossier.py`).** It is one entity (a `pub.groups` group) or one lone row, on one pane. It is built
   from the published views and from pub.groups, pub.links, pub.names and pub.decisions alone. No link is made by
   looking. There is no claims section: no claims lane publishes yet, and the pane says so. It shows:
   - the name and the note that it is the fullest filed name (ruling 105);
   - the names as filed, each with its row count, a row counted once;
   - a timeline of the rows by register, in date order. Each row shows its role, the company or body its relation
     names, its dates, its fields whole with their flags (ruling 102) and its citation, with links to its own pane
     and to its register's table;
   - the companies and bodies it holds a role on, in date order;
   - money as filed: donations by year. Each year is summed only from the filed amounts the view adds, and every
     addend is listed. A disclosure, a replaced row and a row with no amount are listed and not added. Declared
     interests are listed by year;
   - related companies, with the relation as the column states it;
   - near matches with their reasons;
   - whether the group is contested, and every decision;
   - a link to the full subject report at `QV4_REPORT_URL/report/<ref>`, using the group's own row key.

   A row in a group opens its group's dossier. A suppressed row is never gathered or named (hard limit 16). When one
   is chosen, the pane says only that its name is suppressed.
3. **Opening it.**
   - `GET /dossier?d=<entity:group id|view:key>&q=&…` answers the pane's HTML.
   - On the search tab the dossier sits under the graph, beside the results. On the graph tab it sits under the
     graph.
   - `graph.js` fetches it with no reload when a result is clicked or a node is tapped (not a lineage frame). It
     sets `d=` in the address with `history.replaceState`. A reload then renders the dossier server-side, and
     `#side`'s `data-start` redraws the graph.
   - Without script, each result carries a plain "dossier" link, and the graph tab shows the dossier of its
     centred row.
   - The content security policy is unchanged.

## Cost (live, 28 October)

Every query goes by row key or group id: people.entity's indexes, one query per far view, the declared interests by
`member_return`, and one read of the documents' states.

| Dossier | Rows | Gather | Pane | `/dossier` over HTTP | Size |
| --- | --- | --- | --- | --- | --- |
| Largest group | 1,220 | 0.10 s | 0.02 s | 0.14 s | 0.9 MB |
| "Graeme Hart", 20-row group | 20 | 0.044 s | | 0.10 s | |
| "Graeme Hart", 7-row group | 7 | 0.042 s | | | |
| "Graeme Hart", lone donation row | 1 | 0.028 s | | | |

- The search page for "Graeme Hart" in entities took 3.03–3.05 s without `d=` and 3.06–3.08 s with it. That is
  about 0.03 s added; the 3 s is the search page itself.
- The two-second floor holds: `test_a_search_answers_within_two_seconds` is green, and the new live test holds each
  dossier under 1 s and a page with one open within 0.5 s of the same page without.

## Verified

- `python -m products.board check`: green, with new item 25.
  - The largest group holds every row but the suppressed, each once on the timeline.
  - The group with the most party-return rows sums each year to an SQL sum of the views' own amounts, read apart
    from the dossier.
  - A suppressed row, when chosen, is not named.
  - Both tabs carry the dossier with `d=`, and there is no "matching here".
  - The first run was red on item 5's pane count: the placeholder dossier counted as a pane. The fix excludes it
    there, as the side graph already is.
- `tests/test_real.py`, `test_night`, `test_canvas` and `test_dossier`: green together, 48 tests in 1 m 43 s.
  `test_real` plants an added disclosure, and item 25 turns red.
- `tests/test_dossier.py` (9 fixture tests) was mutation-checked. Each of these planted faults turns a test red:
  a replaced row added, a disclosure added, the timeline reversed, a suppressed chosen row gathered, a suppressed
  far row named.
- `QV4_INTEGRATOR=1 bin/fast products/board`: green in 45.0 s. Root `test_imports_one_way`, `test_reading_limits`
  and `test_lessons_search` pass.
- Headless Chrome on a scratch server (127.0.0.1:8493), "Graeme Hart":
  - A real click on an entity result opened the graph to the right and the dossier under it: 7 sections, 20
    timeline rows, `d=` in the address, no reload.
  - After a reload, the server-rendered dossier and the graph (from `data-start`) were back.
  - A real tap on a node beside the results opened that node's dossier.
  - A row result's click opened its row's dossier.
  - On the graph tab, a tap on an entity node opened its dossier under the graph.
  - `d=` for the largest group rendered 1,220 timeline rows.
  - No console error, and no request off the board: 34 requests, 4 to `/dossier`.

## Known limits

- No claims section until a claims lane publishes.
- `pub.mp_interests` is read by `member_return`, which the lane's table does not index: a sequential scan of 25k
  rows, a few milliseconds.

## The integrator must

1. Merge `session/board-11`.
2. **Restart `qv4-board` at the release.** This brings a new route (`/dossier`), a new `graph.js` hash and a new
   page layout. No table, unit or setting changes.
3. Regenerate `lessons/INDEX.md` for the one new lesson.

## Result (integrator, 28 October 18:20 NZDT)
Merged f4a55b1, gate green at the second run (the first refused on test_every_links_rule_in_pub_links_has_its_words: the fifth links rule, refiled-name@1, had gone live between the session's close and the gate; its words were added to the board's RULE_WORDS, RELATED_NOTE and the lineage frame's WORDS at the merge). Released; `qv4-board` restarted 18:20. Branch and the working copy retired. board-12 (rulings 111, 112) launched.
