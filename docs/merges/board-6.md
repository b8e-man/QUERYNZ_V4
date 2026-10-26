# board-6: ruling 92 items 2, 4, 5 and 6 on the search tab (rulings 80 to 91 kept)
branch: session/board-6 (pushed, 8a70bd6; five commits on da00cf7)
session: board-6 (Opus, build, scope products/board/)
raised: 2026-10-26 (written to the session's scratch folder: the fence refused the inbox link; move it to
inbox/merge-requests/)
claims: products/board/ (catalogue.py, search.py, panes.py, server.py, near.py, check.py, spec.md; new given_names.py;
tests: new test_far.py, test_given_names.py, test_table.py, test_modes.py, test_real.py extended);
lessons/count-a-row-once-across-its-name-columns-when-counting-names.md; docs/status/board.md.
No card opened or closed. `graph.py` and the SVG styles in panes.CSS untouched (board-5's).

## What it does

1. **Item 2, names not keys.** `catalogue.pointers(v)`: a shown field that names another view's row (the parent tuple,
   a Relation matched to the far view's key, and `POINTERS` as data: holder and body NZBNs, held_key, group_key, the
   gazette's register keys). The results pane, the row pane and the table show the far row's title as a link, the key
   in the hover title; "(row not held)" beside the key where the far view lacks it. `search.far_rows`: one query per
   far view per page. Live: a director's company reads e.g. FOLEY WINES LIMITED, not companies/9429000001311.
2. **Item 4, near names.** A "near names" submit beside the box (`near=1`). The pane lists, per given name typed, the
   given names filed with the same surname words in the registers searched (suppressed and revoked rows never read):
   forms from `given_names.GROUPS` (about 160 groups, English and Māori, folded), names sharing the first three letters,
   or one letter apart; each with its row count (a row counted once across its Names). Each is an href adding it as an
   alternative in the name's place, `garry|gary payinda` (box or name field); `search.word_re` makes that an "or"
   within the word. The pane says a variant is a candidate, never a link (plan 4.9).
3. **Item 5, register tables.** Each held register's name in the left pane opens `t=<view>&o=<offset>` (riding every
   href and the form): its main view (`catalogue.MAIN_VIEW`, else the first), a chooser for the others, the count of
   all rows, 100 one-line rows in the view's order (title and fields, cut at 40 characters, whole value on hover),
   "more" appending 100 to 1,000. A search with the table open renders search, results, table, then the path panes.
4. **Item 6, all or any.** Radio inputs in "narrow by field": all (default, unchanged) or any (`mode=any`, in hrefs only
   when any). Under any a row matches on any filled field its view holds, and each result says "matched: …"
   (`_matched_<field>` columns). Near matches use the any search for exclusion. The graph tab stays "all".
5. **Check** cases 16 to 19 (one per item), each shown red with its rule broken in memory.

## Checked

- `QV4_INTEGRATOR=1 bin/fast products/board`: green (44.7 s).
- Whole repository (`QV4_INTEGRATOR=1 bin/fast`): one red, `tests/test_generators.py::test_the_committed_records_generate_cleanly`,
  because the committed `lessons/INDEX.md` lags the new lesson (the fence refuses generated files). Regenerated in the
  working copy, it passes. 634 s, over the 300 s target (recorded).
- `python -m products.board check` against live data: green (36 s).
- Slow tests (`-m slow`): 16 passed, five new (a director's company by name; the near-names button over HTTP, 200; a
  register table with 100 rows and its count; both modes against the same four fixture rows in a temporary table).

## For the integrator

1. Move this file into `inbox/merge-requests/`.
2. Merge (beside or after board-5; this branch touches no line of `graph.py`), **rebuild `lessons/INDEX.md`**
   (`bin/lessons-index`), then **restart `qv4-board`** at the release. No table, unit, setting or other module changes.
3. If board-5 merges first and changes how `graph.py` uses `search.search` or `Boxes`: `Boxes` gained `table`,
   `upto` and `mode` with defaults, and `search.search` a `mode` keyword defaulting to "all".

## Result (integrator, 26 October 13:35 NZDT)

Merged as fe032a7 after board-5 (d2d47a7). The merge onto board-5 conflicted in `products/board/spec.md` and `docs/status/board.md` only; the integrator folded board-5's graph sentences into board-6's versions (2,912 bytes). First gate red on `tests/test_generators.py` (the lessons index missed the new lesson because the generators ran on a tree with unmerged files); regenerated at ea78411, second gate green. Released and `qv4-board` restarted 13:33; near names, a register table and the any-field search answer 200. The report's copy of the board's search went red against this branch's `search.py` (the copy test does its job): `fix-products-report-2` re-copies it and follows. Branch and working copy retired.
