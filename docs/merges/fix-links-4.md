# fix-links-4: ruling 116, member-on-the-day@1
branch: fix/links-1 (pushed, b0d5a55). **Builds on fix-links-3**: the same branch carries fix-links-3's three commits (to 1ce26f3) and these two (ec5b32d, b0d5a55). Merge the branch once and both land; main (ecc101a) has no change under links/, lessons/ or docs/status/links.md since the branch point 957bfd6.
session: fix-links-1 (Opus, fix weight, scope links/)
raised: 2026-10-28
claims: links/ (rows.py, rules.py, build.py, check.py, measure.py, spec.md, README.md, measurements.md section 11, tests/test_member_day.py new); one lesson, lessons/INDEX.md (regenerate at the merge if main's lessons moved); docs/status/links.md
publish.sql: **unchanged**. tables.sql: **unchanged**.
job after the merge: queue `qv4-links-build`, then `python -m links.check` live (items 4, 9 and 10), and read the run's `peak_mb`.

## How this was proved

As for fix-links-3: the owner login is refused on live and the sample database publishes none of the four views, so: (1) the new code run read-only over live through the read login, nothing written (the figures below); (2) the build step, check item 10 and measurement 11 on the real engine in a rolled-back schema of the sample database, with planted faults; (3) the live rows through each source's own SQL in slow tests. `QV4_INTEGRATOR=1 bin/fast links`: green (44 s). All of `links/tests`, slow included: pass.

**Mutations, each run and reversed by hand:** `rows.member_name` returning the printed name (title kept): 24 tests red, the four live ones among them. `rules.sitting` returning true (day ignored): 8 red, the four live ones and the engine test among them.

## The reading

`rows.SOURCES` gains four views. Each row is the member's name as printed (`name_filed`), the view's own key, the day in `started_on`, the document, no entity, `politician` true, kind person:

| View | Register | Name | Day | Not read |
| --- | --- | --- | --- | --- |
| hansard_speeches | hansard | member_name | sitting_on | 7,145 Speaker turns (no name) |
| parliament_written_questions, asker | parliament | from the title, before " to the " | question_released_on | 8,678 withdrawn (no asker) |
| parliament_written_questions, minister | parliament | minister_name | question_released_on | "No Minister", blank |
| beehive_release_ministers | beehive | name | published_on | |
| minister_diary_releases | ministers_diaries | minister | the last day of `month`, else last_on | |

A written question is two rows: refs `parliament:<key>#asker` and `#minister`, both under the question's view and key (so `pub.names` finds the row by view and key, as for a coupled donor's part; `part_of` stays null). The keys are read with the titles off: `rows.MEMBER_TITLES` (the rt hon, rt hon, right honourable, the hon, hon, honourable, dr, sir, dame, before or after the comma) and `MEMBER_POST_NOMINALS` (kc, qc, mp and the honours, with or without a comma), in `rows.member_name`, one list with tests. `keys.names` has its own list and takes a title off the front only (lesson of 26 October); keys/ is outside this fence, so the integrator may want to fold the two (no card raised: ruling 323's price).

**Live, read-only:** +1,398,092 rows (3,618,803 → 5,016,895); every ref unique; no key keeps a title word; the SQL asker equals the title's Python parse on all 683,524 titles.

## The rule

`member-on-the-day@1` (`rules.member_on_the_day`, `build.member_day_links`, after `seat-and-window@1`): the row's first and last name key and the member rows of that key whose term covers the day, a term from `from_on` up to, not on, `coalesce(ended_on, to_by)` (the polling day is the new term's; lesson filed). One → confirmed to that member row. Two or more → near to each, `NEAR_DAY_TWO`. None, with a member of the name at another time → near to that member, `NEAR_DAY_NONE` (names the members view's gap). No member of the name, or a day before 17 October 2020 (the view's first term) → no link, counted. Middle names that differ on both take a member out. First and last name, not the full key, because the House files middle names the others omit ("SEYMOUR, David Breen", "Seymour, Hon David"). Evidence: day, member, election, term, members of the name, members sitting, role, as printed, name read, and `parliament_member_id` for a turn or an asker (never decides). One link per row and member, copied in batches; these rows take no `name-only@1` star (their near grade is this rule's), so the near step does not grow.

| Rows of | Rows | Confirmed | Two | Near, other term | No member of the name | Before 17 Oct 2020 |
| --- | --- | --- | --- | --- | --- | --- |
| speech turns | 40,098 | 37,874 | 0 | 958 | 1,266 | 0 |
| question askers | 674,846 | 267,757 | 0 | 19,877 | 32,051 | 355,161 |
| question ministers | 674,846 | 314,262 | 0 | 0 | 5,423 | 355,161 |
| release ministers | 5,742 | 5,742 | 0 | 0 | 0 | 0 |
| diary releases | 2,560 | 1,911 | 0 | 0 | 30 | 619 |

The names finding none on a held day, ten confirmed pairs per view, named, and the reasons: `links/measurements.md` section 11. In short: all are members the view lacks for the day (list members who filled a vacancy; Sam Uffindell and Tama Potaka before their 2023 terms, the 2022 by-elections not held), and one name form, "Hon Kiritapu Allan", whom the House files "ALLAN, Kiri" (5,453 rows; never guessed; Arthur's if he wants a rule). Parliament's id agrees on every confirmed turn and asker: 133 ids, none on two members, no member under two ids.

## Checks

Item 10, new, SQL apart from the Python, against `pub.members`: every confirmed `member-on-the-day@1` link is a member view's row and a member row of its first and last name sitting on its day, no other member of the name sitting, no row confirmed to two members. Planted in the rolled-back sample schema, each red: the member's term ended before the day; a second member of the name sitting; a row confirmed to a member of another name (and so to two). Item 4 covers the four views with no change in code.

## Time and memory

Reading every source read-only through server cursors: 48 s for the 27 views, 69 s for the 31. The rule over the new rows read-only: 28 s, 277 MB peak. To come: 627,546 confirmed and 20,835 near links; about 628,000 more rows in the confirmed components held in memory (about +150 MB). From the 28 October runs (958 to 969 MB of 4,096): about 1.2 GB, so `memory_gb = 4` in jobs.toml still covers it (not edited); about three minutes more on 18 to 27. Read the first run's `peak_mb`.

## The board and the report

Nothing changed there. The rows join their member's group, so the board's fold shows a member's turns, questions, releases and diaries under the member. A `#asker`/`#minister` ref is found by `pub.names` view and key. Rule words are keyed by name: suggested for `member-on-the-day`: "a member's printed name, titles off, and the one member of that name sitting in the House on the row's day".

## After the merge

Queue `qv4-links-build`, then `python -m links.check` live. Nothing here prints a home address or a suppressed name: members of Parliament by their public names and seats, and counts.

## Result (integrator, 28 October 21:35 NZDT)
Merged 256f4f9 with fix-links-3, see that request's result. Rule words for member-on-the-day added to both catalogues at the merge. Build queued; the live check and the measured peak follow. For Arthur: the Kiritapu/Kiri Allan name form (5,453 rows joining nobody) and the list-replacement members (card of 28 October).
