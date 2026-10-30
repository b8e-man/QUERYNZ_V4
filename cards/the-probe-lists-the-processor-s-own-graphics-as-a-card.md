# The probe lists the processor's own graphics as a card, and the manager loads the page reader on it
kind: blocker
state: closed
use-case: -
session: integrator-9d788fb
opened: 2026-10-30
closed: 2026-10-30

30 October 13:49, node2, the first tick after the night-window merge (44ecfec) with page work queued (rows 854 and
855): `rocm-smi --showmeminfo vram --showproductname --json` listed a third device for a moment, index 2, product
"AMD Ryzen 9 9950X 16-Core Processor", 2.0 GB: the processor's own graphics, not a card. `register_cards` wrote it
as `scheduler.cards` (node2, 2); the planner saw a cold card and loaded page-reader on it ("ready in 2s"); the
server, started with HIP_VISIBLE_DEVICES=2, ran on the processor (15 cores, 6.4 GB) and two candidate-return pieces
sat on it for four minutes. `probe.cards()` run by hand a minute later listed the two R9700s only.

Done by hand: the row reserved (`reserved_why` names this card), the server killed (the manager logged "card 2: the
server for page-reader exited (-9); card is cold"); the two pieces went back to todo, rows 854 and 855 are queued
for the window. A fix session on `support/scheduler/` owes: (1) the probe keeps a device only when it is a discrete
card (the product is not a processor and the memory is above a floor, say 8 GB), (2) `register_cards` marks a row
whose card the probe no longer lists, so a stale row is never planned, (3) a test for each. Until it merges the
hand reservation stands.

Closed 30 October by fix-support-scheduler-4 (session fix-support-scheduler-1, fourth sitting). (1) `probe.cards`
keeps a device only when `probe.is_card` says so: its product does not name a processor (`PROCESSOR`) and its memory
is at or above `CARD_FLOOR_GB` (8 GB; the R9700 has 31.9, the Ryzen's graphics 2.0); the dropped devices come back
in the profile as `devices_dropped` and the worker's probe log line names them. (2) `Manager.reconcile_listing`,
run by `register_cards` and at the top of every tick, reserves a `scheduler.cards` row whose card the probe no longer
lists with `cards.STALE_WHY` (a hand reservation is replaced; another live worker's row and a failed probe are left
alone), and clears that reservation, and only that one, when the card is listed again. (3) One probe test and
three manager tests on the fake worker, each seen failing on main's code. The hand reservation on (node2, 2) is
replaced by `STALE_WHY` on the worker's first tick after the release and restart.
