# board-8: ruling 105, the graph's people state (the rows state unchanged)
branch: session/board-8 (pushed, af28b5a; two commits on ae89e90)
session: board-8 (Opus, build, scope products/board/)
raised: 2026-10-28
claims: products/board/ (new people.py, tests/test_people.py; graph.py, panes.py, server.py, search.py, check.py,
static/graph.js, spec.md, tests/test_panes.py, tests/test_canvas.py); lessons/ask-pub-links-for-all-the-rows-at-once-not-once-per-row.md;
docs/status/board.md.

## What it does

1. **The switch.** "show: rows · people" above the graph (`graph.switch`). The state rides every href as `g=people`
   (`search.Boxes.people`, written only when on), so a view reopens in it. The rows state is unchanged; its key, edge
   list and answer are byte-for-byte as before.
2. **The fold** (`people.fold`, after `graph.build(people=True)` keeps the rows and their record relations and skips
   a row's own links). It reads `pub.groups` by the row keys in hand and draws one node `entity:<group_id>` per group.
   The node is labelled by the fullest filed name in `pub.names` (most words, then most letters, then first by key)
   with "n rows, n registers". An organisation joined by its official number names the number in its pane. Every edge
   is moved to its group ends. An edge inside one entity is dropped and counted. Duplicates merge, and each cause keeps
   the row pairs it came from, which the tooltip lists. A row in no group is a lone row. A contested group is marked.
3. **Near, one hop** (decision 2): `pub.links` near grade from the matched rows, at most 10 per row with the rest
   counted, dashed in the near colour, the reason on the line. The far row is pulled in as its own entity or lone row
   and never merged. A `pub.decisions` row on a pair whose rows land on two nodes is shown on their line.
4. **Compound open.** Tap an entity: `/graph.json?open=<group_id>` answers its rows (40 at most, the count said) as
   Cytoscape children in their register colours, joined by the group's own links labelled with the rule. Tap again to
   close it. A lone row grows as before.
5. **Entity pane** (path step `entity:<group_id>`, double-tap): the name and the note that it is no link, the count,
   contested, the rows by register, the confirmed links with the rule, the evidence whole and any decision, and the near
   links with their reasons and the row each leaves from.
6. **Hard limit 16.** A row whose name is suppressed is never gathered. It keeps its own node and draws no near link,
   and no group counts, lists or labels it. Ruling 102: evidence is shown whole on the board.

## Cost (live, 28 October)

- Every new query goes by row key or group id on an index: groups_pkey, groups_group, rows_pkey,
  links_row_a_row_b_rule_key, links_row_b, decisions_rows. That is five queries per graph, plus one per view that can
  suppress.
- The fold itself takes 20 to 28 ms. The people state drops the rows state's own links step, which costs 130 to 155 ms.
  So a people graph costs about 0.1 s less than the rows graph of the same search: smith 1.98 s against 2.06 s, hart
  1.83 s against 1.99 s.
- Opening the largest group (1,220 rows, 1,225 links) takes 80 to 150 ms.

## Verified

- `QV4_INTEGRATOR=1 bin/fast products/board`: green in 57.1 s. Root `test_imports_one_way`, `test_reading_limits` and
  the spec tests pass.
- `python -m products.board check`: green in 62 s, with the new item 22. Item 22 goes red when the label rule is
  broken, when near links are dropped, or when the fold stops keeping a suppressed row apart.
- `tests/test_real.py` plus the contrast tests (`test_night`, `test_canvas`): green. On the first run
  `test_a_search_answers_within_two_seconds` was red because it ran straight after the 60 s check. It is green alone
  and on a full re-run. The search code is unchanged.
- Headless Chrome against a scratch server on 127.0.0.1, on "smith" with `g=people`:
  - 39 nodes: 6 entities drawn as rounded squares and 33 lone rows with dotted borders.
  - Near lines are dashed and show their reasons.
  - A real tap opened a 157-row entity: 40 children in 3 register colours, inner links labelled with the rule. A second
    tap closed it.
  - Double-tap opened the entity pane.
  - No console errors, and no requests to any address but the board's own.
- Mid-session one search timed out (20 s) on a cold `pub.parliament_written_questions`: 12 s cold, 0.8 s warm. This
  branch did not cause it.

## The integrator must

1. Merge `session/board-8`.
2. **Restart `qv4-board` at the release**: new routes, new path step, and a new `graph.js` hash read at start. No
   table, unit or setting changes.
3. Regenerate `lessons/INDEX.md` for the new lesson.

## Result (integrator, 28 October 10:44 NZDT)
Merged 69fe1a8, gate green at the first run. At the merge the state was named "entities" on the switch, in the address (`g=entities`) and in the answer's mode, on Arthur's correction of the integrator's word "people" (the code keeps `people` as the state's name); the lessons index rebuilt. Released; `qv4-board` restarted 10:44, the switch live above the graph. The lineage frame for the links lane's new "related" grade (links-3) goes to a later board session. Branch and the working copy retired.
