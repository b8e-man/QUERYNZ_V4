# fix-registers-companies-1: the monitor's night fixture stamps its rows from its own clock
branch: fix/registers-companies-1 (pushed, de524b9; one commit on 3ca428f)
session: fix-registers-companies-1 (scope registers/companies/)
raised: 2026-10-25
claims: registers/companies/tests/test_companies_monitor.py; card closed: the-monitor-s-block-test-stamps-its-requests-with-the-real-clock-so-it-fails-after-23-october; lessons/a-fixture-on-a-fixed-clock-stamps-every-row-it-writes-from-that-clock.md (lessons/INDEX.md regenerated)

## The finding, confirmed

Reproduced red alone on 25 October before the change: the block test's request carried the real time from
`asked_at DEFAULT now()`, younger than 48 hours against the fixture's clock moved to 25 October 23:30.

## The change (tests only)

- The `night` fixture's `ask` writes `asked_at` from the fixture's clock.
- The watch test's one direct `watch` insert writes `asked_at` from the fixture's clock.
- Other timestamps searched: `calls.at`, `requests.answered_at` and `changes` are written by `M.run` from the clock
  the fixture passes. `lookup_set_aside.at` is the monitor's own DEFAULT, and no test or check reads it. The hand-off
  test goes through `pub.request_company_check` and asserts no time.
- `monitor.py`, `check.py` and `tables.sql` are unchanged.

Checked: the 24 monitor tests green with the clock at 2026-10-22 23:30, and again with it moved to 2026-10-01 23:30
(the old fixture fails there too). `QV4_INTEGRATOR=1 bin/fast registers/companies` green (84 s, 60 s target missed,
recorded). The named test green alone. tests/test_lessons_search.py green. Known to fail: nothing.

## What the integrator does after the merge

Nothing but merge. The `board-2` gate waits on this; re-run its fast tier on the combined branch.

## Result (integrator, 25 October 13:25 NZDT)

Merged as ddf9bc4: fast tier green (627 s), gate green (companies lane
republished through staging, 1,920,468 entity rows). Tests only; card
closed; lesson indexed. Working copy and branches retired; release copy
moved. `board-2`'s gate re-runs on main behind it.
