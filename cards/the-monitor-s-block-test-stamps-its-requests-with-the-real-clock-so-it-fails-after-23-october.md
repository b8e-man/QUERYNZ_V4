# The monitor's block test stamps its requests with the real clock, so it fails after 23 October
kind: finding
state: closed
use-case: machinery; step 5.5 (company monitoring); the fast tier
session: integrator
opened: 2026-10-25
closed: 2026-10-25
module: registers/companies

Found 25 October 2026 12:30 gating `board-2`: the fast tier is red on
`registers/companies/tests/test_companies_monitor.py::test_a_block_stops_the_night_and_leaves_the_request_waiting`,
a test the branch never touched and that was green at the `release-copy-1`
gate on 23 October. Deterministic alone. The fixture's clock is fixed at
2026-10-22 23:30 NZDT and the test moves it on three days, then expects
`check.monitor_failed` to say the waiting request is older than
`ANSWER_WITHIN` (48 hours). But the fixture's `ask` inserts into
`requests` without `asked_at`, so the column takes the table's
`DEFAULT now()`: the real clock. Until 23 October 23:30 NZDT the real
stamp was older than the threshold and the test passed; from then on it
is younger and the test fails. Code under test is sound; the test is
date-dependent. Fix in the module: the fixture stamps `asked_at` from its
clock (and any other row the fixture writes with a defaulted timestamp).
The gate for `board-2` waits on it.

Closed 25 October (fix-registers-companies-1). Test-only; `monitor.py`,
`check.py` and `tables.sql` unchanged. The `night` fixture's `ask` now
writes `asked_at` from the fixture's clock, and
`test_a_watch_falls_due_by_its_interval_and_off_peak_holds_the_night`'s one
direct `watch` insert does the same. Searched the other rows: `calls`,
`answered_at` and `changes` are written by `M.run` from the `now` the
fixture passes, so they already take its clock; `lookup_set_aside.at`
defaults to now() in the monitor's own insert, but no test or check reads
it; the hand-off test goes through `pub.request_company_check` (the
product's path, real clock by design) and asserts no time. Proof: the
module's 24 monitor tests are green with the clock at 2026-10-22 23:30 as
it stands, and again with it moved to 2026-10-01 23:30 (where the old
fixture fails too: the real stamp falls after the fixture's clock).
`QV4_INTEGRATOR=1 bin/fast registers/companies` is green (84 s against the
60 s target, recorded); the named test passes alone. Lesson:
`lessons/a-fixture-on-a-fixed-clock-stamps-every-row-it-writes-from-that-clock.md`.
