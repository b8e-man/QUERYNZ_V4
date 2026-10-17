A merge-gate step that looks for a file on disk sees the main checkout, not the branch: the staging load found no `load.py` and would have merged the first lane with nothing loaded. Run every gate step inside the gate's own worktree.
area: merge gate, staging, full tier, founding
paid-for-by: 2026-10-18, founding session, 1.11 (fixed in bin/merge-gate before the first lane merged)

`support.staging.touched_modules` tests `os.path.isfile(repo/module/load.py)`.
Called from the main checkout on `main` it is always false for a new lane.
The silent form of the failure is the expensive one (lesson: checks that
silently pass): the gate printed a reassuring line and merged. The test
that caught it was running the step by hand before trusting the gate.
