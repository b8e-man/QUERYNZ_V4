# The next sessions to start

Kept current by the integrator (by the founding session during step 1).
Arthur starts sessions from here. `bin/start-session` prints the section
headed with the session's name as the brief.

## ask

A question session (step 1b's proof). On node2, in `/home/user/querynzv4`:
`bin/ask`. Change into the folder it prints, start Claude there in the mode
that accepts file edits without asking, and ask it anything about the
estate. There is no brief. Its two lines land in
`/home/user/querynzv4-work/times/session-times.jsonl`.

## scheduler

Step 2, the scheduler's first build. Several sessions, one at a time, each
under this name, continuing from `docs/status/scheduler.md`. Model: Fable.

Launcher, on node2 in `/home/user/querynzv4`:
`bin/start-session scheduler support/scheduler support/installer support/profiles`

Then start Claude (Fable) in the folder it prints and paste:

```text
You are a build session for QueryNZV4, running as Fable on node2, in
the working copy the launcher made for you. Read docs/PLAN.md, then
docs/plan/step-2.md, docs/status.md and your own status file
docs/status/scheduler.md, and continue where it stops. Do step 2: the
scheduler's first build. Extend the old fleet service (ops/fleet in
the reference copy /home/user/qnz3-ref, at the frozen tag) rather than
starting again; carry its tests first. The job contract is
docs/contracts/job.md and support/jobspec and support/jobrun already
hold step 1's half of it; build on them. Search the lessons for
scheduling, memory and model serving before you write anything.
node1 is out of the plan (ruling 55): the estate is node2 alone until
a second box exists, so prove the two-box items with a second worker
on node2 under its own name, as the decision queue's default says
(docs/decisions/queue/step-2-on-one-box.md). Card 0 on node2 is the
carve-out's (querynz-agent-llm on :8020 and querynz-vision-ocr on
:8032): a fixed reservation, never touched. Card 1 is free. Never
touch the frozen product's servers or the cards they hold; every job
you install carries the prefix qv4-. A timer is not a blocker (ruling
56): fire the unit by hand and record it. Push your branch and raise
a merge request for each finished piece. Update your status file at
every close. Finish by telling Arthur what closed, what is carded,
what waits on him, and whether step 2 is finished.
```

## integrator

From the close of step 1 one Fable session owns the main line, started
fresh for each batch of merge requests. Launcher, on node2 in
`/home/user/querynzv4`: `bin/start-session --main integrator`

Then start Claude (Fable) there and paste:

```text
You are the integrator for QueryNZV4, running as Fable on node2 in
/home/user/querynzv4. Read docs/PLAN.md, docs/plan/core.md and
docs/status.md, then the requests waiting in
/home/user/querynzv4-work/inbox/merge-requests/. For each: run
bin/merge-gate on its branch, merge with --no-ff or refuse, write the
result into the request file and commit a copy under docs/merges/.
Rebuild the generated files (bin/board, bin/lessons-index,
bin/decisions), roll the session status files into docs/status.md
(under 3 KB) and the queue files into docs/decisions/queue.md, file
any inbox cards, and keep docs/briefs/next.md current. Obey the hard
limits; never touch the old estate. Finish by telling Arthur what
merged, what was refused and why, and what waits on him.
```

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
1.11 is done; 1.4's negative half is done: the three batches are
stopped on node2 and the 16:17 release of 18 October, the first with
every batch off, ran green inside the yardstick (docs/baseline.md).
querynz-pi-web is in the carve-out. 1.5 is done: both freeze commits
and the tag v3-frozen-2026-10-18 are in. Step 1 is closed bar the
positive half of 1.4, which waits for a new declaration; read
docs/PLAN.md for what follows step 1 and ask Arthur before starting it.
Work alone. The only changes you may make to the old estate are
stopping old jobs outside the carve-out, with proof (1.4), and the
freeze commits (1.5), and never in a session that started without
the hooks. Never touch a job in the carve-out. Obey the hard limits.
Put questions for Arthur in the decision queue with a default and
keep working. Update docs/status.md at every close. Finish by telling
Arthur in plain words what closed, what is carded, what waits on him,
and whether step 1 is finished or needs another session.
```
