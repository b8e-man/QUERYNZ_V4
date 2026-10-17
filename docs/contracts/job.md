# Contract: a job

**Fixes:** what a scheduled job declares and what the machinery gives it.
**Test:** `support/jobspec/tests/`. **Taken from:** the old
`config/job_types.yaml` (one card, one job type; context per slot; VRAM
measured, never computed) and the old units that had deadlines with no
query time limit under them.

A job declares, in `support.jobspec.JobNeeds`:

1. **What it needs:** a model profile (a model plus its settings on a
   graphics card) by name, or the processor only.
2. **Memory per parallel worker,** measured, never computed. A ceiling
   above what the box has free is not a control.
3. **A deadline,** longer than its work and shorter than its interval. One
   old job was killed 55 times in a week.
4. **A query time limit under the deadline,** so a job killed at its
   deadline does not leave its query running and holding a snapshot.
5. **Whether it can share** a card's profile slots, and optionally that it
   prefers the most memory.

The machinery gives every job: a unit named `qv4-…` (hard limit 23), a
record of each run, an alarm when it fails, and the same job file on both
boxes from one installer (step 2.11). After step 2 no job starts a model
server by hand; every use of a graphics card goes through the scheduler,
which holds one model profile per card at a time and records every swap
(hard limit 25). A deliberate stop never raises the failure alarm.
