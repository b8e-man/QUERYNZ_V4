A clock that owes a new job its latest past slot runs it the moment it is read; record the timetable each job was served under, and treat no row, or a different timetable, as "mark the slot due now served, first run the next".
area: scheduler, timetable, jobs.toml, worker, enabling a job, the merge window
paid-for-by: 2026-10-22, procurement-1 and settlements-1 jobs ran before their gates; fixed by fix-support-scheduler-1, 2026-10-23

`queue.enqueue_due` treated a job with no `last_slot` as owed `slot_for(now)`,
which before the day's first time is yesterday's last: six jobs ran live the
minute the worker read an integrate branch's catalogue. Detecting "new" by
diffing the worker's catalogue in memory would miss a worker restarted after
the merge and a job enabled after its adopt run, so the rule lives on the
`timetable` row (`clock`, from `queue.clock_of`), which every worker and every
start sees. Rows written before the column (`clock` NULL) adopt their
timetable and keep any slot they are owed, so the deploy skips nothing.
This replaces "that is right for a new job" in
`a-clock-moves-by-marking-the-slot-the-timer-served`; `handover` still matters
for a job a timer served under an existing row.

The other half: the worker now reloads `jobs.toml` only while its checkout is
on main (`worker.checkout_branch`, asked of git by path). The code a job runs
is still the checkout's working tree; see
`a-worker-that-reads-the-checkout-runs-the-branch`.
