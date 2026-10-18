A session's fence is the `.scope` of the folder Claude was started in, not the folder its brief names: started in the main checkout, a build session is judged by the integrator's scope and every write to its own working copy is refused, so check the first write's verdict before building anything.
area: fences, sessions, launcher, hooks
paid-for-by: 2026-10-18, windowed session (track E)

The windowed brief said "run every command from inside the working copy",
but Claude's project folder was `/home/user/querynzv4`. The scope hook reads
`CLAUDE_PROJECT_DIR/.scope`, so it saw `founding-f05585e`, treated
`/home/user/querynzv4-work/windowed` as outside the repository, and allowed
writes only under `scratch/founding-f05585e`. `cd` does not change it. A
clone into scratch to commit from was refused by the auto-mode classifier as
a way round the fence, which is right: the fix is to start the session in
the right folder, not to route around the hook.

What to do: a brief's first step writes one line to its own status file and
reads the verdict. Refused means stop building and say so; the work done
anyway goes to scratch at repository paths so the next session can copy it in.
