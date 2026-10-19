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

Closed. Step 3 halted under ruling 60 and merged as `trial-3` (7608be8):
GLM-OCR Q8_0 under "OCR" is the page reader alone; no second reader
(`cards/no-second-reader-qualifies-under-the-trial-s-rules`). The trial
resumes after the plan: TeleOCR's patched server, the prompt variant, the
rows pass, the 111-page repeat, two scheduler proofs
(`docs/trials/page-readers.md`). Nothing to start.

## scheduler-fix

A fix session on `support/scheduler` for three cards the trial raised:
`the-lease-lapses-while-a-large-model-loads` (renew the claim's lease
while a card loads a profile), `the-card-manager-loads-a-profile-for-a-
job-no-box-can-claim` (rule 6 must not load a profile for a row no worker
is eligible for), and `teleocr-needs-a-patched-server-the-scheduler-cannot-
choose` (a server binary named per profile; `<live>/llama/built-teleocr/`).
About twenty lines each, with a test that fails without the change. On
node2: `cd /home/user/querynzv4 && bin/fix support/scheduler`, then start
Claude as Fable in the folder it prints and paste its brief, adding:
"Work the three cards named under `## scheduler-fix` in
docs/briefs/next.md, one commit each; the worker is live, so restart
`qv4-worker@node2` only after the merge, from the main checkout."

## disclosures

Step 4.1, the first lane: large-donation disclosures (over $20,000), the
one feed the frozen site still depends on. Model: Opus. Builds in
`registers/disclosures/` from the files the old estate already holds
under `var/staging/` by hash, read-only; fetches nothing (the old
`ec-disclosures` job stays the only fetcher until the switch). Read
`docs/plan/reference/facts-and-traps/electoral-commission-forms.md` before
a line of code; the Commission states which declaration an amendment
replaces, never infer it. The reader is GLM-OCR through the profiles
(ruling 60). On node2: `cd /home/user/querynzv4 && bin/start-session
disclosures registers/disclosures`, then start Claude as Opus in the
folder it prints and paste the lane brief from `docs/plan/step-4.md`
with `<lane>` = disclosures.

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

Track E is built and merged (`windowed-1`, `-2`, `-3`); the nightly capture
takes the rest on the queue's clock. Session 2 has nothing more carded.
The line for its window: "Arthur: windowed-3 is merged (ae1481b). Nothing
more is carded for track E. Update your status file, push, and stop."
The open fetch-gate card (redirect to another host, gzip) is a fix
session on `support/fetchgate` when wanted, not this session's.

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
