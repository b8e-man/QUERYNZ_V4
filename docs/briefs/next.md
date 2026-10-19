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

Sessions 1 and 2 merged (`docs/merges/disclosures-1`, `-2`): 520
declarations from the Commission's table, 2023-on total equal to the
cent, 15 of 16 party-years equal (National 2023 is the old estate's
double count, queued for Arthur); the 246 scans read; form check 223
equal, 3 differ (carded: a handwritten total, a struck-out total, a link
to the wrong month's scan, all the Commission's to say), 50 no total read.
The read job reads on the worker's card. No session 3 now: the lane's
next items (`docs/status/disclosures.md`) wait on the cards and on
Arthur's word for the feed (step 4.8).

## party-returns

Session 2 merged (`docs/merges/party-returns-2`): Part A donors on 22
returns (476 rows), loans on 6, 14 returns replaced by amendments; 99
rows, 49 party-years equal, 0 differing. `qv4-read-pages` (new, the
scheduler's) read the 41 unread returns' image pages (queue rows 110 and
111, done 20 October); the gate's reload at offsite-2b published 137
rows, 15 set aside. Session 3, when Arthur wants it: the lane's own next
items (`docs/status/party-returns.md`): re-measure against the frozen
site; the sample label `no stored page reading` now tests from an empty
store (`tests/test_pixels.py`, integrator); Part A's refused
pages (column-by-column, page breaks, schedules outside the heading); the
outside check against the Commission's by-year table. On node2:
`cd /home/user/querynzv4-work/party-returns && git checkout -- docs/board.md docs/decisions/queue.md lessons/INDEX.md && git fetch origin && git merge --ff-only origin/main && claude --model opus --permission-mode acceptEdits`

```text
You are the party-returns session, session 3, in your working copy. Read
docs/PLAN.md, docs/plan/step-4.md, docs/status.md and
docs/status/party-returns.md. Queue rows 110 and 111 (qv4-read-pages)
have read every image page of the 41 returns set aside at stage read,
and the live load holds 137 rows. Re-measure the frozen-site comparison
and update the status file, then do your status file's next two items: Part A's refused pages, and the outside
check against the Commission's by-year table. Edit nothing outside your
folder, push and raise party-returns-3. Finish by telling Arthur what
closed and what is carded.
```

## parties

Session 1 merged (`docs/merges/parties-1`): 78 registrations from the
Commission's page and 136 Gazette notices (exported once from the old
estate's text), 149 names with windows, every stated rename read, 17 on
the register, 6 off it with no cancellation held (carded). No session 2
now: the lane takes the Gazette lane's notices when that lane exists.
Its blocker is a fix on `keys` (next section).

## keys-fix

Card `keys-parties-should-read-the-party-names-the-lane-publishes`:
`keys.parties` holds an 18 October snapshot of 17 parties, so returns and
declarations by a renamed or deregistered party resolve to nothing. The
parties lane publishes `pub.party_names` with windows; 31 of 34 and 46 of
53 unresolved labels resolve by name and filing year alone. A fix
session, Opus, does not count against the three. On node2:
`cd /home/user/querynzv4 && bin/fix keys`, then `cd` into the folder it
prints and `claude --model opus --permission-mode acceptEdits`.

```text
You are a fix session on keys, in your working copy. Read CLAUDE.md,
docs/PLAN.md, docs/plan/core.md, keys/README.md and the card
keys-parties-should-read-the-party-names-the-lane-publishes. Give
keys.parties a party_name(label, on=date) that resolves a label against
pub.party_names by name key and the registration's window, returning the
registration's key and the basis; keep every rule it has (a fuzzy match
never joins two parties). Measure on the unresolved labels the card
counts. Edit nothing outside keys/, push and raise fix-keys-1. Then stop.
```

## offsite

Track B closed (`docs/merges/offsite-2a`, `-2b`): `qv4-offsite-copy`
nightly 21:00 NZDT, tables over 1 GB as ranges, an order-free restore
check, a copy restored from the bucket to equality in 1 h 50 min; the
step 1.8 dump retired. Next measurements, no session: the Sunday full on
25 October and the first 28-day rehearsal (`qv4-offsite-rehearsal`).
Waiting on Arthur: card `the-press-graph-leaves-the-old-nightly-push`
(after the election). The dump's local folder is gone (five files, not
14: the session quoted the job's keep limit; Arthur removed them 20 October).

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
