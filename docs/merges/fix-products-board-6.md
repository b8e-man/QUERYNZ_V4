# fix-products-board-6: ruling 120 (the graph is entities only), ruling 118 (the full-name fold leaves), the graph fold's card
branch: fix/products-board-6 (pushed, 2a13cff; one commit on 9d788fb). The working copy is `fix-products-board-1`; its
local branch `fix/products-board-1` was pushed to `fix/products-board-6` because origin still holds a stale
`fix/products-board-1` from 25 October (Arthur may delete it: `cd /home/user/querynzv4 && git push origin --delete fix/products-board-1`).
session: fix-products-board-1 (Opus, fix, scope products/board/)
raised: 2026-10-29
claims: products/board/ (graph.py, collapse.py, people.py, search.py, server.py, panes.py, check.py, static/graph.js,
spec.md; tests/test_collapse.py, test_people.py, test_results.py, test_entity_graph.py, test_panes.py, test_real.py);
cards/the-graph-tab-s-fold-is-mislabelled-in-rows-mode-and-cites-the-superseded-filing.md (closed);
lessons/a-mode-removed-from-a-default-changes-every-caller-that-never-named-it.md; lessons/INDEX.md regenerated.
publish: nothing. tables.sql: unchanged. units: unchanged.
**After the merge: restart `qv4-board`** at the release, so the live board serves the new code (graph.js changed).

## What it does

1. **Ruling 120 (the card's fault 1 overtaken).** The graph has one state, entities. Gone: the rows mode, the switch
   (`graph.switch`, `id="state"`), `g=` (`search.Boxes.people`, `search.PEOPLE`), the rows-only `pub.links` hop in
   `graph.build` and its `people` argument; `build` always folds into the groups. An address naming `g=rows` or
   `g=entities` is read without it and opens the entities graph; the old `/graph?…` redirect drops it. A graph fold's
   name is the fullest of every member's, and its type and colour come from the register most of its members' rows
   in hand are in (`collapse.drawn_as`), never the member that sorts first; its id is still `fold:<member>`.
2. **Fault 2.** Causes merging into one edge, in the entity fold (`people.fold`) or the collapse fold
   (`collapse.fold_graph`), cite the latest filing: a row marked not in the latest file never wins, then the later
   `last_file` (`people.cite_latest`).
3. **Fault 3.** The "N more match: narrow the search" note counts a fold's members' matching rows as drawn
   (`graph.rows_in_hand`).
4. **Ruling 118.** "A shared full name, with middle names" leaves `collapse.CRITERIA` and `search.COLLAPSE_CHOICES`;
   `cl=full` is read without it (and `fold:full:…` is no fold). pub.names is now asked for `fl_key` alone.

## Tests that fail on main and pass here

Run against an export of 9d788fb with this branch's tests copied in:
- (1) `test_results.py::test_the_graph_has_one_state_entities_and_no_switch` (main: the switch is on the pane);
  `test_collapse.py::test_a_graph_fold_is_typed_and_coloured_by_the_whole_fold_never_its_first_member` (main: charities).
- (2) `test_collapse.py::test_causes_merged_into_one_edge_cite_the_latest_filing` (main: cites the July row) and
  `test_people.py::test_an_entity_s_merged_causes_cite_the_latest_filing_never_one_not_in_the_latest_file`.
- (3) `test_collapse.py::test_no_more_match_note_when_every_matching_row_is_drawn_inside_a_fold` (main: "1 matching
  rows drawn as 1 nodes; 2 more match").
- (4) `test_collapse.py::test_the_shared_full_name_left_the_list_and_an_address_naming_it_is_read_without_it`.

## Measured live (read-only), "Arthur Falls", "a shared first and last name" ticked, graph open

| | main, rows (the default) | main, entities | this branch |
| --- | --- | --- | --- |
| The fold | "7 entities, 7 rows", charities colour | "2 entities, 7 rows", companies | "2 entities, 7 rows", companies |
| Simply Industrial "shareholder of" cites | `…/shareholder/af38…` (July, not in the latest file) | the same | `…/shareholder/b23c…` (August, in the latest file) |
| The note | "1 matching rows drawn; 6 more match" | "1 … as 1 nodes; 6 more match" | "7 matching rows drawn as 1 nodes" |
| Switch / `cl=full` offered | yes / yes | yes / yes | no / no |
| Render, two runs | | 4.76 / 4.67 s | 4.82 / 4.68 s |

An address with `g=rows&cl=name&cl=full` opens the entities graph with `cl=name` alone, the same fold.

## Verified

- `bin/fast products/board`: green (73.1 s; the 60 s target missed, recorded; 71.5 s of it the sample fill).
- Slow tests, whole board suite, live, read-only: the first run turned four red that took `build`'s rows default
  (item 7 of the outside check and three tests asserted every node id is a row); fixed with `check.rows_drawn`, and
  item 21's JSON-to-SVG node comparison now maps an entity to the row its SVG link opens on. Last run: 30 passed, one
  red, `test_the_tabbed_search_answers_within_two_seconds_in_both_states`, which runs no code this branch changes;
  passed twice alone at 1.87 s (the slow-search card stands). `test_the_outside_check_is_green` passed alone.

## Lesson

`lessons/a-mode-removed-from-a-default-changes-every-caller-that-never-named-it.md`.

## Known limits

- An entity node on the no-script SVG still opens on its first row in hand (as before); the canvas opens the entity.
- The colour rule weighs rows in hand; a group's rows not drawn do not count.

## Result (integrator, 29 October 15:54 NZDT)

Merged: `e58a404 merge integrate/fix-products-board-6: gate green`. The branch alone was refused by the first
gate (15:25 to 15:37) on one test, `tests/test_generators.py::test_the_committed_records_generate_cleanly`:
the card was closed but `docs/board.md` was not regenerated. The integrator merged the branch into
`integrate/fix-products-board-6` off main, ran `bin/board` (b7a578b), and the second gate was green at 15:53
(the fast tier for the whole repository and the board's slow tests; no module with a load.py, nothing staged).
Released; `qv4-board` restarted so the live board serves the new graph.js. Working copy
`fix-products-board-1` removed; the stale remote `fix/products-board-1` and the merged `fix/products-board-6`
are Arthur's to delete (the hook refuses a deleting push). `board-14` (ruling 119) launched after this merge.
