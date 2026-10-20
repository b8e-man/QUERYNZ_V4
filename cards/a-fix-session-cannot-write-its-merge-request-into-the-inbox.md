# A fix session cannot write its merge request into the inbox
kind: finding
state: open
use-case: 0
session: founding
opened: 2026-10-20

`bin/fix products/board` made the copy `fix-products-board-1` with the
inbox linked at `merge-requests/`, as `bin/start-session` does, but the
scope hook refused the session's write of
`merge-requests/fix-products-board-1.md`: a fix weight's fence is its one
module and the hook does not except the inbox link for it, where it does
for a build copy. The session pushed `fix/products-board-1` and handed its
request text to Arthur in chat instead; the integrator wrote the inbox
file from the session's log. Fix, in the hooks (`.claude/hooks/scope.py`)
or `bin/fix`: a fix copy's inbox link is writable like a build copy's,
with a test in `bin/` that a fix weight may write one file there and
nothing else outside its module.
