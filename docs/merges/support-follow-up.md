# support-follow-up: the gate marks itself, and three job lines
branch: integrate/support-follow-up (the integrator's own; no inbox request)
session: integrator-9d788fb (Fable, node2)
raised: 2026-10-30
claims: bin/merge-gate, tests/test_launcher_and_gate.py, support/scheduler/jobs.toml

- `bin/merge-gate` sets `QV4_INTEGRATOR=1` for its own runs when the checkout running it carries an integrator or founding
  scope (`bin/_session.read_scope`), so support.db's live guard and the scan product's live test run as the integrator
  whoever typed the command; a build copy's gate sets nothing. With a test. Cause: a support merge refused after 27
  minutes on 30 October for want of the mark (flash-next-1).
- `jobs.toml`: `qv4-candidate-returns-load` nightly at 02:40 NZDT (13:40 UTC), class due, 1 GB, before the site build
  (candidate-returns-3's proposed job); `memory_reserve_gb` 24 → 40 (Flash-Next's host pool holds 31 GB, ruling 121);
  `qv4-mcp-rewalk` memory 0.3 → 1.0 GB (killed at 622 MB on 29 October: the walk holds every corpus's page list).

## Result

Merged 30 October 2026, 09:58, as 4f88eec (gate green, marked, every slow test since the branch touches bin/ and support/;
nothing to load). A first gate of this branch at 08:55 was lost with the integrator session that ran it, after its fast tier
had passed; the gate's worktree was left behind and the second run replaced it. Released after the push; the installer owed no
worker restart (the worker reads the catalogue each cycle since fix-support-scheduler-1).
