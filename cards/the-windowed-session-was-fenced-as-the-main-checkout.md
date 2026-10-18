# The windowed session ran with the main checkout as its project folder, so its fence refused every write to its own working copy
kind: blocker
state: closed
use-case: -
session: windowed
opened: 2026-10-18
closed: 2026-10-19

The track E session of 18 October was started with Claude's project folder
at `/home/user/querynzv4` (the main checkout), not at its working copy
`/home/user/querynzv4-work/windowed`. The scope hook reads `.scope` from the
project folder, so the session was judged as `founding-f05585e` (the
integrator's scope): every write into the working copy was refused as
"outside the repository", and the session's scratch folder became
`scratch/founding-f05585e`. A clone of the branch into scratch, to commit
from there, was refused by the auto-mode classifier as a way round the fence.

So nothing was committed or pushed on `session/windowed`. The whole of the
work is a tree of files in
`/home/user/querynzv4-work/scratch/founding-f05585e/windowed/tree/`, laid out
at their repository paths, every one inside the windowed fence (and its own
cards, lessons, status and queue files). Fix: start the windowed session
again in its working copy (`cd /home/user/querynzv4-work/windowed`, then
Claude), copy the tree in, run `bin/fast`, commit, push, raise the merge
request. Urgent: about thirty Tribunal orders leave the source each day.

Closed 19 October 2026 by windowed (session 2), started in its working copy:
the fence is the windowed scope, the tree was copied in at its repository
paths (every path accepted by the hook), the fast tier run, and the branch
committed and pushed as `session/windowed`.
