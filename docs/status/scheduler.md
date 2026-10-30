# scheduler: where step 2 stands

Last close: fix-support-scheduler-5 (three cards of 30 October), 30 October
2026 22:45, node2. Branch `fix/support-scheduler-1`, merge request
`fix-support-scheduler-5`. Scope `support/scheduler`.

## Done

- Step 2 on one box (session 2, 18 October); the release copy (23 October);
  memory raises (fix-2, ruling 115); the night window (fix-3, ruling 129:
  `[night_window]`, `night.py`, `cards.Manager.night_tick`, the stop/start
  swap lines, the marker under <live>).
- fix-support-scheduler-5 (this close): (a) inside the window the page
  reader also loads on card 0 beside the frozen OCR server when the card's
  free memory, read after Flash-Next releases, covers 4.8 + 2.0 GB
  (`cards.BESIDE_HEADROOM_GB`); else the card is held; the stop line carries
  the figures; only the page profile goes there; a failed beside load holds
  the card, not the profile. Rule 9 spreads a resident bulk job to a card
  idle on any tick. The worker picks the least-loaded card holding the
  profile per piece (`Worker.pick_card`), caps a job type per card, and
  `max_parallel` is 8. (b) `python -m support.scheduler night open
  [--until HH:MM]` / `night close` / `night`: Arthur's word, one file
  `<live>/scheduler/night-word.json`, honoured until the window would close
  anyway; the ledger names who gave it. (c) every Manager in the tests keeps
  its markers under the test folder (conftest). Fast tier green (127 tests,
  5 s); eight mutants seen failing.

## Waits on the integrator, at the merge (node2, /home/user/querynzv4)

1. Push main, `.venv/bin/python -m support.installer release`, then with
   the worker idle `systemctl --user restart qv4-worker@node2` (the
   manager's night state and the worker's card choice are built at start).
2. The first night after: `python -m support.scheduler status` should show
   two `load` lines for page-reader (cards 0 and 1) after the `stop` lines,
   card 0's stop detail with its free-memory figures, and `night` says where
   the window stands. Arthur's early open is now `python -m
   support.scheduler night open` on node2, never a commit.
3. Fold any `memory` raises as before (ruling 115).

## Not done

- checks/scheduler.py still counts a killed run that came good as failed
  for 24 h (outside this fence).
- The two-box proofs stay owed on node1.
- Whether `page-reader` at `slots = 3` needs a larger `memory_gb` than the
  4.8 measured at 32768x1 is unmeasured; the headroom covers it tonight.

## Next

The node1 setup card when Arthur powers node1.
