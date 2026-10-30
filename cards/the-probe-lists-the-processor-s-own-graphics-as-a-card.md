# The probe lists the processor's own graphics as a card, and the manager loads the page reader on it
kind: blocker
state: open
use-case: -
session: integrator-9d788fb
opened: 2026-10-30
closed:

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
