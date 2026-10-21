# The database application role `querynz`: the sitting

**The sitting is Arthur's.** He chooses the day and is present. **Default:
the first quiet day after the election of 7 November 2026**, well clear of
the 06:19 release. It is stop-the-world for the old estate: every old job
restarts. It is the third kind of change to the old estate this plan
allows (hard limit 22): credential files and running jobs, never the old
repository. **Rehearsed on a scratch pair of database instances first**
(the session builds that rehearsal before the sitting; the last replication
rotation forced a 326 GB standby rebuild).

**Reach:** local network only. The database accepts this role from
10.0.0.0/24, so the password is not usable from outside, which is why it
waits.

**Files that hold it, by path only, node2** (the session's presence
checks of 22 October; node1's copies when it is back):

- `~/.querynz/factory-db.env`: `V3_DSN`, `V3_BACKLOG_DSN`, `V3_REGISTER_DSN`, `EXTRACTIONS_URL`, `INCOMING_NEWS_URL`, `NZBN_CANONICAL_URL`
- `~/.querynz/era3-node2-fleet.env`: `V3_DSN`, `V3_REGISTER_DSN`
- `~/.config/systemd/user/querynz-api.service.d/10-era3-review.conf` and
  `~/.config/systemd/user/querynz-research.service.d/20-era3-cutover.conf`: inline connection strings (the "override files"; the leak search lists any others)
- The old `api.env` and `v3.env` do not hold it on node2 (absent lines, absent file).

**Before the sitting, the session prepares and Arthur reads:**

1. The list above, re-checked on the day (presence, verdicts only).
2. One script that takes the new value **at a prompt, from Arthur's
   keyboard, echo off**, sets the role's password (`ALTER ROLE`), rewrites
   every file above without showing anything, and writes nothing else.
3. The order of restarts: the carve-out last (`querynz-pi-web`, the
   gateway, the model server), the capture timers before it, nothing
   stopped that the public site stands on until the password is in place.
4. The tightened access file (`pg_hba.conf`): each role from where it is
   used only, applied in the same sitting with a reload.

**In the sitting:** run the script; restart in the order; then the proofs.

**The session then proves, verdicts only:**

- Every kept job starts (the board's job list, no failed unit).
- The standby is streaming.
- `ops/pi_release.py --dry-run` is green (the integrator runs it).
- The watcher is green.
- The old password is refused: one connection attempt with the previous
  value, made by the script from memory before it forgets it, prints
  "refused". The session never types either value.

**Inventory line:** the application role row, "Last rotated: <date>,
sitting; access file tightened". The other two roles' pages are done in
the same sitting.
