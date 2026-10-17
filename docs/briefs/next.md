# The next sessions to start

Kept current by the integrator (by the founding session during step 1).
Arthur starts sessions from here. `bin/start-session` prints the section
headed with the session's name as the brief.

## founding

Launcher, on node2 in `/home/user/querynzv4`: `bin/start-session --main founding`

Then start Claude (Fable) in that folder and paste:

```text
You are a founding session for QueryNZV4, running as Fable on node2,
started in /home/user/querynzv4. If the folder docs/plan/ does not
exist yet, you are the first: read docs/PLAN.md in full, do 1.1, and
stop when 1.1 is merged. Otherwise read docs/PLAN.md, which is now
the index, then the files it names for a build session on step 1,
then docs/status.md, and continue where it stops. Do step 1 only, in
this order: 1.1, 1.2, 1.3, 1.6, the first commit of 1.5, 1.4, the
rest of 1.5, 1.7 to 1.10, step 1b (stop when it is built), then 1.11.
Work alone. The only changes you may make to the old estate are
stopping old jobs outside the carve-out, with proof (1.4), and the
freeze commits (1.5), and never in a session that started without
the hooks. Never touch a job in the carve-out. Obey the hard limits.
Put questions for Arthur in the decision queue with a default and
keep working. Update docs/status.md at every close. Finish by telling
Arthur in plain words what closed, what is carded, what waits on him,
and whether step 1 is finished or needs another session.
```
