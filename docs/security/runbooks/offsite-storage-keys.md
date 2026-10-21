# The off-site storage keys (push and read)

**Why:** both reach outside storage. The push key can write and overwrite
the nightly copies; the read key can fetch every backup (still sealed by
the passphrase, see `offsite-backup-passphrase.md`).

**Where:** the AWS console → IAM → Users → `querynz-offsite-push` →
Security credentials → Create access key. Then the same for
`querynz-offsite-read`. After the proofs, **deactivate, then delete, the
old access key of each user.**

**Permissions:** the users keep their existing inline policies; nothing
is granted, a key is replaced. Push: put-only on the bucket's `push/`
prefix with the object lock as now. Read: list, get, versioning and
lifecycle read only.

**File and variable, node2:**

- `~/.querynz/offsite.env`: the lines `OFFSITE_KEY_ID=` and `OFFSITE_SECRET=`.
- `~/.querynz/offsite-read.env`: the lines `OFFSITE_READ_ACCESS_KEY_ID=` and `OFFSITE_READ_SECRET_ACCESS_KEY=`.

Copy each pair from the console's one-time view straight into the file.

**Timing:** clear of the nightly copies (the old `offsite-push.timer` and
the new `qv4-offsite-dump` on the scheduler's clock, both in the small
hours).

**Tell the session:** "rotated".

**The session then proves, verdicts only, on node2:**

1. Push: from `/home/user/qnz3-ref`, `ops/offsite_push.py --dry-run` lists
   the bucket and plans the upload; then the next nightly copy succeeds
   (the checks board's offsite line, and the old estate's run record).
2. Read: in `/home/user/querynzv4`, `python -m support.offsite restore
   --databases querynz_v4_sample` fetches one object with the new read key.
3. The old keys are refused: the console shows them deleted; the session
   never held them.

**Inventory line:** the two off-site key rows, "Last rotated: <date>".
