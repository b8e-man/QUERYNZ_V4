# board-13: ruling 117, the dossier folds and states facts, the table sorts and resizes, the entity graph is one drawing
branch: session/board-13 (pushed, 5042766; five commits on 159ca0b: one per tranche, then the many-rows years read beside the page)
session: board-13 (Opus, build, scope products/board/)
raised: 2026-10-29
claims: products/board/ (facts.py new, static/table.js new, dossier.py, people.py, panes.py, search.py, server.py, graph.py,
collapse.py, check.py, assets.py, static/README.md, spec.md; tests/test_facts.py and tests/test_entity_graph.py new, test_dossier.py,
test_table.py, test_results.py, test_collapse.py, test_near.py, test_real.py);
lessons/a-picture-of-one-entity-is-drawn-from-the-whole-group-never-from-the-row-it-was-opened-at.md; docs/status/board.md.
publish: nothing. tables.sql: unchanged. units: unchanged.
**After the merge: restart `qv4-board`** at the release, so the live board serves the new code (one new static file, `table.js`).

## What it does (ruling 117)

1. **The fold (`facts.py`).** A line per view (`facts.SAYS`, data) says what its row makes the entity: the noun or the
   register's role column, the body a role relation names, where (an electorate, a party), the event (listed, removed).
   Rows equal on those are one entry, never folded by view. Each entry: one sentence, a small line (days, roles, counts,
   details), one citation line (register, each document once), the rows as filed closed under it. Near links fold the same
   way, said of the name the other record files. The many-rows dossier keeps its shape; each view's heading is its fact
   over all its rows, its years read in SQL (`dossier.spans`). The companies-and-bodies section left: its facts are the
   entries. A suppressed row never reaches the fold.
2. **Facts, not database shape.** The dossier head: the name, what it is (`facts.what_it_is`), one small provenance line.
   The entity card: what it is (`people.what_of`, one read by key per view whose word reads a column) and "from" its
   registers. A single-row card: its row's own fact. No "n rows, n registers", view names or "single-row entity".
   Check item 25 reads "records of n kinds".
3. **The table.** `ts=<column>` / `ts=-<column>` in the address, accepted only for a column the table shows
   (`search.table_columns`), ordered in SQL under the page's limit (`search.table_order`, the key last). Headings flip
   and set it; "more" keeps it. Cells hold the whole value (to 2,000 characters), one line clipped by default;
   `static/table.js` (no library, nothing sent) sets three lines or whole values and keeps dragged widths in
   sessionStorage.
4. **The fault.** Cause: in the entity state a graph centred on one of Lloyd Budd's rows drew only that row's one hop, so
   his entity showed the charity when opened from the charity officer's row and the company when opened from the
   director's row; the entity node took the first row in hand as its stand-in; a graph fold was named `fold:<n>`, its
   place in the answer. Fix: the centre is the group's rows (`graph.group_rows`, at most 40, connections first, then ref
   in byte order); the stand-in is the group's first row by ref (`people.stand_for`); a fold is `fold:<member>`
   (`collapse.stands_for`). Relation lookups are memoised per build (a minister's centred graph 2.3 s to 0.6 s).

## Measured, live (read-only), main on 8420 against this branch on 8496

| Page | Before | After |
| --- | --- | --- |
| Lloyd Budd's dossier | 0.06 s, 9.6 KB | 0.06 s, 8.4 KB |
| Lloyd Budd's entity graph, from the charity row / the director row | 0.04 s (8 nodes) / 0.04 s (2 nodes) | 0.08 s / 0.05 s (9 nodes each) |
| The largest group's dossier (30,836 rows), gathered | 0.55 s | 0.64 s |
| The same, the whole HTTP answer, two runs | 0.58 / 0.73 s, 476 KB | 0.76 / 1.04 s, 572 KB |
| A minister's centred entity graph | 0.38 s (1 node) | 0.51 s (11 nodes) |
| The companies table sorted by name / at row 1,000 by status | | 0.41 s / 1.04 s |
| "lloyd budd", "graeme hart", "john smith" searched, all registers | 3.07 / 3.08 / 3.5 s | 3.06 / 3.10 / 3.3 s |

The search page's three seconds with every register is as before (the card on searched names stands).

## Verified

- `QV4_INTEGRATOR=1 bin/fast products/board`: green (49.9 s).
- `python -m products.board check`: green.
- Slow tests (live, read-only), whole board suite: two failed on the first run. (a) The largest dossier at 1.04 s against the test's
  1.0 s: mine (the years of each many-rows view read by queries of their own, 0.29 s); fixed by reading them as window aggregates
  in `view_rows`' own sort (commit 5042766), 0.64 s. (b) `test_the_tabbed_search_answers_within_two_seconds_in_both_states` at
  2.02 s: the search scan alone, 1.88 to 1.99 s on main's code too (the entity gather 0.02 s on both); noted on the open card
  `a-minister-s-name-searched-takes-the-search-page-past-two-seconds`. Re-run of the dossier, Lloyd Budd and tabbed tests: all pass.
  The whole suite was not re-run after 5042766.
- New tests that fail on real data: `test_real.py` Lloyd Budd's dossier reads as facts (two entries, two near entries, five
  Gazette lists, no register, view or count words); his results say what he is; his entity graph is one drawing from each
  of his three rows and in both states, the fold lifting every plain node and line. Mutations: turning off
  `group_rows` or naming a fold by its place turns the live graph test red; folding by view, dropping the event from the
  key, or keying a no-line view by view turns `test_facts.py` red; dropping `stand_for` turns the fixture search test red.
- Headless Chrome on 127.0.0.1:8496: the companies table at one line 20 px, three lines 53 px, whole 69 px; a heading
  dragged 144 → 294 px and the row choice both survive a reload (sessionStorage, one key per view); a heading's descending
  arrow puts `ts=-title` in the address and the note says so; no request off the box.

## Found on the way (not mine)

- 04:30 the Parliament lane reloaded `parliament.written_questions` (683,768 rows, 825 MB); the first searches after read it
  cold and timed out at 21 s (the live board answered "hart" with a 500 for some minutes). It warmed by itself; nothing to do
  unless a reload happens during use.

## Known limits

- A written question in a minister's group reads "named on written questions to ministers": pub.names holds the asker only.
- A group past 40 rows is drawn from its first 40 (connections first, then by ref).
- In the many-rows dossier, a view's heading reads its noun; the role words are read from the page's rows.

## Result (integrator, 29 October 05:32 NZDT)
Merged 13f97a6 as `integrate/board-13`, gate green at the first run (the board's slow tests). Released; `qv4-board` restarted and answering. Ruling 117's four parts live: the dossier folds same-fact rows and states facts, the result cards say what an entity is, the table sorts and the reader sets row height and column width, the entity graph is one drawing from the whole group in both fold states. Branch and working copy retired. The slow-search card stands with its new measurement.
