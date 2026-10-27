The integrator's hooks refuse `git apply`, a write whose path is built at run time, and any edit in a worktree outside the repository; apply a session's patch with literal paths, one file each, in the main checkout between gates.
area: integrator, hooks, scope fence, safety hook, merging, memory
paid-for-by: 2026-10-27, the integrator's merge stretch (mcp-1 to fix-registers-parliament-1c): seven refusals in one day, each costing a re-run or a re-gate

Rule: when a fix session hands a patch to a file outside its fence, do not
reach for `git apply` (refused even with `--include`), nor a Python helper
that takes the path as a parameter (the scan cannot see where it writes).
Write the hunks with a Python heredoc that names each file's path as a
literal, or take one side of a conflict with `git show <sha>:<path> > <path>`.
Resolve conflicts only in the main checkout and only between gates: a
worktree under `querynzv4-work/` is outside the repository, so every edit
there is refused (the integrator may only remove such copies). Run `rmdir`
and `git rm` as a command on their own; inside `a && rmdir b` the safety
hook reads a recursive delete. `git push --delete`, `git checkout -- file`
and any DROP or TRUNCATE text are refused outright: the first two are not
needed, the last is Arthur's own line in his own terminal.

Outside the repository the scope hook allows the scratch folder, the
inbox's merge-requests, the `qv4-` unit folder, the working copies and,
since ruling 103 (28 October 2026), Claude Code's memory folder for the
checkout a founding or integrator session runs in; nothing else. A fix or
build session has no memory folder the fence allows: what it learns goes
here, as a lesson, where every session's search finds it.

Why: each shape above was tried once on 27 October and refused; the hooks
stay on (hard limit 24), so the cost is only in finding the passing shape,
which this file now gives.
