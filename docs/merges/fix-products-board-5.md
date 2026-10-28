# fix-products-board-5: a fold's dossier shows each member's records under its name
branch: fix/products-board-5 (pushed, 8f9d951; one commit on cd72cb5)
session: founding-f05585e (Fable, founding weight; the fix copy fix-products-board-1 was made by bin/fix but the scope hook binds this session to the main checkout, so the work was done on a branch there and the empty copy removed)
raised: 2026-10-29
claims: products/board/ (dossier.py, check.py, spec.md, tests/test_dossier.py, tests/test_collapse.py); docs/status/board.md one line.
publish: nothing. tables.sql: unchanged. static/: unchanged.
**After the merge: restart `qv4-board`** at the release, so the live board serves the new dossier.

## The ask

Arthur, 29 October: search "Arthur Falls", tick "a shared first and last name", and the graph and dossier should
show everything. The graph did; the folded entry's dossier showed two names and a line each, and in rows mode seven
bare rows, each needing another click. "Put the row data under the entity names."

## The fix

`dossier.gather_fold` gathers each member's own dossier (the first `dossier.FOLD_GATHERED` = 20 members; an entity's
or a lone row's, through `gather`, so a many-rows group keeps its by-view shape) and `fold_pane` prints each member's
"What the records say" (and its money where it has any) under the member's name, after the link the check reads.
In a fold of rows (the rows-mode graph node), rows of one group open one dossier: it is shown once and the other rows
say "one of the records shown under its entity above". Heading ids are per member (`m0-rows`, `m0-money`, …) so the
page's ids stay unique. Past 20 members a note says the rest open their own dossier.

Item 27 now also requires a timeline per listed member of the fold it reads. spec.md says so.

## Measured, live

The results' fold for "Arthur Falls" (one entity of six rows and one lone row): gathered and rendered in 0.16 s,
two timelines, Betelgeuse director and 100 shares, Ocean Beach officer, Simply Industrial's two filings (July not in
the latest file), Vesica 69 shares, the charity trustee since 14 August 2025. The rows-mode fold of its seven rows:
0.37 s, two timelines, five "shown above" notes. Item 27 live: 0 problems in 20.6 s.

## Proof

`bin/fast products/board`: green (43.8 s). `test_a_fold_s_dossier_shows_each_member_s_records_under_its_name` fails
on main (no records under the names, duplicate ids) and passes here. `test_the_fold_s_dossier_lists_its_members_as_
the_entities_they_are` sets `FOLD_GATHERED` to 0: it tests the listing on a fake reader that answers no other query.

## Not done here, seen on the way (the earlier assessment, same day)

- The graph tab opens in rows mode; its fold reads "7 entities, 7 rows" and takes the charity row's view and colour.
  Entities mode reads "2 entities, 7 rows". Default the tab to entities when a collapse is ticked.
- A fold merges the two Simply Industrial shareholder causes and cites the superseded July filing. Prefer the latest.
- The note "1 matching rows drawn; 6 more match: narrow the search" is false under a fold.

## Result (integrator, 29 October 10:53 NZDT)
Merged 9facd57 as `merge fix/products-board-5`, gate green at the first run (the whole fast tier, then the board's slow tests; no module with a load, so no staging). Released; `qv4-board` restarted. The three faults seen on the way (the graph tab opening in rows mode under a fold, the merged Simply Industrial edge citing the superseded July filing, the false "6 more match" note) are one card, `the-graph-tab-s-fold-is-mislabelled-in-rows-mode-and-cites-the-superseded-filing`, owner board. Branch retired; the empty fix copy was already removed by the founding session; its scratch folder removed, its scratch schema in querynz_v4_sample is Arthur's line to drop.
