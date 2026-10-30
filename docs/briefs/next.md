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

Sessions 1 to 3 merged (`docs/merges/disclosures-1` to `-3`): 520
declarations, 15 of 16 party-years equal to the frozen site, the form check
on every scan held, 27 scans set aside (ruling 62), the gift's year the
money year. New card 21 October: the frozen site gained an ACT New Zealand
declaration the lane's one-off capture predates
(`act-new-zealand-2026-a-declaration-filed-after-the-lane-s-capture`);
the gap widens with every filing until the lane captures the Commission's
table nightly or Arthur says the gap stands until the switch.

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

Session 5 merged (`docs/merges/party-returns-5`): Part A on 52 returns
(1,133 rows) over the stored page readings, three declarations mended,
two published faults fixed. Set-aside pages for a later re-read are
listed by `python -m registers.party_returns.replay rereads` (ruling 62:
not queued until the build is done). Queue: may Part A pass a rounding
cent (National 2023, default no).

## parties

Sessions 1 and 2 merged (`docs/merges/parties-1`, `-2`): 77 registrations,
149 names with windows, 137 Gazette notices read from the gazette lane,
`pub.party_labels` (1,154 labels from 17 tables, 119 unresolved after
`fix-keys-1`'s spelling rules). No session 3 now.

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

Merged (`docs/merges/links-1`, `review-1`, `links-2`): the two rules, the
old ledgers mapped, test pairs, six measurements; track C's review agent
measured and recording, applying nothing; every published register read,
2.82 M links, the House's rows joined to seats, declared interests
anchored. Live reload at the links-2 merge. Open for the lane: the keys
card on a judge's title and a surname particle; the search route
(`support/fetchgate`, a fix session). Queue: three questions on what a
register's own structure may confirm (defaults built as settings).

## gazette

Sessions 1 to 5 merged (`docs/merges/gazette-1` to `-5`): 207,133 notices
typed; celebrants, prohibitions, liquidations, company notices of twelve
kinds (removals, winding-up, receiverships, creditors, administrations,
overseas companies ceasing, restorations, society dissolutions,
rectifications, amalgamations, transfers out, deeds), bankruptcies,
appointments, mortgagee possessions; every address private; 76,803 unread.
Session 6, Opus, launched headless by the integrator 21 October 07:35 on
the card `published-gazette-titles-can-carry-a-street-address` (the brief
is in the integrator's scratch folder; its gist: cut every published title
before any property it names, the uncut title private, a check). Queue:
may the lane read notices that name people for their conduct (default no).

## site

Sessions 1 to 3 merged (`docs/merges/site-1` to `-3`): the shape and the
template at version 3 (keys from the settled display name, one donor one
page, a declaration in the gift's year). The version-3 build is refused by
the site's own fall gate until it is told the fall is a recorded
correction; the classifier refused that flag to the integrator, so Arthur
runs it on node2: `cd /home/user/querynzv4 && .venv/bin/python -m
products.published_site build --allow-drop`. Session 4 when the comparison
names a cause that is the shape's.

## charities

Step 4.1 closed: the capture (`charities-capture-1`), the two builds
(`charities-a` Fable, `charities-b` Opus, merged as records with the
comparison lesson), and `charities-3` (the Opus build kept, moved to
`registers/charities/`, published: `pub.charities`, `pub.charity_officers`,
`pub.charity_returns`; `qv4-charities-load` nightly 06:30). Ruling 64: a
body corporate's address for service shown, a trust's withheld. Next for
the lane: nothing. For the report shape and the templates: the charities
views to reach (card `the-report-shape-and-five-templates-still-say-the-
charities-register-is-not-published`), a fix session on `products/report`
then one across the templates, after the merges of 21 October.

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

Session 2 merged (`docs/merges/house-2`): the comparison's six house cards,
three closed, three open with what each needs (the two 2020 pages the
old jobs alone may fetch until the switch; the Stats NZ key). Session 3
when a comparison card or Arthur's key calls for it.

## companies

Session 1 merged (`docs/merges/companies-1`): 1,920,468 entities from
the old estate's loaded July and August 2026 files. Session 2 merged
(`docs/merges/companies-2`, step 5.5): the monitor, `pub.request_company_check`,
`pub.watch_company`, `pub.unwatch_company`, `qv4-companies-monitor` nightly
23:30 NZDT, profile `nzbn-entity-detail-any-kind`. No session 3 now.

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

Merged (`comparison-1`, `-2`): `python -m checks.comparison run` daily
08:45. Day two (frozen 2026-10-20T0620 against rebuilt 1513): 29,508
differences, 0 uncarded, 7,947 under cards saying the new side is short.
Site-3 measured 29,336 in scratch; the live figure follows the version-3
build. Queue: which frozen sections the template carries (default all).

## review

Merged (`docs/merges/review-1`): `review-agent@2`, scored on 577 pairs on
the live schema 20 October 21:00 (0 of 144 one-person pairs split, 363 of
430 two-people caught; the model's own one-person rate unmeasured until a
charities lane supplies pairs); verdicts recorded, nothing applied. Queue:
may the agent's splits be applied (default no). The test pairs were redrawn
by links-2: score again (`qv4-links-review --args '{"mode": "score"}'`).

## report

Merged (`docs/merges/report-1` to `-3`, `fix-report-2`): the subject-report
shape on 10.0.0.2:8440, contract 0.4: template parameters (`[[params]]`,
`report["params"]`), the Charities Register catalogued and reached, eight
not-held keys, an officer's near links, the companies above in the chain.
`fix-templates-1` (raised 21 October, `products/templates`): construction
and property declare `window_days`; the ten templates read the charities
register; a healthcare trust board's trustees read from its charity.
Three template cards stay open for a later `bin/fix products/templates`.

## ownership

Step 5.2 closed 21 October: templates 13, 7 (+ `construction-2`), 5, 6,
11 (`healthcare-1`), 12 (`property-1`) merged beside 08, 04, 03, 02. Step
6.1 (`scan-1`, Fable, `products/scan`) runs; step 7 held (ruling 63).

## party-boards

Merged (`party-boards-1`, ruling 72): the declared tier from the held
party-website capture, 2017 on; `pub.party_board_roles` and
`pub.party_board_pages`, on the board, not on the site and not in the
links. `qv4-party-boards-load` reloads on demand. Carded: Labour's and the
Greens' boards are not in the capture. Next, when Arthur asks: the
historic private-positions tier.

## openlaw

HELD (`openlaw-1`, step 5.4): the OpenLaw NZ interface's terms (clause
3.6(a)/3.7) bar the copy; queue item
`whether-openlaw-api-content-may-be-copied` has no default. Lane built
and proven in memory; profile appended; schemas made; no job. Nothing
runs until Arthur rules or OpenLaw NZ authorises in writing.

## courts

Merged (`courts-1`, step 5.4): the senior courts' judgments from
courtsofnz.govt.nz and the held Waitangi Tribunal reports; five profiles;
`qv4-courts-capture` nightly 03:30 NZDT; `pub.court_judgments` and
`pub.court_judgment_parties` (board views in the merge after). Carded:
District Court judgments not captured, High Court outcomes not read,
Tribunal reports held and not read. The Ministry of Justice letter is
Arthur's.

## sanctions

Merged (`sanctions-1`, step 5.3): limited partnerships through the NZBN
interface (`qv4-limited-partnerships-capture` nightly 21:00, never
Wednesday; `-load` 06:50) and the Building Practitioners Board's decisions
(`qv4-building-practitioners-capture` nightly 23:00, the spec's weekly
Sunday until the catalogue carries a weekday; `-load` 06:40). HELD: the
practitioner register (Building Act s 307/308) and the three sanctions
lists (MFAT, UN, Police), five queue items. Both checks red until the
first full passes. Board views in the merge after.

## scan

Merged (`scan-1`, step 6.1): the register-scan shape on 10.0.0.2:8450, two
proving scans, `qv4-scan-rerun` after the links' build; the two trust
settings "default in force" (queue). Step 6.2 templates follow, in the
plan's order: 1 (tender and award intelligence, on `pub.award_notices`),
2, 3, 4(b) to (d).

## tenders

Merged (`tenders-1`, step 6.2's register): the GETS award notices, 29,874
(July 2014 on) from the old estate's files of 14 August, read by six
profiles; `pub.award_notices`, `pub.award_suppliers` with the CC BY 3.0 NZ
attribution on every row. The ministry's host answers 403 and
data.govt.nz challenges: failed reads, not got around; `qv4-tenders-refresh`
asks nothing before 2 November, then weekly. Arthur's: a letter to the
ministry; the queue item on keeping the old copy (default: kept).

## regulators

Merged (`regulators-1`, step 5.3): Commerce Commission cases (1,727
listed), FMA warnings and enforcement (825), WorkSafe prosecutions and
undertakings (670), each captured verbatim, read by profile, no model;
six jobs nightly from 22:30. Checks red until a full pass is held.

## diaries

RULED (`diaries-1`, 6.2 4(a); ruling 78): the Beehive and Hansard are not
captured; Arthur has a third-party source. The reader's one attempt was
refused by the wall (hard limit 6: a failed read, nothing got around);
records merged, no lane code; the blocker card and the letter question
closed with the ruling. Diaries begin January 2019. Next: Arthur names the
source; its position (ruling 61), then the register from it. The headed
browser still has no home in the new estate (finding card).

## oio

Merged (`oio-1`, 5.3): overseas investment decision summaries from
linz.govt.nz, 1,337 listed from 2017, read by profile, no model;
`pub.overseas_investment_decisions`, `pub.overseas_investment_parties`;
the land's address withheld on every row (queue, default applied);
`qv4-overseas-investment-capture` 23:10, `-load` 06:35. Check red until
the first full pass.

## hdc

HELD (`hdc-1`, 5.3): the Commissioner's copyright allows research use
only; queue item `whether-the-hdc-decisions-may-be-copied-for-the-estate`
has no default (the session recommends a letter asking permission). Lane
built and proven on twelve pages; profiles appended; no job.

## grants

Raised (`grants-1`, step 6.3, Opus): the Department of Internal Affairs'
national file of class 4 grants (178,739 records, 2021 to 2025, CC BY 4.0)
and the Lottery Grants Board's records of grants on Community Matters;
`pub.grants`, `pub.grant_recipients`, `pub.grant_publishers`; 31 society
sites surveyed and carded by class. Nothing held on terms. Jobs
`qv4-grants-capture` 22:45, `-load` 06:35 at the merge. Queue: declined
applications naming an individual (default: as the Department shows them,
inside the estate only).

## fetchgate

Raised (`fix-support-fetchgate-1`): Imperva's interstitial is a blocked
read; a redirect is returned, not followed, unless the caller asks
(`follow=`). At the merge the integrator adds a same-host default (http to
https, a trailing slash) so the nightly captures do not thin. Card for the
six lanes that stop on the final address.

## scan-templates

Raised (`scan-templates-1`, step 6.2 templates 1 and 2): `tender-awards`
(33,744 lines), `procurement-directors-donors` (80), `procurement-
shareholders-donors` (6); a shape diff over ten scan files to apply at the
merge (`patch -p1`; the hooks refuse `git apply`). The award join stays
off the public site (6.2 row 2; 6.4 is Arthur's question).

## candidate-returns-3

MERGED 30 October 08:58 (402dd42; record in docs/merges/candidate-returns-3.md).

Build session, Opus, scope `registers/candidate_returns/`. Step 4.5: the
Commission's spreadsheet figures published as rows where no return is read
(card `electorate-money-waits-on-the-candidate-returns-lane`; no model, no
reading, ruling 79 untouched). Launched headless by the integrator 30 October,
or on node2: `cd /home/user/querynzv4 && bin/start-session candidate-returns-3 registers/candidate_returns`.

```text
You are a build session for QueryNZV4, running as Opus on node2, in the
working copy the launcher made for you, scope registers/candidate_returns/.
Read docs/PLAN.md, docs/plan/core.md, your lane's spec.md, pane.md,
commission.py, publish.sql, load.py and check.py, docs/status/candidate-returns.md,
the card cards/electorate-money-waits-on-the-candidate-returns-lane.md, and
checks/comparison.py where it names "candidate-returns-not-held". The
comparison with the frozen site (step 4.5) counts 5,133 differences a day
under that cause, and the card says what clears most of them without any
model reading: the Commission's own summary spreadsheet rows published as
rows where no return is read. The lane holds 2,151 Commission rows
(candidate_returns.commission, 2020: 1,184, 2023: 967); 1,346 of them join
no row of pub.candidate_return_totals by year, electorate and surname.
Build: publish one pub.candidate_return_totals row per Commission row that
no read return covers, carrying the candidate, electorate, party and year
as the Commission lists them and its donations, expenses and (2023) loans
figures in the columns the template already reads as the headline, marked
plainly as the Commission's figure with no return read (a `read_from` or
`source` value the pane and the template can tell apart; say which in
pane.md), with a stable key that does not collide with a read return's
and a citation to the spreadsheet document (its hash, sheet and row). A
return read later replaces the Commission's row for that candidate; the
replacement rule is in publish.sql, not in the template. Keep the catch
log reconciling and the outside check (the spreadsheet against each read
return) as it is. Measure: build the site in your scratch schema as
site-2 did and run checks/comparison.py against the latest frozen day in
/home/user/querynzv4-work/live/checks/comparison/days/; record in your
status file how many of the cause's differences fall, by page kind, and
what remains (the donor pages wait on the scans' readings under ruling 79;
say so, do not read). Propose the nightly qv4-candidate-returns-load job
in your spec for the integrator; queue nothing live. No model is called;
no document is read; nothing is fetched. Each tranche with a test that
fails on main and passes on your branch, on the real rows. Never print a
home address or a suppressed name (a donor's address lives in
candidate_returns_private and never enters your session). Push your
branch, raise the merge request candidate-returns-3 (if the inbox refuses
you, leave it in your scratch folder and say so), update
docs/status/candidate-returns.md.
```

## candidate-returns

Merged (`docs/merges/candidate-returns-1`): 1,105 returns by hash, 372
totals (353 equal), Part A 175 donors; 713 scans wait (ruling 62; 60 read
stand as the sample). Session 2, Opus, launched headless by the integrator
21 October 08:25 on the sample: Part A of the nine candidate-made copies,
Part A from pixels on the 60 read scans with the rest listed for the later
re-read, Parts D and H where the form supports them, the eleven-returns
card, the no-reading case pinned.

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

Views and the worker (integrator, 23 October): on every integrate branch,
before its fast tier and its gate, catalogue on the board the `pub.*` views
the previous merge published (the gate's full tier runs the board's
outside check against the live tables, so a view named late turns it red
and a view named early fails as unpublished; two gates were refused this
way on 23 October). After every push of main, run `.venv/bin/python -m support.installer release`
(node2, /home/user/querynzv4); the worker, its jobs, the four product
services and the checks' timers run that copy (`/home/user/querynzv4-release`,
one pushed commit of origin/main with its own `.venv`), so an integrate branch
no longer needs the worker stopped. When it says `worker restart owed`,
restart the idle worker: `systemctl --user restart qv4-worker@node2` (node2); a job new to the catalogue now waits for its next slot
(fix-support-scheduler-1), so a lane's first run is queued by hand.

Reading (Arthur, 20 October, ruling 62): no page-reader job is queued in
bulk until the build is done. A lane's request for readings is answered
with the store's sample and a note; the hashes it sets aside are the queue
for later, one command.

## fix-support-scheduler-4

MERGED 30 October 14:35 (4f57fdf; record in docs/merges/fix-support-scheduler-4.md).

Fix session, Fable, scope `support/scheduler/`. The probe listed the processor's
own graphics as a card and the page reader ran on it (card
`the-probe-lists-the-processor-s-own-graphics-as-a-card`). Launched headless by
the integrator 30 October, or on node2: `cd /home/user/querynzv4 && bin/fix support/scheduler`.

```text
You are a fix session for QueryNZV4, running as Fable on node2, in the
working copy the launcher made for you, scope support/scheduler/. Read
docs/PLAN.md, docs/plan/core.md, support/scheduler/spec.md, probe.py
(cards), cards.py (register_cards, held, the night window), queue.py
(cards, upsert_card) and the card
cards/the-probe-lists-the-processor-s-own-graphics-as-a-card.md. Fix
that card. What happened: at 13:49 on 30 October, the first tick after
the night-window merge with page work queued, rocm-smi listed a third
device on node2 for one tick (index 2, product "AMD Ryzen 9 9950X
16-Core Processor", 2.0 GB: the processor's own graphics); the probe
passed it as a card, register_cards wrote the row, the planner saw a
cold card and loaded page-reader on it, and the server ran on the
processor. The integrator reserved the row by hand and killed the
server; rows 854 and 855 wait for tonight's window. Build: (1) the probe
keeps a device only when it is a discrete card: its product is not a
processor and its memory is at or above a floor (8 GB; the R9700 has
31.9), and says in its log line what it dropped; (2) register_cards
marks a scheduler.cards row whose card the probe no longer lists as
reserved with a reason naming this, so a stale row is never planned,
and clears that reservation when the card is listed again; (3) a fast
test for each on the fake worker, with a probe payload carrying the
Ryzen device, each seen failing on main's code; (4) the integrator's
hand reservation on (node2, 2) is replaced by yours on the first tick.
Nothing else in the window logic changes; ruling 121's tests stand. No
model is called by the tests. Never print a home address or a
suppressed name. Push your branch and raise fix-support-scheduler-4 in
/home/user/querynzv4-work/inbox/merge-requests/ (if the fence refuses,
leave it in your scratch folder and say so). Finish by telling the
integrator what closed, in a few lines.
```

## fix-support-scheduler-3

MERGED 30 October 13:48 (44ecfec; record in docs/merges/fix-support-scheduler-3.md).

Fix session, Fable, scope `support/scheduler/`. Ruling 129: the standing
server's night window. Launched headless by the integrator 30 October, or on
node2: `cd /home/user/querynzv4 && bin/fix support/scheduler`.

```text
You are a fix session for QueryNZV4, running as Fable on node2, in the
working copy the launcher made for you, scope support/scheduler/. Read
docs/PLAN.md, docs/plan/core.md, support/scheduler/spec.md, cards.py
(the standing-server section, ruling 121), policy.py, profiles.toml,
jobs.toml, and rulings 121, 128 and 129 (30 October) in
docs/decisions/rulings.md. Build ruling 129: a night window in which the
card manager may stop the standing server qv4-radiance for the page
reader and start it again. Rules: the window is 22:00 to 05:45 NZDT,
its hours in jobs.toml's top section; inside it, when a page-reader job
(profile page-reader) is queued and no piece of a view on flash-next
(text-reader, review) is running or leased, the manager stops the unit
with systemctl --user stop qv4-radiance.service, waits until the cards
no longer hold its model, loads page-reader on one card (the other
stays free for the frozen product's OCR server, which is never
touched), and the planner runs the page pieces; when the page queue is
empty, or at the window's end, or when a text-reader piece becomes due
with none left to do, the manager unloads page-reader and starts the
unit again, waits for the model to read back on :8060, and marks the
cards standing as today. Outside the window the standing server is
never stopped or planned (ruling 121 holds). Each stop and start is a
swap-ledger line with its reason and the measured seconds. A failure to
start the unit again is a card for the integrator and an alarm line,
and the manager keeps trying each tick. Tests on the fake worker: the
window opens and closes by the clock, a text piece in flight blocks
the stop, the OCR server's card is never taken, the restart is
retried. Measured figures today: Radiance 56.0 GB over both cards, the
OCR server 4.7 GB, page-reader 4.8 GB; Radiance starts in 21.6 s. No
model is called by the tests. Never print a home address or a
suppressed name. Push your branch and raise fix-support-scheduler-3 in
/home/user/querynzv4-work/inbox/merge-requests/ (if the fence refuses,
leave it in your scratch folder and say so). Finish by telling the
integrator what closed and what the first night will do.
```

## fix-support-mcpsource-2

MERGED 30 October 13:07 (00266ae; record in docs/merges/fix-support-mcpsource-2.md).

Fix session, Fable, scope `support/mcpsource/`. Ruling 126: the pull lands
every file a record points at. Launched headless by the integrator 30
October, or on node2: `cd /home/user/querynzv4 && bin/fix support/mcpsource`.

```text
You are a fix session for QueryNZV4, running as Fable on node2, in the
working copy the launcher made for you, scope support/mcpsource/. Read
docs/PLAN.md, docs/plan/core.md, support/mcpsource/spec.md and README.md,
and rulings 96 and 126 (30 October) in docs/decisions/rulings.md. Build
ruling 126's first part: a download step. The MCP now has a tool
`download` (arguments record_id, corpus, format; format "raw" returns a
meta block and the file as an embedded resource, a base64 blob, with
delivered_sha256 and captured_sha256) and resources qnz-pdf://<corpus>/
<seq>, qnz-html://<corpus>/<seq>, qnz-text://<corpus>/<seq>; its readme
is the resource qnz://readme. Use the tool or the raw resources, never
qnz-text (the text is ours to read from the bytes, one reading per
document). For every record of every corpus whose record carries a
capture block with a sha256 and a content type (today the courts
corpus: case pages, judgment PDFs, media releases), fetch the file,
refuse it when the hash differs from the record's, and land it through
the same `land` the records use, by hash, named by the record's source
url, source query-nz, with the record's content type; a file already
held by hash is never fetched again (the tool is metered per call).
One request at a time, the pull's pause between them, resumable
(record per corpus where the download step is up to, like the cursor),
inside the nightly budget, and run after the records of all corpora so
a short budget still lands the listings. Record arrivals and catches as
the records have them. Add the courts corpus's shape to shapes.json
from the records (fields: id, url, kind, fetched_at, http_status,
sha256, path, bytes, content_type, case_slug, court, case_name,
discovered_via, date, updated_at, capture, file). Tests on the fake
server for: hash match lands, hash mismatch is caught, a held file is
not fetched, resume after a budget stop; the live shape test extended
to the new tool. Update spec.md (the job's description gains the
files; memory and deadline figures revisited) and README.md. No model.
Never print a home address or a suppressed name. Push your branch and
raise fix-support-mcpsource-2 in /home/user/querynzv4-work/inbox/
merge-requests/ (if the fence refuses, leave it in your scratch folder
and say so). Finish by telling the integrator what closed and what the
first full download run will cost in calls.
```

## courts-2

Build session, Fable, scope `registers/courts/`. Rulings 126 to 128: the
MCP's `courts` corpus is the lane's only source, its own capture is
retired, every document kind is read, and the reading adds model-read
fields. Starts after `fix-support-mcpsource-2` merges and the first
download run has landed the files. Launched headless by the integrator, or
on node2: `cd /home/user/querynzv4 && bin/start-session courts-2 registers/courts`.

Measured 30 October 14:40, during the first download run: the corpus holds
5,611 file pointers, not 4,946 records; it carries crawl noise (a case
page's `++resource++courts-contenttypes.css`, its `sendto_form`, both served
as 75 KB of HTML) and a few records whose delivered bytes do not match the
record's hash (`mcpsource.files` state `caught`, 7 by 14:20). The lane's
recognise step sets both kinds aside by shape, not by name.

```text
You are a build session for QueryNZV4, running as Fable on node2, in the
working copy the launcher made for you, scope registers/courts/. Read
docs/PLAN.md, docs/plan/core.md, registers/courts/spec.md, read.py,
caption.py, suppress.py, pane.md, docs/status/courts.md,
support/mcpsource/spec.md (the records and the files it lands), the
reader contract support/docread, support/profiles, and rulings 126, 127
and 128 (30 October) in docs/decisions/rulings.md. Build them. (1) The
lane's only source is the MCP's courts corpus: its listing is the
corpus's records in the document store (source query-nz, names
courts/<id>), and its documents are the files the pull landed by hash
under the record's url. Retire capture.py and the proposed job
qv4-courts-capture; delete nothing from the store; a document the old
listing holds that the corpus lacks is a line in the catch log, not a
row. The case page carries the court, the case name and the dates the
records lack: read it, and join it to its PDFs by case_slug. (2) Every
kind is read under its own profile, recognised by shape before its
reader is built (profiles before readers): judgment, hearing transcript,
counsel's submission, media release, case page. Measure the recognition
markers on the landed files and record the counts. (3) The reading of
each document keeps the caption's deterministic fields (citation, court,
registry, case numbers, date, judges, parties and roles, numbered
paragraphs, outcome) and adds, read by the text-reader model
(Flash-Next through support.modelclient, one reading per document,
stamped with the model and version, stored by hash): every person and
body the document names with the role the text gives each (party,
counsel, witness, judge, company, agency), counsel for each party, and
a one-line summary. Publish them as rows the links lane can read
(pub.court_people or the like: name as filed, role, document, place),
listed in pane.md; the deterministic fields stay as they are. A page
with no text layer goes through the page reader (profile page-reader)
as the disclosures lane does. (4) Suppression is unchanged: suppress.py
and the ledger apply to every name the reading produces, model-read
names included, on every document of a citation. Jobs: propose
qv4-courts-load (deterministic, nightly after the pull) and
qv4-courts-read (model-profile text-reader, class whenever, one piece
per document without a stored reading) in spec.md; the integrator
installs and queues them. Build in tranches, each with a test that
fails on main; the lane's fast tier green; check.py counts every record
of the corpus as a document read, a document waiting on a reader, or a
catch-log line. No fetch of any court site. Never print a home address
or a suppressed name. Push your branch, raise courts-2, update
docs/status/courts.md.
```

## links-5

MERGED 30 October 12:03 (62b65c0; record in docs/merges/links-5.md).

Build session, Fable, scope `links/`. Ruling 125: the organisation rules run
on every row that names a body, time-aware. Starts after `links-4` merges
(one session on `links/` at a time). Launched headless by the integrator, or
on node2: `cd /home/user/querynzv4 && bin/start-session links-5 links/`.

```text
You are a build session for QueryNZV4, running as Fable on node2, in the
working copy the launcher made for you, scope links/. Read docs/PLAN.md,
docs/plan/core.md, links/spec.md, links/pane.md, docs/status/links.md,
and ruling 125 (30 October) in docs/decisions/rulings.md. Build what it
says: organisation-sole-company@3 and organisation-one-live-company@3
run on every organisation-named row of every people view the lane reads
(shareholders, directors, MPs' interests, charity and society officers,
the Gazette views, local election returns, and the donor and disclosure
rows as now), same grades and reasons as @2. "Alive" is judged on the
row's own date, not today: a body registered on or before that date and
not removed before it counts; one removed before it or registered after
it does not. The date is the donation's return period, the interests
return's date, the officer's appointment, the shareholding's filing. A
row with no date of its own stays near with the reason "undated".
pub.shareholders carries no date today (1,170 organisation-named rows,
none dated in links.rows): leave those near as undated and raise a card
for the companies lane to publish the shareholding's filing date; do
not reach into registers/. Measured today: MPs' interests 2,139 rows
with exactly one body under the name and 239 with one live body of
several; shareholders 76 and 5; society officers 16; charity officers
18; directors 2. Record what the time-aware rule gives, by view, in
your status file, and keep the lane's measurement table. Tests that
fail on main and pass on your branch, including one where the one live
company today was not alive on the row's date. No model, nothing
fetched. Never print a home address or a suppressed name. Push your
branch, raise links-5, update docs/status/links.md; the integrator
queues qv4-links-build after the merge.
```

## links-4

MERGED 30 October 11:18 (b5099ba; record in docs/merges/links-4.md).

Build session, Fable, scope `links/`. Waited on Arthur's word on three queue
items of 30 October (ruling 106's method, each measured with twenty named
pairs): the organisation rules on every row that names a body; bodies under
one name on different registers; an entities view. Launched headless by the
integrator once he has ruled, or on node2:
`cd /home/user/querynzv4 && bin/start-session links-4 links/`.

```text
You are a build session for QueryNZV4, running as Fable on node2, in the
working copy the launcher made for you, scope links/. Read docs/PLAN.md,
docs/plan/core.md, links/spec.md, docs/status/links.md, and in
docs/decisions/rulings.md the rulings of 30 October on the three queue
items named under "## links-4" in docs/briefs/next.md: do what each
ruling says and nothing it refused. (1) If ruled: organisation-sole-
company@3 and organisation-one-live-company@3 run on every organisation-
named row of every people view the lane reads (shareholders, directors,
MPs' interests, charity and society officers, the Gazette views), same
grades and reasons; several live bodies stays near. (2) If ruled: a near
rule body-name@1 over links.bodies, bodies under one name key on
different registers, one star per name as company-name@1 draws it, never
confirmed. (3) If ruled: pub.entities, one row per entity (group id or
lone row ref, kind, the display name by the one ordering every reader
shares, rows, registers, contested, politician), built beside
pub.groups, in pane.md and spec.md. Each with tests that fail on main;
measure each rule's count against the queue item's figures and record
it in your status file. No model, nothing fetched. Never print a home
address or a suppressed name. Push your branch, raise links-4, update
docs/status/links.md; the integrator queues qv4-links-build after the
merge.
```

## site-4

MERGED 30 October 09:30 (8e8321a; record in docs/merges/site-4.md).

Build session, Opus, scope `products/published_site/`. Step 4.5: two causes
the template owns, now that candidate-returns-3 is merged: a Commission
spreadsheet row's citation and evidence text (never "donations $0.00" from
the empty return columns), and the filed party label on a candidacy the
official result prints no party for. Launched headless by the integrator
30 October, or on node2: `cd /home/user/querynzv4 && bin/start-session site-4 products/published_site`.

```text
You are a build session for QueryNZV4, running as Opus on node2, in the
working copy the launcher made for you, scope products/published_site/.
Read docs/PLAN.md, docs/plan/core.md, your module's spec.md,
docs/status/site.md, registers/candidate_returns/pane.md and publish.sql
(the rows with read_from 'commission', merged as candidate-returns-3),
the cards cards/electorate-money-waits-on-the-candidate-returns-lane.md
(its 30 October note) and
cards/an-unregistered-party-label-is-not-on-the-rebuilt-candidacy.md, and
checks/comparison.py where it names "candidate-returns-not-held" and
"unregistered-label-not-on-candidacy". Two causes of step 4.5 are the
template's now. (1) A pub.candidate_return_totals row with read_from
'commission' is the Commission's spreadsheet figure with no return read:
its citation file must say so (its own label, not "EC candidate return
(declaration)") and its evidence text must state the Commission's figures
from the commission_* columns, or none, never "donations $0.00" from the
empty return columns (render.cites). (2) Where the official result prints
no party for a candidacy (51 in 2020, 84 in 2023; pub.candidacies party
null), the person and electorate pages show the label as filed from the
candidate's return or the Commission's row, joined the way the template
already joins returns to candidacies (year, electorate, surname), and say
it is the filed label; a candidacy with neither stays blank, as now.
Measure as site-2 did: build the site in your scratch schema from the
latest frozen day in /home/user/querynzv4-work/live/checks/comparison/days/
and run checks/comparison.py base and branch; record in your status file
what each cause's count was and is, by page kind, and what remains. No
model, no reading, no fetch; nothing on the public site (hard limit 21);
the version-3 fall gate as it is. Each tranche with a test that fails on
main and passes on your branch. Never print a home address or a suppressed
name. Push your branch, raise the merge request site-4 (if the inbox
refuses you, leave it in your scratch folder and say so), update
docs/status/site.md.
```

## flash-next-1

MERGED 30 October 08:16 (838e048; record in docs/merges/flash-next-1.md).

Build session, Opus, scope `support/scheduler/ support/installer/`. Ruling
121 (29 October): Qwen3.8-Flash-Next, served by Radiance on both cards,
replaces Qwen3.6 as node2's text-reader and review model. The container
runs now by hand (`radiance-fn`, port 8060, model `qwen4exp`); a reboot
loses it until this session's unit exists. Read first:
`/home/user/querynzv4-work/scratch/integrator-9d788fb/exp/results.md` and
`start-radiance-ngram-disk.sh` beside it. On node2:
`cd /home/user/querynzv4 && bin/start-session flash-next-1 support/scheduler support/installer`

```text
You are a build session for QueryNZV4, running as Opus on node2, in the
working copy the launcher made for you, scope support/scheduler/ and
support/installer/. Read docs/PLAN.md, docs/plan/core.md, the two
modules' spec.md, support/scheduler/profiles.toml, ruling 121 and
rulings 25 and 79 in docs/decisions/rulings.md, and the integrator's
experiment record at
/home/user/querynzv4-work/scratch/integrator-9d788fb/exp/results.md with
the start script beside it. Build, in tranches each with a test that
fails on main: (1) a user unit qv4-radiance (installed by
support.installer like every qv4- unit, enabled, restarts the container
on boot) that runs Radiance with the recorded shape: image
docker.io/stilldeadcode/radiance:latest, model
/home/user/models/radiance/qwen3.8-next-flash-fp8-iq4r-moe.rad, both
cards (render nodes passed one by one), memlock unlimited, --tp 2, 16
slots, --max-model-len 16384, --max-num-batched-tokens 4096,
--draft-window adaptive, --checkpoint-policy tip-only, --ngram-placement
disk, --host-pool-mib 10240, --gpu-headroom-mib 2560 (the frozen
product's OCR server keeps its room: hard limit 23), port 8060 on
127.0.0.1 only; (2) a profile flash-next in profiles.toml naming its own
server (binary = radiance), both cards as one profile, memory figures
measured with rocm-smi and the host RSS, load_seconds measured;
text-reader and review repoint to it (model name qwen4exp, thinking off
for the reader, on with a budget for review) and the qwen3.6 profiles
leave; the swaps table records the standing load (rows 514 and 515 are
the integrator's by hand); (3) the model client accepts Radiance's
OpenAI-style answers and refuses any other model name; a page of 4k
tokens at 8 streams measured through the worker's own path. Never
touch the frozen product's units or program (limits 19 to 23);
querynz-agent-llm stays stopped and is Arthur's. Ruling 79 still holds
bulk model reading until node1 returns: build and prove, queue no
reading. Push session/flash-next-1, raise the merge request
flash-next-1, write docs/status/flash-next.md.
```

## board-15

MERGED 29 October 19:21 (4bfad35; record in docs/merges/board-15.md).

Build session, Opus, scope `products/board/`. Ruling 122: a permanent
right-hand chat pane on the board. Launched headless by the integrator,
or on node2: `cd /home/user/querynzv4 && bin/start-session board-15 products/board`.

```text
You are a build session for QueryNZV4, running as Opus on node2, in the
working copy the launcher made for you, scope products/board/. Read
docs/PLAN.md, docs/plan/core.md, products/board/spec.md, rulings 80, 86,
100, 102, 111, 121 and 122 in docs/decisions/rulings.md,
products/board/server.py, products/board/panes.py (page, left_pane, CSS),
products/board/search.py (search, row, table), products/board/dossier.py
(gather), products/board/assets.py, support/modelclient/__init__.py and
docs/contracts/model-client.md, and docs/status/board.md. Build ruling
122: a chat pane fixed to the right-hand edge of every page the board
serves (search, use cases, pinned, saved paths, a dossier), always open,
about 26rem wide, sticky, the page's own panes flowing in the width left;
a question box at its foot, the thread above it, the newest turn in view.
The thread lives in the browser (sessionStorage) and is posted whole with
each new question to a new route of the board (`/chat`, JSON over POST,
same origin; the content security policy stays as it is, the page asks
nothing of any other address); the server keeps no table and its log
line carries no question text. The server answers each question by
calling the chat model through support.modelclient.chat (lane
"board-chat"; the address from QV4_CHAT_URL, default
http://127.0.0.1:8060/v1/chat/completions, the model from QV4_CHAT_MODEL,
default qwen4exp; put both in units/qv4-board.service) with tools the
model may call, at most six rounds a question: `registers` (the
catalogue: each register held, its views, its row count), `search` (the
board's own search over the pub views, the same term and register
selection a reader could type, results grouped by register with each
row's view, key and title and the entity groups, cut to a size), `row`
(one row's shown fields, through panes.shown so a suppressed or withheld
value never leaves, its source citation, and its far rows), and
`dossier` (an entity's rows and money as dossier.gather gives them).
Every tool reads on the product reader, pub views only, the columns
catalogue.FIELDS_OF declares and an address only from ADDRESS_COLUMNS,
exactly as the field search does; the one-way test must still pass. The
system prompt tells the model what the estate is, that it answers only
from what the tools return, that every fact is cited as [view:key] and a
line it cannot cite is marked uncited, that it never guesses a link
between people (same name is not the same person), and that it says
plainly when the registers do not hold the answer. The server turns each
[view:key] in the answer into the board's own row link (panes.href with
that one step), so a citation opens the row's pane in the main page;
unknown citations are shown struck with "not a row". When the model
server is down or answers with a different model, the pane says "the
chat model is not running" and nothing else changes; the pane never
blocks the page. Rendering: the dark scheme in panes.CSS, every text
colour at 4.5:1 (panes.contrast_problems must stay clean); a small
chat.js in static/, listed in assets.FILES, no library. Change spec.md:
the jobs line "no capture, no fetch, no model" becomes "no capture, no
fetch; the chat pane alone calls the chat model through
support.modelclient"; record the route, the env names and the tools.
Add check items to `python -m products.board check`: every page carries
the pane; /chat with the model up asked "which registers hold Rank Group
Limited?" answers within 30 s with at least one citation that resolves to
a real published row; with the model unreachable (point the URL at a
closed port) /chat answers 200 with the not-running line; the check
reports "model not running, chat item skipped" rather than failing when
QV4_CHAT_URL answers nothing, so the gate stays green without the model.
Measure the live answer time of three real questions and record them in
your status file. Each tranche with a test that fails on main and passes
on your branch. Never print a home address or a suppressed name. Push
the branch, raise the merge request board-15 (if the inbox refuses you,
leave it in your scratch folder and say so), write docs/status/board.md.
```

## board-14

MERGED 29 October 16:42 (b9c06a5; record in docs/merges/board-14.md).

Build session, Opus, scope `products/board/`, after board-13 merges.
Ruling 119: a fold by hand for organisations. Launched headless by the
integrator, or on node2: `cd /home/user/querynzv4 && bin/start-session board-14 products/board`.

```text
You are a build session for QueryNZV4, running as Opus on node2, in the
working copy the launcher made for you, scope products/board/. Read
docs/PLAN.md, docs/plan/core.md, products/board/spec.md, rulings 105 to
112 and 117 to 119 in docs/decisions/rulings.md, products/board/collapse.py
and docs/status/board.md. Build ruling 119: in the results pane every
organisation entity (a group or a lone row whose view the catalogue
marks "organisation") carries a tick box; the collapse section gains
"collapse the ticked into one", which folds the ticked entities into one
entry for this view, named by the fullest name among them
(collapse.label), the entry saying "collapsed here by hand; not a link"
(collapse.words), its dossier listing the members as the entities they
are (dossier.gather_fold), and the graph drawing the fold as one node
with the same words (collapse.fold_graph). The fold is carried in the
address so the view reopens folded and a saved path (board.paths) keeps
it; a fold is never written anywhere else, never a link, never a
decision, and the board still makes no link by looking. A person entity
has no tick box. Test it on the search "Rank Group": the group Rank
Group Limited, the five RANK GROUP LIMITED shareholder-holder rows and
the Commerce Commission row fold into one node; the twenty other Rank
Group companies stay apart unless ticked. Each tranche with a test that
fails on main and passes on your branch, and the live render measured.
Never print a home address or a suppressed name. Push the branch, raise
the merge request board-14, write docs/status/board.md.
```

## fix-products-board-6

MERGED 29 October 15:53 (e58a404; record in docs/merges/fix-products-board-6.md).

Fix session, Opus, scope `products/board/`. The card
`the-graph-tab-s-fold-is-mislabelled-in-rows-mode-and-cites-the-superseded-filing`
(29 October). On node2: `cd /home/user/querynzv4 && bin/fix products/board`,
then start Claude in the copy it makes and paste:

```text
You are a fix session for QueryNZV4, running as Opus on node2, in the
working copy the launcher made for you, scope products/board/. Read
docs/PLAN.md, docs/plan/core.md, products/board/spec.md, rulings 105 to
112 and 117 to 120 in docs/decisions/rulings.md, and the card
cards/the-graph-tab-s-fold-is-mislabelled-in-rows-mode-and-cites-the-superseded-filing.md.
Fix its three faults: (1) is overtaken by ruling 120: the graph has one
state, entities; the rows mode, its switch and its address value leave
(an address naming it opens the entities graph), and the fold's label
and colour come from the whole fold, not the member that sorts first; (2) when causes merge into one
edge, cite the latest filing, never one marked not in the latest file;
(3) the "N more match: narrow the search" note is not shown when every
matching row is drawn inside a fold. And (4), ruling 118: drop the
criterion "a shared full name, with middle names" from the collapse
section (collapse.CRITERIA, search.COLLAPSE_CHOICES, their tests); an
address carrying `cl=full` is read without it. Each with a test that fails on main
and passes on your branch, and the live render of the search "Arthur
Falls" with "a shared first and last name" ticked, measured. Never print
a home address or a suppressed name. Push the branch, raise the merge
request fix-products-board-6, close the card in it.
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

**A column the gate publishes is catalogued and tested at the next merge
(integrator, 23 October).** The gate's full tier runs the real-data tests
(`products/board/tests/test_real.py`, `products/scan/tests/test_templates_real.py`)
against the live database before the gate's staging step publishes the
branch's lane. So a catalogue field or a test that names a column the branch
adds to a published view fails that gate with `UndefinedColumn`
(`fix-registers-iwi-directory-1`, second sitting: `settlement_key`). Merge the
lane first; catalogue the column and repoint the test on the next integrate
branch, as with a new view.
