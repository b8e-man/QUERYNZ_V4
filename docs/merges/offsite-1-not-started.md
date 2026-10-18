# offsite-1: track B did not start; the session could not write its own working copy
branch: session/offsite (unchanged at c140f97; nothing to merge)
session: offsite (track B, Opus, 18-19 October night)
raised: 2026-10-19
claims: nothing

Nothing to merge. The session was launched with its project folder set to the
main checkout (/home/user/querynzv4), so the scope hook read the main
checkout's scope file (founding-f05585e, whole repository) instead of
/home/user/querynzv4-work/offsite/.scope. Two results:

1. Every write into the working copy (support/offsite/, cards/, lessons/,
   docs/status/, docs/decisions/queue/) was refused as "outside the
   repository", and the brief's scratch folder
   (/home/user/querynzv4-work/scratch/offsite) was refused too.
2. The opposite hole: writes into the main checkout would have been
   allowed under the founding scope. None were made.

A clone of the branch into the harness scratch folder, to work there and
push, was refused by the permission classifier as data exfiltration, and
so was a size listing of the old estate's var/ folders. The session
stopped rather than work around either refusal.

What the integrator must do: restart track B with Claude started inside
/home/user/querynzv4-work/offsite (so CLAUDE_PROJECT_DIR is the working
copy), and card the hook's fallback: when the event's cwd is a working copy
with its own .scope, the hook should judge by that file, not by the
project folder's. The measurements and the design this session made
(read-only) are in its end-of-session report to Arthur.

Known to fail: nothing new; no file changed.

## Result (integrator, founding session, 19 October 07:10)

Nothing to merge; recorded. The session's read-only measurements and its
design are kept in `docs/briefs/next.md` (## offsite) so session 2 starts
from them, and its three decisions are in the queue with defaults:
`whether-the-press-graph-leaves-the-old-nightly-push`,
`whether-the-ec-archive-and-residue-join-the-weekly-full-copy`,
`whether-the-papers-past-dump-stays-local-only`. The hook question is
`whether-the-scope-hook-reads-a-working-copys-own-scope-file` (default no).
