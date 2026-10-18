# scheduler-2a: the four founding timers on the queue's clock (step 2.12)
branch: session/scheduler
session: scheduler (session 2)
raised: 2026-10-18
claims: support/scheduler (jobs.toml: the four jobs in UTC; registry: at_utc as a list, nice; queue.handover; probe: pg_dump, gpg; runner: nice; tests); support/installer (a timer whose job is timetabled is superseded; support/*/jobs seen; tests); cards/the-founding-timers-belong-in-the-schedulers-clock.md closed; lessons/a-clock-moves-by-marking-the-slot-the-timer-served.md; docs/decisions/queue/the-board-heartbeat-on-the-queues-clock.md; docs/status/scheduler.md

What it claims: the four founding jobs run on the queue's clock. Proven on
node2 18 October: the installer superseded the four timers at 20:36 (no
`qv4-` timer is left; the old estate's timers untouched), each clock handed
over to the slot its timer had served that morning (nothing ran twice; the
worker queued nothing at the switch), and each job then ran once by hand
through the queue (ruling 56): heartbeat ok, board ok, dump ok, full tier
green on the second run (783 passed; the first run was red on a test this
session added, fixed). One failure alarm reached ntfy from that first run,
as designed.

Note: the same branch carries 2b and 2c; one gate run covers all three.

After the merge, on node2, in /home/user/querynzv4:
1. `python -m support.installer apply --units` — restores the shipped
   `qv4-worker@.service` (the rehearsal unit names this working copy) and
   finds the four timers already superseded (nothing to do).
2. `systemctl --user restart qv4-worker@node2.service`.
3. Three small edits outside the scheduler's fence (the card named them):
   `support/db`'s schema list and the owner map in
   `tests/test_imports_one_way.py` name `scheduler` → `support.scheduler`;
   the checks board reads `<live>/checks/scheduler.json`. The four timer
   files in `checks/jobs/` and `support/offsite/jobs/` can be deleted (the
   installer ignores them; the catalogue is the record) or left.
4. Regenerate the board, the lessons index and the decision queue.

Known: `tests/test_generators.py` fails on the branch until the generated
files are rebuilt at the merge (by design).

## Result (integrator: founding-f05585e, 18 October 21:1x)

MERGED into main as 5e45437 (one gate run for 2a, 2b and 2c on an integration
branch; the generated files rebuilt there; one queue item put into the
queue's shape). The contract patch for support/modelclient and
docs/contracts/model-client.md was applied line by line and verified equal
to the patch. The three edits outside the fence are done: `scheduler` in
support.db's schema list and in the owner map of tests/test_imports_one_way.py;
the checks board has a `scheduler` check reading <live>/checks/scheduler.json
(report fresh, workers up, reserved card clean, failed runs in 26 h). The
timer files in checks/jobs/ and support/offsite/jobs/ are left (the
installer supersedes them). Post-merge: the installer re-placed the shipped
worker unit and the worker restarted from the main checkout at 21:05.
