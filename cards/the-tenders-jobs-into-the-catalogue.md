# The award notices' two jobs go into the job catalogue, and the lane's position and profiles move
kind: blocker
state: closed
use-case: 10 tender and award intelligence
session: tenders-1
opened: 2026-10-21
closed: 2026-10-21

Outside the tenders-1 fence. At the merge of `tenders-1` the integrator:

1. Moves `registers/tenders/position/government-procurement-award-notices.md`
   to `docs/legal/positions/`, sets `capture.POSITIONS = None`, and deletes
   the lane's `position/` folder.
2. Appends the six lines of `registers/tenders/profiles-proposed.jsonl` to
   `support/profiles/profiles.jsonl` (each is version 1; none exists there).
3. Floors `catalogue.data.govt.nz` at 10 s in `support/fetchgate.FLOORS`
   (its own crawl delay; the gate already honours it from robots.txt).
4. Adds these entries to `support/scheduler/jobs.toml`, runs
   `python -m support.scheduler check`, then the installer:

```toml
# ── registers/tenders: the GETS award notices (step 6.2, template 1) ─────────
[jobs.qv4-tenders-refresh]
description = "The ministry's GETS award-notice files through the fetch gate, each current file once a quarter. Asks nothing until a set was last acquired 80 days ago, or within a week of a block; off-peak, 10 s apart; stops and goes red at a block (card the-ministry-s-gets-files-answer-403)."
needs = "processor"
memory_gb = 0.2
deadline_s = 1200
query_timeout_s = 60
class = "due"
priority = 30
command = ["python", "-m", "registers.tenders.capture", "--refresh"]
at_utc = "10:00"
nice = 10

[jobs.qv4-tenders-load]
description = "The award notices read from the listed files into staging, checked against the files' own counts, published only on green; nothing when the listing is the one published."
needs = "processor"
memory_gb = 0.5
deadline_s = 1800
query_timeout_s = 600
class = "due"
priority = 34
command = ["python", "-m", "registers.tenders.load", "--job"]
at_utc = "17:30"
nice = 10
```

Closed by the integrator at the merge of `tenders-1` (21 October 2026): the position is `docs/legal/positions/government-procurement-award-notices.md` (the lane's `POSITIONS` set to none); the six profiles are versions 1 in the ledger (92 slugs), the proposed file removed; the gate floors `catalogue.data.govt.nz` at 10 s; `qv4-tenders-refresh` (priority 57, 23:00 NZDT) and `qv4-tenders-load` (58, 06:30) in the catalogue, `support.scheduler check` green; the two award views are catalogued on the board in the merge after this one, once the gate has published them.
