# fix-registers-charities-1: the charities check run bare answers about the live tables
branch: fix/registers-charities-1 (pushed, e58e9af)
session: fix-registers-charities-1 (scope registers/charities/)
raised: 2026-10-23
claims: registers/charities/check.py; registers/charities/tests/test_charities_check.py (new); lessons/a-lane-check-run-bare-answers-about-the-live-tables.md (new). No card existed for this; none closed or raised.

## The finding

The board's journal on node2, every morning since 20 October:
`RED module-checks/charities psycopg.errors.UndefinedTable: relation "scratch_charities_full.read_pages" does not exist`.
`checks/module_checks.py` runs `python -m registers.charities.check` with no
arguments; its defaults were `--schema scratch_charities_full --database
querynz_v4_sample`, a build session's scratch proof since dropped. The board
has never seen the charities lane.

## The fix

- Bare run: schema `charities` in `querynz_v4`, read-only login (`qv4_read`),
  as `iwi_directory` and `grants` do. One connection serves both the reading
  and the capture's tables.
- The live run also holds `pub.charities`, `pub.charity_officers`,
  `pub.charity_returns` to the lane's tables by row count.
- Nothing reads `charities_private` (the reader is refused it by design;
  confirmed: `permission denied for schema charities_private`).
- `--schema <scratch>` still works: the sample with the owner's login, or the
  database `--database` names. A schema with nothing loaded prints
  `check RED: nothing loaded under <db>.<schema>` and exits 1, no traceback.
- The verdict line is printed first, so the board's green detail carries the counts.

## Verdict, run by hand on node2 against querynz_v4 (`python -m registers.charities.check`)

Exit 0, 9 s. `charities: check green on querynz_v4.charities: Organisations 46136, Officers 589291, AnnualReturn 430665, Groups 357`.
Reconciles; registered charities held 29276 against the register's 29265 on
20 October, difference 11 within the 618 modified since; the register's
`vOrganisations` names agree for 46135 compared (1 moved between captures);
no officer name column holds a date or an address; the three views match
their tables; the capture's measure green (pass 20, registered held 29272
against 29276 asked now, within 618 moved). Through `checks.module_checks`
(`run_one` + `item`): ok, with that line as the detail.

`--schema scratch_charities_full --offline`: exit 1, "nothing loaded" (the schema is gone), as it should.

## Tests

`bin/fast registers/charities`: green in 52.3 s. New tests: the bare main
opens only the reader on querynz_v4 and looks for `charities.read_pages`;
`--schema scratch_charities_full` opens the owner on querynz_v4_sample; the
`--database` switch is honoured; no table a check reads is in the private twin.

## For the integrator

1. Run the gate and merge. No table, view or job changes; nothing to load.
2. Pull the main checkout (the board runs from `/home/user/querynzv4`); the
   07:30 run of `qv4-checks-board` then shows `module-checks/charities` green.
   Optionally run `python -m checks.module_checks` once after the merge to see it.
3. No change to `TIMEOUTS_S` needed: 9 s against the 120 s default. The
   check makes two requests to the charities feed through the fetch gate per run (check 1), as the spec says.
4. Regenerate the lessons index.

## Result (integrator, 2026-10-23 09:27 NZDT)

Merged with the three other fixes of the morning as `integrate/fixes-2`:
`d710863 merge integrate/fixes-2: gate green` (fast tier green in 628 s on the
integrate branch; the gate's staging step loaded and published the touched
lanes). Branches and the working copy retired. Integrator items on the
branch: the board's windowed check takes the call the board makes (with a
registry test in checks/tests), `qv4-disclosures-load` in the catalogue
(priority 84, 18:40 UTC), the compare-gate card, board and lessons index
regenerated. The worker was stopped for the window and started after the
push.
