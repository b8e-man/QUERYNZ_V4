# The night window is opened early only by a commit on main, not by a command
kind: finding
state: closed
use-case: -
session: integrator-9d788fb
opened: 2026-10-30
closed: 2026-10-30

30 October 15:15, Arthur: fire the window now for the 663 queued page documents. The window's hours live in
`support/scheduler/jobs.toml`, which the worker reads from the release copy, and the release copy may not be
edited: the worker keeps no catalogue and claims nothing while a tracked file is edited there (15:31 to 15:37,
the MCP pull stalled with it), and the installer refuses to release over the edit. So the start was moved to 15:00
by a commit on main (8e9567c) with the test that pins the shipped hours changed to match, released, and the worker
restarted: the window opened at 15:37:19 and the page reader was on card 1 five seconds later.

Owed: (1) the integrator puts the start back to 22:00 (ruling 129) once rows 854 and 855 are done, by the same
route; (2) a scheduler fix so Arthur's word is one command on node2 (say `python -m support.scheduler night open`
writing a marker under `<live>/scheduler/` that `night_window()` honours until the window would close, with the
ledger line saying who opened it), never a commit.

21:20, 30 October: (1) done. The window closed itself at 21:14 (page queue empty; Radiance back on :8060 at 21:14,
both cards flash-next); `start_local` is 22:00 again by 07bad0d with the pinning test, released; no restart needed.
(2) stands.

22:45, 30 October, fix-support-scheduler-5: (2) done. On node2, in /home/user/querynzv4 (or the release copy):
`.venv/bin/python -m support.scheduler night open [--until HH:MM]` writes `<live>/scheduler/night-word.json`; the card
manager hears it each tick, and the moment counts as inside the window until the window would close anyway (05:45), or
until HH:MM local if sooner (a later hour is capped at the close). `night close` inside a window closes it for the rest
of the night (the page readers drain, Radiance starts again, no new stop until 05:45); outside one it withdraws an early
open. `night` alone says where the window stands. The stop line in the swap ledger carries "opened early by <user> at
HH:MM NZDT (night open), until …"; the start line names the close the same way. Nothing in jobs.toml moves, nothing is
committed or released; a torn or stale word is silence and a stale one is removed. Nine fast tests on the fake worker.
