# gate-scope: the merge gate tests in isolation (ruling 113)
branch: integrate/gate-scope (the integrator's own; no inbox request)
raised: 2026-10-28

## Result (integrator, 28 October 18:45 NZDT)
Merged 8101c63, gate green at the first run (the last full run of the old shape: 27 minutes). `bin/merge-gate` now runs the fast tier for the whole repository, then the slow tests of the modules the branch touches and of their readers (links/, checks/, products/ when a lane's publish.sql, pane.md, tables.sql, spec.md or profiles change), then the staging load; a branch touching support/, bin/, .claude/, the root tests, the plan or the test configuration still runs every slow test. The plan's row for the gate reworded; a toy test in tests/test_launcher_and_gate.py proves the four cases. Released.
