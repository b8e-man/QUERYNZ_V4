# release-copy-1: the worker runs from a release copy that moves only when main is pushed
branch: session/release-copy-1 (pushed; d23218e)
session: release-copy-1 (build, Opus)
raised: 2026-10-23
claims: support/installer/release.py (new) and its tests; support/installer/__init__.py, __main__.py, README.md, spec.md; support/scheduler/worker.py, units/qv4-worker@.service, tests/test_reload.py; support/installer/tests/test_installer.py; the card's dated note; lesson `a-moved-release-copy-does-not-move-the-running-worker`; docs/status/scheduler.md

Closes the second half of card
`the-scheduler-s-worker-runs-the-main-checkout-s-working-tree-so-an-integrate-branch-s-jobs-ran-live-before-the-gate`
(the first half closed in fix-support-scheduler-1). With this merged and the
steps below done, the card closes: close it at the merge.

## What it does

- **The release copy**, `/home/user/querynzv4-release`: a separate clone of
  origin (not a worktree, so nothing the main checkout's `git worktree`
  commands do can reach it), holding exactly one pushed commit of
  origin/main, detached, never a branch, never edited.
- **`python -m support.installer release [--commit SHA]`** makes or moves
  it: clone if missing; refuse an edited copy (tracked or untracked), a
  branch checked out, or a path that is not a clone; fetch; refuse unless
  the target (default origin/main) is on origin/main; check out detached,
  delete any local branch; bring the copy's `.venv` to its requirements;
  record `<copy>/.git/qv4-release.json` (inside `.git`, so the record never
  dirties the copy); log one line to `<live>/installer/release.log`. It
  reports `worker_restart: owed` when the move touched the worker's own code
  (`support/scheduler`, `support/db`, `support/alarm`, requirements; not the
  catalogue, which reloads itself) or the copy is new. It restarts nothing.
- **Its own `.venv`, not a link to the main checkout's.** A shared
  environment is changed by whoever runs pip in the main checkout, so a
  branch changing requirements.txt would change the live jobs' packages
  before its gate. Built the same way (`python -m venv`, `pip install -r
  requirements.txt`, ~80 MB), re-run only when requirements.txt's hash moves.
- **The worker unit** names the copy in `WorkingDirectory` and `ExecStart`.
  `worker.py` already took `REPO` from its own file, so in the copy every job
  runs the released commit. The catalogue now reloads only while its
  checkout stands, unedited, at a commit of origin/main (replaces the
  branch-name test); it logs at start which copy and commit it runs from.
  There is no `EnvironmentFile` line in the unit and none was added.
- **The installer** still places only `qv4-` units. It refuses to place the
  worker unit (and leaves the one on the box as it is, and does not enable
  it) until the copy and its `.venv` exist. A rehearsal from a working copy
  rewrites the release path to that copy, as it rewrote the main path.

## Proof

- Tests: `support/installer` 20 and `support/scheduler` 152 pass; whole-repo
  fast tier green (630 s, over the 300 s target, recorded). Each new check
  was broken on purpose and its test went red: no origin/main check, no
  dirty check, no worker-unit refusal, the unit pointed back at main, no
  ancestor test and no edit test in `release_state`.
- On a scratch clone of the real origin
  (`/home/user/querynzv4-work/scratch/release-copy-1/release`): made at
  8618b41 with its own `.venv` (psycopg 3.3.4 imports; the worker module
  resolves `REPO` to the copy); a rerun "stays at"; an untracked file
  refused; this branch's pushed tip refused as not on origin/main;
  `release_state` is None for the copy and for the main checkout on main, and
  names the branch for this working copy.
- Nothing was installed or restarted on the box; `/home/user/querynzv4-release`
  was not made.

## What the integrator does at the merge (node2, in /home/user/querynzv4)

1. Merge, push main as usual.
2. `.venv/bin/python -m support.installer release` makes the copy at the
   pushed main (clones from GitHub over ssh; pip fetches three packages).
3. `.venv/bin/python -m support.installer apply --units --only qv4-worker@.service`
   places the new unit and daemon-reloads. (`enable --now` does not
   restart a running worker, so it is still on the main checkout.)
4. When the worker is idle (`.venv/bin/python -m support.scheduler status`
   shows no leased row): `systemctl --user restart qv4-worker@node2`. Check:
   `journalctl --user -u qv4-worker@node2 -n 20` shows `running from
   /home/user/querynzv4-release at <commit>`.
5. In `docs/briefs/next.md`, integrator section, replace the sentence that
   starts "Until the worker's release copy lands" (through "start it after
   the push;") with:

   > After every push of main, run `.venv/bin/python -m support.installer
   > release` (node2, /home/user/querynzv4); the worker and its jobs run that
   > copy, so an integrate branch no longer needs the worker stopped. When it
   > says `worker restart owed`, restart the idle worker:
   > `systemctl --user restart qv4-worker@node2` (node2).

   keeping the rest of that paragraph (a new job waits for its next slot,
   so a lane's first run is queued by hand).
6. Close the card; rebuild the lessons index (my working copy's test run
   regenerated it; that change is not on the branch).

## Left for you, outside this fence

The product surfaces' standing units (`products/{board,report,published_site,scan}/units/qv4-*.service`)
still name `/home/user/querynzv4` in `WorkingDirectory` and `ExecStart`, so
one restarted during a merge window runs the branch's code. Repointing them
at `/home/user/querynzv4-release` is two lines each, and the installer's
refusal then covers them too. Not done here; the card's note records it.

Lesson: `a-moved-release-copy-does-not-move-the-running-worker`.

## Result (integrator, 2026-10-23 13:50 NZDT)

Merged: `e433ea0 merge integrate/release-copy-1: gate green` (fast tier green on
the integrate branch; the gate's staging step had nothing to load).
Integrator items on the branch: the four product services' units and the
checks' three timers (`qv4-checks-board`, `qv4-checks-heartbeat`,
`qv4-full-tier`) point at the release copy too, with their two pinned tests
repointed; the worker card closed, both halves; the brief's stop/start
interim replaced by the release command. After the merge: pushed main; `python -m support.installer release` created `/home/user/querynzv4-release` at e433ea0 with its own `.venv` (log `/home/user/querynzv4-work/live/installer/release.log`); `apply --units` updated the worker template, the four product services and the three checks services (their timers are superseded by worker jobs and were never installed); the worker started and the four product services restarted from the copy at 13:49, `systemctl show` confirming WorkingDirectory and ExecStart under the release copy; `qv4-offsite-rehearsal` is queued once Arthur clears `/mnt/hdd2/qv4-restore` (see fix-support-offsite-1). From here the integrator runs the release command after every push and no longer stops the worker for a merge window.
Branches and the working copy retired.
