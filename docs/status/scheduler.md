# scheduler: where step 2 stands

Session 1 closed 18 October 2026 ~19:10 NZDT on node2. Branch
`session/scheduler`, merge request `scheduler-1` raised. Scope
`support/scheduler`, `support/installer`, `support/profiles` (untouched).

## Done (proven on node2, card 1 only; card 0 and the carve-out never touched)

- Old fleet planner, registry, run ledger carried with their tests; rules 6–9; the catalogue (`jobs.toml`) and the four profiles (`profiles.toml`).
- The queue in `querynz_v4.scheduler` (7 tables, readable by the session reader): leases, fencing tokens, pieces, the timetable in the queue, standing counts, demands, swaps, runs.
- The probe, the runner (PSS ceiling, deadline, query limit, peak), the worker, the card manager, the installer, the re-read job type. 139 tests (33 slow, on the sample database).
- Live record, 18 Oct 18:47–19:00: `qv4-worker@node2` and `@node2-b` registered probed profiles; text-reader, embedding, page-reader and review loaded on card 1 (2–4 s each), every swap ledgered with the served model read back; ten published returns re-read by the text-reader, all ten EQUAL to the published totals; a frozen worker's lease lapsed and the other finished the job (3+7 pieces), the silence alarm reached ntfy once; a deliberate stop handed a job over with no alarm; the two-minute timetable ran on the survivor; the memory ceiling, the program gate and the peak flag proven on the sample database.

## Done-when, step 2

Every item ticked on the one-box rehearsal except: the real two-box proof (owed when a second box exists, the queue's default); "the text-reader reproduces a reading the old estate holds" is proven against the published totals (10 of 10), not the old estate's stored model readings.

## Half-done / not built

- `qv4-embed` has no piece command: the model client lacks `embed()` (carded). `qv4-questions` (ruling 22's default hold) is in the catalogue, disabled until a product is served.
- The four founding timers still run on systemd's clock (carded).
- The worker unit on node2 was placed from THIS working copy (rehearsal); the merge's `python -m support.installer apply --units` restores the shipped unit, then `systemctl --user restart qv4-worker@node2.service`.

## Live changes made (all ticked)

- [x] schema `scheduler` in `querynz_v4`; [x] model server copied to `<live>/llama/bin` (old build read only); [x] `qv4-worker@.service` placed, `qv4-worker@node2` enabled and running; `qv4-worker@node2-b` stopped at the close (queue item: a second worker on node2).
- Two alarms reached the phone: `qv4-reread failed` at 18:41 (a server I had stopped under a run; not a fault of the estate) and `worker node2-b silent` at 18:55 (the proof).

## Next

Session 2, if any: the founding timers into the queue; `embed()` then `qv4-embed`; the questions hold when a product is served; the model server built from source beside the copy.
