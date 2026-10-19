# offsite-2a: the off-site copy and its restore rehearsal (track B)
branch: session/offsite (pushed; 3fd04c4)
session: offsite (session 2)
raised: 2026-10-19
claims: support/offsite/{pieces,copy,restore}.py, spec.md, tests/test_copy.py, the `copy`/`plan`/`restore` commands; card `the-press-graph-leaves-the-old-nightly-push`; lesson `an-empty-selection-is-not-no-selection`; the catalogue patch `offsite-2a-catalogue.patch`

1. **What is copied (`pieces.py`).** Every table of `querynz_v4`,
   `nzbn_canonical`, `incoming_news`, `extractions`, and nine file trees (the
   new document store, `live/` without the model server build, the inbox, the
   old `var/staging` (EC archive and residue included, queue default),
   `var/audits`, `var/eras`, `var/review`, `ops/systemd`). Copied unless a
   rule names its rebuild and the rebuild is on disk: OUT the candidate
   register (120 GB), the extract queue, four public reference tables
   (wikidata labels and attributes, geonames twice); LOCAL (second disk,
   never sent) the article vectors. A table added later is copied.
2. **How (`copy.py`).** One piece per table: its `COPY ... TO STDOUT` text in
   one repeatable-read transaction per database, sha256 and rows taken on the
   way, zstd, gpg (passphrase on a pipe). Old databases through the read-only
   old login. Nightly only what moved (write counters and file node, read
   before the snapshot; a restarted counter recopies the database); full on
   Sunday; the press graph frozen (sent when it moves or every 28 days,
   inside the bucket's 45). Every run's manifest is complete, so a restore
   needs only the newest; a killed run resumes and sends nothing twice. Kept
   on `/mnt/hdd2/qv4-offsite` too. Bucket prefix `qv4/`.
3. **Restore (`restore.py`).** Newest copy from the bucket (read-only key) or
   the local copy, into our own scratch server (socket only, port 5434) on
   `/mnt/hdd2/qv4-restore`: schema before data, rows, sequences (from the
   recorded value, else the owned column's maximum: the old read login cannot
   read sequences), schema after data, trees. Equality is exact: each table
   read back gives the manifest's sha256 and rows; each file its sha256.
   Removed after unless `--keep`.
4. **Catalogue (patch, outside my fence).** `qv4-offsite-copy` replaces
   `qv4-offsite-dump` at priority 14, 08:00 UTC (21:00 NZDT), deadline 4.5 h
   so it ends before the old push at 01:38; `qv4-offsite-rehearsal` every 28
   days, priority 15. `registry.problems()` on the patched catalogue: [].
   Apply: `patch -p1 < offsite-2a-catalogue.patch`. The unit files in
   `support/offsite/jobs/` and the scheduler spec's job list then name the
   retired dump; the dump code stays until you remove it.

Checked: fast tier for support/offsite green (19 tests, no database, no
network); by hand on the real `querynz_v4` and the inbox: a full and a
nightly, the nightly restored equal from objects of two stamps; a tampered
table hash and file hash both reported NOT EQUAL.

Known to fail: nothing. One thing to know: before the fix in this branch a
test passed `databases={}` and copied real registers into pytest's /tmp
folder under the test passphrase (the lesson); Arthur removes them (status
file).

The full copy and the bucket rehearsal follow as offsite-2b.

## Result (integrator, founding session, 19 October 08:25)

Merged into main as fe236e1 (integration branch integrate/offsite-2a from
session/offsite at 3fd04c4, main merged in, gate green). The catalogue
patch was applied with one change: qv4-offsite-dump (step 1.8) is kept
beside the new qv4-offsite-copy (priority 16, since 14 stays the dump's and
15 is the rehearsal's) until offsite-2b restores a copy from the bucket to
equality; then the dump is retired and the unit files and spec renamed.
Scheduler check: 34 job types, green; the worker reloads on its clock, so
the first qv4-offsite-copy run is tonight at 21:00 NZDT. The 34 GB of test
copies in /tmp/pytest-of-user (a memory file system, 55 % full) are still
there: the safety hook refuses a recursive delete to the integrator too;
Arthur removes them (status file).
