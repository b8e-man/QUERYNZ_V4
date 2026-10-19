# offsite (track B, session 2)

**Updated:** 2026-10-19 19:45 NZDT. Overwritten at every close.

## Done

- offsite-2a merged (fe236e1): the copy, the delete rule, the rehearsal;
  `qv4-offsite-copy` in the catalogue at 21:00 NZDT (the step 1.8 dump kept
  beside it until 2b).
- First full copy 19 October 07:45 to 09:44 (1 h 59 min): 278 pieces, 24 GB
  sent, 34.5 GB of vectors kept on /mnt/hdd2. It is the press graph's last
  full copy (5.4 GB sealed; the old push sends 10.7 GB of it a night).
- On the branch since (5dfaa6c..9e07785, not merged): tables over 1 GB as
  ranges of heap pages, only changed ranges sent; one copy at a time per
  spool; the restore compares rows as a multiset (a reloaded table does not
  read back in load order), downloads overlap the load. Local rehearsals:
  querynz_v4 35/35 and the ranged registers 137/137 equal.

## Under way

- The bucket rehearsal, unit `qv4-offsite-rehearsal-bucket` (started 19:40),
  log `/home/user/querynzv4-work/scratch/offsite/rehearsal-bucket.log`,
  record `/home/user/querynzv4-work/live/checks/offsite-restore-last.json`.
  It restores copy 20261019T193457 into /mnt/hdd2/qv4-restore and removes
  it when equal; on failure everything is kept for a look.

## Next

1. When it is equal: merge request offsite-2b (the branch since 2a and the
   rehearsal's time), and the integrator retires `qv4-offsite-dump`.
2. If not: read the record's `out_bad`/`in_bad`, fix, rerun.

## Waiting on Arthur

- The old read login points at db-primary: with node1 down there is no
  standby, so the copy reads the old databases on the primary (read only).
