# fix-support-scheduler-4: a device is a card only when it is discrete, and a stale card row is never planned
branch: fix/support-scheduler-1 (pushed; e013c47, on main 035d369)
session: fix-support-scheduler-1 (fix, support/scheduler/), fourth sitting; the three earlier requests of this working copy are merged (docs/merges/fix-support-scheduler-1.md, -2.md, -3.md)
raised: 2026-10-30
claims: support/scheduler/probe.py, cards.py, worker.py; tests/test_probe.py (+1 test), tests/test_cards.py (+3 tests); cards/the-probe-lists-the-processor-s-own-graphics-as-a-card.md (closed); lessons/a-probes-device-list-is-not-a-card-list.md (new)
closes: card the-probe-lists-the-processor-s-own-graphics-as-a-card (blocker, 30 October 13:49: rocm-smi listed the processor's own graphics as a third device for one tick; the row was written, the planner loaded page-reader on it, the server ran on the processor)

1. **The probe keeps a device only when it is a discrete card.** `probe.is_card`: the product does not name a
   processor (`PROCESSOR`, matching processor / cpu / apu / ryzen / epyc / athlon / core(tm), case-blind) AND its
   memory is at or above `CARD_FLOOR_GB = 8.0` (the R9700 reports 31.9; the Ryzen 9 9950X's graphics 2.0; a device
   whose memory could not be read fails the floor). `probe.cards(payload, run, dropped=None)` leaves the others out
   and appends them to `dropped` when a list is given; `probe.profile` puts them in the profile as `devices_dropped`.
   The worker's `probe()` logs `probe: not a card, dropped: index 2 'AMD Ryzen 9 9950X 16-Core Processor' 2.0 GB`
   when the dropped set changes (not every probe). The night window's `_wait_released` reads the same filtered
   list; the two R9700s pass it unchanged.
2. **A stale row is never planned.** `Manager.reconcile_listing(worker)`, run by `register_cards` after the listed
   cards are written and at the top of every `tick` (one SELECT): a `scheduler.cards` row on this box whose card the
   probe does not list is reserved with `cards.STALE_WHY` ("the probe does not list this card: the row was written
   from a device that has gone (card …)"), with a log line naming the card, its product and memory; a hand
   reservation on such a row is replaced (the log says so). The reservation is cleared, and only `STALE_WHY` is
   cleared, when the probe lists the card again and the card is not in jobs.toml's fixed reservations. A failed
   probe (cards None) marks nothing: a failed command is not data. Another live worker's unreserved rows are left
   alone (the rehearsal). Only `reserved`, `reserved_why` and `worker` are written: the row's profile and port are
   not touched, so a running server's state stays true until `_reap_dead_servers` sees it.
3. **Nothing else in the window logic changes.** `held`, `night_tick`, `mark_standing` and the planner are as
   merged in 44ecfec; the ruling-121 and ruling-129 tests stand unchanged.

Tests (fast, on the fake worker; no model, no card):
- `test_the_processors_own_graphics_is_not_a_card`: the 13:49 payload (two R9700s and the Ryzen) gives cards 0 and
  1 and reports the Ryzen dropped with its product and 2.0 GB; a 4 GB "Radeon 780M Graphics" is dropped on the
  floor alone; the floor is 8.0. Failed on main's code: `cards() got an unexpected keyword argument 'dropped'`, and
  without it the list was `[0, 1, 2]`.
- `test_the_processors_graphics_in_the_probe_listing_is_not_registered`: `register_cards` from that payload writes
  rows 0 and 1 only. On main: `[0, 1, 2] == [0, 1]` failed.
- `test_a_row_whose_card_the_probe_no_longer_lists_is_reserved_and_never_planned`: rows 0, 1 and a hand-reserved row
  2 in the table, the probe listing 0 and 1: row 2 is written reserved with `STALE_WHY`, logged, `held` shows n:2
  reserved and n:0 not; a second reconcile writes nothing; a failed probe writes nothing. On main: no write for
  card 2 (`STALE_WHY` absent).
- `test_a_stale_reservation_clears_when_the_probe_lists_the_card_again`: row 1 stale and row 5 reserved for another
  reason, both listed: row 1 is written `reserved=False, reserved_why=None`, row 5's reservation stands.
`bin/fast support/scheduler` green in 46.3 s (179 tests). The real probe on node2 at 14:3x lists the two R9700s
and drops nothing. The root `tests/test_generators.py::test_the_committed_records_generate_cleanly` fails on the
branch only because the card board and the lessons index are stale (a closed card, a new lesson); the integrator
regenerates both at the merge as before. No slow test added.

**What the integrator must do after the merge (node2, /home/user/querynzv4):**

1. Regenerate the board and the lessons index (`bin/board`, `bin/lessons-index`) and commit them with the merge.
2. Push main, `.venv/bin/python -m support.installer release`, then before 22:00 and with the worker idle
   `systemctl --user restart qv4-worker@node2`: the new probe and manager code run only from a restart. On the
   first tick the manager's `reconcile_listing` replaces the hand reservation on (node2, 2) with `STALE_WHY`; the
   journal shows `card 2: not listed by the probe ('AMD Ryzen 9 9950X 16-Core Processor', 2.0 GB); the hand
   reservation is replaced; the row is reserved so it is never planned`. Rows 854 and 855 then run in tonight's
   window on card 1 as merged.
3. Should the row ever be wanted gone rather than reserved, it is a regenerable row of the scheduler's own table and
   may be deleted by hand; nothing in this fix deletes it.

Lesson filed: lessons/a-probes-device-list-is-not-a-card-list.md.

## Result

Merged 30 October 2026, 14:35, as 4f57fdf (integrate branch d3eeeda; gate green, marked, every slow test since
support/ changed; nothing staged). One integrator commit on the way: the lessons index and the card board
regenerated (the card closes). Released after the push. `qv4-worker@node2` is restarted once the MCP pull it is
running (row 856, the courts files) finishes, and before 22:00, so the hand reservation on (node2, 2) is replaced by
`STALE_WHY` on the first tick and the window opens on the new code. Working copy `fix-support-scheduler-1` and the
local branches retired; `fix/support-scheduler-1` on the remote is Arthur's to delete.
