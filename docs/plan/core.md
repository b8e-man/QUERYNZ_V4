## Read this first

### Who you are

You are a Fable agent running in Claude Code on node2, started by Arthur. You have not seen the two days of discussion that produced this plan. This document is your whole brief. It is self-contained on purpose: do not go looking for another plan.

The old repository carries its own orientation file (`CLAUDE.md`), doctrine and operating method. Those were written for a different way of working: one queue at a time, one muster, Arthur ruling each step. **Where they conflict with this plan, this plan wins.** The exception is the section "Hard limits" below, which nothing overrides.

**Which copy of this plan is the master.** From the day it is saved, `docs/PLAN.md` in the new repository is the master copy. Once step 1.1 has split it, the files under `docs/plan/` are the master and `docs/PLAN.md` is their index. Either way it changes only by Arthur's ruling, recorded in `docs/decisions/rulings.md`, and the integrator makes the edit. The document it was first written in is a snapshot and may fall behind.

### Who Arthur is

Arthur owns the project and is its builder. His own words: "I never review apart from setup. I am not systemically in the loop. I am a builder."

- **He rules on design, sets things up, and starts each session.** He does not review data, approve merges or fire jobs.
- **Write to him in plain language.** Define any technical term the first time. Keep it short. He often uses voice input, so read his messages for meaning, not spelling.
- **Questions go in a decision queue.** Batch them, tie each to what it blocks, and carry on with unblocked work. Do not stop a session to wait for an answer you can work around.
- **He is interviewed, not surveyed.** When a decision is his, give your recommendation and the reason with it.

### What you may decide, and what you may not

| Yours | Arthur's |
| --- | --- |
| The order of work inside a step | A change to the design or to this plan |
| Code structure, names, tests | Anything put on the public site |
| Anything reversible inside the new repository and its scratch data | Deleting anything that cannot be regenerated |
| Installing, enabling, stopping and placing the new estate's scheduled jobs on both boxes | Any change to the old estate beyond the three this plan names: stopping old jobs outside the carve-out, the freeze commits, and rotating credentials under track H |
| Raising, closing and dropping cards | An emergency fix to the frozen repository |
| Splitting a doubtful link (through the review agent) | Hardware, credentials, privileged setup, letters to outside bodies |
| Going ahead on the stated default when a queued decision has one | The rules that confirm a link between two person rows |

**When a decision is Arthur's and he has not answered:** every decision in the queue carries a default. Build on the default, build so the choice is a setting and not a rewrite, and say in your end-of-session note that you did. Only a decision marked "no default" stops the work it blocks.

## How the work runs

These are the new operating rules. They replace the old muster method and are a draft Arthur may change. Follow them until he does.

### Keeping the work quick

Ruling 54. The old estate was slow to work on for four reasons: a session read hundreds of kilobytes before it started; every prompt, even a question, ran the full card ceremony; the tests and rebuilds behind a change took from 25 to 90 minutes; and the modules were large enough that any change meant a lot of reading. Seven rules keep the new estate from going the same way.

1. **Three weights of session.** A question is not a card. See "Three weights of session".
2. **Required reading has a limit.** See "What to read, and how much", in the index.
3. **Nothing that grows is read whole.** Cards, lessons and decisions are one file each, and a search returns a handful. A status file is overwritten and kept to a page. There is no day-log.
4. **Two tiers of checks.** A session runs the fast tier on a small sample. The integrator runs the full tier. See "Two tiers of checks".
5. **Rebuild only what changed.** This is register rule 10, and it holds for links, groups and search tables too.
6. **Questions about the data are answered from the published tables and the board,** through a login that can only read, with a time limit and a row limit on every query.
7. **It is measured.** Every prompt is timed, and the checks board shows the typical and the worst wait for each weight over the last seven days.

| Measure | Starting target |
| --- | --- |
| A question session, from prompt to answer | Two minutes, typically |
| A fix session, from prompt to merge request | Twenty minutes, typically |
| The fast tier for one module | 60 seconds |
| The fast tier for the whole repository | Five minutes |
| Filling a session's sample | Two minutes for all of it; seconds for one lane |
| Required reading | Within its limits |

