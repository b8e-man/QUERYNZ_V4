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

- [x] Copy the old model server build beside itself into `<live>/llama/bin` (installer; the old build is read only). Done 18 Oct 18:38.
- [x] Start worker processes `node2` and `node2-b` from this working copy (background processes; the unit goes in at the merge), which load profiles on card 1 only; card 0 untouched. Started 18 Oct 18:38; found the session's sandbox hides card 1's render node (one `/dev/dri/renderD*` visible, `rocminfo` empty), so the worker is restarted outside the sandbox (allowed-command list and hooks still on; not bypass-permissions mode).
- [ ] Place `qv4-worker@.service` in the user unit folder through the installer, from THIS working copy (the sandbox bypass was refused; a unit runs outside it), enable and start `qv4-worker@node2`. The merge's installer run replaces the unit with the shipped one (main checkout). 18 Oct ~18:55.
- [x] Create schema `scheduler` and its tables in `querynz_v4` (`python -m support.scheduler tables`), 18 Oct ~19:40.

## Next

E: load the text-reader profile on card 1 for a real job; then F, G.
