# scheduler: where step 2 stands

Last close: fix-support-scheduler-1 (second sitting), 28 October 2026,
node2. Branch `fix/support-scheduler-1`, merge request
`fix-support-scheduler-1`. Scope `support/scheduler`.

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
  `working_mb` and `rerun_of_raise`. Seven slow tests and five fast, each
  seen failing on its mutant.

## Waits on the integrator, at the merge (node2, /home/user/querynzv4)

1. Fold nothing by hand now; after a night, `python -m support.scheduler
   memory` names any `memory_gb` to fold into jobs.toml.
2. Release, then with the worker idle restart `qv4-worker@node2`: its
   start runs `queue.tables`, which makes `memory_raises` and the two
   `runs` columns (the gate's staging does not: no load.py here).
3. `qv4-scheduler-report` runs from the release copy hourly; no restart.

## Not done

- checks/scheduler.py still counts the killed run of a re-run that came
  good as a failed run for 24 h (outside this fence; noted in the request).
- The two-box proofs stay owed on node1.

## Next

The node1 setup card when Arthur powers node1.
