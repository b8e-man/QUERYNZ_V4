# scheduler: where step 2 stands

Last close: fix-support-scheduler-3 (ruling 129), 30 October 2026, node2.
Branch `fix/support-scheduler-1`, merge request `fix-support-scheduler-3`.
Scope `support/scheduler`.

## Done

- Step 2 on one box (session 2, 18 October): the four founding jobs on the
  queue's clock; the model server built from source beside the copy.
- fix-support-scheduler-1 (23 October): a job new to the catalogue waits
  for its next slot.
- release-copy-1 (23 October): the worker and every job run from the
  release copy `/home/user/querynzv4-release`, moved by
  `python -m support.installer release` after every push.
- fix-support-scheduler-1 (this close, ruling 115): a run stopped at its
  memory ceiling raises the job's working figure to twice the ceiling,
  rounded up to 0.5 GB, in `scheduler.memory_raises` (never jobs.toml), and
  queues the job again at once; at most two raises per first row, never
  over the box's memory less the reserve (recorded, not applied); every
  other failure as before. Placement and the ceiling use the working
  figure, read from the table each tick. `report` and the new `memory`
  subcommand list raises jobs.toml has not folded; the run record carries
  `working_mb` and `rerun_of_raise`. Seven slow tests and eight fast, each
  seen failing on its mutant.

- fix-support-scheduler-3 (this close, ruling 129): the standing server's
  night window. jobs.toml `[night_window]` (22:00 to 05:45 Pacific/Auckland,
  flash-next stopped for page-reader on card 1); `night.py` is the clock;
  `cards.Manager.night_tick` stops `qv4-radiance` when page work is queued
  and no text-reader or review piece is running or leased, waits for the
  cards to release the model, holds card 0 for the frozen OCR server, lets
  the planner load the page reader on card 1, and starts the unit again when
  the page queue is empty, a view piece is due, or the window closes; every
  stop and start a `stop`/`start` swap line with measured seconds; a failed
  start is a `failed` line, one alarm, one inbox note, retried each tick; a
  marker under <live>/scheduler survives a worker restart. Fourteen fast
  tests on the fake worker, four mutants seen failing.

## Waits on the integrator, at the merge (node2, /home/user/querynzv4)

1. Release, then with the worker idle restart `qv4-worker@node2` so the
   manager reads the window (the catalogue reloads on the probe's clock, but
   the manager's injected pieces are built at start).
2. Queue the page work (`qv4-read-pages-candidates`, `qv4-read-pages`, the
   disclosures pages) before 22:00; the first night opens at 22:00 NZDT.
3. The morning after: `python -m support.scheduler status` shows the
   `stop`/`start` lines and their seconds; a `failed` start is also a note
   in the inbox's cards folder.
4. After a night, `python -m support.scheduler memory` names any
   `memory_gb` to fold into jobs.toml (ruling 115, unchanged).

## Not done

- checks/scheduler.py still counts the killed run of a re-run that came
  good as a failed run for 24 h (outside this fence; noted in the request).
- The two-box proofs stay owed on node1.

## Next

The node1 setup card when Arthur powers node1.
