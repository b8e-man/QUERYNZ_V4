# The two track E capture jobs go into the job catalogue
kind: blocker
state: open
use-case: -
session: windowed
opened: 2026-10-18

`support/scheduler/jobs.toml` is outside the windowed fence. After the merge
of `windowed-1`, the integrator adds these two entries (below the founding
jobs) and runs `python -m support.scheduler check`, then the installer:

```toml
# ── track E, the windowed sources (capture and hold; read in step 5) ─────────
# Each night spends at most its budget, five seconds between requests, one at a
# time, and stops at 06:00 NZ time whatever is left (the lane checks off-peak
# itself). memory_gb is a ceiling until the first run record measures it.

[jobs.qv4-tenancy-tribunal-capture]
description = "Track E: the Tenancy Tribunal's published orders (public for three years, then taken down), through the fetch gate, soonest to leave first, each fetched once. Nightly at 22:30 NZDT, at most 4.5 hours."
needs = "processor"
memory_gb = 0.5
deadline_s = 21600
query_timeout_s = 60
class = "due"
priority = 30
command = ["python", "-m", "registers.tenancy_tribunal.capture", "--budget-s", "16200"]
at_utc = "09:30"
nice = 10

[jobs.qv4-real-estate-authority-capture]
description = "Track E: the Real Estate Authority's decisions database (Committee decisions leave after three years), through the fetch gate, the Committee's oldest first, each page fetched once. Nightly at 23:00 NZDT, at most 4 hours."
needs = "processor"
memory_gb = 0.5
deadline_s = 18000
query_timeout_s = 60
class = "due"
priority = 31
command = ["python", "-m", "registers.real_estate_authority.capture", "--budget-s", "14400"]
at_utc = "10:00"
nice = 10
```

The two hosts differ, so the jobs may overlap. At 5 s a request, a night is
about 3,200 requests: the Tribunal's 33,501 listed orders (18 October) take
about eleven nights, the Authority's database three or four. The clocks are
NZDT (UTC+13) until 5 April 2027; move them with the founding jobs.
Also register `python -m registers.tenancy_tribunal.check` and
`python -m registers.real_estate_authority.check` on the checks board.
