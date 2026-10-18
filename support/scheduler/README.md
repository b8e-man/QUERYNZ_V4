# support/scheduler — the scheduler (plan step 2)

The one service that places every job on a graphics card or on the
processor. `python -m support.scheduler` is the command line (`check`,
`tables`, `status`, `enqueue`, `probe`, `worker`, `report`, `rereads`).
The module docstring in `__init__.py` names the pieces; `spec.md` is the
five-line spec; `jobs.toml` is the job catalogue and `profiles.toml` the
four model profiles of step 2.15. Extended from the old fleet service
(`ops/fleet` at `v3-frozen-2026-10-18`); its tests were carried first.
