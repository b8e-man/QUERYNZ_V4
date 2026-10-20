# The companies monitor's job, profile and position go in at the merge
kind: blocker
state: open
use-case: 5
session: companies-2
opened: 2026-10-21

Three edits outside the companies fence, for the integrator at the merge of
`companies-2`:

1. Append `registers/companies/profile-proposed.jsonl` (profile
   `nzbn-entity-detail-any-kind` v1) to `support/profiles/profiles.jsonl` and
   delete the proposed file.
2. Widen `docs/legal/positions/nzbn-register-entities.md` (it says "incorporated
   societies ... this path only") to every entity kind a product asks about or
   watches: companies, sole traders, partnerships and trading trusts. The four
   answers for that widening are in `docs/status/companies.md`; the host and the
   path are the same, so the gate already permits the call.
3. Add to `support/scheduler/jobs.toml` and run `python -m support.scheduler check`:

```toml
# ── step 5.5, company monitoring (the NZBN register's entity detail, one entity at a time) ──
# Waiting requests first, then due watches; one gated call each, at least 5 s
# apart, at most 300 a New Zealand day (the interface states no limit; ours).
# Off-peak 22:00 to 01:00 NZ time, before qv4-societies-capture asks the same
# host at 01:00, never Wednesday 21:00 to 23:00 (maintenance). A 403, 429,
# 5xx or challenge stops the night (exit 1).
[jobs.qv4-companies-monitor]
description = "Step 5.5: company monitoring. Each product request, then each due watch, checked against the NZBN register's entity detail through the fetch gate with our own key; the answer landed by hash and every difference stored as a dated change. Nightly at 23:30 NZDT, at most 25 minutes."
needs = "processor"
memory_gb = 0.3
deadline_s = 2400
query_timeout_s = 60
class = "due"
priority = 36
command = ["python", "-m", "registers.companies.monitor", "--night", "--budget-s", "1500"]
at_utc = "10:30"
nice = 10
```

The clock is NZDT (UTC+13) until 5 April 2027; move it with the founding
jobs. The job needs the lane's monitor tables, which the next publish of the
companies lane creates (`tables.sql`, `IF NOT EXISTS`; the queue and the
ledger survive every later load). `memory_gb` is a first figure, not yet
measured from a run record. The checks board's `python -m
registers.companies.check` now carries the monitor's three checks too.
