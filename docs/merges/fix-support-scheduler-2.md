# fix-support-scheduler-1: a job stopped at its memory ceiling is raised and re-run by the worker (ruling 115)
branch: fix/support-scheduler-1 (pushed; 1cf7e3a, on main 7c36971)
session: fix-support-scheduler-1 (fix, support/scheduler/), second sitting; the 23 October request of the same name is merged and kept in docs/merges/fix-support-scheduler-1.md
raised: 2026-10-28
claims: support/scheduler/queue.py, worker.py, runner.py, runs.py, __main__.py, tables.sql, spec.md, README.md; tests test_memory_raise.py (new, fast), test_memory_raise_worker.py (new, slow), test_worker.py (one test updated); lessons/a-memory-figure-the-box-cannot-hold-is-recorded-never-applied.md; docs/status/scheduler.md
closes: nothing

1. **The raise.** When a run ends with reason `memory`, the worker calls `queue.raise_memory`: one row in the new
   `scheduler.memory_raises` (job, run id, queue row, first row of the chain, peak, the ceiling crossed, the
   figure held, the raised figure, the budget, applied, the row queued again, a note). The raised figure is twice
   the ceiling crossed, rounded up to the next 0.5 GB (0.3 → 1.0, 1.0 → 2.5, 1.5 → 4.0). jobs.toml is never
   written.
2. **The re-run.** The job is queued again at once with the row's args, class and priority, unless (a) the raised
   figure is over the box's budget, its probed memory less `memory_reserve_gb`: the raise is recorded with
   `applied = false` and the working figure is unchanged, because an applied figure that cannot fit is never
   claimed and never alarms (the lesson); or (b) the first row has had two raises already: the raise is applied
   (the next run starts from it), no re-run. In both the row stays failed and alarmed with the note. A pieced job
   gives its own row back with its pieces' progress; a standing service's next copy comes from
   `enqueue_standing`. No other failure is touched; the requeue on a lost lease or a stopping worker is unchanged.
   A re-run that comes good raises no alarm.
3. **The working figure** is the larger of the declared figure and the latest applied raise, read from the table
   at start and every tick (so a restarted worker and the other box place by it). Eligibility, the committed
   memory and the ceiling all use it.
4. **Listing.** `python -m support.scheduler memory` prints every raise jobs.toml has not folded (declared below
   raised) and one `fold: [jobs.X] memory_gb = N` line per job; `report` writes them as `memory_raises` in
   `<live>/checks/scheduler.json` and prints the same lines. A raise drops out when jobs.toml declares at least
   its figure.
5. **The run record.** job-runs.jsonl's end row carries `working_mb` and `rerun_of_raise` beside
   `over_declared` (declared_mb stays jobs.toml's figure, so a re-run past it is still flagged); `scheduler.runs`
   gains `working_mb` and `raise_id`.

On the budget: the brief named "the reservations and the worker's own limit in jobs.toml [queueing]". The
`[[reservations]]` are graphics cards, not memory, and the worker unit has no memory limit, so the budget is the
box's memory less `memory_reserve_gb`. If Arthur means a separate limit, it is one line in
`Worker.memory_budget_gb`.

Tests: fast, eight (the rounding at five figures, the re-run's run record, two on the memory lines); slow, seven against
the sample database with the burn rehearsal job at a 128 MB ceiling: killed once → re-queued at 0.5 GB and runs;
killed twice → 1.5 GB and runs; killed three times → stays failed, alarmed, next figure 4.0 GB; over a 0.4 GB
budget → stays failed, not applied; exit code 3 → no raise; `memory` and the report list the raise and stop when a
copy of jobs.toml declares 0.5; a new Worker reads 0.5 from the table and waits for 0.5 GB of room. Seen failing:
three raises per row, applying every raise, placing by the declared figure, capping by the declared figure, not
reading the table at start. `QV4_INTEGRATOR=1 bin/fast support/scheduler` green in 47.7 s; the scheduler's slow
tests, 36 passed.

**What the integrator must do after the merge (node2, /home/user/querynzv4):**

1. Push main, then `.venv/bin/python -m support.installer release`; it will report `worker_restart: owed`.
2. **The DDL is applied by hand, by the worker's restart**, not by the gate's staging (support/scheduler has no
   load.py): with the worker idle, `systemctl --user restart qv4-worker@node2`. Its start runs `queue.tables`,
   which creates `scheduler.memory_raises` and adds the two `runs` columns (all `IF NOT EXISTS`). Until then the
   report shows no raises (it checks the table exists).
3. `qv4-scheduler-report` is a job on the queue's clock, a new process from the release copy each hour: it takes
   the new code at its next run after the release; there is no unit of its own to restart.
4. At later merges, fold what `python -m support.scheduler memory` names into jobs.toml.

Note, outside this fence: `checks/scheduler.py` counts every non-ok run in 24 h as red, so the killed run of a
re-run that came good still turns the board's `runs` item red for a day. It could skip a run whose
`scheduler.memory_raises` row has a `requeued_id` that finished `done`. Not carded (ruling 323's price); the
integrator's call.

## Result (integrator, 28 October 21:15 NZDT)
Merged dde8f87 as `integrate/fix-support-scheduler-2`, gate green at the second run (the first fell on a stale docs/board.md from two cards the integrator wrote that evening; the fix's own tests passed both times; full runs, 27 minutes each, since support/ was touched). At the merge the diaries load's figure was raised to 1.5 GB from its measured 1,127 MB peak. Released. The worker was carrying `qv4-offsite-copy` (started 21:00) at the release, so its restart, which makes `scheduler.memory_raises`, waits for that run to end; the report job takes the new code at its next hourly run. Branch and working copy retired. The 23 October request of the same name is kept as docs/merges/fix-support-scheduler-1.md; this one is fix-support-scheduler-2.md. Noted for checks/scheduler.py, not carded: a stopped run keeps the board's runs check red for 24 hours after a good re-run.
