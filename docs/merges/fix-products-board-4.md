# fix-products-board-4: a many-rows dossier is shown by view (ruling 116's ministers)
branch: fix/products-board-1 (pushed, 55bbfbe; one commit on e9930c7)
session: fix-products-board-1 (Opus, fix weight, scope products/board/)
raised: 2026-10-28
claims: products/board/ (dossier.py, check.py, server.py, people.py comment, spec.md, tests/test_dossier.py, tests/test_real.py); one card; one lesson (regenerate lessons/INDEX.md); docs/status/board.md
publish: nothing. tables.sql: unchanged. static/: unchanged.
**After the merge: restart `qv4-board`** at the release, so the live board serves the new dossier.

## The fault

Ruling 116's member-on-the-day@1 made one minister's group 30,836 rows. `dossier.gather` stops at 1,500
(`people.PANE_ROWS`), so item 25 went red: "the dossier of beehive:…#minister/1 holds 1500 rows and 0 suppressed of 30836".

## The fix

A group of more than `dossier.MANY_AT` (300) rows: views and names as filed counted in SQL (`counted`), money by year
summed in SQL as `addends` adds (`money_counted`); the newest 50 rows of each view read (`view_rows`, keys first for a
view of up to 2,000 rows: computed mp_expenses 0.20 s → 0.02 s); the page says "30,836 rows across 9 views", lists the
newest 40 and says how many more, and shows each view closed with its count, rows newest first, paged by `dv=`/`do=` on
`/` and `/dossier`. A suppressed row is never read, named or counted on the page. 300 rows or fewer: as before.

Check item 25 (`many_problems`): each view's count on the page equals the group's rows of that view counted apart, plus
its suppressed; all add to the group; names count the shown rows once; the whole count said; one page per view; the
newest list; money equal to `dossier_sums` (now also by group id); gathered and rendered inside two seconds.

## Measured, live, largest group (30,836 rows)

Before: 0.55 s, holding 1,500 rows (red). The old path uncapped: 4.4 s, a 58.7 MB page. After: 0.54 s, 469 KB.
One group of each of the 17 views in groups over 300 rows: no problems from item 25.

## Proof

`QV4_INTEGRATOR=1 bin/fast products/board`: green (45.6 s). Slow tests (live, read-only): 27 pass, 1 fails:
`test_lloyd_budd_s_rows_pub_names_does_not_hold_fold_with_his_entity_by_name`, the failure your uncommitted change on
`integrate/fix-links-5` already answers (ruling 114 put charity_officers into pub.names). This branch leaves that test
untouched; take yours. `test_the_outside_check_is_green` and the dossier tests pass. Mutations: a view dropped from the
count goes red on a 3,000-row, three-view fixture and on live; a disclosure added to the year goes red as before.

## Card raised

`a-minister-s-name-searched-takes-the-search-page-past-two-seconds`: the search page for "Simeon Brown" takes 4.9 to
6.2 s without any dossier (the scan 3.1 s, near names 1.6 s, the entity gather 1.4 s); the dossier adds 0.7 s.

## Result (integrator, 28 October 23:58 NZDT)
Merged 5356f1d as `integrate/fix-products-board-4`, gate green at the first run (the board's slow tests: 15 minutes). At the merge the Lloyd Budd fold test was rewritten to assert one entry whichever way the rows arrive (ruling 114 put the celebrants and charity officers into the lane). Released; `qv4-board` restarted and answering. Branch and working copy retired. The slow-search card ("Simeon Brown") stands.
