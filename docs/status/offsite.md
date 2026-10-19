# offsite (track B, session 2)

**Updated:** 2026-10-20 03:30 NZDT. Overwritten at every close.

## Done

- offsite-2a merged (fe236e1): the copy, the delete rule, the rehearsal;
  `qv4-offsite-copy` on the queue's clock at 21:00 NZDT. It ran 19 October
  10:33 (catch-up) and 21:00, both green.
- First full copy 19 October 07:45 (1 h 59 min, 24 GB sent; 34.5 GB of
  vectors kept on /mnt/hdd2): the press graph's last full copy.
- **Restore from the bucket to equality, 19 October 19:40 to 21:30: 1 h 50
  min**, copy 20261019T193457 (objects of four runs): 269 of 269 tables, 530
  million rows, and 90,123 of 90,123 files equal; 24.5 GB fetched in 41 min.
  The vectors table is kept on the box, never sent (by design).
- offsite-2b raised (branch at the commit that carries this file): ranges
  for tables over 1 GB, the spool lock, the multiset check, prefetch, and
  the step 1.8 dump retired (code and units here; the scheduler's three
  files by patch).

## Under way

- The vectors from the local copy: unit `qv4-offsite-rehearsal-vectors`,
  log `/home/user/querynzv4-work/scratch/offsite/rehearsal-vectors.log`,
  record under `/home/user/querynzv4-work/scratch/offsite/live/checks/`.

## Next

- Nothing in track B's brief is left. After 2b merges, a normal night sends
  only changed ranges; the first Sunday full (25 October) and the first
  28-day rehearsal are the next measurements.

## Waiting on Arthur

- Card `the-press-graph-leaves-the-old-nightly-push` (after the election).
- The old read login points at db-primary: with node1 down there is no
  standby, so the copy reads the old databases on the primary (read only).
