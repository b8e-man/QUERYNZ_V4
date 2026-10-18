# The worker's lease lapses under a run of short pieces
kind: finding
state: open
use-case: the scheduler (step 2.8, leases; seen on step 3's pass one)
session: trial
opened: 2026-10-19

During pass one (`qv4-trial-read-glm-ocr` #54, 264 runs over 3.8 hours)
the worker on node2 reaped its own row six times: "reaped queue row 54:
lease lapsed, 60/255 pieces kept, lost [61]", then "lease lost; stopping
the child", then claimed the row again and went on. Each lost piece was
killed 30 s in (exit -15, outcome `failed`, detail `lease`) and re-run
clean; nothing was lost beyond the page in flight, because every page
read is stored before the next and a re-run replays stored pages.

Cause, in `support/scheduler/worker.py` (`_run_one`, around line 280):
`last_renew` is reset to now at the start of every piece, and `tick()`
renews only once `lease_seconds / 3` (30 s) has passed since that
start. A run of pieces each shorter than 30 s (a one-page or four-page
document takes 4 to 23 s) never renews, and the 90 s lease lapses. The
log shows exactly that: pieces of 4, 16, 23 and 14 s in a row before the
lapse at 23:13:04.

Fix (a fix session on `support/scheduler`, a few lines): keep
`last_renew` on the worker across pieces of one claim, or renew
unconditionally between pieces. Until then every bulk job of short
pieces pays one killed piece per lapse; the 35B's pieces are long and
will not see it.

Blocks: nothing. The proof "a worker stopped mid-run loses at most one
piece" was shown by accident six times.
