# An HTTP 500 from the Real Estate Authority ends the run as failed
kind: finding
state: open
use-case: 1
session: founding
opened: 2026-10-21

The `qv4-real-estate-authority-capture` run of 20 October (queue row 150,
23:00) listed 20 pages and 184 cases, held 169, landed 292 PDFs and set 28
aside, then stopped at 23:45 on an HTTP 500 read as "a block or a
challenge; a challenged read is a failed read (hard limit 6)", exit 1, and
the checks board went red for it.

Stopping on a challenge is right. A 500 is the server's own error, not a
challenge or a block, and it ended a run that had done its night's work.
Recommended: a 500 is one failed read, set aside with its status, the run
resting and continuing, and its exit green when it landed what it listed.
If the lane keeps 500 as a stop, the run should still exit green with a
"stopped early" line so the board does not call a polite stop a failure.
The lane's call.
