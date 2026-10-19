# The charities capture job goes into the job catalogue
kind: blocker
state: open
use-case: -
session: charities-capture
opened: 2026-10-20

`support/scheduler/jobs.toml` is outside the charities-capture fence. After
the merge of `charities-capture-1`, the integrator adds this entry and runs
`python -m support.scheduler check`:

```toml
[jobs.qv4-charities-capture]
description = "Step 4.1: the Charities Register's open data feed, verbatim pages of 1,000 by key through the fetch gate; a full copy, then changes by ModifiedOn, a full copy again every 28 days. Nightly at 23:30 NZDT, at most 4 hours."
needs = "processor"
memory_gb = 0.5
deadline_s = 18000
query_timeout_s = 60
class = "due"
priority = 34
command = ["python", "-m", "registers.charities.capture", "--budget-s", "14400"]
at_utc = "10:30"
nice = 10
```

Pick another priority if 34 is held (they must be unique). Its host differs
from the two track E jobs, so they may overlap. The first full copy is about
1,170 requests at about 6 s each: about two hours, one night. Afterwards a
night is a few dozen requests. The clocks are NZDT (UTC+13) until 5 April 2027.
After the first night, run `python -m registers.charities.capture --measure`
(the held copy against the register's count of registered charities) and put
it on the checks board as the lane's capture check.
