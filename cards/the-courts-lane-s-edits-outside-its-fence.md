# The courts lane's research note, profiles, position, schema and job go in at the merge
kind: blocker
state: open
use-case: 2
session: courts-1
opened: 2026-10-21

Six edits outside the courts fence (`registers/courts/` only: the launcher's
scope file did not carry `docs/research/legal-documents.md`, which the brief
names), for the integrator at the merge of `courts-1`:

1. Move `registers/courts/research-legal-documents.md` to
   `docs/research/legal-documents.md`, unchanged but for its second paragraph
   (which says it is in the lane folder). The brief's one file outside the
   folder; the fence refused it.
2. Append `registers/courts/profile-proposed.jsonl` (five profiles, version
   1: `courts-nzsc-judgment`, `courts-nzca-judgment`,
   `courts-nzhc-civil-judgment`, `courts-nzhc-criminal-judgment`,
   `waitangi-tribunal-report`) to `support/profiles/profiles.jsonl`, then
   remove the proposed file. `read.profile_version` reads the ledger first.
3. Move `registers/courts/legal-position-court-judgments.md` to
   `docs/legal/positions/court-judgments.md` (ruling 61). Until then the
   fetch gate refuses courtsofnz.govt.nz and the capture job stops at once.
4. Add `"courts"` to `support.db.LANES`, so `apply` makes `courts` and
   `courts_private` in both databases with the grants: the session reader on
   `courts`, never on `courts_private` (it holds withheld names, hard limits
   11 and 16). The load creates the two schemas if they are missing, without
   the grants.
5. Add the job to `support/scheduler/jobs.toml`, run
   `python -m support.scheduler check` and the installer:

```toml
[jobs.qv4-courts-capture]
description = "Step 5.4: each senior court's RSS feed on courtsofnz.govt.nz, the case pages it links and the judgment PDFs not held, plus the listed judgments whose old file is gone; through the fetch gate, five seconds apart, each fetched once. Daily at 03:30 NZDT, at most an hour."
needs = "processor"
memory_gb = 0.5
deadline_s = 4500
query_timeout_s = 60
class = "due"
priority = 34
command = ["python", "-m", "registers.courts.capture", "--budget-s", "3600"]
at_utc = "14:30"
nice = 10
```

6. Register `python -m registers.courts.check` on the board as the lane's
   outside check (pane: `registers/courts/pane.md`).
