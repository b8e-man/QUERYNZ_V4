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

Session 5 running (Opus, launched headless 20 October 14:45) on the
comparison's Part A cards:

```text
You are a build session for QueryNZV4, running as Opus on node2, in the
working copy the launcher made for you. Read docs/PLAN.md, then
docs/plan/step-4.md (4.1 and 4.5), docs/plan/reference (the Electoral
Commission forms), docs/status.md, docs/status/party-returns.md and
docs/status/comparison.md, registers/party_returns/spec.md, the lane
contract and the row contract, and the cards owned by party-returns that
the comparison session opened on 20 October (session: comparison;
"Owner: party-returns"):
part-a-rows-are-read-on-a-minority-of-the-returns-held,
part-a-rows-the-frozen-site-has-and-no-rebuilt-page-carries,
party-years-the-frozen-site-totals-and-the-lane-holds-no-total-for,
the-rebuilt-lane-holds-declared-totals-the-frozen-site-lacked, and the
lane's own open cards. Build the lane's fifth tranche in
registers/party_returns/: Part A rows from every return whose pages have
a stored reading (the page reader's stored readings under the lane's
stamp; call no model yourself; a return with no stored reading is set
aside with its hash and pages so the integrator can queue it), the two
party-years with no total, and for each card either a close with its
figure measured on all the returns held or a line saying what it still
needs. The example row drops by the hash of its cell (ruling 190); an
unreadable line is a line, not a donor (191); a disclosure is never
summed into a return (192); the donor is the EC-filed entity (253).
Addresses only in the private schema. Every change measured on the real
tables through replay. Work in your scratch schema; edit nothing outside
registers/party_returns/; push your branch and raise party-returns-5.
Finish by telling Arthur which cards closed, what the comparison should
see fall, and what waits on him.
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

Merged (`docs/merges/links-1`): the two rules, the old ledgers mapped,
the test pairs, the six measurements; loaded live 20 October. Track C
(the review agent) runs in this folder as session `review` below. Open
card for the lane: `the-links-tables-do-not-migrate-an-existing-column`.
Queue: a company name alone confirming a donor; one company's office as
a shared address.

## gazette

Sessions 1 to 3 merged (`docs/merges/gazette-1` to `-3`): 207,133
notices typed; celebrants, prohibitions, liquidations, the company
notices, bankruptcies and appointments read, every address private, the
companies register joined. Session 4 when wanted: the four pane
paragraphs (card `the-gazette-pane-spec-omits-the-four-tables-of-gazette-3`),
the `au` notices for the parties lane, the remaining sections by use
case.

## candidate-returns

Merged (`docs/merges/candidate-returns-1`): 1,105 returns by hash, the
Commission's listing and spreadsheets, 372 totals (353 equal), Part A
175 donors. The 713 scans are queued as `qv4-read-pages-candidates`;
session 2 rebuilds when they land, then Part A from pixels and the
nine candidate-made copies (status file).

## site

Session 1 merged (`docs/merges/site-1`). Session 2 running (Fable,
launched headless 20 October 14:45) on the comparison's eighteen site cards:

```text
You are a build session for QueryNZV4, running as Fable on node2, in the
working copy the launcher made for you. Read docs/PLAN.md, then
docs/plan/step-4.md (4.4 and 4.5), docs/status.md, docs/status/site.md and
docs/status/comparison.md, products/published_site/spec.md,
products/templates/ftm/README.md, checks/README.md (read only; the
comparison's day record is under
/home/user/querynzv4-work/live/checks/comparison/), and the eighteen cards
owned by site that the comparison session opened on 20 October
(session: comparison; "Owner: site"), with the queue item
which-frozen-sections-belong-in-the-follow-the-money-template (default:
all sections; recommendation: money sections stay, person-page sections
go to step 5). Build the shape's second tranche in
products/published_site/ and products/templates/ftm/: the frozen sections
the template does not carry, under the queue's default (every money
section; the person-page sections too until Arthur rules, marked in the
template as the ones the queue would move); financial statements on the
party page; electorate money from pub.candidate_return_totals and
pub.candidate_return_donors; list-only candidacies on the person page;
the donor picker and the display-name and key choices each settled with a
line in the template saying which side's rule it takes and why; and for
each card either a close with the figures that fell in a rebuild measured
against the frozen version (python -m checks.comparison run reads both
sides; run it, never edit checks/) or a line saying what it still needs.
No deploy step, no deploy token, never 8300 or 8301, never the frozen
publisher; no home address; a suppressed name suppressed, the money
stays. Build in small tranches, each with a gate that can fail on the
real published tables. Edit nothing outside your two folders; push your
branch and raise site-2. Finish by telling Arthur how many of today's
differences fell, by cause, what is carded and what waits on him.
```

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

Session 2, when a slot frees (Opus), on the comparison's five house cards:

```text
You are a build session for QueryNZV4, running as Opus on node2, in the
working copy the launcher made for you. Read docs/PLAN.md, then
docs/plan/step-4.md (4.1 and 4.5), docs/status.md, docs/status/house.md
and docs/status/comparison.md, registers/house/spec.md, the lane contract
and the row contract, and the cards owned by house that the comparison
session opened on 20 October (session: comparison; "Owner: house"):
candidacies-the-frozen-site-shows-and-the-house-lane-lacks,
the-house-lane-has-no-result-for-a-race-the-frozen-site-shows-won,
an-unregistered-party-label-is-not-on-the-rebuilt-candidacy,
a-candidate-s-given-name-differs-between-the-return-summary-and-the-results,
the-rebuilt-site-splits-one-candidate-across-two-name-forms,
the-rebuilt-pages-carry-vote-counts-the-frozen-site-never-read. Build
the lane's second tranche in registers/house/: each card either closed
with its figure measured on the real published tables, or left open with
a line saying why the frozen side is wrong and what the card still needs.
Documents only from what the old estate holds or the official results
already captured; fetch nothing new without the four questions in your
status file. Every row keeps its stable key and citation; the catch log
reconciles; the outside check stays green. Work in your scratch schema;
edit nothing outside registers/house/; push your branch and raise
house-2. Finish by telling Arthur which cards closed, what the comparison
should see fall, and what waits on him.
```

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

## comparison

Merged (`docs/merges/comparison-1`): `python -m checks.comparison run`
pairs the frozen release with the rebuilt version built from its listing;
`qv4-site-compare` daily 08:45 NZDT; the lanes' checks on the board. Day
one: 43,062 differences, all carded, 23,067 under cards saying the new
side is short. The cards name their owners (house, party-returns, site,
disclosures, parties); the owners' next sessions are briefed below. Queue:
which frozen sections the template carries (default all).

## review

Track C, the review agent, in `links/`. Fable. Launched headless by the
integrator 20 October 12:50.

```text
You are a build session for QueryNZV4, running as Fable on node2, in
the working copy the launcher made for you. Read docs/PLAN.md, then
docs/plan/track-c.md, docs/plan/step-4.md (4.2 and 4.3),
docs/plan/design.md, docs/status.md, docs/status/links.md, links/README.md,
links/spec.md, links/review.py, links/measurements.md, the cards that
name the links lane, and make your own status file docs/status/review.md.
Do track C: the review agent, in links/. Build on the old refute-only
agent in /home/user/qnz3-ref/data-layer/research/research/merge_refuter.py
and webtools.py and the screen-then-re-read pattern in
data-layer/healer/healer/crawler.py and reread.py, as ideas; the three
verdicts match the decisions table (not the same; contested; no reason
to doubt). The agent runs on the boxes only, through the scheduler's
qv4-links-review job on the review-and-questions profile (the worker
gives QV4_MODEL_URL and QV4_MODEL); nothing it reads leaves the boxes.
Measure it before it acts: score it on the test pairs of 4.3 (links'
pairs tables), at least 200 of each kind per name band where supplied;
the default pass mark is fewer than 1 in 100 known-one-person pairs
wrongly split, and report what share of the known-different pairs it
catches. Until it passes, verdicts are recorded in links.readings and
never applied; build the apply path (a decision added, then a rebuild)
behind a switch that is off, with a check that fails if a reading ever
becomes a decision while the switch is off. The web is searched only for
evidence that two rows are different people, a name and a public role at
most, through the fetch gate, and every citation must be a page fetched
in that run; the gate has no search route yet, so card what support/
needs and do not build around it. Also the lane's open card
the-links-tables-do-not-migrate-an-existing-column, and re-run
links.old --map --promote and links.pairs in your scratch schema now that
candidate-returns publishes (the integrator reloads the live schema).
Never print a home address: the evidence is registered offices and
roles. Build in small tranches, each measured on the real published
tables. Work in your scratch schema; edit nothing outside links/; push
your branch and raise review-1. Finish by telling Arthur the two
figures, what is carded and what waits on him.
```

## report

Merged (`docs/merges/report-1`): the subject-report shape in
`products/report/`, unit `qv4-report` on 10.0.0.2:8440. Next, step 5.2 in
the plan's order, each template its own session once the one before is
merged: `bin/start-session recruitment products/templates/08-recruitment`
with the step 5 template brief (`docs/plan/step-5.md`), then agriculture
(04), banking (03), legal (02). Cards for the links session (same-name
donor rows) and a board fix ("report from here").

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
