# Where the build stands

Overwritten at every close; under 3 KB. What happened is in the cards, the
lessons and the commit messages. Written by the founding session during
step 1; by the integrator after.

**Date:** 2026-10-18. **Step:** 1. **Boxes:** node2 is the primary since the
17 October failover; node1 is down and rejoins as the standby after a
rewind (Arthur's). **Alarm channel:** the old estate's ntfy address, present
(step 0).

## Done

- Step 0: all but the third machine, which is held with track A.
- 1.1, merged: the folder layout; the two hooks (`.claude/hooks/safety.py`,
  `scope.py`, shared `fence.py`) with their carried tests; the allowed-command
  list; `bin/start-session` (build and `--main`); `bin/merge-gate` (proven on
  a failing branch); the one-way import test; card, lesson and decision
  formats with `bin/board`, `bin/lessons-index`, `bin/decisions`; the plan
  split into `docs/plan/` with `manifest.json` and `headings.md`, proven to
  rejoin; `CLAUDE.md`; the stop list at
  `/home/user/querynzv4-work/live/stop-list.md` (empty); the inbox at
  `/home/user/querynzv4-work/inbox/`.
- 1.2, merged: the reference copy at `/home/user/qnz3-ref`, a clone of the
  live old folder at its commit `29f0412a` (no tag exists yet; 1.5 moves it
  to the frozen tag), remote `live`. Its own Python 3.12 environment at
  `/home/user/qnz3-ref/.venv`, built from `ops/requirements-factory.lock`
  and all 24 editable packages; the installed list matches the live one.
  Imports resolve to the reference copy; the old root suite collects (1,127
  tests) and its hook tests pass there. The fence lets a founding session
  write under the reference copy. Run old tests there only without a DSN:
  node2's localhost is the primary now (`lessons/old-tests-can-write-live-now.md`).
- 1.3, merged: `docs/baseline.md`, node2 measured in full, node1 down and
  marked "not measured" throughout; twelve differences from the plan listed
  there, two for Arthur (archive_mode off on the promoted primary; a password
  in the old `querynz-api` unit file, for track H).

## Next

1.6 (the watcher and the first checks board), then the first commit of
1.5, 1.4, the rest of 1.5, 1.7–1.10, step 1b, 1.11 — the order in the step
1 brief. When node1 returns, re-measure it into `docs/baseline.md`. Start with `bin/start-session --main founding` in
`/home/user/querynzv4`; the brief is in `docs/briefs/next.md`.

## Half-done

Nothing.

## Known gaps left on purpose in 1.1

- The query half of the one-way test (`tests/test_imports_one_way.py`,
  `SCHEMA_OWNER`) is filled when the schemas exist, in 1.8.
- The hooks know the weights `founding`, `integrator`, `build`; `fix` and
  `question` get their rules in 1b.1.
- The merge gate is one tier until 1b.7.
- The installer and the probe (step 2) are the only remote route; until they
  exist `ssh` asks.
