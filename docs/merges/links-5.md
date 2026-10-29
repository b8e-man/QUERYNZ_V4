# links-5: the organisation rules on every organisation-named row, judged on the row's own date (ruling 125)
branch: session/links-5 (pushed, d9c4f38; one commit on main's b5099ba; main has since moved to 728d7b5, docs only)
session: links-5 (build, Fable, scope links/)
raised: 2026-10-30
claims: links/rules.py (`body_on_date`, `_judge_bodies`, `BODY_TAILS`, `WHEN_*`, `VIEW_DATE`, `RULE_SOLE_BODY_DATED`, `RULE_ONE_LIVE_BODY_DATED`, `NEAR_BODY_UNDATED_ROW`; @2 in `RETIRED`), build.py (`body_links` over every organisation-named row; the declared interests' SQL near step removed), check.py (item 9), measure.py (`_org_judgment`, m10, new `m12_ruling_125`), measurements.md (§12), spec.md, README.md, tables.sql (a comment only), tests/test_bodies.py (four pure tests and the slow engine test extended; all five fail on a copy of main); docs/status/links.md; one card; one lesson (regenerate lessons/INDEX.md and the card board at the merge)
publish.sql: unchanged. tables.sql: **no DDL change** (one comment). No DDL by hand.
job after the merge: queue `qv4-links-build`, then `python -m links.check` live. In the merge after this one: the board's and report's rule words for `organisation-sole-company` and `organisation-one-live-company` (`products/board/catalogue.py`, `products/report/catalogue.py`, keyed by the rule name without its version, so @3 is already covered) still say "a donation's organisation name … live in its year"; reword for every organisation-named row, judged on the row's date.

## What it builds

`organisation-sole-company@3` and `organisation-one-live-company@3`
(`rules.body_on_date`, through the one core `_judge_bodies` that `sole_body`
(@2) also runs on): every organisation-named row of every people view the
lane reads (shareholders, directors, MPs' interests, charity and society
officers, the Gazette views, local election returns, the donor and
disclosure rows) against every body of its name key on the companies,
societies, limited partnerships and charities registers (`links.bodies`), a
body on two registers counted once. "Live" is judged on the row's own date,
`started_on` .. `ended_on` as the view files it, never today: registered on
or before the window's end and not removed before its start. One body of
the name, live on the date: confirmed, sole. Several, exactly one live on
the date and none whose removal is undated: that one confirmed, the others
near. Otherwise near under `organisation-name@1`, the reasons @2's (a
donor row's text byte for byte as ruling 114 stored it; any other row's
says "on the row's date" and "the row carries no official number"). A row
with no `started_on` stays near on every pair with the reason "undated: the
row carries no date of its own, …", whatever the bodies' dates. The
evidence adds `dated`, `date_is` (what the view's date is), `row_view`,
`row_register`, `outcome`. @2 is retired (built no longer, a stored link
still reads as it meant), and the declared interests' old near step (every
company of the name on the companies register alone, time-unaware) is
gone: those rows are judged by @3 like every other.

## Measured, read-only on live (measurements.md §12)

By view, confirmed rows (sole + one live of several) of the
organisation-named rows: MPs' interests 2,039 + 259 of 3,593 (87 whose one
body was removed before the return and 64 registered after it stay near,
with the reason); party donors 163 + 18 of 291, disclosures 83 + 12 of 151,
candidate donors 16 of 87 (the same 292 pairs @2 confirmed); society
officers 24 + 1 of 77; charity officers 15 of 77; directors 2 of 154;
shareholders 0 of 1,170 (all undated, 484 near links). 2,632 confirmed
rows, one link each, by the body's register: companies 2,577, incorporated
societies 28, limited partnerships 20, charitable trust boards 5, other
incorporated bodies 2. Near 1,182 (was 2,980).

Against the queue item's figures (interests 2,139 and 239; holders 76 and 5;
society officers 16; charity officers 18; directors 2): those counted "live"
as today, by a method not written down; counted that way here the figures
are 1,557 and 232, 395 and 3, 20, 16, 2, so the item's are not reproduced
exactly. The time-aware rule's figures are above; the direction is the
ruling's (more interests confirm on the row's date than today, because
returns of 2006 to 2017 name companies since removed).

The case the brief names, on live: 33 rows where the one body of the name
live today is not the one alive on the row's date: the disclosures of
Christopher & Banks Ltd (2022, 2023) to 3482091 (removed December 2024),
not 9321019 (registered March 2025); Ivory Limited, Bakshi Enterprises
Limited, Oriwa Limited, Malachy Properties Limited, AMP Limited in the
interests returns. Judged today every one would join the wrong company.

## Checks

Fast tier for links: green, 121 tests (baseline 117). The lane's 15 slow
tests: green. `test_bodies.py`'s four new pure tests and the extended slow
engine test fail on a copy of main (AttributeError / KeyError). Check item
9 reads the @3 links (and any @2 still stored): an organisation-named row,
dated, the one body of its name live on the row's date; it goes red in
the slow test on three planted faults (an undated row confirmed; the linked
body removed before the row's date; another body live). Root checks run
here: reading limits, imports one way, lessons search green;
`tests/test_generators.py::test_the_committed_records_generate_cleanly` RED
because `docs/board.md` is stale by the card this branch adds (the test's
run rewrote the file in this working copy; uncommitted, not on the branch;
the scope hook refuses a restore, as links-4 recorded).

## Carded

- `pub-shareholders-publishes-no-filing-date-so-every-organisation-named-holding-stays-undated`
  (for the companies lane: publish the shareholding's filing date; the
  links then read it as `started_on`; about 400 confirmations wait on it).

## Not built

Nothing in `registers/` (the shareholders' date is the companies lane's);
no model, nothing fetched.

Lesson: `judge-a-body-s-life-on-the-row-s-own-date-never-today-and-never-let-an-unknown-date-count-for-it`.

## Result

Merged 30 October 2026, 12:03, as 62b65c0 (integrate branch c591a30; gate green, marked; the readers' slow tests ran
since tables.sql changed; nothing staged). One integrator commit on the way: `pub.entities` catalogued on the board
(the merge after its lane, ruling 123), the two organisation rules' words on the board and the report reworded for
every row's organisation name judged on the row's own date, the card board and the lessons index regenerated. No DDL
by hand. Released after the push; `qv4-links-build` queued again so the @3 rules build on live (the 11:19 build ran
links-4's code). The card for the companies lane (no filing date on pub.shareholders) stays open. Working copy and
local branches retired; `session/links-5` on the remote is Arthur's to delete.