The targets are guesses. After the first week of timings the integrator proposes measured ones in the decision queue. A missed target is recorded and does not stop the work. Once a week the integrator looks at the misses, and at any module past about 3,000 lines, and each is fixed, accepted or dropped. The old `registers` package reached 14,800 lines and `ops` 47,500.

**The tools behind these rules are built in step 1b.** Until it closes there is one tier of checks, the merge gate of step 1.1, and there are no question or fix sessions.

**Speed never buys a hard limit.** A question session obeys every one of them, and no check is dropped from the full tier to make a merge faster.

### Starting a session

- **Arthur starts every session on node2.** A session does not start another session.
- **One session, one working copy, one task, one brief.** A working copy (git calls it a worktree) is a second checkout of the same repository in its own folder on its own branch, so several sessions edit at once without colliding.
- **A launcher makes the working copy.** `bin/start-session <name> <folder> [more folders]` creates the working copy under `/home/user/querynzv4-work/<name>`, creates its branch, writes its scope file listing those folders, and prints the folder to start in and the brief to paste. Arthur runs it, changes into that folder, and starts Claude there in the mode that accepts file edits without asking. The launcher is built in step 1.1.
- **The scope hook is the fence.** It reads the scope file in the working copy and refuses an edit outside the folders named there. Always allowed: the session's own files in `cards/`, `lessons/`, `docs/status/`, `docs/decisions/queue/` and `merge-requests/`. Generated files are never allowed. **No scope file means refuse everything.** The integrator and the founding sessions get a scope file that names the whole repository. Outside the repository, a session may write only under its scratch folder; a founding or integrator session also writes Claude Code's memory folder for the checkout it runs in (ruling 103).
- **Sessions run on a list of allowed commands** in `.claude/settings.json`, so an unattended session neither stalls on prompts nor runs with permissions bypassed. The list is written out in step 1.1.
- **Three build sessions at once, plus one integrator.** Track sessions count toward the three. Long machine jobs running in the scheduler do not. Raise the number once merges have stayed clean for a week.
- **Contracts first, then fan out.** Step 1 is done by one session at a time. The integrator starts when step 1 closes. Tracks may run beside steps 2 and 3. Lanes fan out at step 4.

**Three additions to the fence.** The launcher writes the session's name and weight into the scope file, and the hooks read them. `bin/start-session --main founding` and `--main integrator` write the whole-repository scope file in the main checkout; nothing else may. And whatever a scope file says, only those two kinds of session may edit `.claude/`, `bin/`, `docs/plan/`, the orientation file or a scope file.

### Three weights of session

The launcher sets a weight, and the weight sets what a session may change, what it reads and what it must record. The old estate had only the heaviest.

| Weight | For | Started with | May change | Must record | Ends with |
| --- | --- | --- | --- | --- | --- |
| Question | Arthur asking something: what do we hold, why is this figure what it is, where is that code, what would this take | `bin/ask` | Nothing | Nothing | Its answer |
| Fix | A small change inside one module: a bug, a wording, a setting, a test | `bin/fix <module folder>` | That one module | Its merge request, which is the whole record. A lesson if it taught one | The fast tier passed and the merge request named |
| Build | A step, a lane, a template, a track | `bin/start-session <name> <folder> [more folders]` | The folders in its brief | Everything under "Closing a piece of work" | The end-of-session note |

