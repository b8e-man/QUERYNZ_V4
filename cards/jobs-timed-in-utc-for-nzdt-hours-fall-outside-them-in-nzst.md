# Jobs timed in UTC for NZDT hours fall outside their own hours when New Zealand returns to NZST
kind: finding
state: open
use-case: none (the scheduler; every lane with a local-hours window)
session: integrator (ruling 140, courts tranche 3)
opened: 2026-11-03

`at_utc` is a fixed UTC time, and 51 clock-timed jobs in `support/scheduler/jobs.toml` describe their time in NZDT
(UTC+13). When New Zealand returns to NZST (UTC+12) on the first Sunday of April 2027 (4 April), each fires an hour
earlier by the local clock. For most that is only an hour's shift. For the jobs whose own code refuses to fetch outside
a local window (`off_peak` in the lane's capture), the earlier start lands outside the window, and the run stops at once
with "outside the hours" every night until `at_utc` moves.

Measured 3 November 2026 by evaluating each lane's own `off_peak` at its job's `at_utc` plus a minute on a Thursday in
NZDT (5 November 2026) and in NZST (3 June 2027): inside the window in NZDT, outside it in NZST, so the run does nothing:

- `qv4-insolvency-removals` (08:00; window 21:00 to 22:00) and the capture it queues
- `qv4-courts-jdo-capture` and `qv4-courts-era-capture` (09:00; window 22:00 to 06:00)
- `qv4-companies-history` (its 09:05 firing)
- `qv4-building-practitioners-register-capture` (09:05)
- `qv4-commerce-commission-capture` (09:30)
- `qv4-iwi-directory-capture` (09:30)
- `qv4-grants-capture` (09:45)
- `qv4-contract-disclosures-refresh` (09:40)
- `qv4-council-minutes-capture` (09:15)
- `qv4-council-procurement-watch` (09:50; switched off by ruling 136)
- `qv4-local-elections-listings` (09:10) and `qv4-local-elections-files` (09:20)

Not evaluated this way: the gates that take a local time and a configured window (charities, LINZ, tenders, the Real
Estate Authority, the tenancy tribunal, the old OpenLaw lane); their start against their window is to be checked the
same way. The other clock-timed jobs (loads, checks, the full tier, the offsite copy) shift an hour and keep running.

What closes it: the scheduler takes a local time for a job (`at_local` with the zone, as `[night_window]` already does
in `night.py`), and the jobs above move to it; or, the narrow form, each `at_utc` above moves an hour later on 4 April
2027 and back on the last Sunday of September. A test fails when a job's start, in either offset, falls outside its
lane's own `off_peak`.
