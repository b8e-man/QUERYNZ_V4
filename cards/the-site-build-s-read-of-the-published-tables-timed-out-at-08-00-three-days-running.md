# The site build's read of the published tables timed out at 08:00 three days running, so the comparison had no rebuilt side on 4, 5 and 6 November
kind: finding
state: open
use-case: Follow the Money; step 4.4 (the build), 4.5 (the comparison's clean days)
session: integrator
opened: 2026-11-07

Found 7 November 2026 reading the comparison ledger and node2's journal.
`qv4-site-build` (08:00 daily, node2 each time) on 4, 5 and 6 November
read its listing, then two minutes later: `fail  the published tables
could not be read: QueryCanceled: canceling statement due to statement
timeout` (read.py's 120 s limit). No version was written, so the
comparison recorded "no rebuilt version" those days.

What is known:

- A normal build takes 4 to 6 s (07:00 and 09:10 on 7 November, the
  second with `qv4-links-build` mid-run). So the read is not slow; it
  waited.
- On each failing day `qv4-links-build` (07:45, about two hours) was
  running, and the bulk readers (courts, parliament, beehive) were
  loading. On 3 November links-build did not run and the read passed.
- 68c65cd (4 November 10:27) ended the links reader's transaction
  between stages because a lane's `DROP ... CASCADE` queued behind its
  share locks and every reader queued behind the drop. The timeouts on
  5 and 6 November came after it, so either another lock chain of the
  same shape remains (a load's DROP or DELETE behind a long reader, the
  build's read behind the load) or the cause is different.
- The cancelled statement is in the Postgres server log, which this
  session cannot read (permission). The next step is that log for
  4 to 6 November 08:00 to 08:02 on node2, with `log_lock_waits`.

Separately, on 7 November the build ran from yesterday's listing: the
release failed safe at 06:29 on the drill's crash and fired again at
07:27, and the 07:30 watcher still saw 2026-11-06T0616 as current. That
is one day's timing, not this card.
