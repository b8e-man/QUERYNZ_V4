A fixture that fixes the clock writes every timestamp from that clock, never a column's DEFAULT now(): the mix compares a fake time with the real one, and the test turns red on a date nobody chose.
area: tests, fixtures, fake clocks, any table with a timestamptz DEFAULT now(), age thresholds in checks
paid-for-by: 2026-10-25, the board-2 gate (fast tier red); fixed in fix-registers-companies-1

`registers/companies/tests/test_companies_monitor.py`'s `night` fixture
fixed its clock at 2026-10-22 23:30 NZDT and passed it to the monitor, but
its `ask` inserted requests without `asked_at`, so the database stamped
them with the real time. The block test moved the fixture's clock on three
days and expected `check.monitor_failed` to call the request older than 48
hours. That held only while the real date was before 23 October 23:30. The
test was green at one gate and red two days later with no change to the
code.

The shape to look for: a fixed or fake `now` in the test, and an INSERT
that leaves out a column that defaults to now() (`asked_at`, `at`,
`created_at`). Grep the table definitions for `DEFAULT now()` and the
fixture for inserts that omit those columns. Prove the fix by running the
tests with the fixture's clock moved well before the real date; a mixed
fixture fails there at once instead of waiting for the calendar.
