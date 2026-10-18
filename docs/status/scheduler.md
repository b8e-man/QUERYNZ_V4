# scheduler: where step 2 stands

Overwritten at every close; under 3 KB. Session 1 began 18 October 2026
18:04 NZDT on node2, branch `session/scheduler`, scope `support/scheduler`,
`support/installer`, `support/profiles`.

## Plan of tranches (verified against the box, one at a time)

- A. Carry the old fleet planner and registry with their tests; rules 6–9.
- B. The queue in the database (`scheduler` schema): leases, tokens, pieces, timetable, standing counts.
- C. The probe (cores, memory, cards, disks, programs) and the worker's registration, heartbeat and the silence alarm.
- D. The worker loop: pull, run under a memory ceiling and a deadline, peak memory, run records; two workers on node2.
- E. Cards and model profiles: card state, swaps and their ledger, the model server beside the old one.
- F. The installer.
- G. The re-read job type.

## Done

Nothing yet.

## Half-done

A: starting.

## Intended changes to live things

None yet. (Written here before they are made; ticked after.)

## Next

A.
