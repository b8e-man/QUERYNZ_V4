# scheduler-1: step 2, the scheduler's first build
branch: session/scheduler
session: scheduler
raised: 2026-10-18
claims: support/scheduler (planner, registry, queue, probe, runner, worker, cards, re-read, CLI, unit, spec, tests); support/installer (units by prefix, model server beside the old one, models, venv, credentials box to box, spec, tests); four lessons; three cards; one queue item; docs/status/scheduler.md

What it claims: step 2's done-when list is ticked on the one-box rehearsal
(docs/status/scheduler.md, "Live record"). 139 tests, 33 slow against the
sample database (two workers, real queue), the rest under five seconds.

After the merge, on node2, in /home/user/querynzv4:
1. `python -m support.installer apply --units` — replaces the rehearsal's
   `qv4-worker@.service` (which names the working copy) with the shipped one.
2. `systemctl --user restart qv4-worker@node2.service` — the worker then runs
   from the main checkout. It unloads card 1's server on stop and reloads on demand.
3. Regenerate the board, the lessons index and the decision queue (four
   lessons, three cards, one queue item are new).

Known: `tests/test_generators.py::test_the_committed_records_generate_cleanly`
fails on the branch until the generated files are rebuilt at the merge (by
design). `bin/fast` in a working copy without `.venv` runs the system Python
(carded). Nothing in this branch touches `support/profiles`.

## Result (integrator: founding-f05585e, 18 October 19:3x)

MERGED into main as 1c35089 after the gate ran green on an integration
branch (the branch's own gate run failed only the generated-files test, as
the request said; the board, lessons index and decision queue were
regenerated at the merge). Nothing outside the fence but `lessons/INDEX.md`,
a generated file, regenerated. Post-merge steps done on node2: the installer
placed the shipped `qv4-worker@.service` (WorkingDirectory now the main
checkout) and enabled `qv4-worker@node2`; the worker restarted 19:37 and runs.
Card 0 at 28 GB in use by the carve-out, card 1 at 1.9 GB (worker idle),
the five carve-out services active. The working copy is kept for session 2.
