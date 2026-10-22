# fix-support-scheduler-1: a job new to the clock takes its next slot; the worker reloads its catalogue only on main
branch: fix/support-scheduler-1 (pushed; 8b2dee3)
session: fix-support-scheduler-1 (fix, support/scheduler/)
raised: 2026-10-23
claims: support/scheduler/queue.py, worker.py, tables.sql and their tests (test_queue.py, test_worker.py, new test_reload.py); the card below (appended, not closed); lessons/a-job-new-to-the-clock-is-owed-nothing-until-its-next-slot.md
closes: nothing. Card the-scheduler-s-worker-runs-the-main-checkout-s-working-tree-so-an-integrate-branch-s-jobs-ran-live-before-the-gate stays open for its code half

1. **(a) Next slot, 069e58c.** `scheduler.timetable` gains a `clock` column (`ALTER TABLE … ADD COLUMN IF NOT
   EXISTS`, run by `queue.tables` at worker start). In `enqueue_due`, a timetabled job with no row (new to the
   catalogue, or enabled for the first time) or whose timetable differs from its row's `clock` is not queued:
   the slot due now is marked served, as `handover` does, and the worker logs one line naming the first run,
   which is the next timetabled time. Live rows have `clock` NULL: each adopts its timetable on the first tick
   and keeps any slot it is owed, so the deploy skips nothing. A job with no timetable is untouched. `handover`
   now records the clock too; its signature is unchanged (the installer calls it).
2. **(b) Main only, 792ae77.** `worker.checkout_branch` asks git, by the catalogue's path, which branch is
   checked out. Off main (an integrate branch, a detached head, or git unable to say) `reload_catalogue` keeps
   the last good catalogue and logs one line saying why, once per change, plus one line when the checkout is
   back on main. A worker started off main has no good catalogue and holds an empty one until main (its cards
   manager then sees no demand). No job's command changed.

Tests: six new in test_queue.py (slow, need the sample database: new job before and after the day's time,
timetable changed, reordered times are no change, enabled after entering disabled, a pre-column row served as
before, no timetable untouched), the old "queued once" test updated to the new first sighting, and the worker's
timetabled test seeded with a known clock. Four fast tests in test_reload.py (branch answer monkeypatched; one
asks a real git repository). Proved able to fail: disabling the new-to-the-clock branch fails five, treating a
NULL clock as changed fails the deploy test, and removing the branch check or the once-per-change guard fails
the reload tests. test_queue + test_worker run against the sample database: 29 passed. `bin/fast
support/scheduler` green in 47 s; whole repository green in 686 s (target 300 s missed, recorded).

**What the integrator must do after the merge:**
- Restart the worker on node2 so it runs the new code and adds the column:
  `systemctl --user restart qv4-worker@node2` (node2, any directory). Do it while the worker is idle. Restart
  any other `qv4-worker@` instance running on node2 the same way (`systemctl --user list-units 'qv4-worker@*'`).
- Check the log after the restart: `journalctl --user -u qv4-worker@node2 -n 50` (node2). Expect no
  "new to the clock" lines for jobs already in the catalogue. Their rows adopt a clock silently.
  Then confirm: `bin/q "SELECT count(*) FILTER (WHERE clock IS NULL) FROM scheduler.timetable"` (node2, main
  checkout) reads 0 once every enabled timetabled job's slot has come round. A job in the catalogue that has
  never been served gets its line and runs at its next slot.
- From now on a job merged into the catalogue, or enabled, waits for its next timetabled time. A lane that
  needs a first run at once has to queue it by hand (`python -m support.scheduler enqueue <job>`).
- Keep the interim on the card until the release copy lands: stop the idle worker before checking out an
  integrate branch and start it after the push. This fix stops the catalogue reloading off main, but a job
  started in the window still runs the branch's code.
- Nothing to install; no unit changed.

Not done, outside the fence: the release copy (the code half of finding 2) is a build session's work. It stays
on the card. Lesson: one filed (first line 226 characters). It says that `a-clock-moves-by-marking-the-slot-the-timer-served`'s
"that is right for a new job" no longer holds.

## Result (integrator, 2026-10-23 08:55 NZDT)

Merged: `a178d95 merge integrate/fix-support-scheduler-1: gate green` (fast
tier green in 627 s on the integrate branch; gate green, staging had no
load to run). Branches and the working copy retired.

Done after the merge: the worker `qv4-worker@node2` restarted at 08:53
while idle (no running row in `scheduler.runs`; no other worker instance
on node2). `scheduler.timetable` now carries `clock`; 44 of 46 rows adopted
one on the first tick, 2 wait for their slot to come round. The interim on
the card stands until the release copy lands: the integrator stops the
idle worker before checking out an integrate branch and starts it after
the push (first practised at 08:56 for `integrate/fixes-2`).

While the fast tier ran, the integrator found that the worker ran
`qv4-full-tier` at 04:30 and five lane loads at 06:20 to 06:50 from the
main checkout while it sat on this integrate branch (03:22 to 08:33), the
hazard the card names; the branch was main plus this fix, so the runs were
the right code.
