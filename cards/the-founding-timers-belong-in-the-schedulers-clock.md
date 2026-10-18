# The four founding timers still run on systemd's clock, not the queue's
kind: finding
state: closed
use-case: -
session: scheduler
opened: 2026-10-18
closed: 2026-10-18

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

Closed 18 October 2026 by scheduler (session 2): the four jobs are in
`jobs.toml` in UTC with their units' deadlines, a query limit each,
`nice = 10` and `requires` for the dump; the installer superseded the four
timers on node2 at 20:36 (disabled, removed, each clock handed over to the
slot its timer served that morning) and each job then ran once by hand
through the queue (ruling 56): heartbeat, board, dump ok; the full tier red
once on a new test of this session (fixed) and green on the second run,
783 passed. The three edits outside this session's fence (`support/db`'s
schema list and the owner map naming `scheduler`, the checks board reading
`<live>/checks/scheduler.json`) are listed in merge request scheduler-2a
for the integrator; the timer files in `checks/jobs/` and
`support/offsite/jobs/` can go at the same time (the catalogue is the
record; the installer ignores them either way).
