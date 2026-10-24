# The monitor's block test stamps its requests with the real clock, so it fails after 23 October
kind: finding
state: open
use-case: machinery; step 5.5 (company monitoring); the fast tier
session: integrator
opened: 2026-10-25
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
