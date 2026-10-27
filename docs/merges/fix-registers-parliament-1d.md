# fix-registers-parliament-1d: the check answers inside the board's 120 s (1 min 55 s → 36 s)
branch: fix/registers-parliament-1 (pushed, 0d0969a; one commit on main's 0f87dfc)
session: fix-registers-parliament-1 (Opus, fix weight)
raised: 2026-10-28
claims: registers/parliament/ (check.py, load.py, tables.sql, spec.md, tests), one lesson, docs/status/parliament.md

`python -m registers.parliament.check` ran the Postgres street pattern over
every text column of the three views on every run. checks/module_checks.py
gives a check 120 s, so the board recorded "the check did not run (exit 3):
no answer in 120 s" every night: red with no finding.

## What changed

- `load.stamp_scan`: after the views are refreshed (in `publish`, inside its
  transaction, and after `views` in a `--schema` proof), the load runs the
  check's own pattern (`check.STREET_SQL`, still written apart from
  shapes.py) over every row of every text column of each view and writes
  `street_scan`: per view and column, the rows scanned, their `loaded_at`
  and the count holding a street with the flag false or absent. New table
  in `TABLES`, regenerable, wiped and refilled each load.
- `check.shown`: the flag counts against `address_flags` stay whole (booleans
  only, instant). The pattern runs afresh over a fixed sample only: the
  first `SAMPLE` = 5,000 rows of each view by md5 of the key. The check now
  fails when a view has no stamp, a text column has no stamp line, the
  stamp's rows or `loaded_at` differ from the view's (a stamp of another
  load), the stamp found a street, or the sample finds one.
- The check's statement limit for this step drops from 300 s to 60 s.

What it proves is unchanged: flags equal the load's `address_flags` lines
(whole), and every row is searched for an unflagged street by the second
pattern (now at the load, held to the rows by count and load time), with a
fresh sample as proof the stamp is honest.

## Measured on the live tables (node2, 28 October 2026)

| | Before | After |
| --- | --- | --- |
| `python -m registers.parliament.check`, wall time | 1 min 54.7 s | 36.4 s |
| The whole scan, now in the load (read-only timing of the same statements) | | 99.1 s (written questions 70.2 s, pages 27.6 s, API 1.3 s) |

The load's longest new statement (70 s) is under its 600 s query limit;
its deadline is 60 min.

Live output after (figures only): written questions 683,524 rows, flagged
question 1,988 / reply 699; API 6,752, 0; pages 8,836, 182; a street with
no flag 0 in each fixed sample of 5,000. Red on five lines, none from this
fix's logic:
- three "the load's whole scan has no line for the view": `street_scan`
  does not exist live until the first load of this branch. Clears at the
  merge's staging load.
- two wayback lines: 10,067 documents taken, 8,836 records read. The pull
  grew since the last load; the next load reads them.

## Tests

`QV4_INTEGRATOR=1 bin/fast registers/parliament` green (50 tests, 44 s).
New: `test_the_check_scans_a_fixed_sample_never_every_row` records every
statement the check sends and fails if the pattern runs without the
sample bound (mutant `street_counts(conn, vs, vn)` with no sample: red,
run under `python -B`); with the sample cut to one row, a street planted
outside it is missed by the fresh scan and caught by the load's stamp.
`test_the_check_fails_without_the_load_s_whole_scan_or_with_another_load_s`:
stamp of another load, stamp emptied, stamp table dropped. The planted-street
mutant test now also re-stamps and sees both lines.

## What the integrator does at the merge

1. Gate and merge. The staging load (`load` + `publish`) creates
   `parliament.street_scan` and stamps it (about 100 s more than before),
   which also reads the wayback pages the pull added since the last load.
2. Run `python -m registers.parliament.check` after: the three stamp lines
   should be gone.
3. Lessons index: one new lesson, not indexed on this branch.
4. This request was written to the session's scratch folder because the
   fence refused the inbox link; copy it into `merge-requests/`.

## Lesson

`lessons/a-check-the-board-times-scans-a-fixed-sample-and-holds-the-load-s-whole-scan-to-its-rows.md`:
a board check doesn't scan every row of a growing table; the load stamps the
whole scan with its rows and load time, the check holds the stamp to the
rows and re-samples. "Only the rows loaded since" did not fit: this load
rebuilds every row nightly.

## Result (integrator, 28 October 09:56 NZDT)
Merged 959f474, gate green at the first run; the staging load wrote `parliament.street_scan` (700,333 rows in 98 s). The lesson's rule line shortened under 240 characters at the merge. Released. The check run live after the merge answers inside the limit and is red only on the wayback count (10,067 held of the provider's 10,237: the corpus grows between the pull and the check, a trailing red that clears each night and returns as the provider adds pages; a lane question whether the floor should read against the count at the pull). Branch and the working copy retired.
