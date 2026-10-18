# scheduler: where step 2 stands

Session 2 open, 18 October 2026, on node2 from the working copy
`/home/user/querynzv4-work/scheduler` (branch `session/scheduler`, at origin/main
18f1897 plus this session). Scope `support/scheduler`, `support/installer`,
`support/profiles` (untouched).

## Done this session (code, tests green on the fast tier)

- The model server built from source beside the copy: `python -m support.installer build`
  clones `/home/user/llama.cpp` (read only) into `<live>/llama/src`, builds
  `llama-server` for the probed card architecture (gfx1201, rocminfo) with the
  old build's flags, and puts it with its libraries in `<live>/llama/built/bin`
  with `VERSION.json` (commit, flags, hash, runpath). Built 18 Oct: 10276
  (6ea215d17), self-contained (`$ORIGIN`); the copy is not (it loads the old
  build tree's libraries; the card manager's LD_LIBRARY_PATH covers it). Which
  one the cards run is `profiles.toml [server] binary` ("copy" for now).
- The four founding timers in the catalogue (`qv4-checks-board` 18:30 UTC,
  `qv4-checks-heartbeat` 20:00 and 08:00, `qv4-full-tier` 15:30, `qv4-offsite-dump`
  14:05), with their units' deadlines, a query limit each, `nice = 10`, and
  `requires` for the dump. `at_utc` takes a list; the queue has `handover()`;
  the installer supersedes a timer whose job is timetabled (disable, remove,
  hand the clock over, keep the service unit for a hand run).

## Live changes intended (ticked when done)

- [ ] On node2, from this working copy: supersede the four timers through
      the installer (`apply --units --repo <wc> --only` the four `.timer`
      names), which hands each clock over so nothing runs twice.
- [ ] Place `qv4-worker@.service` from this working copy and restart
      `qv4-worker@node2` (the rehearsal pattern; the merge's install restores
      the shipped unit).
- [ ] Hand-run the four jobs through the queue (ruling 56) and read their
      run records: outcome, peak against declared.
- [ ] `[server] binary = "built"`, then the embedding profile loaded on card
      1 by the rehearsal job, served model read back, the ledger naming the
      built server.

## Not yet / next

- `embed()` in the model client (a contract change, the integrator's) and
  `qv4-embed`'s piece command.
- Merge requests, lessons, cards, the end-of-session note.
