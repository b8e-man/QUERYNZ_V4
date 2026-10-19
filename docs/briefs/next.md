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

Step 2 is closed on one box (sessions 1 and 2 merged: `docs/merges/`). What
is left waits on node1 (`cards/node1-setup-as-the-second-box.md`, ruling
57). No scheduler session is owed until node1 is powered.

## trial

Step 3 halts under ruling 60 (19 October): Arthur prefers the trial to
stop with the results in hand and resume once the plan is complete. The
unfinished pass-two rows are cancelled; the stored readings keep every
page read. Session 2 is running in its working copy; this is the line for
its window, not a new start:

```text
Arthur: ruling 60. Halt the trial with the results you have (rows 66 to 69
and 74 are cancelled; what was read is kept). Close step 3 now: score what
pass two read, choose GLM-OCR as the primary reader and the second reader
from the partial scores or card it as open, write both into the profiles,
write docs/trials/page-readers.md with what ran and what did not, file the
lessons, update your status file, push and raise trial-3. Then stop.
```

If the session has to be started afresh instead, on node2:
`cd /home/user/querynzv4-work/trial && git fetch origin && git merge origin/main && claude --model fable --permission-mode acceptEdits`
and paste the same text with "You are the trial session, session 3, in
your working copy. Read docs/PLAN.md, docs/plan/step-3.md, docs/status.md
and docs/status/trial.md first." in front of it.

## offsite

Track B, the off-site copy. Model: Opus, reviewed by the integrator.
Session 1 (18-19 October, an agent of the founding session) wrote nothing:
it was fenced as the main checkout (`docs/merges/offsite-1-not-started.md`).
Its read-only measurements, for session 2: nothing writes the press graph
(`extractions`, 276 GB; counters equal 21:24 to 06:59); the old push ran
19 October 01:39, green, 83 minutes at 3.5 MB/s, after the writers stopped,
so that run is a valid last full copy (the bucket keeps 45 days);
`querynz_v4` is small; `/mnt/hdd2/qv4-docs` 641 MB; `nzbn_canonical`
27.5 GB of which about 12 GB is public reference data that can be fetched
again; `incoming_news` 67 GB, its 38 GB vectors stay out with a second
local copy; `extractions`' 120 GB `candidates.*` can be rebuilt, the rest
cannot; old `var/staging` 27 GB. Its design: one piece per database (table
by table) and per file tree; a full copy weekly, nightly only tables whose
write counters moved and files whose size, time or checksum changed; the
press graph frozen with a fresh full copy every 28 days; checksum and row
count per table and file, checked exactly after a restore into a scratch
server on `/mnt/hdd2`; run before 01:38 so it never shares the link with
the old push. Three of its decisions are in the queue with defaults.
The working copy exists; start session 2 in it, on node2:
`cd /home/user/querynzv4-work/offsite && git pull && claude --model opus --permission-mode acceptEdits`

```text
You are a build session for QueryNZV4, running as Opus on node2, in
your working copy /home/user/querynzv4-work/offsite (session 2). Read
docs/PLAN.md, then docs/plan/tracks.md and docs/plan/track-b.md,
docs/status.md, your own status file docs/status/offsite.md, and the
## offsite section of docs/briefs/next.md, which holds session 1's
measurements and design; continue from them.
Do track B: the off-site copy, in support/offsite (step 1.8's nightly
dump of querynz_v4 is there already; its job qv4-offsite-dump runs on
the scheduler's clock, support/scheduler/jobs.toml). Build the new
copy as qv4- jobs beside the old nightly job, which keeps running
untouched: changes nightly with a weekly full checkpoint (ruling 21);
sorted by the delete rule (what cannot be regenerated first and
always; what can be regenerated stays out unless rebuilding costs more
than storing); the press graph stays in until its last writers are
proven stopped (they are stopped since 18 October; take one last full
copy then, and card the removal for Arthur). Rehearse a restore to
equality on /mnt/hdd2 and record the time. Credentials are read from
the old estate's off-site credential file at the moment of use and
never printed (hard limit 1); never read the credential folder. Never
touch the old estate's jobs, folders or databases; the old nightly job
is retired only on Arthur's word after the election. A timer is not a
blocker (ruling 56). Push your branch and raise a merge request for
each finished piece. Update your status file at every close. Finish by
telling Arthur what closed, what is carded, what waits on him, and
whether track B is finished.
```

## windowed

Track E, the windowed sources. Model: Opus. Session 1 (18 October, an
agent of the founding session) built both legal positions and both lanes
but could not write to its working copy: it was fenced as the main
checkout. Its tree sits at repository paths in
`/home/user/querynzv4-work/scratch/founding-f05585e/windowed/tree/`, and
the documents leaving the sources soonest are held by hash in
`.../windowed/held/` (`docs/merges/windowed-1-not-yet.md`). The working
copy exists; start session 2 in it, on node2:
`cd /home/user/querynzv4-work/windowed && git pull && claude --model opus --permission-mode acceptEdits`

```text
You are a build session for QueryNZV4, running as Opus on node2, in
your working copy /home/user/querynzv4-work/windowed (session 2). First:
copy session 1's tree from
/home/user/querynzv4-work/scratch/founding-f05585e/windowed/tree/ into
this working copy at the same paths, read it, run bin/fast, commit,
push, and rewrite merge-requests/windowed-1.md as a request on a real
branch. Then land what is held in .../windowed/held/ through the
landing wrapper. Then read docs/PLAN.md, docs/plan/tracks.md,
docs/plan/track-e.md, docs/contracts/lane.md, docs/status.md and
docs/status/windowed.md and continue. Track E: capture the Tenancy Tribunal's
and the Real Estate Authority's published decisions now and hold
them; the reading comes in step 5. Two lanes, registers/tenancy_tribunal
and registers/real_estate_authority (their folders, schemas and five-line
specs exist; registers/party_returns is the model lane). First, for
each class of source, write its one-page legal position in
docs/legal/positions/<class>.md from the four questions (hard limits
4 and 9; the README there gives the shape, and the fetch gate refuses
a host no position names). Then capture through support/fetchgate and
the landing wrapper only: politely, slow, low concurrency, off-peak,
cached; honour a stated crawl delay; never solve a challenge or get
around a block (a challenged read is a failed read, logged). Store
each document by its sha256 and never print a person's home address
or a suppressed name into the session, a card or a log. Capture jobs
carry the qv4- prefix and go on the scheduler's clock
(support/scheduler/jobs.toml is the catalogue; card the catalogue
line for the integrator, it is outside your fence). A timer is not a
blocker (ruling 56). Push your branch and raise a merge request for
each finished piece. Update your status file at every close. Finish
by telling Arthur what closed, how many decisions are held per
source, what is carded, what waits on him, and whether track E is
finished.
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