- **A question session cannot change anything, and that is held three ways.** The hooks refuse every edit inside the repository and every command that commits, pushes, merges, installs or controls a job. The only database login it is given can only read. And it runs in a throwaway copy of the main line. It needs no brief: Arthur asks.
- **It answers from what is published first:** the published tables, the board, `docs/status.md`, the card board and the module specs. It reads code, or a lane's inner tables, only when the question is about them. A question about data the new estate does not hold yet goes to a build session: the old databases hold home addresses, so a question session is given no login to them.
- **A session looks at data through `bin/q`,** which uses a read-only login, stops at 30 seconds and returns at most 200 rows. `bin/q --long` allows ten minutes, one such query at a time across all sessions; it writes the full result to the session's scratch folder and shows the first 200 rows. Fix and build sessions use it too whenever they only want to look.
- **The session reader is never granted the tables that hold a person's home address, or the seal.** Hard limit 11 binds every weight alike.
- **A fault a question session finds** goes as a note into the inbox outside git, and the integrator files it as a card. When a question turns into work, the session gives Arthur the one line that starts a fix or build session. It does not do the work.
- **A fix session gets its own working copy and branch,** scoped to one module folder. `bin/fix` refuses a folder that is not a module, and one a build session already holds; that fix goes to the session holding it. Its brief is Arthur's own sentence. A fix that grows past one module stops and becomes a card.
- **Question and fix sessions do not count toward the three build sessions.** Question sessions start once step 1b closes, and fix sessions once the integrator exists.

### Picking up where another session stopped

A step is larger than one session's memory, and a session can die mid-task.

- **Each session keeps its own status file,** `docs/status/<session name>.md`: what is done, what is half-done and exactly how far, what is next. The integrator rolls these up into `docs/status.md`, which is the single place that says where the whole build stands. During step 1, with no integrator, the founding session writes `docs/status.md` itself.
- **Every brief begins the same way:** read `docs/PLAN.md`, then `docs/status.md` and your own status file if it exists, and continue where it stops.
- **Before any change to live jobs, write the intended change in your status file first,** and tick it off after. A session that dies between leaves a trail.
- **A question for Arthur is one small file** in `docs/decisions/queue/`, so parallel sessions never edit the same file. The integrator rolls them up into `docs/decisions/queue.md`. Arthur also hears each question in the end-of-session note, which is what he actually reads.
- **`docs/briefs/next.md` holds the next sessions to start,** each fully filled in: the launcher command with its name and folders, the model, and the brief. The integrator keeps it current. Arthur starts sessions from there.

**A status file says where things stand now, and nothing else.** It is overwritten at each close and stays under 3 KB; the reading-limit check holds this too. What happened is in the cards, the lessons and the commit messages. And "read `docs/PLAN.md`" in a brief means the whole document only for the first founding session; after the split it is the index, which names the files to read.

### Merging

- **During step 1 there is no separate integrator.** The founding session runs the merge gate itself before every merge to the main line.
- **From the close of step 1 one session, always Fable, is the integrator** and owns the main line. It is needed that early because tracks run beside steps 2 and 3.
- **How a build session hands over:** it pushes its branch and adds a file to `merge-requests/` naming the branch and what it claims. The integrator works through that folder, runs the gate, merges or refuses, and writes the result into the same file. A refused session reads the result when Arthur next starts it.
- **The merge gate** is one command, run by the integrator: the full tier of checks at a merge, set out under "Two tiers of checks". It refuses on any failure of what it runs. The old estate checked its documents on a push but did not run its tests; this is the fix.
- **Generated files are rebuilt by the integrator at the merge and edited by nobody:** the card board, the lessons index, the job manifest, `docs/status.md`, `docs/decisions/queue.md`.
- **A contract from step 1 is changed only by the integrator,** on a merge request that says why. A session blocked by another module raises a blocker card and a merge request; it does not reach across the fence.

**`merge-requests/` is one shared folder outside git,** `/home/user/querynzv4-work/inbox/merge-requests/`, linked into every working copy by the launcher. So the integrator sees a request the moment it is written, and the session sees the result. The integrator commits a copy of each finished request under `docs/merges/`, so git keeps the record.

**The integrator is a role, not one long session.** Arthur starts a fresh one, with `bin/start-session --main integrator`, for each batch of requests, so its context stays small. Beyond its brief it handles a fix request like any other, refills the sample's published tables after each merge, files the notes question sessions leave in the inbox, removes a working copy once its last request is merged, and once a week proposes what to do about missed targets.

The integrator's brief:

