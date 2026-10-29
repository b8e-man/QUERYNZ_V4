# The memory shape under Flash-Next wants a stress test before reading moves to node1
kind: finding
state: open
use-case: -
session: integrator-9d788fb
opened: 2026-10-30

Arthur, 30 October, 07:40, on the host-memory bounds for Flash-Next
beside the database and the jobs: "let's flag this for stress testing".

What was measured (node2, 125 GB): Radiance holds 31 GB of host memory
at the unit's pool of 11 GiB a card (24 GB at 8 GiB; the 8 GiB shape
started only before the page reader, flash-next-1), 26 GB of each card;
the page cache holds 83 GB of the 114 GB model file, from which the
n-gram table and the off-card experts are read. The jobs declare up to
6 GB each (the full tier), 13 GB for three at once. The scheduler's
reserve for the database and the standing services is 24 GB
(`support/scheduler/jobs.toml`, `memory_reserve_gb`), sized before
Flash-Next existed: on node2 it is already short of the 31 GB and has
not bitten because 90 GB is spare.

What is not measured, and what the test is for:

1. node1 (64 GB, the same two cards): the unit as built (pool 11 GiB),
   the database streaming as the standby at its default buffers, the
   seven carve-out units, and the bench job (`qv4-rehearsal-bench`) at
   8 and 16 streams while the links build and the full tier run. About
   40 GB held and 24 GB left for the page cache that the model file and
   the database share. Record: the bench's prompt tokens a second
   against node2's 5,600 and 6,100; the database's replay lag; whether
   a job is refused for room or killed; the page cache's size.
2. node2 now: the same three jobs at once with the chat pane in use,
   so the reserve line's figure is set from a measurement, not a sum.
3. The one line to change on both boxes, after the test: line 32 of
   `support/scheduler/jobs.toml`, `memory_reserve_gb = 24` to `40`
   (31 GB for Flash-Next, ruling 121), a support change through the
   gate. Not changed yet: the flash-next-1 merge is in the gate on that
   module.

Clears when both runs are recorded in `docs/status/flash-next.md` and
the reserve is set from them. Owner: integrator for node2 now; node1's
half when node1 returns (ruling 79 and the fence come first).
