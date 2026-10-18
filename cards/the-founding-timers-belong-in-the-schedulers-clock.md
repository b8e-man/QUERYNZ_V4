# The four founding timers still run on systemd's clock, not the queue's
kind: finding
state: open
use-case: -
session: scheduler
opened: 2026-10-18

Step 2.12: a job on a timetable has its timetable in the queue, so a lost
box's jobs run on the survivor with no hand step. `qv4-checks-board`,
`qv4-checks-heartbeat`, `qv4-full-tier` and `qv4-offsite-dump` were
installed by the founding session as systemd timers (checks/ and
support/offsite, outside the scheduler session's scope). Move each into
`support/scheduler/jobs.toml` with `at_utc` (and the deadlines the units
carry), then disable the timers through the installer. Also `support/db`'s
schema list and the owner map in `tests/test_imports_one_way.py` should
name `scheduler` → `support.scheduler`, and the checks board should read
`<live>/checks/scheduler.json`.