```text
You are the integrator for QueryNZV4, running as Fable on node2 in the
main checkout at /home/user/querynzv4. Read docs/PLAN.md, then
docs/status.md. Work through merge-requests/: run the merge gate on
each branch, merge what passes, refuse what fails and write why into
its file. Load each merged lane's real tables and install its jobs.
Rebuild the card board, the lessons index and the job manifest. Keep
docs/status.md and docs/briefs/next.md current. Run the daily
comparison with the frozen site once step 4.5 begins. Finish by
telling Arthur what merged, what was refused, what waits on him, and
which briefs in docs/briefs/next.md to start.
```

### Two tiers of checks

A session must be able to find out within a minute whether its change works. The old estate had one tier: 585 test files, with rebuilds of 40 to 90 minutes behind them.

| Tier | Holds | Runs against | Run by |
| --- | --- | --- | --- |
| Fast | Unit and contract tests; the one-way import test; the spec check; the reading-limit check; each module's own tests | The sample and stored readings. No graphics card, no network, no full table | Any fix or build session, as often as it likes |
| Full, at a merge: the merge gate | The fast tier for the whole repository; every test marked slow; the outside check and product checks of each module the branch touches | The modules the branch touches, loaded into a staging schema of the real database and moved into place on a pass. A long load runs as a job | The integrator. During step 1, the founding session |
| Full, nightly | Everything: every outside check, every product check, the comparisons | The real database | The checks board. A failure raises a card or an alarm; it does not block a merge |

- **A session never waits on the full tier.** It raises its merge request and carries on; the result comes back in the same file. A source that is down, or a difference from the frozen site, never blocks an unrelated merge.
- **A test that takes more than five seconds, or needs a graphics card, the network or a full table, is marked slow,** and the fast tier fails on any unmarked test that does. The 60-second and five-minute figures are targets; the tier fails outright only at three times its target.
- **The sample is a fixed list of documents and source keys.** Each module keeps its own list in its own folder, as hashes and keys only, never bytes or rows, so no personal data enters git. A lane lists what its tests need, its known hard cases among them.
- **Each session fills its own copy.** The fast tier loads the sample through the session's own branch into the session's scratch schema in `querynz_v4_sample`, so sessions on different branches cannot disturb each other. What a module reads from other modules comes from the published tables there, which the integrator refills from the main line at each merge.
- **Stored readings.** Every model reading is kept in the document store, keyed by the document's hash, the model and its settings (ruling 50). The fast tier replays them and never calls a model. A missing reading fails the test and names the document, and the session asks for it as a re-read job (step 2.14).
- **The sample is for building, never for measuring.** No figure given to Arthur, put on a known-limits page or used in a comparison comes from it. A sample of neighbouring rows once said 96.6% where the truth was 51.1%.

### What is live, and who may touch it

Live means anything outside a session's own scratch schema, and any installed job.

| Who | May change live things |
| --- | --- |
| The founding session (step 1) | Yes: it sets up the database and the repository, and installs the first jobs |
| The scheduler session (step 2) | The scheduler's own tables and jobs |
| The trial session (step 3) | Model files and model profiles, through the installer and the scheduler |
| Track sessions | Their own jobs, with the `qv4-` prefix, within hard limits 22 and 23 |
| Every other build session | No. It works in its scratch schema. The integrator loads its real tables and installs its jobs after the merge |
| A question or fix session | No. A question session changes nothing. A fix session works in its scratch schema, like any build session |

### Shared things on the boxes

- **One database server, four graphics cards.** Those are the real limits, not the repository.
- **The new estate has its own database,** `querynz_v4`, beside the old three, on the same server that feeds the frozen site. So the new estate is a guest there until the election.
- **Its login has a cap on connections and a time limit on every query,** set in step 0. An old job once took 97 of the server's 100 connections.
- **The old databases are read through the standby, with a read-only login, and never written to.** No old database address is ever pointed at the primary by the new estate, and no old test that writes a row is run against an old database.
- **Before 7 November, bulk loading into the new database stays small:** lane loads are fine; the Papers Past ingest stops after its hundred-thousand batch. Larger loads swell the change log the standby must replay and the disk both share. After the election, or on Arthur's word, the limit lifts.
- **After step 2, no session starts a model server by hand.** Every use of a graphics card goes through the scheduler.
- **Every scheduled job has:** a deadline, a time limit on its database queries, a record of each run, an alarm when it fails, and the same job file installed on both boxes by one installer. A job killed at its deadline otherwise leaves its query running.

