# Whether the checks-board heartbeat keeps a clock of its own outside the queue

Raised 2026-10-18 by scheduler (session 2), while moving the four founding timers into the catalogue (step 2.12).

**Default, used until he rules:** the heartbeat runs on the queue's clock like the other three (as the card asked). On one box nothing independent watches the worker; `Restart=on-failure` restarts a crashed one, and a box that is down could not have fired a timer either. When node1 is set up, the other worker's silence alarm (2.10) is the independent watcher.

**Blocks:** nothing.

**Recommendation:** the default. The heartbeat's old independence was from the BOARD, not from the box; the queue keeps that (a board that fails raises the failure alarm from the worker, and the heartbeat still alarms after 26 hours without a board). If Arthur wants a watcher outside the queue on one box, it is one timer re-shipped from `checks/jobs/` with the job taken out of the catalogue: a line, not a rewrite.
