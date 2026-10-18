# scheduler: where step 2 stands

Session 2 closed 18 October 2026 ~20:50 NZDT on node2. Branch
`session/scheduler` (on origin/main 18f1897); merge requests scheduler-2a,
2b, 2c raised. Scope `support/scheduler`, `support/installer`,
`support/profiles` (untouched). The worker on node2 runs from THIS working
copy (rehearsal unit); the merge's `apply --units` restores the shipped one.

## Done this session, each proven live on node2 (card 1; card 0 and the carve-out never touched)

- The four founding timers on the queue's clock: `qv4-checks-board` 18:30
  UTC, `qv4-checks-heartbeat` 20:00 and 08:00, `qv4-full-tier` 15:30,
  `qv4-offsite-dump` 14:05 (their units' deadlines, a query limit each,
  `nice = 10`). The installer superseded the timers at 20:36 (disabled,
  removed, each clock handed over so nothing ran twice); each job ran by hand
  through the queue (ruling 56): heartbeat, board, dump ok; full tier green
  on its second run (783 passed; the first red was this session's own test).
  No `qv4-` timer is left on node2. Queue item: the heartbeat's own clock.
- The model server built from source beside the copy: `python -m
  support.installer build` → `<live>/llama/built/bin` (10276, gfx1201 from
  rocminfo, self-contained `$ORIGIN`; the copy loads the old build tree's
  libraries). `profiles.toml [server] binary = "built"` now; the embedding
  and text-reader profiles loaded on card 1 by the built server (2 s, 4 s),
  models read back, the ledger naming the server.
- `embed()` for the model client, as a patch beside merge request 2b (a
  contract change; the integrator applies it): proven live, 3 texts, 1,024
  dims; a wrong model name refused because the served model is read back
  from `/v1/models` (an embeddings answer echoes the request; lesson filed).
  `qv4-embed` has its piece command and is enabled.

## Not done / waits

- `qv4-embed`'s first queued run waits on the patch landing on main.
- Outside this fence, for the integrator (in 2a): `support/db` and the
  owner map naming `scheduler`; the board reading `scheduler.json`; the four
  timer files in `checks/jobs/` and `support/offsite/jobs/` can go.
- The two-box proofs stay owed on node1 (cards/node1-setup-as-the-second-box.md).

## Next

The node1 setup card when Arthur powers node1 (each node1 line his word).
Step 2 is otherwise finished on one box.
