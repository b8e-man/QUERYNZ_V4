A lease is stamped from a clock read at the claim, never from one read earlier in the tick: the worker's `now` was 124 s stale after a model load, and the lease it stamped had already lapsed when the row was claimed.
area: scheduler, leases, the worker tick, anything that threads one `now` through a loop
paid-for-by: 2026-10-19, the trial's pass two (two rows reaped by their own worker, two pieces re-run); fixed in fix-support-scheduler-1

The card (`the-lease-lapses-while-a-large-model-loads`) read the log as a
missing renewal: nothing renews while the worker waits for the card. The
real cause was a timestamp. `Worker.tick()` read `now = q.utcnow()` once at
its top, let the card manager block for the whole load, then passed that
`now` to `q.claim`, which stamped `lease_until = now + 90 s`: a time already
in the past. The next tick's reaper took the row. Renewal was never the
problem and the earlier renewal fix was right.

The shape to look for: one clock value captured at the top of a loop and
reused after a call that can take minutes. Anything that writes a deadline,
a lease or an expiry reads the clock at the write. The slow test is a fake
card manager that takes two leases to load; one claim, a live lease, zero
reaps.