### One short spec per module

Checked at every merge. Five lines:

1. What it owns (tables, files).
2. What it reads.
3. What it publishes.
4. Its one check against the outside world.
5. Its scheduled jobs.

### Cards

Each card is one small file in `cards/`. The card board is generated from them. There are three kinds with three fates.

| Kind | What happens to it |
| --- | --- |
| Blocker: stops the step in hand | Fixed now |
| Finding: a gap or failure met in a product test | Carded against the use case and not worked. At the next checkpoint it is fixed, accepted, or dropped |
| Idea | Goes to a parking list, not the board |

A finding that is accepted leaves the board and becomes a line on that product's known-limits page. So every card is in a session, on a limits page, or gone. This is how the backlog is kept from piling up; do not let it slow the work.

**The old cards are not carried over.** All 564 were read for this plan and the durable ones are in the reference sections. Read an old card for context when you touch its area, with three cautions: many were corrected by their own later text, so trust a card's last figure and not its first; several rest on a premise the card itself later found false; anything quoting 2014, 2020 or "the eight parties" predates the 2019 window and the seven-party scope.

### Lessons

The lessons flow is kept, because lessons filed in dated records were being re-learned weeks apart.

- **Before building or changing anything,** search the lessons for the area you are about to touch. A build session searches again if days have passed, because the set moves. A fix session searches once. A question session does not.
- **The search returns the few closest rules, never whole sections:** at most eight, one line each, with the file to open. The old tool also printed every claim in each section a path pointed at, up to 160 KB at a time. Do not carry that across. The search reads the first line of every lesson file in the main checkout, and the old estate's one-line index, so a merged lesson is found at once, with no index to wait for. Open a rule only when its line looks relevant.
- **Before closing a piece of work,** write what it taught as one new file in `lessons/`, tagged with the area where it bites, or write "nothing new" in the card or merge request and mean it. A lesson's first line is the rule in one sentence, because that line is what the search shows.
- **A thin search result means search again in your own words,** never "there is no lesson".
- The old lessons come across in step 1 as the starting set, read-only, searched together with the new ones.

### Closing a piece of work

Record it then and there: the card closed, the lesson filed, your own status file (in step 1, `docs/status.md`) updated, the branch pushed, the merge request raised. Then start the next. A session's end adds nothing that was not already recorded.

**Nothing is written twice, and no file grows with every close.** There is no day-log. The card, the lesson and the commit message are the record; the status file says only where things stand now. A file that every close adds to becomes a file every session has to read: the old estate's day-log reached 1.6 MB in one month.

### Checkpoints

When a product is built, work on it stops and its checklist runs. The checklist for a product is: its own tests; the publication rules in this plan, each checked on real output; the question its use case answers, asked of ten real subjects and the answers read against the source documents; and, where the old estate has a requirements list for that use case (`data-layer/docs/USE_CASE_REQUIREMENTS.md`), that list. Each failure becomes a finding card. Each finding is then fixed, accepted onto the known-limits page, or dropped. The purpose is a working estate whose limits are understood, not a perfect one.

### The decision queue and the rulings

- **`docs/decisions/queue.md`:** each open question for Arthur, with your recommendation, its default, what it blocks, and what carries on meanwhile.
- **`docs/decisions/rulings.md`:** each answer, numbered on from 55, with the date and his words.
- **At the end of every build or integrator session, tell Arthur in a few plain lines:** what closed, what was carded, what you went ahead with on a default, what is waiting on him, and the exact launcher command and brief for the session to start next. From 1 November, add one line on whether the director addresses have been sealed.

