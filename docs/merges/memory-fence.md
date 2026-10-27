# memory-fence: the fence opens Claude Code's memory folder to a founding or integrator session (ruling 103)
branch: integrate/memory-fence (the integrator's own; no inbox request)
raised: 2026-10-28

## Result (integrator, 28 October 07:50 NZDT)
Merged a0410d1, gate green at the first run. `fence.MEMORY` names Claude Code's memory folder for the checkout a session runs in (`~/.claude/projects/<slug>/memory`); `scope.judge` allows a founding or integrator session to write under it and nothing else outside the repository that was not already allowed; a build, fix or question session is unchanged (tests/test_hook_scope.py, one new test). The two hook hunks were applied by Arthur with `git apply` from a patch in the session's scratchpad: the auto-mode classifier refuses a session editing its own hooks, whatever its scope. Ruling 103 recorded; docs/plan/core.md's fence sentence extended; the morning's lesson on the hooks reworded. Released. The first memory written under the new rule: `integrator-hook-traps.md`. The line to make the V3 and V4 memory folders one was withdrawn at 07:55 (ruling 104): V3 is deprecated.
