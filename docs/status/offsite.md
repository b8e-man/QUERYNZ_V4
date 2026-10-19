# offsite (track B, session 2)

**Updated:** 2026-10-19 07:50 NZDT. Overwritten at every close.

## Done

- The copy and the rehearsal, in `support/offsite/` (`pieces.py` the
  delete rule, `copy.py`, `restore.py`, `spec.md`): one piece per table
  (its `COPY` text, sha256 and rows, zstd, gpg) and per file tree; nightly
  only what moved, full on Sunday, the press graph frozen (sent when it
  moves or every 28 days); every manifest complete, so a restore needs the
  newest one only. Proven on `querynz_v4` and the inbox: a nightly restored
  to equality from objects of two stamps; a tampered hash fails the check.
  Fast tier green.
- Card `the-press-graph-leaves-the-old-nightly-push`; lesson
  `an-empty-selection-is-not-no-selection`.

## Under way

- The first full copy, unit `qv4-offsite-copy-first` (user unit, started
  07:45), log `/home/user/querynzv4-work/scratch/offsite/first-full.log`,
  local copy `/mnt/hdd2/qv4-offsite`. It is the press graph's last full
  copy. If it dies, rerun `python -m support.offsite copy --full` from this
  working copy: it resumes the same stamp within 20 hours.

## Next

1. When it finishes: `python -m support.offsite restore` (from the bucket)
   on `/mnt/hdd2/qv4-restore`, record the time, raise merge request 2.
2. The integrator applies the catalogue patch in merge request 1
   (`qv4-offsite-copy` replaces `qv4-offsite-dump`, `qv4-offsite-rehearsal`).

## Waiting on Arthur

- 32 GB of copies sealed under the test passphrase in
  `/tmp/pytest-of-user/pytest-{251,253,256,261,263}` (outside the fence).
- The old read login points at the primary (no standby while node1 is down).
