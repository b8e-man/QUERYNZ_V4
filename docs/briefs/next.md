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
carded); the Commission's table 117 equal, 5 carded; Part A on 30
returns (679 rows). Session 4, Opus, launched headless by the integrator.

```text
You are the party-returns session, session 4, in your working copy. Read
docs/PLAN.md, docs/plan/step-4.md, docs/status.md and
docs/status/party-returns.md. Do your status file's next items: Part A
rows across a page break (ACT 2019, Labour 2020, 2023, 2024, NZ First
2023); schedules outside the Part A heading found by their own heading
or total (National 2024, NZ First 2021, 2022); and switch the lane's
party labels to keys.parties.party_name(label, rows, on=date) from
pub.party_names (fix-keys-1), measuring how many of the 27 unresolved
labels now resolve. The cell-scale re-read of column-order pages is the
scheduler's: leave its card. Measure every change on all 152 returns,
replay only. Edit nothing outside your folder, push and raise
party-returns-4. Finish by telling Arthur what closed and what is carded.
```

## parties

Session 1 merged (`docs/merges/parties-1`): 78 registrations from the
Commission's page and 136 Gazette notices (exported once from the old
estate's text), 149 names with windows, every stated rename read, 17 on
the register, 6 off it with no cancellation held (carded). No session 2
now: the lane takes the Gazette lane's notices when that lane exists.
Its blocker is a fix on `keys` (next section).

## party-finance

Session 1 merged (`docs/merges/party-finance-1`): 116 documents, 30 of
37 expense totals equal the Commission, broadcasting to the dollar, 69
promoters, the financial-statements roster. Row 115 read the three
unread returns' image pages. Session 2, Opus, launched headless by the
integrator.

```text
You are the party-finance session, session 2, in your working copy.
Read docs/PLAN.md, docs/status.md and docs/status/party-finance.md. Do
your status file's next items: the financial statements' figures (card),
text-layer statements first, each figure checked against the
statement's own printed totals; the promoter returns' own totals against
the Commission's table (card); and the five unread expense returns now
that queue row 115 has stored every image page of three of them (the
lane replays the reader contract's stamp {"dpi": 300, "prompt": "OCR"},
added at the merge). Switch party labels to
keys.parties.party_name(label, rows, on=date) where the lane resolves a
party. Measure on every real file. Edit nothing outside your folder,
push and raise party-finance-2. Finish by telling Arthur what closed and
what is carded.
```

## links

Session 1 merged (`docs/merges/links-1`): rows from nine registers under
the shared reading (2.75 M person rows), the two confirming rules
(1.26 M and 0.94 M confirmed), number and identifier links, the watch,
669,863 groups, the old ledgers copied exactly (77,179) and 5,355
decisions promoted, 573 test pairs (three kinds unsupplied, carded), the
six measurements in `links/measurements.md`. Two queue questions for
Arthur (a company name alone confirming a donor; one company's office as
a shared address). `qv4-links-build` rebuilds after lane loads;
`qv4-links-review` waits for track C. No session 2 now.

## gazette

Sessions 1 and 2 merged (`docs/merges/gazette-1`, `-2`): 207,133
notices typed; celebrant lists, director prohibitions and liquidator
appointments read, addresses private. Session 3, Opus, launched headless
by the integrator.

```text
You are the gazette session, session 3, in your working copy. Read
docs/PLAN.md, docs/status.md and docs/status/gazette.md. Do your status
file's next items: the other insolvency, bankruptcy and appointment
notices, each its own document profile proposed for the integrator, each
measured on every notice of its type; the printed tables by the
organisation vocabulary; and the liquidations check against
pub.companies now that lane is published (a liquidated company that the
register does not hold is a catch-log line, never a guess). Mask every
sample before printing it (the two gazette lessons). Addresses go to
gazette_private only. Edit nothing outside your folder, push and raise
gazette-3. Finish by telling Arthur what closed and what is carded.
```

## candidate-returns

Step 4.1, built: candidate donation and expense returns, held after all
under the old estate's `var/staging/ec-donations/` (its README: 2011,
2014, 2017, 2020 as 610 per-candidate PDFs, 2023). Totals come from the
Commission's own spreadsheet, joined on year, electorate and surname;
amended returns are republished under a different file-name pattern.
Opus. Launched headless by the integrator.

