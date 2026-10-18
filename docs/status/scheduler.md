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

- A: `registry.py`, `policy.py` (nine rules), `runs.py` carried with tests; `jobs.toml`, `profiles.toml`.
- B: `tables.sql`, `queue.py` (leases, tokens, pieces, timetable, standing, demands, runs, cards, swaps); 13 tests on the sample database.
- C: `probe.py` (cores, memory, pressure, cards, disks, programs; the carried server parsers).
- D: `runner.py` (ceiling, deadline, query limit, peak), `worker.py`, the CLI; 6 worker proofs on the sample database. Real tables in `querynz_v4.scheduler`.

## Half-done

E: `cards.py` written, not yet proven on card 1.

## Intended changes to live things

- [x] Create schema `scheduler` and its tables in `querynz_v4` (`python -m support.scheduler tables`), 18 Oct ~19:40.

## Next

E: load the text-reader profile on card 1 for a real job; then F, G.
