# The lease lapses while a large model loads
kind: finding
state: open
use-case: the scheduler (step 2; the trial's pass two, 19 October)
session: trial
opened: 2026-10-19

The worker takes a queue row's lease (90 s) at the claim and then asks the
card manager for the row's profile. A load longer than the lease lapses
it before the first piece starts, so the row is reaped and its piece
lost at once. Twice on 19 October, both on the 35B model:

- 13:43:31 the card releases `trial-chandra-q4`; 13:45:35 `trial-infinity-q4`
  ready in 124 s; 13:45:35 "claimed row 68"; 13:45:40 "reaped queue row
  68: lease lapsed, 0/255 pieces kept, lost [1]"; 13:46:05 "row 68: lease
  lost; stopping the child"; 13:46:09 claimed again. Run
  `0faeafa27ddd4e3c`, "stopped: the lease was lost".
- 14:47:14 `trial-infinity-q8` ready in 202 s; run `da3935edc6344f60`
  (row 73) lost the same way; the row's detail still says "lease lapsed
  from node2 at 2026-10-19T01:47:19+00:00".

The earlier fix (the renewal clock on the claim, not the piece: card
`the-worker-s-lease-lapses-under-a-run-of-short-pieces`, closed by the
integrator at trial-2) does not reach this: nothing renews while the
worker waits for the server. The small models load in 2 to 42 s and never
hit it. Each lapse cost one piece and a second claim; the pieces re-ran
and nothing was wrong in the readings.

Blocks: nothing. The scheduler proof "a worker stopped mid-run loses at
most one piece" still holds; this is a self-inflicted stop.

Fix (a fix session on `support/scheduler`): renew the lease inside the
wait for the card (the same `tick()` the pieces use), or claim after the
profile is ready. A slow test: a fake card manager that takes two leases
to load, one claim, zero reaps.
