# The night window is opened early only by a commit on main, not by a command
kind: finding
state: open
use-case: -
session: integrator-9d788fb
opened: 2026-10-30
closed:

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
