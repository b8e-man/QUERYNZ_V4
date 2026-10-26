To build on a board branch still waiting at the gate, cherry-pick its own board commit, not its integration branch: that merge brings conflicts in the integrator's files, which a fix session's fence keeps out.
area: board, fix sessions, merging, integration branches
paid-for-by: 2026-10-27, fix-products-board-2 (the diaries and Parliament views, placed beside the Beehive entries of fix-products-board-1i)

The brief asked for the ministers' diaries "near the Beehive in the
catalogue's order", and the Beehive entries were on
`integrate/fix-products-board-1i`, gated but not on main. Merging that
branch into this one, which carries `integrate/diaries-parliament`,
conflicted in `support/profiles/profiles.jsonl`, its test and
`support/scheduler/jobs.toml`: the integrator's files, which a session
scoped to `products/board/` may not resolve. The board commit itself
(f43b5d1) touched only `products/board/`, `lessons/` and
`docs/status/board.md`, so it cherry-picked cleanly. When the original
lands, the same change merges without conflict, because both sides hold
the same text.

Rule: before merging an unlanded branch into a fix, list the files its
merge would conflict in (`git merge --no-commit`, then `git diff
--name-only --diff-filter=U`, then `git merge --abort`). If any of them
is outside the fence, cherry-pick the one commit that is inside it, and
name that commit in the merge request so the integrator can drop it if
the original lands first.