```text
You are a build session for QueryNZV4 on node2, running as Opus, in the
working copy the launcher made for you. Read docs/PLAN.md, then
docs/status.md and your own status file docs/status/candidate-returns.md
(make it), the lane contract, the row contract,
docs/plan/reference/facts-and-traps/electoral-commission-forms.md and
registers/party_returns/ for how a Commission return is read from the
page reader's stored readings (replay only; never call a model here).
Build one lane only: candidate-returns, in registers/candidate_returns/.
Its documents are held under the old estate's var/staging/ec-donations
(read its README first): take them by hash, read-only; fetch nothing.
Profiles before readers: assign or propose a document profile for each
form kind before reading it. Totals from the Commission's own
spreadsheet where held, joined on year, electorate and surname; an
amended return replaces its original only where the Commission says so.
A donor's address goes to candidate_returns_private and nowhere else;
never print one into your session; view pages only through a masking
tool as the party-returns lane's replay does. Give every row a stable
key and a citation. Keep a catch log that reconciles. Build in small
tranches, each measured on every real file. Work in your scratch schema;
edit nothing outside your folder; never touch the old estate's jobs,
folders or primary database. Push your branch and raise
candidate-returns-1. Finish by telling Arthur what closed and what is
carded.
```

## site

Step 4.4, the published-site shape and the Follow the Money template,
in `products/published_site/` and `products/templates/ftm/`: the release pipeline
behind the new contract with its gates, without its last steps. Fable.
Launched headless by the integrator.

```text
You are a build session for QueryNZV4, running as Fable on node2, in
the working copy the launcher made for you. Read docs/PLAN.md, then
docs/plan/step-4.md (4.4 and 4.5), docs/plan/design.md, docs/status.md,
products/published_site/spec.md and products/templates/ftm/README.md
(the thin slice of 1.11 lives in products/published_site/ and grows into
the shape here; a folder named site clashes with Python's own) and your
own status file
docs/status/site.md (make it). Do the part of step 4 named here: the
published-site shape and the Follow the Money template, in
products/published_site/ and products/templates/ftm/. Move the old release
pipeline's shape behind the new contract with its gates, without its
last steps: the new pipeline reads only pub views and the template,
writes a version folder of the ten kinds of published file and stops;
it has no deploy step, holds no deploy token, never drains the live
site's feedback, serves its preview on a port other than 8300 and 8301
on the local network only, and never touches the frozen product's
publisher job or its ports. The template applies the 2019 window
(ruling 347) and the rules for what may be shown (no home address, a
suppressed name suppressed, the money stays). Build from a frozen
release's recorded listing of the captured-document folders so the
comparison in checks/ (4.5) can run on the same inputs. Build in small
tranches, each with a check that can fail against the real published
tables. Edit nothing outside your two folders; push your branch and
raise site-1. Finish by telling Arthur what closed, what is carded, how
to see the preview, and what waits on him.
```

## gazette

Sessions 1 and 2 merged (`docs/merges/gazette-1`, `-2`): 207,133
notices typed; celebrant lists, director prohibitions (537) and
liquidator appointments (43,478 of 43,587) read, addresses private. No
session 3 now; its items (`docs/status/gazette.md`): the other
insolvency, bankruptcy and appointment notices; the printed tables; the
liquidations check against the companies register now that lane is
merged; the parties lane takes this lane's `au` notices.

## charities

Step 4.1: the Charities Register, built twice (plan: Fable and Opus,
`charities_a` and `charities_b`, against the same tests) from one
shared capture. This session is the capture, in `registers/charities/`:
the register's own open data feed, verbatim copies by hash with a
listing, politely; the four questions answered in the status file as it
goes (ruling 61). Opus. Launched headless by the integrator.

```text
You are a build session for QueryNZV4 on node2, running as Opus, in the
working copy the launcher made for you. Read docs/PLAN.md, then
docs/status.md and your own status file docs/status/charities.md (make
it), the lane contract, the row contract, and
docs/plan/reference/old-estate/names-addresses-and-capture.md (the old
charities client bypassed the fetch gate; take the idea, not the code).
Do the capture half of the charities lane only, in registers/charities/:
find the register's current open data feed and its terms, answer the
four questions in your status file (open without a lock; lawful copying;
the terms accepted; what privacy law or the Charities Act limits) and
keep going under ruling 61 (the legal position page is written before
product); capture every charity, officer and annual return record
verbatim through support.fetchgate, landed by hash with a listing, slow,
off-peak, cached, the feed's stated limits honoured, never a challenge
solved; then a qv4-charities-capture job for changes, nightly, proposed
in your spec for the integrator to add to the catalogue (a build session
does not queue live jobs). Never print an officer's address into your
session. Keep a catch log that reconciles. Measure the capture against
the register's own count of registered charities. Write read.py only as
far as a listing of what is held; the reading is the two builds' work.
Edit nothing outside your folder; push and raise charities-capture-1.
Finish by telling Arthur what closed, what is carded, and the figures.
```

## societies

Step 4.1, copied through the per-entity interface: incorporated societies
and their officers, in `registers/societies/`. First the old estate's
loaded rows exported once by hash (as companies did), then the
register's per-entity pages a seventh a night, party societies first,
under ruling 61. Opus. Launched headless by the integrator.

