# job-memory: qv4-mcp-pull 1 GB and qv4-beehive-load 3 GB
branch: integrate/job-memory (the integrator's own; no inbox request)
raised: 2026-10-28

## Result (integrator, 28 October 09:30 NZDT)
Merged ae89e90, gate green. The night's first runs of both jobs over the live documents were stopped by the worker at a quarter over their declared memory (the pull at 549 MB against 307; the Beehive load at 1,489 MB against 1,024, after it had wiped its tables, so the Beehive views were empty until 09:05). Both run by hand with the peak measured: the pull 615 MB in 311 s, every corpus level; the Beehive load 2,459 MB in 48 s, 59,381 releases back. Figures set to 1.0 and 3.0 GB with the measurements as comments. Released; the worker restarted.
