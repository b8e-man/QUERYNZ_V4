# links-4: pub.entities, one row per entity (ruling 123)
branch: session/links-4 (pushed, 88acb45; one commit on main's dd03637)
session: links-4 (build, Fable, scope links/)
raised: 2026-10-30
claims: links/tables.sql (new table `links.entities`), build.py (`build_entities`), build_all.py, publish.sql (`pub.entities`), check.py (item 11, and entities in item 3), spec.md, pane.md (new), README.md, __init__.py, tests/test_entities.py (new, six tests; all six fail on main), tests/test_old_ledgers.py (the job-sequence test learns the step); docs/status/links.md; two cards; one lesson (regenerate lessons/INDEX.md at the merge)
publish.sql: **changed** (one view added). tables.sql: **one table added**, made by `links.ddl()` at the job's start (no DDL by hand).
job after the merge: apply `links.ddl()` (the table) and then the lane's publish DDL (the view reads the table; a lane with no load.py is not republished by the gate); queue `qv4-links-build`, then `python -m links.check` live. The board's own check will list `pub.entities` as uncatalogued until the board catalogues it in the merge after this one (the board, scan, report and site read it under rulings 117 (4), 119, 120).

## What it builds

`links.entities`, rebuilt whole after the groups in `build_all.run`,
`build.build_all` and `build --groups`, published as `pub.entities`:
`entity_id` (the group id, or the lone row's ref), `kind` (person,
organisation, estate: the kind of the row that gives the name), `display_name`,
`rows`, `registers` (distinct, sorted COLLATE "C"), `contested` (the group's),
`politician` (any row), `built_at`.

The display name, the one ordering every reader shares (pane.md): among the
entity's rows of `pub.names`, the filed name with its whitespace folded, the
most words, then the most characters, then the smallest ref by bytes
(`links.ORDER`). It is ruling 105's decision 1 as the board's `people.fullest`
reads it, so the board's names do not move. A group holding no `pub.names` row
(4,333 on live: a company and its Gazette liquidation row joined by
`official-number@1`) is an organisation named from `links.bodies` by the same
ordering; nothing is blank.

## Measured

The build's SQL run on live through the session reader (read-only, 43 s),
against the brief's figures:

| | brief | this SQL |
| --- | --- | --- |
| groups | 724,964 | 724,964 |
| lone rows | 1,872,249 | 1,872,249 |
| entities | 2,597,213 | 2,597,213 |
| rows counted | | 5,025,996 (= 3,153,747 grouped + 1,872,249 lone) |

By kind: 2,587,173 person, 9,845 organisation, 195 estate. 43,395 contested,
798,692 politician, 82,878 on more than one register, the largest 30,845 rows.
In the scratch build on the sample: 5 entities from 4 groups and 1 lone row
(the slow test's own rows). No model, nothing fetched, nothing outside links/.

## Checks

`check.py` item 3 counts `pub.entities` against the table; item 11 counts the
view against the groups and the lone rows (each side missing counted apart,
rows summed, kinds, blank names). Fast tier for links: green, 41 s, 45 tests
(baseline 40 before). The lane's 14 slow tests: green. `test_entities.py`'s
six tests fail on a copy of main (run in the scratch folder).

## Carded

- `the-display-name-ordering-counts-a-title-and-a-register-s-suffix-as-words`:
  the ruled ordering names a minister's entity "Brown, Simeon (4)"; one line
  to fold if Arthur rules it.
- `a-coupled-donor-s-part-rows-are-entities-beside-their-donor-row`: 63 lone
  part rows (ruling 73) are entities beside their donor's; the brief's count
  includes them.

## Not built

The two other items of 30 October (organisation rules on every row naming a
body; bodies under one name across registers): not ruled.

Lesson: `a-published-entity-is-counted-from-the-groups-and-the-rows-in-no-group-never-from-the-names-alone`.

## The whole-repository fast tier, run here for information

RED on one test, `tests/test_generators.py::test_the_committed_records_generate_cleanly`:
`docs/board.md` is stale by the two cards this branch adds (open 155 → 157).
The card board is a generated file, rebuilt by the integrator at the merge
and edited by nobody; nothing else failed. The run took 742 s against the
300 s target (recorded by bin/fast); the lane's own tier is 41 s.
That test's run rewrote `docs/board.md` in this working copy; the file is uncommitted, not on the branch, and the scope hook refuses the session even a restore, so it stays as an uncommitted change here until the working copy is removed.

## Result

Merged 30 October 2026, 11:18, as b5099ba (integrate branch 191ff50; gate green, marked; the readers' slow tests ran
since publish.sql changed; nothing staged, the lane has no load.py). One integrator commit on the way: the lesson's
first line cut to 229 characters (it was 254, which stops `bin/lessons-index`), the lessons index and the card board
regenerated. After the push and the release: `links.ddl()` then `links.publish_ddl()` applied on the live database
through the owner login at 11:20 (`links.entities` and `pub.entities` exist, the view empty until the build), and
`qv4-links-build` queued. The board catalogues `pub.entities` in the merge after this one (links-5's integrate branch).
The two cards stay open; the display-name fold is Arthur's. `links-5` (ruling 125) launched from the merged main at
11:22. Working copy and local branches retired; `session/links-4` on the remote is Arthur's to delete.