```text
You are a build session for QueryNZV4 on node2, running as Opus, in the
working copy the launcher made for you. Read docs/PLAN.md, then
docs/status.md and your own status file docs/status/societies.md (make
it), the lane contract, the row contract, registers/companies/capture.py
(a once-only export from the old database by hash) and
support/fetchgate. Build one lane only: societies, in
registers/societies/. First export the old estate's society and officer
rows once (read-only, the old read-only login, a statement timeout,
server-side cursors; never at load) and read them under the register's
own identifiers with windows; an officer's address goes to
societies_private and nowhere else, never into your session. Then the
per-entity capture: answer the four questions in your status file and
keep going under ruling 61; design qv4-societies-capture as a seventh of
the societies a night, party societies first, through the fetch gate,
slow, off-peak, cached, a stated crawl delay honoured, never a challenge
solved; propose the job in your spec for the integrator (a build session
does not queue live jobs) and prove it on a handful of pages only. Give
every row a stable key and a citation. Keep a catch log that reconciles.
Find one figure from the register itself to check against. Build in
small tranches, each measured on the real rows. Work in your scratch
schema; edit nothing outside your folder; never touch the old estate's
jobs, folders or primary database. Push your branch and raise
societies-1. Finish by telling Arthur what closed and what is carded.
```

## interests-expenses

Session 1 merged (`docs/merges/interests-expenses-1`): expenses, 100
workbooks read with a standard-library reader proven cell for cell
against LibreOffice, 6,206 lines published, 12 listed workbooks not held
(11 on parliament.nz, one overwritten in the old folder; cards);
interests, 21 editions, 2,526 returns, 24,931 declarations, real
property withheld by default (queue item for Arthur). Waiting on Arthur:
the ten releases whose printed totals are the publisher's own slips
(accept onto the known-limits page, or a skip list). No session 2 now.

## house

Session 1 merged (`docs/merges/house-1`): 28 elections, 216 electorates
(2020 and 2023 joined to Stats NZ 72 of 72), 1,611 candidacies, 243
seats, the Commission's own figures 82 of 82. Waiting on Arthur: the
Stats NZ key for the 2025 boundaries (card); whether to ask the
Commission about reading its results site (card: three by-elections and
two 2020 pages not held). Mid-term changes come from the Gazette lane
(card). No session 2 now.

## companies

Session 1 merged (`docs/merges/companies-1`): no raw monthly file
survives, so the old estate's loaded tables of the July and August 2026
files were exported once by hash; 1,920,468 entities, 1,185,805 director
roles, 1,581,955 shareholdings, 867,277 registered offices; the
Companies Office's own statistics equal within 0.02%. Residential
addresses private. Cards: the old loader folded shareholdings and kept
no role numbers; no monthly file is held for the 18 November step; the
statistics page's legal position (ruling 61: before product). Queue:
the package carries sole traders. No session 2 now.

## board

Step 4, the board, in `products/board/`: one search across every
published register, panes chaining left to right, local network only;
a desktop launcher file ships with it (Arthur, 20 October). Fable.
Launched headless by the integrator.

```text
You are a build session for QueryNZV4, running as Fable on node2, in
the working copy the launcher made for you. Read docs/PLAN.md, then
docs/plan/step-4.md (the board, under "Do"), docs/plan/design.md ("How
the code is laid out"), docs/status.md and your own status file
docs/status/board.md (make it). Do the part of step 4 named here: the
board, in products/board/. One search across every published register
at once: the first pane lists results grouped by register with a count
each, a register not held says "not held"; clicking a result opens a
pane to its right with the row, its fields, its source document and its
links grouped by register (confirmed first, near after, each with its
rule and reason; the links tables may be empty until links/ is built,
and the board must show that plainly); clicking a link opens the next
pane, the row of panes being the path walked; a person pane shows the
group with namesakes apart; a pane can be pinned and a path saved. Each
lane's pane.md says how its rows appear: read them, and read only the
pub schema, never a lane's inside (the one-way test enforces this). Take
the mechanics from the earlier boards named in step 4 (React and
TypeScript panels in /home/user/qnz3-ref) as ideas, not code; the estate
has no npm build step, so prefer a server-rendered page with the least
machinery that works. The surface listens on the local network only, on
a port you record in your spec, under a qv4- unit if it needs one; it
never opens to strangers and never touches the frozen product's
publisher or its ports. Never show a home address or a suppressed name:
only pub views carry what may be shown. Build in small tranches, each
with a check that can fail against the real published tables. Work in
your scratch schema if you need one; edit nothing outside your folder;
push your branch and raise board-1. Finish by telling Arthur what
closed, what is carded, how to open the board, and what waits on him.
Arthur wants a launcher on his desktop that opens the board. Ship it in
your folder as a freedesktop .desktop file (Name, Icon, Exec opening the
board's address in the default browser, starting the board's unit first
if it is not running), with a test that the file parses; no session may
write outside the repository, so also print, in your closing report, the
one line Arthur runs on node2 to copy it onto his desktop and mark it
trusted.
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
