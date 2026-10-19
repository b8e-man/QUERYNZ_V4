# fix-support-scheduler-1: the three scheduler cards the trial raised (the lease, rule 6, a server per profile)
branch: fix/support-scheduler-1
session: fix-support-scheduler-1 (weight fix, scope support/scheduler/)
raised: 2026-10-19
claims: support/scheduler only (worker.py, cards.py, policy.py, probe.py, registry.py, profiles.toml's `[server]` comment, spec.md, README.md, tests); two cards closed, one card progressed, one card raised, one lesson

Four commits on main at fe00545, one per card and one for the records:

- `cba95ef` **the-lease-lapses-while-a-large-model-loads** (closed). The cause
  was a stale clock, not a missing renewal: `Worker.tick()` read `now` once,
  the card manager blocked 124 s loading the 35B model, and the claim
  stamped its lease from that `now`, so the lease had lapsed before the first
  piece and the worker's own reaper took the row. The claim now reads the
  clock again. Slow test: a fake card manager that takes two leases to load;
  one claim, a live lease, zero reaps, one attempt. Red before, green after.
- `9c89e13` **the-card-manager-loads-a-profile-for-a-job-no-box-can-claim**
  (closed). `policy.plan` takes `eligible`, the job types this box can claim
  at all, and sees no other demand, so rule 6 and rule 3's "others waiting"
  never act for a row no worker here may take. The card manager passes
  `Manager.claimable(worker)`: enabled, required programs present, not on a
  profile whose load failed here while the box's programs are as they are
  now (`failed_loads`; a stray on the port is not held against the profile).
  The binary and weights checks moved ahead of the unload, so a load that
  cannot start no longer discards a working profile. Four tests, each red
  without its change.
- `91f383b` **teleocr-needs-a-patched-server-the-scheduler-cannot-choose**
  (progressed, left open). A profile may carry `binary = "<probe name>"`;
  `probe.PROGRAMS` has `qv4-llama-server-teleocr` at
  `<live>/llama/built-teleocr/llama-server` (the real probe on node2 lists it
  now); `cards.server_binary` gives such a profile that program or nothing,
  never the `[server]` setting; a job whose profile's server this box lacks
  is never eligible here; a binary the probe does not look for is a
  catalogue problem. Three tests, red without the change.
- `b636e6e` the lesson `a-lease-is-stamped-from-the-clock-at-the-claim` and the
  card `the-trial-s-catalogue-check-wants-its-additions-verbatim`.

## Checked

- Fast tier, the module: green, 116 tests, under 5 s. Fast tier, the whole
  repository: green but for `tests/test_generators.py::
  test_the_committed_records_generate_cleanly`, which is red on this branch
  because two cards closed and `docs/board.md` is generated at the merge (it
  rebuilt the board in my working copy as a side effect; that change is not
  committed, the scope hook refuses a non-main session touching it).
- Slow: every test in test_worker.py and test_cards.py against the sample
  database here, 24 green in 1 m 49 s.
- `python -m support.scheduler check`: green, 34 job types, 13 profiles.
- `support/trials/tests/test_readers_catalogue.py::test_the_merged_catalogue_passes`:
  green on the branch as pushed.

## At the merge (integrator)

1. **The two TeleOCR profile lines, in both files in one commit.** The trial's
   merged-catalogue check (`support.trials.catalogue.merged_text`) wants
   `support/trials/scheduler/profiles-additions.toml` verbatim inside the
   shipped `support/scheduler/profiles.toml`, so a fix session on the
   scheduler could not add them (the additions file is outside the fence).
   Add this line directly under `model = "teleocr"` in `[profiles.trial-teleocr]`
   and under `model = "teleocr-f16"` in `[profiles.trial-teleocr-f16]`, in
   BOTH files, identically:

   ```toml
   binary = "qv4-llama-server-teleocr"
   ```

   Then `python -m support.scheduler check` and `python -m support.trials.catalogue check`
   (both green), and close the TeleOCR card. The `requires` line on the two
   TeleOCR jobs stays: the probe now lists the program, so it is satisfied
   wherever the profile is loadable, and it mirrors the additions file.
2. **Rebuild the board** (`bin/board`), as every merge does; the generators
   test goes green with it.
3. **Restart the worker after the merge, from the main checkout, on node2:**

   ```text
   cd /home/user/querynzv4 && systemctl --user restart qv4-worker@node2
   ```

   Arthur's sentence: the worker is live, so not before the merge and not
   from this working copy. The worker reloads the catalogue on its own clock,
   so step 1's profile lines need no further restart.

## Notes for the integrator

- `bin/fast` falls back to the system Python (no pytest) when the working
  copy has no `.venv`; it only uses the main checkout's environment for the
  fill. I ran the same command through `/home/user/querynzv4/.venv/bin/python`.
  `bin/` is protected, so this is a note, not a fix.
- The card `the-trial-s-catalogue-check-wants-its-additions-verbatim` says
  the same check will trip by itself when the first swap writes `memory_gb`
  or `load_seconds` back into a trial profile; the fix is the trial's.
- Nothing live was touched: no restart, no unit, no job, no table outside
  the scratch schema. The worker on node2 still runs main's code.

## Result (integrator, 2026-10-19 20:45)

Merged into main as 5d8c704. At the merge: `binary = "qv4-llama-server-teleocr"`
under both TeleOCR profiles in both catalogue files, identically; both checks
green (35 job types, 13 profiles); the TeleOCR card closed; board rebuilt.
The worker was restarted from the main checkout at 20:39 and registered with
no programs missing. The `bin/fast` note stands as a note.
