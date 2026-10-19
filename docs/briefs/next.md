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

Sessions 1 to 3 merged (`docs/merges/party-returns-1` to `-3`): 137
rows, 71 party-years equal to the frozen site, 1 differing (Labour 2017,
carded); the Commission's by-year table 117 equal, 5 differing, each
carded; Part A on 30 returns (679 rows), loans on 6, 14 amendments. No
session 4 now; its items (`docs/status/party-returns.md`): rows across a
page break, schedules outside the Part A heading, the cell-scale re-read
of column-order pages (the scheduler's, carded), and the switch to
`keys.parties.party_name(label, rows, on=date)`.

## parties

Session 1 merged (`docs/merges/parties-1`): 78 registrations from the
Commission's page and 136 Gazette notices (exported once from the old
estate's text), 149 names with windows, every stated rename read, 17 on
the register, 6 off it with no cancellation held (carded). No session 2
now: the lane takes the Gazette lane's notices when that lane exists.
Its blocker is a fix on `keys` (next section).

## party-finance

Session 1 merged (`docs/merges/party-finance-1`): 116 documents; party
expense tables (58 rows), 34 returns' own totals read (30 equal the
Commission, 2 explained, 5 unread), broadcasting allocations (89 rows, to
the dollar), 69 promoters and 303 people (contacts private), the
financial-statements roster (47). `qv4-read-pages-expenses` reads the
three unread returns' image pages (queued after the merge). No session 2
now; its items (`docs/status/party-finance.md`): statement figures,
promoter returns' totals, the five unread once the readings land.

## gazette

Session 1 merged (`docs/merges/gazette-1`): 207,133 notices typed by the
Gazette's own section code; the celebrant lists read (2,941 of 2,975;
123,187 rows; 8,943 addresses private). Session 2, when a slot frees
(`docs/status/gazette.md`): director prohibitions, then liquidator
appointments (43,587 notices), each its own profile; then the printed
tables. Launched headless by the integrator 20 October 08:45, Opus.

```text
You are the gazette session, session 2, in your working copy. Read
docs/PLAN.md, docs/status.md and docs/status/gazette.md. The export and
the celebrant lists are merged; do your status file's next two items:
director prohibitions (one template; addresses private), then liquidator
appointments, each with its own document profile proposed for the
integrator; measure each on every notice of its type, not the sample.
Mask every sample before printing it (lesson
a-gazette-celebrant-list-can-print-home-addresses). Edit nothing outside
your folder, push and raise gazette-2. Finish by telling Arthur what
closed and what is carded.
```

## interests-expenses

Step 4.1, copied from published files: MPs' and ministers' expenses
(held under `var/staging/mp-expenses/` and `minister-expenses/`) and the
Register of Pecuniary Interests (where held is for the baseline to say).
Two folders, one session, Opus: `registers/mp_interests/`,
`registers/expenses/`. The integrator launches it:
`bin/start-session interests-expenses registers/mp_interests registers/expenses`.

```text
You are a build session for QueryNZV4 on node2, running as Opus, in the
working copy the launcher made for you. Read docs/PLAN.md, then
docs/status.md and your own status file docs/status/interests-expenses.md
(make it), the lane contract and the row contract. Build two lanes:
expenses, in registers/expenses/, from the releases held under the old
estate's var/staging/mp-expenses and minister-expenses, by hash,
read-only; and mp_interests, in registers/mp_interests/, from the
published register editions: first find in docs/baseline.md and the old
folder whether the editions are held; if they are not, card it with
where they are published and build the expenses lane alone. Key the
interests on the category heading, never its number (renumbered 2018);
every edition reprints the rules after the last member. Profiles before
readers. Fetch nothing. Give every row a stable key and a citation. Keep
a catch log that reconciles. Find one figure from each source itself to
check against. Build in small tranches, each measured on the real files.
Work in your scratch schema; edit nothing outside your two folders;
never touch the old estate's jobs, folders or primary database. Push
your branch and raise interests-expenses-1. Finish by telling Arthur
what closed and what is carded.
```

## house

Session 1 merged (`docs/merges/house-1`): 28 elections, 216 electorates
(2020 and 2023 joined to Stats NZ 72 of 72), 1,611 candidacies, 243
seats, the Commission's own figures 82 of 82. Waiting on Arthur: the
Stats NZ key for the 2025 boundaries (card); whether to ask the
Commission about reading its results site (card: three by-elections and
two 2020 pages not held). Mid-term changes come from the Gazette lane
(card). No session 2 now.

## companies

Step 4.1, copied: companies and the other entity types, directors,
shareholders, addresses, from the Companies Office's monthly file Arthur
downloads by hand (never raised as outstanding). Opus. The integrator
launches it: `bin/start-session companies registers/companies`.

```text
You are a build session for QueryNZV4 on node2, running as Opus, in the
working copy the launcher made for you. Read docs/PLAN.md, then
docs/status.md and your own status file docs/status/companies.md (make
it), the lane contract and the row contract, and docs/baseline.md for
the old estate's nzbn_canonical tables. Build one lane only: companies,
in registers/companies/. First find where the raw monthly files are
kept; if only the loaded tables survive, export them once from the old
database by hash, read-only, the way registers/gazette/capture.py did
(the old read-only login, a statement timeout, a server-side cursor),
and never run the export at load. Entities, directors and shareholders
under the source's own identifiers, with windows; a company's registered
address is published, a person's residential address goes to
companies_private and nowhere else; never print one into your session.
The monthly file is Arthur's to download and is never raised as
outstanding. Give every row a stable key and a citation. Keep a catch
log that reconciles. Find one figure from the Companies Office itself to
check against. Build in small tranches, each measured on the real rows.
Work in your scratch schema; edit nothing outside your folder; never
touch the old estate's jobs, folders or primary database. Push your
branch and raise companies-1. Finish by telling Arthur what closed and
what is carded.
```

## keys-fix

Merged (`docs/merges/fix-keys-1`): `keys.parties.party_name(label, rows,
on=date)` resolves a label against `pub.party_names` by name key and
the registration's window; 38 of 42 unresolved return labels and 53 of
53 disclosure labels resolve on the published tables, every old rule
kept. Each lane switches to the new call in its own next session
(party-returns 3 may do it now; disclosures and parties when they next
open); the parties lane's `lifecycle` takes `keys.parties.name_key`.

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

Launching (Arthur, 20 October): the integrator launches build and fix
sessions itself, headless, after `bin/start-session` has made the copy:
from that folder, `claude -p --model <opus|fable> --permission-mode auto
"<brief>"` in the background, output to a log under the scratch folder;
it relays from the log when the session raises its request or stops to
ask. Auto is the classifier mode, not bypass (hard limit 3). An agent of
the integrator's own does not work: the scope hook fences it to the main
checkout (`docs/merges/offsite-1-not-started.md`). Start lines are handed
to Arthur only when he asks for a window.

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
