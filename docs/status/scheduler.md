# scheduler: where step 2 stands

Last close: fix-support-scheduler-6 (the chain runs itself), 31 October
2026, node2. Branch `fix/support-scheduler-1`, merge request
`fix-support-scheduler-6` (on top of -5, not yet merged). Scope
`support/scheduler`.

## Done

- Step 2 on one box (18 October); the release copy; memory raises (ruling
  115); the night window (ruling 129); the page reader beside the OCR server
  and `night open`/`night close` (fix-5, 30 October).
- fix-6 (this close), Arthur 31 October 08:40: (1) `pieces_command` in
  jobs.toml: a pieced row claimed with no pieces runs it in the job's
  environment and its lines are the pieces (`queue.add_pieces`,
  `pieces_source` = command / listed); no lines = done "nothing waiting".
  (2) `then = [...]`: a finished row queues one row of each named job, class
  whenever, one in flight, the detail saying "then: queued row N" or
  "already queued as row M" (`queue.then_rows`, `then_of` on the new row);
  a pieced row with failed pieces still fires it, a failed load does not.
  Wired: courts-load then courts-read; the disclosures, candidate-returns,
  tenders, iwi-directory and charities loads then scan-rerun. (3) The
  pieces of one row run N at once, N = min(concurrency, (profile streams −
  other rows' in flight) ÷ threads), never under 1, written to the row
  (`in_flight`); text-reader `streams = 8` (measured); courts-read
  concurrency 8. `check` refuses: pieces_command on a non-pieced job, a
  `then` to an unknown job, to itself, to a clocked job or to a pieced job
  without a command; concurrency × threads over the streams. `status`
  prints a line per open row: source, in flight, running, then rows.
  Fast tier green (220 tests, 7 s); 16 mutants seen failing.

## Waits on the integrator, at the merge (node2, /home/user/querynzv4)

1. Push main, `.venv/bin/python -m support.installer release`, then with
   the worker idle `systemctl --user restart qv4-worker@node2` (the runner
   is the worker's own code). The tables add three columns on the first
   tick (`ALTER TABLE ... IF NOT EXISTS`).
2. Queue ONE row of `qv4-courts-read` with no pieces; `status` should show
   `in flight 8`; measure Radiance's `num_requests_running` (expected 7 to
   8, was 1) and the pieces a minute (expected about 100 for short
   documents; was 9).
3. The beehive, hansard and parliament readers get `pieces_command` and
   `then` lines when their modules print their waits (the request names
   the commands).

## Not done

- qv4-courts-pages has no pieces listing in the courts lane yet: not in
  courts-load's `then`.
- A load finishing while scan-rerun is already running queues nothing
  (one in flight): the stale lines wait for the next load that fires it.
- checks/scheduler.py's 24 h red on a killed run that came good; the two-box
  proofs on node1.
