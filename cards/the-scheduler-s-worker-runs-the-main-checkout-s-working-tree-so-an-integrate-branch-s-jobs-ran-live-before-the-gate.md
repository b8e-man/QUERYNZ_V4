# The scheduler's worker runs the main checkout's working tree, so an integrate branch's jobs ran live before the gate
kind: finding
state: open
use-case: machinery; plan 1b.7 (the gate), step 2 (the scheduler)
session: integrator
opened: 2026-10-22

Found at the merge of `procurement-1` (22 October 2026). The worker unit
`qv4-worker@node2` has `WorkingDirectory=/home/user/querynzv4`, the main
checkout, and re-reads the job catalogue from that working tree every few
minutes. The integrator does its items on an `integrate/<name>` branch in
that same checkout and runs the fast tier there, about ten minutes, before
the gate. Two things follow:

1. **New jobs run at once.** `queue.slot_for` makes a timetabled `at_utc`
   job due the moment it enters the catalogue (before the day's first time,
   yesterday's last time is the slot, never served). So the three jobs
   appended for `procurement-1` ran at 22:30:01 to 22:30:12, as soon as the
   worker reloaded (70 job types), while the branch was still under its
   fast tier: `qv4-contract-disclosures-refresh` landed ACC's file and two
   catalogue descriptions on the live database (3 requests through the gate,
   polite), `qv4-council-procurement-watch` asked its four pages (one
   answered 302 and was set aside, so the run is red), and
   `qv4-contract-disclosures-load` published an empty `contract_disclosures`
   schema and `pub.agency_contract_costs`. The settlements-1 jobs did the
   same at 08:35 that morning (the capture stopped at once, outside its
   off-peak window; the load failed on tables not yet made; the watch failed
   on its daytime guard). Nothing fetched was impolite and nothing wrong was
   published, but the gate had not yet said yes.
2. **The branch's code is live.** Every job the worker starts in that window
   runs the integrate branch's code, not main's. A fix branch changing a
   lane's load would run unreviewed on the live database.

The refusal from `fix-support-db-1` cannot see this: the worker marks every
job with `QV4_RUN_ID`, as it must.

What closes it, a `bin/fix support/scheduler` session: the worker runs from
a copy that moves only when main is pushed (or refuses to reload a catalogue
whose checkout is not on `main`), and a job entering the catalogue takes
its NEXT slot, not a slot already past. Until then the integrator stops the
worker (`systemctl --user stop qv4-worker@node2`) when it is idle before
checking out an integrate branch and starts it again after the push; a
merge window is about twenty-five minutes.

Lesson filed with this card: `a-worker-that-reads-the-checkout-runs-the-branch`.

## 2026-10-23, fix-support-scheduler-1 (branch `fix/support-scheduler-1`)

Done, in `support/scheduler` only:

- **Finding 1 closed in code.** A timetabled job the clock has never served
  (no `scheduler.timetable` row: new to the catalogue, or enabled for the
  first time) or whose timetable differs from the one its row records
  (`timetable.clock`, new column) no longer runs at once: `enqueue_due` marks
  the slot due now served, as `handover` does, and logs one line naming the
  first run, which is the next timetabled time. Rows from before the column
  adopt their timetable and keep any slot they are owed. No timetable, no
  change.
- **Finding 2, the catalogue half.** The worker reloads `jobs.toml` and
  `profiles.toml` only while the checkout they sit in is on `main` (git
  asked by path). On an integrate branch or a detached head it keeps the
  last good catalogue and logs why once; started off main it holds an empty
  catalogue until main.

Still open, so this card stays open:

- **The code half of finding 2.** Every job, and the worker itself, still
  runs the main checkout's working tree (`WorkingDirectory`, `cwd=REPO`). A
  job the worker starts during a merge window runs the integrate branch's
  code. The fix is a release copy that moves only when main is pushed, and
  the unit (`support/scheduler/units/qv4-worker@.service`) pointing at it.
  The copy and what moves it (the installer, the integrator's push) are
  outside this module, so it is a build session's.
- Until that lands the integrator's interim stands: stop the idle worker
  before checking out an integrate branch, start it after the push.
