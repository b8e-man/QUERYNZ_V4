# fix-registers-overseas-investment-1: the lane's check answers under the session reader
branch: fix/registers-overseas-investment-1 (pushed; e529c7e)
session: fix-registers-overseas-investment-1 (fix)
raised: 2026-10-23
claims: registers/overseas_investment/check.py, load.py, tables.sql, tests/test_overseas_investment_reading.py;
cards/overseas-investment-statements-on-the-view-still-carry-street-shaped-text.md;
lessons/a-check-the-board-runs-under-the-reader-takes-its-private-figure-from-a-count-the-load-writes.md

The board's 07:30 run of `python -m registers.overseas_investment.check` has been
RED with InsufficientPrivilege on overseas_investment_private since the lane merged:
the check counted the private twin under db.READ_KEY, which has no grant there by
design. Now the load (owner) writes a one-row count, `overseas_investment.read_statements`
(statements held in the twin, and of them those whose key is no decision's), beside its
ledger. The bare check reads that (`reading(private=False)`) and names no _private
schema. The owner's runs (the job, the gate's staging `load`) still count the twin and
red if it differs from the written count. No grant changed, no private row moved.

Fast tier: `bin/fast registers/overseas_investment` green in 49.5 s (36 tests, two new:
the reader's SQL names no `<x>_private.` reference, red with the private branch forced
on; the count matches the twin and goes red on a stray row, missing row, extra row,
wrong figure and dropped table).

Check run by hand, bare, under the reader, on querynz_v4 (this branch, 23 Oct): it
answers, exit 1 (red), with no permission error. Stated 1,337 rows, 1,297 read, 40 not
captured yet (2018 12, 2019 4, 2022 2, 2024 2, 2025 20). Problems: (1) "the private
statements' count is missing": expected until the table is published, clears at this
merge; (2) 44 values of pub.overseas_investment_decisions.investment, 2 of
consideration_stated and 2 of overseas_investment_parties.status shaped like a street
address: carded (finding above), not fixed here. No value was printed.

For the integrator:
1. Run the gate. Its staging step loads and publishes this lane (load.py is touched),
   which creates overseas_investment.read_statements in querynz_v4. Without that publish
   the bare check stays red on (1). `job()` alone does not do it while the listing is unchanged.
2. After the merge, run `python -m registers.overseas_investment.check` bare as the reader
   and confirm (1) is gone. It stays red on the 40 not-captured rows (the capture's clock)
   and on the carded street-shaped values until that card's fix lands.
3. File the card; regenerate the board and the lessons index.
Lesson: filed (above).

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
