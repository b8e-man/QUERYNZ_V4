# The societies capture job, its position and its floor go in at the merge
kind: blocker
state: closed
use-case: -
session: societies
opened: 2026-10-20
closed: 2026-10-20

Three edits outside the societies fence, for the integrator at the merge of
`societies-1`:

1. Move `registers/societies/position/nzbn-register-entities.md` to
   `docs/legal/positions/` (ruling 61: written before product; it names
   `api.business.govt.nz`), then delete the lane's `position/` folder and the
   `POSITIONS` override in `capture.py` (one line: the gate's default folder
   is then right).
2. In `support/fetchgate` `FLOORS`, add `"api.business.govt.nz": 5.0` (the
   position's floor; the lane holds 5 s itself until then).
3. Add to `support/scheduler/jobs.toml` and run `python -m support.scheduler check`:

```toml
# ── step 4.1, incorporated-society officers (the NZBN register's entity detail) ──
# One ask per society, 5 s apart, party societies first, then the stalest
# seventh (about 3,300 a night, about 4.6 hours). The lane checks off-peak
# itself: 01:00 to 06:00 NZ time, never the API's Wednesday 21:00 to 23:00
# maintenance window. A 403, 429, 5xx or challenge stops the night (exit 1).
[jobs.qv4-societies-capture]
description = "Step 4.1: incorporated-society officers, the NZBN API's entity detail, one gated ask per society with our own key, party societies first then the stalest seventh. Nightly at 01:00 NZDT, at most 4h50."
needs = "processor"
memory_gb = 0.5
deadline_s = 18000
query_timeout_s = 60
class = "due"
priority = 34
command = ["python", "-m", "registers.societies.capture", "--night", "--budget-s", "17400"]
at_utc = "12:00"
nice = 10
```

The clock is NZDT (UTC+13) until 5 April 2027; move it with the founding
jobs. The job reads `societies.societies` and `societies.asks`, so it waits
for the lane's first real load. Register `python -m registers.societies.check`
on the checks board. Each night's answers are read by the next
`qv4-societies-load` (the merge gate's load, then a nightly load once a
product asks for it).

Closed at the merge of `societies-1`: the position is `docs/legal/positions/nzbn-register-entities.md` and `POSITIONS` is the gate's default; `api.business.govt.nz` is floored at 5 s; `qv4-societies-capture` is in the catalogue at priority 35 (34 went to the charities capture the same morning), 01:00 NZDT nightly.
