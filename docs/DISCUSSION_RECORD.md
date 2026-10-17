# Use Cases and Source Gaps

Oct 10, 2026 · @arthur falls

Four services that New Zealand firms already pay for could guide the estate alongside Follow the Money. Tender and award intelligence has the fewest source gaps and no regulated ground. What is held is taken from the repository as at the morning of 10 October 2026.

## Path-critical points

Three points govern everything below. Where anything else in this document conflicts with them, they win.

1. **Follow the Money does not stop, and the build goes toward it first.** (Arthur, 10 October.) The public site keeps its daily release throughout. Every new module is built for Follow the Money first and proven on Follow the Money's own data before any other use case draws on it. The detail is under [Building toward Follow the Money first](#building-toward-follow-the-money-first).
2. **Rebuild the shape, move the scar tissue, and make the cards account for every difference.** Pieces whose problem is their structure are rebuilt with the old code as reference. Pieces whose value is their accumulated fixes are moved as they are. A rebuilt piece replaces the old one only when every row where the two disagree is explained by a named card. The detail is under [Rebuild or move](#rebuild-or-move).
3. **Every use case is an independent service that can be exported whole.** (Arthur, 10 October.) Each can run apart from the estate. The limit is that code and state are not heavily duplicated: the estate stays the one source, and a product can be exported as a complete service to another environment. The detail is under [Products as exportable services](#products-as-exportable-services).

## Rulings, 10 October evening

Given by Arthur after the review below. They sit beside the path-critical points and override anything further down that conflicts.

1. **This is a capability build-out.** Plan as if customers exist for every use case. Billing, accounts and metering are left out.
2. **Legal work comes after the build and before any service is sold.** It does not shape the plan.
3. **The partner model is an enhancement, not the frame.** For a partner, the design follows their needs. Partners were always meant to supply the criteria that guide the estate; in this plan the use cases supply them.
4. **Order and parallel work are free.** The muster rules and the operating method were written for a different way of working. New operating rules and principles will be written for this one, harvesting what still makes sense.
5. **The ten August use cases join the plan.** The state of the earlier work does not matter: plan them, then harvest the useful parts.
6. **Parked and retired work is a resource to draw on.**
7. **Press is demoted entirely for now.** It comes back later.

Added later the same evening:

8. **Keyword search is back for journalism other than Papers Past.**
9. **History search is a use case.** It searches Papers Past deeply, with every tool available.
10. **The capture rules are abandoned.** Collection is judged on legality and politeness, not on inferred intent. See "The capture test" below.
11. **NZME is to be thought through on what is legal.** See "NZME: what is legal" below.

12) **NZME is dropped.** The NZ Herald and the other NZME mastheads are out of the build. I have read "drop NZ Herald" as all of NZME, because every masthead sits under the same terms.
13) **The Papers Past archive is on the boxes.** As it is ingested, each catch is to be identified exactly where it happens, as it is met.

## Rulings, 11 October

14. **Work is parallelised as far as it can be.** The lessons flow and the lessons already learned are kept. The card board is kept. The backlog is not allowed to pile up again, but not at the cost of the work.
15. **Follow the Money is the first thing recreated in the new estate.** After it, the order is mine.
16. **Each product is tested when it is built.** Gaps and failures are carded, not necessarily fixed. The purpose is a working estate whose limits are understood; that is what the use cases are for.
17. **The live Follow the Money is frozen.** Nothing changes. It is kept as an exported, working product.
18. **The held legal sources are in.** They were held because they need effective extraction profiles and document extraction, not because they were unwanted. Researching legal document extraction and trying newer page-reading models are part of the work. Easiest first.
19. **Company monitoring goes as deep as the business-number interface allows.** The monthly import stays. On top of it, an entity is polled whenever a product looks it up, and the estate updates itself from the differences found.
20. **The Papers Past meaning index is stored on the hard disks for now.**
21. **The off-site copy stores changes, with a weekly checkpoint.** It has to be efficient.
22. **Four cards, switched between jobs by the scheduler.** Embedding shares them with everything else. Whether one card stays free for answering queries is undecided.
23. **Papers Past is read whole.** The coverage gap in both indexes is to be fixed.
24. **The build method for the full meaning index is agreed** as set out under history search below.

The gates, hooks and the choice of repository are to be settled by interview.

### Is Follow the Money exported and complete?

- **Exported: yes.** The public site is a directory of files on an outside host, with search running in the reader's browser and one small hosted function that takes feedback. Nothing on the public side talks to the boxes. With both boxes off, the site stays up as it was at its last release.
- **Complete as a published product: mostly.** It publishes ten kinds of page data. Holes already on record: the donor list is cut at 1,500 before names are folded, so a donor can lose its page; a return total is held for under half the party-years since 2019; the announced-candidates tier is empty.
- **Not a complete service in the sense of path-critical point 3.** What is exported is the output. The machinery that makes it lives inside the estate and reaches into the registers' internals, so it could not be lifted out and run elsewhere by itself today.
- **One thing inside the freeze to confirm.** I have read it as: the code and the chain behind it are frozen, and the daily release keeps refreshing the data, because declarations keep arriving before the election. If the daily release should stop too, say so.

The frozen product is also the reference: the rebuilt Follow the Money has to reproduce it.

### How the work is structured (proposal)

1. **Contracts first, then fan out.** Parallel work only holds when the seams are fixed. A short first stretch, done by one session, writes the shared keys, the shape of a register row, and the published views, and builds one thin slice of Follow the Money end to end. Then sessions fan out.
2. **One session, one worktree, one module, one brief.** A worktree is a second checkout of the same repository in its own folder on its own branch, so sessions edit at once without colliding. The existing scope hook, which refuses edits outside a session's brief, becomes the fence between them.
3. **Each lane owns its own tables and its own rebuild.** No two sessions land through one shared wipe-and-reload.
4. **One integrator.** Branches merge to the main line through one place that runs every test and the product checks, and refuses a red merge. This is the missing run-on-every-change.
5. **Generated files are rebuilt at the merge, never edited on a branch.** The lessons index, the board and the card register all conflict if two branches touch them. Each card and each lesson becomes its own small file; the lists are generated.
6. **The boxes are the real limit, not the repository.** There is one database and there are four cards. Sessions work in their own scratch schema; the scheduler queues the cards; only the integrator touches live tables and scheduled jobs.
7. **Product checkpoints.** When a product is rebuilt, work stops, its checklist runs, and the findings are carded.
8. **A decision queue for Arthur.** Questions are batched, each tied to what it blocks. Sessions carry on with unblocked work.

**Keeping the backlog from piling up, without the two-closures rule.** Three kinds of card with three fates:

| Kind | What happens to it |
| --- | --- |
| Blocker: stops the product step in hand | Fixed now |
| Finding: a gap or failure met in a product test | Carded against the use case and not worked. At each checkpoint it is fixed, accepted, or dropped |
| Idea | Goes to a parking list, not the board |

A finding that is accepted leaves the board and becomes a line on that product's known-limits page. So every card is in a session, on a limits page, or gone. The board shows work; the limits pages show what the estate cannot do.

**Kept from the old method:** lessons checked before building and recorded at the close; the card board; the daily checks board; the safety hook; the scope hook; the catch log.

### What the first build tasks need from Arthur

The six identity measurements, the live row counts and the first Papers Past batch need nothing from you. They do need a session on the boxes; this one cannot reach them. The answer set needs one thing: a sample of its labelled pairs for you to check, once.

### Interview, round one (11 October)

25. **A new repository for the new estate.** The current repository stays exactly as it is, running the frozen Follow the Money. Old code is harvested across piece by piece.
26. **The two-closures rule is dropped.** The three kinds of card replace it.
27. **The four questions shrink to one short spec per module** that must stay true, checked at the merge.

Still open from round one: "quarantine, never delete" and the safety hook. My view, given when asked: keep the safety hook unchanged, and split the data rule three ways.

| Class | Examples | Rule |
| --- | --- | --- |
| Cannot be regenerated | Captured source documents, judgments, ledgers, corrections | Never deleted. Withdrawn or quarantined, as now |
| Can be regenerated | Views, indexes, scratch schemas, build output | Deleted freely. A lane wiping and reloading its own tables is the design |
| Quarantined | Anything set aside | Kept for a fixed period, then removable on Arthur's word, with a logged line |

### The boxes, as the repository records them

Reflected back for correction. Probed figures are from 7 October; the rest are older and marked.

|  | node1 | node2 |
| --- | --- | --- |
| Role | Primary database, holding the floating address. Database-side jobs: the Gazette chain, party feed, charities, the nightly meaning-index build | The factory: every capture job, the conductor API on 8100, Follow the Money on 8300, the publisher on 8301, the daily board, the off-site push, and the standby database |
| Processor | 16 physical cores, 32 threads | The same |
| Memory | 62.3 GB | 62 GB class; recorded as tight, with the API holding a 27 GB index in memory |
| Graphics cards | Two, 34.2 GB each. Nearly idle: 3.5 GB and 2.0 GB in use when probed | Two, 34.2 GB each. Both nearly full: 28.2 GB and 25.8 GB in use |
| What the cards run | The page reader, and the embedding servers when a bulk run is started by hand. Its chat-model jobs were retired on 8 September | Card 0: the agent model, 2 slots of 50,000 tokens. Card 1: the reviewer model, 8 slots of 16,384 tokens. Both run the same 35-billion-parameter Qwen model |
| Disks | Two hard disks of 3.6 TB (`/mnt/hdd1` with 478 GB used on 19 September, `/mnt/hdd2`), one fast disk at `/mnt/ssd`, plus the system disk | One hard disk at `/mnt/hdd`, one fast disk at `/mnt/ssd`, plus the system disk. Sizes not recorded |
| Database files | Change-log archive on `/mnt/hdd1`, kept 14 days | Standby's change log on `/mnt/hdd`, with a mirror of node1's archive |

**Shared.**

- **System:** Fedora 44. Every job is a user-level scheduled job installed by copy, with a manifest saying which box runs it. 75 jobs on record.
- **Network:** the two boxes are joined by a 10-gigabit link (10.0.0.1 and 10.0.0.2, with the database's floating address at 10.0.0.10). Each box reaches the internet over Wi-Fi, behind a satellite connection that allows outbound traffic only. A private overlay network admits the two apps.
- **Models:** one chat model (Qwen 3.6, 35B), one embedding model (bge-m3, which runs on the processor for the steady trickle and for search queries), one page reader (GLM-OCR, one per box, capped at 6 GB of memory).
- **Databases:** three on one server: the graph, the news corpus and the registers. The nightly off-site dump is 368 GB. A rehearsed restore took 17 minutes for the registers and 315 minutes for the graph.
- **Scheduler:** the job registry, queueing rules, executor and run history are built. Nothing runs the scheduler on a clock yet.

**Not found in the repository:** the make and model of the cards and processors, the size of node2's disks and of both fast disks, free space today, and the database version. The cards are measured with AMD's tool, and an earlier note of mine called them Radeon R9700s; I could not confirm that from the files.

**A consequence of demoting press.** Both of node2's cards are held by the press graph's reviewing and crawling jobs; the reviewer alone was 77% of all model calls. Follow the Money uses no press. Stopping those jobs would free both cards for embedding and for trying new page-reading models.

**Corrections and additions from Arthur, 11 October.** The cards are Radeon R9700s. node2 has one 2 TB fast disk and two 4 TB hard disks, one of which is inaccessible. A spare 64 GB of memory will upgrade one machine. From the failover runbook: both databases run PostgreSQL 18.3, and at the time of the August drill the graph was 211 GB, the news corpus 25 GB and the registers 21 GB.

### Interview, round two (11 October)

28. **Stopping the press-graph jobs is a step in the plan**, not something done now. News capture keeps running for keyword search.
29. **The three-way split of the delete rule is agreed**, and the safety hook stays as it is.
30. **Build sessions run on node2, each in its own worktree.** Three at once plus the integrator to start, raised once merges stay clean.
31. **The two boxes are peers, and one service schedules every job.** Set out below.

## The two boxes as peers, and the scheduler

### The requirement, as Arthur gave it

- **Either box can take over from the other** after an unscheduled shutdown, in either direction, and the failover machinery works for both.
- **Everything is held on both:** code, services, data.
- **Both boxes do work all the time.** Neither is a spare.
- **The two stay as current with each other as possible.** When one comes back, it catches up.
- **Every task is scheduled onto a card or onto the processor by one service.** Jobs order themselves by need, and the hardware picks them up in that order. With four cards, four work; with two, two work.
- **Each card is configured for the job it is doing:** which model is loaded and with what settings. A card full of a chat model's context is not also handed a page-reading model. Anything run in parallel on a card is judged against what that card is already doing.

### What to call it

A scheduler. It has three parts: a registry of what each kind of job needs, a planner that decides who gets what, and a worker on each box that does it. The repository already calls this the fleet control plane.

### What exists and what is missing

| Part | Exists | Missing |
| --- | --- | --- |
| What each job needs from a card | A registry with model, context, slots, measured memory and priority per job type | Processor-only jobs are not in it; they are fixed timers |
| Rules for sharing a card | Five written and tested: release when the queue empties; no interruption within a slice; drain, never kill; priority order in turns | Never run against a real queue |
| Changing what a card holds | An executor that swaps a card's model and settings reversibly, dry-run by default | Nothing calls it on a clock |
| Job history | A run ledger; five jobs record their runs | The rest do not |
| Knowing queue depth | Nothing | Needed before the planner can decide |
| Seeing both boxes | The probe reads node2 only | node1's cards and load |
| Taking over a dead box's jobs | A lease-and-token pattern exists in the press extraction queue | Not applied to jobs in general |
| Same code on both | node1 pulls from node2 every 15 minutes | Works one way only; node2 is the author |
| Same jobs on both | Job files are installed on both and enabled on one | Enabling on the survivor is a hand step |
| Database takeover | Primary and standby, a floating address, one drill in August | By design it is run by hand: about 45 minutes, with every privileged line typed by Arthur |
| Files held on both | The database is copied continuously; a few things are mirrored | Captured documents, the Papers Past archive, model files and indexes have no general two-way copy |

### How I would build it

1. **One job queue, kept in the database**, so it moves with the database when a box is lost.
2. **A worker on each box** that reports what it has (cards, processor, memory) and pulls the most urgent job it can run. Losing a box just means one worker stops pulling.
3. **Every job declares what it needs:** a card profile or processor only, how much memory, and whether it can share.
4. **A card holds one profile at a time.** A profile is a model plus its settings. Jobs that match the loaded profile run together up to its stated slots; a job needing a different profile waits for a switch, and the planner weighs the cost of switching.
5. **Leases.** A running job holds a lease it must keep renewing. If its box dies the lease lapses and the other worker takes the job. Jobs are cut into resumable pieces so little is redone.
6. **Standing services are jobs too.** The apps and model servers carry a wanted count and a priority, so the survivor starts what is missing in order of importance, within what one box can carry.
7. **Everything on both.** One installer for code, job files, model files and credentials on both boxes, and a two-way copy for captured documents, archives and index files.
8. **A box that returns rejoins:** it becomes the database standby, catches up its files, and its worker starts pulling again.

I would extend the existing fleet service to do this, not bring in a general cluster manager. Two boxes and four cards with model-specific card settings is a narrow problem, and the existing registry, rules, executor and ledger are the right skeleton.

### Decisions this needs

- [ ] **Automatic database takeover needs a third voter.** With two boxes, neither can tell "the other died" from "the link between us dropped". If both decide they are the primary, committed data is lost; the standing design refuses automatic takeover for exactly this reason. A small third machine that only votes removes the problem. Any always-on computer will do, since it holds no data; it needs its own network path to each box. Parked by Arthur on 11 October to come back to. Without one, takeover stays a single command a person runs, with everything else automatic.
- [ ] **How current is current.** Copying each write to the standby before confirming it loses nothing but stalls the primary when the standby is down. Copying just after loses the last moments on a crash. Since everything above capture can be regenerated, I would copy just after.
- [ ] **Where the spare memory goes.** If either box must carry the essentials alone, the smaller box sets the limit, so one upgrade does not raise it. I would put it in the box that holds the database, where memory has already run out once, and size the survive-alone set to 62 GB.
- [ ] **node2's second hard disk.** Holding everything on both means the Papers Past archive and its vectors on both. One usable 4 TB disk on node2 probably holds it; I overstated this at first. The other box is the second copy, so node2 needs no second disk for safety (Arthur, 11 October). What remains is small: the archive's size on disk is to be measured by the first session on the boxes, and one disk carrying the change log, backups, archive and vectors together may be slow under load.

**Decided by Arthur, 11 October.**

- **The third computer will be set up and on the network before the build.** So automatic database takeover is in the plan.
- **node2's second hard disk will be mounted before the build.**
- **Memory is handled by hardware profiles**, not by treating the boxes as identical. Set out below. The spare 64 GB goes in node2, and the primary database role normally stays on node1 (agreed 11 October). The database then has a steady share of the smaller box and the bigger box is free for heavily parallel jobs. "Primary" is a role that moves on failover, not a property of a box; if it lands on node2 the scheduler reserves memory for it there.
- **Copying each write just after it is confirmed** stands as my recommendation until ruled otherwise.

### Hardware profiles and matching job settings

Arthur's requirement: memory has overflowed before under highly parallel jobs. Each box gets a profile recording exactly what is in it. A job that speeds up with more memory goes to the bigger box with more parallel workers; if that box is unavailable it goes to the other with fewer.

How I would build that into the scheduler:

1. **The profile is probed, not typed.** Each worker reads its own box at start and on a clock: cores, memory, each card and its memory, each disk and its free space. A typed profile goes stale the day hardware changes; the spare memory and the second disk would both make one wrong.
2. **Each job type records what one parallel worker costs**, measured: memory, a card slot or none, processor share. The record already exists for card jobs; it is extended to memory and to processor-only jobs.
3. **Parallelism is worked out, not fixed.** How many workers a job gets on a box is what fits in that box's free memory after a reserve for the database and the standing services. The bigger box gets more workers without anyone keeping two sets of settings in step.
4. **A job may state a preference.** "Prefers the most memory" sends it to the bigger box when that box is up, and lets it run smaller on the other when it is not.
5. **A hard ceiling per job.** If a job outgrows what it declared, the job is stopped, not the box. The record already has this lesson: on 23 September node1 ran out of memory outright and the database's next request triggered the kill.
6. **The declared cost is checked against what runs.** The run history records each job's peak memory, and a job whose peak passes its declared cost is flagged so the figure is corrected.

## Rulings, 11 October afternoon

32. **The frozen Follow the Money keeps its daily data refresh.** How to keep that running while everything else changes is set out below.
33. **The old cards are not carried over.** They belong to a suite that will be deprecated. All of them, open, parked and closed, are read for context, with care: some are irrelevant, some are dead ends, and some rest on mistakes.
34. **The standing product rules are to be gone over one by one**, not assumed.
35. **Arthur starts each build session on node2.** The plan gives a short brief per session.
36. **The new estate's data lives beside the old at first.** Once the old has been properly consumed by the new, the old is deleted.
37. **Lanes re-read from the documents already captured.** Judgments and corrections are copied across untouched.
38. **The new repository is named QueryNZV4**. It was first recorded here with a typing slip in the name; Arthur corrected it on 13 October, and the folder and database names follow: querynzv4 and querynz\_v4.

### Dated jobs on the old estate

These sit outside the build and do not move for it.

| Date | Job | Whose | Note |
| --- | --- | --- | --- |
| 1 November 2026 | Backstop for the privacy-law advice | Arthur | Deferred with the legal work by ruling 2, but the date is in the record |
| 4 November 2026 | The old board goes red without a sealed copy of director addresses |  | Fourteen days before the Act |
| 7 November 2026 | General election |  | The frozen site's busiest period |
| 18 November 2026 | Director address suppression begins. Seal the pre-redaction copy before it (C232) | Arthur fires it | The new estate's address rule depends on that sealed copy |
| No date | The deploy token for the daily release was pasted into a transcript twice (run sheet section AL) | Arthur | The daily release runs on that token |
| No date | A capture window on Tenancy Tribunal and Real Estate Authority decisions: three years only (C212) | Build | History is lost if not taken early |

### Keeping the frozen product running

The old estate runs 75 scheduled jobs. Proving exactly which of them Follow the Money needs is hard; proving which it does not need is easy. So the freeze works by subtraction.

1. **Pin it.** The old repository is tagged at the frozen commit. Nothing is committed after that except an emergency fix: the release is broken, or a published figure is wrong. An emergency fix is Arthur's word.
2. **Keep every job running except the press graph's.** Capture, the register rebuilds, the page reader, the two product apps, the daily release, the feedback drain, backups and the board all stay.
3. **Stop the press-graph group as a plan step.** News extraction into the graph, the crawler and its reviewer, the merge and mint jobs, the research sweep, the two chat-model servers and their gateway, the news meaning index, and the NZME archive job. Follow the Money has served no press row since ruling 355.
4. **Prove the stop changed nothing.** Before stopping, keep the day's published version. After stopping, run a release into a scratch version and compare the two with the release's own comparison. Any difference that is not new data means something in the stopped group was needed, and it is switched back on.
5. **The board keeps watching the frozen estate.** A red is acted on only if it touches the release.
6. **The frozen site is the reference.** The rebuilt Follow the Money has to reproduce it before it replaces it.

### What the old cards say

All 564 card rows were read and sorted: 402 closed, 125 in the open register, 37 parked. Each has one line recording what it established and any caution. The lines are kept with this session's working notes for the plan to draw on.

| Kind | Count | Use in the new estate |
| --- | --- | --- |
| A design rule or ruling worth carrying | 195 | Requirements |
| A fact about the outside world or the data | 74 | Requirements, and test cases |
| An operating failure that would recur on these boxes | 67 | Checks built into the scheduler and installer |
| A defect in the old structure | 70 | At most one line of acceptance each |
| Press graph only | 80 | Set aside with press |
| Old workflow only | 29 | Set aside |
| Dead end, reversed or wrong premise | 24 | Do not repeat |
| A job only Arthur can do | 13 | The dated jobs above, and the decision queue |
| Nothing durable | 12 |  |

**Cautions found in the reading.**

- **Many cards were corrected by their own later text.** Figures were often wrong at first and restated, sometimes twice. A card's first number is not to be trusted without its last.
- **Several owner-raised cards rested on a mistaken premise** and say so: addresses "not being captured" (they were), place-named donors (three real companies), missing list-seat outcomes (already in the Commission's rows).
- **The window and scope moved under many cards.** Anything quoting 2014, 2020 or "the eight parties" predates the 2019 window and the seven-party scope.
- **"The page-reading model question is settled and must not be re-asked"** applies to electoral returns. It does not bind the legal documents, where ruling 18 asks for new models to be tried.
- **Cards written under the old capture rules** keep their facts and lose their policy.

**Operating lessons that change the build.**

- **Identical code on two boxes is not identical capability.** node1 lacked the page-reading program and blanked the database's return totals every night for 17 days with the board green. The hardware profile therefore also records the programs each box has.
- **A job killed at its deadline leaves its database query running.** Every job needs a query time limit as well as its own deadline.
- **node2 went down hard on 2 October and nobody knew for four days.** A dead box has to raise an alarm from the other box.
- **The power cut of 17 September** taught boot ordering, and that both hardware clocks hold local time. The card asks for an uninterruptible power supply.
- **Human review notes were once in no backup at all.** What a person typed is the least replaceable data.

## Standing product rules to go over

Ruling 34. These are truths about what the products may say, not workflow. Each is listed with where it came from, for Arthur to keep, change or drop.

**Identity**

- [ ] **People are never fused on a name alone.** A name match is shown as a possible namesake.
- [ ] **Two rules only make two person records one:** the same first, middle and last name; or the same first and last name at the same street address (ruling 221). Everything else supports and never decides.
- [ ] **A busy address needs a middle name.** An address shared by more than 50 companies counts only when the full name carries a middle name (ruling 217).
- [ ] **A director's name resolves to a person only with a supporting link:** a shared directorship, a shareholding, or a company that person declared. Of 151 name-matched MP directorships, 15 had one.
- [ ] **Every fold is re-checked** for signs it joined two people, and a broken one is withdrawn on Arthur's word (ruling 220).
- [ ] **A joint filed name is one donor; a parent and its subsidiary are a group, not one party.**

**Money**

- [ ] **A donation is from the donor the Commission filed it under.** A wholly-owned company keeps its own row; ownership is a note and is never added to the owner's total (ruling 253).
- [ ] **If a return covers the money, the return is the record.** A separate large-donation disclosure of the same gift is never added (rulings 193, 277, 357).
- [ ] **The headline is all donations:** the return's declared total. Named donors come second.
- [ ] **One figure per party-year, with its basis named.** A party's own committees and branches are not outside donors.
- [ ] **Where our reading and the Commission's figure differ, the Commission's is the headline,** linked to the Commission's own page.
- [ ] **A reading that fails its own check publishes nothing,** not a number.
- [ ] **A total states what it leaves out.**

**Scope of Follow the Money**

- [ ] **2019 onward only** (rulings 333, 347).
- [ ] **The seven front-page parties** are the scope; other parties' data is kept and served, not worked (rulings 351, 356).
- [ ] **A renamed party is the same party** (ruling 349).
- [ ] **A race is the twelve months before the election** (ruling 358).
- [ ] **No press-reported row** (ruling 355).

**Publication**

- [ ] **No physical address is shown or extractable.**
- [ ] **A suppressed name is suppressed on every surface;** the row and the money stay.
- [ ] **An unreadable name is shown as unreadable,** never hidden, guessed or ranked.
- [ ] **Every figure links to the document it came from.**
- [ ] **A blank says whether it means "none found" or "not held".**

**Machinery**

- [ ] **No text leaves the boxes for a cloud model** (ruling 172). This bears on trying new page-reading models: they would have to run locally.
- [ ] **One model per card** (ruling 327).
- [ ] **Credentials are never in the repository or in chat.**
- [ ] **Papers Past is searched, not mined for people and claims** (ruling 203).

## Rulings, 11 October evening

Arthur went over the standing product rules. Twenty-one stay as written; these are the changes.

39. **The Follow the Money rules belong to that product.** The seven money rules and the five scope rules (2019 onward, seven parties, renamed party, twelve-month race, no press rows) are settings of Follow the Money. Company, insolvency and court records go back as far as each source does.
40. **The two joining rules (ruling 221) stay exactly for Follow the Money.** The wider estate starts with them and they are revisited only after the first identity measurements, by Arthur's ruling.
41. **Arthur is not in the review loop.** "I never review apart from setup. I am not systemically in the loop. I am a builder." A suspicious join is reviewed by an agent and split if it is not trusted. A research agent that searches the web for outside evidence was intended. A report can list all near connections. "It was the graph that asked for really hard identity."
42. **The address rule is split.** A company's registered addresses are shown. A person's home address is never shown or extractable, and is still used internally for matching.
43. **Papers Past gets a name index as a search aid.** It covers names broadly: people, towns, roads, organisations and so on. It stays inside the history product and never feeds identity. Ruling 203 otherwise stands.

Still open: the wording of the one-card-one-job rule (rulings 327 and 329) against the four-cards-switched-by-the-scheduler ruling (22).

### What ruling 41 changes

- **Ruling 220 loses "on Arthur's word".** The watch on every join stays. The decision to split moves to an agent, and every split is reversible and written to the ledger.
- **Products show two grades of connection.** Confirmed connections rest on the joining rules. Near connections are listed beside them with the reason each is only near. No product needs every join to be certain.
- **No step in running the estate waits for Arthur.** He rules on design, sets things up and starts build sessions. Anything the plan had him check during operation needs an agent, a rule or a measurement instead.
- **The answer set needs another source of truth.** The earlier agent test failed for lack of cases Arthur had labelled. Test cases should come from the registers themselves, where a pair is known to be two people or one by construction.

### What already exists for agent review of joins

| Piece | What it does | State |
| --- | --- | --- |
| Join watch (ruling 220) | Re-checks each join for signs it covers two people: appointments in different regions at once, a common full name, a bankruptcy on one record while the other keeps appointing, donor rows from far-apart addresses in one year | Built (`registers/roster_folds.py`), counted on the board |
| Healer crawler | A timed job that screens for suspicious records, has an agent re-read the source document, then splits or quarantines with a ledger row | Built 22 August for the press graph; no web tools; in the job group the plan stops |
| Merge refuter | An agent with web search and page reading whose only job is to find evidence that two records are different. It never confirms, because web presence favours the more prominent person | Built 22 August (`research/merge_refuter.py`); never trusted, tested on 13 labelled cases where about 196 are needed (C532, C540) |
| Reviewer | Acts on review queues automatically inside measured bands; no human gate on routine review since 9 August | Built |
| Overseas-leads research agent (C188) | Searches for outside leads behind a verify gate | Not started |

## Rulings, 11 October, late evening

44. **A card runs one model on one kind of job at a time; the scheduler may swap it between jobs and records every swap.** This replaces "permanently" in rulings 327 and 329. It needs a protocol for small jobs that cause swaps and long jobs that block others (below).
45. **The "eras are fired by Arthur only" rule is dropped in the new estate.** The scheduler runs re-reads on its own.
46. **The rule-learning process is kept, and the existing extraction lessons and rules are captured.** "Just as we automatically build document profiles, we also built rules for understanding the press graph and errors we encountered via the healer. We should maintain this process and also capture the existing extraction lessons and rules too. They could come in valuable later even if we don't need them now."

### Protocol for sharing the cards

Five of these rules already exist, from Arthur's ruling 330 of 22 September. They are written and tested in `ops/fleet/schedule.py`; the part that acts on them has only ever run in rehearsal. Rules 6 to 9 are new.

| # | Rule | What it handles |
| --- | --- | --- |
| 1 | A job whose queue is empty gives its card up at once | Idle cards |
| 2 | A job keeps its card for up to one hour while it has work, then others get a turn | Long jobs blocking others |
| 3 | At the end of a turn the card finishes what is in flight and takes nothing new; nothing is killed | Half-finished reads |
| 4 | Waiting jobs take turns in priority order; a job that has had a turn goes to the back | Starvation behind a busy job |
| 5 | A swap must pay for itself: a waiting job needs enough queued work to justify unloading one model and loading another. A card already holding the right model is taken at no cost | Small jobs causing swaps |
| 6 | **A small job never waits for ever.** If its queue stays too short to justify a swap, it gets one anyway after a set maximum wait | Small jobs stuck behind rule 5 |
| 7 | **Long jobs are cut into pieces of minutes, each recording its own progress**, so the end of a turn loses nothing. Papers Past embedding by newspaper and year is the model | Long jobs that cannot be interrupted |
| 8 | **Three classes of job: someone is waiting, due by a time, whenever.** A waiting person goes first; a due job (the daily Follow the Money refresh) goes next when its time nears; bulk work fills the rest | Deadlines and live queries |
| 9 | **A bulk job takes every free card but gives cards back when others queue**, and the swap cost used in rule 5 is the measured load time of each model, not a fixed number | One job holding all four cards |

Recommendation on the open question in ruling 22: do not keep a card empty. While any product is being served, one card holds the question-answering model, takes bulk work for that same model, and keeps part of its capacity for live questions.

### The rule-learning loop and the extraction rulebook

What exists today:

| Piece | Where | Size |
| --- | --- | --- |
| Defect list: every named way a reading goes wrong, with an example and the rule that handles it | `data-layer/docs/DEFECT_TAXONOMY.md` | Four families (prose glued to a name, a name cut short, two names run together, never a name) |
| Rules catalogue and its doctrine | `data-layer/docs/HEALING_SYSTEM.md`, `ERA4_RULES.md` | 364 lines |
| The healing rules as code, each with tests | `healer/crawler.py` and neighbours | 21 rules |
| The return-to-the-document lane for errors a rule cannot settle from the text alone | `reconciliation/defects.py`, `healer/reread.py` | Four classes |
| Lessons on extraction, agents and reading documents | `docs/doctrine/lessons/` sections 2, 5 and 8 | Indexed |
| Document profiles | `data-layer/docreview/profiles.jsonl` | 22 profiles |

The doctrine worth keeping: a rule that cannot decide leaves the row alone; every action is reversible and written to a ledger with the rule's name; the same rule applies when a record is first read and to records read before the rule existed.

Two plan steps follow.

1. **Capture.** The defect list, the catalogue, the rule code with its tests, the name guards and the three lesson sections move into the new repository as a kept rulebook. It is parked with the press work, searchable, and not running.
2. **Carry the process on.** The old loop took new rules from Arthur's review. In the new estate the catch log and the review agent's splits supply the cases: a repeated error is named as a class, a finding card is raised with examples, and a build session writes the rule with a test against real rows.

### Ruling 47: the design is simplified

47. **Redesign in the plain direction** (Arthur, 11 October, 22:08: "I am just trying to simplify what we are building as much as possible"). The estate does five things: copy registers, build registers, link rows, answer with a citation, and check itself. There is no stored person: links, decisions and a rebuilt grouping replace the identity module. The sixteen use cases sit on four shapes (published site, subject report, register scan, archive search), each use case a template. The design is written up in [QueryNZV4 Design](https://claude.ai/code/artifact/a9b8a17d-2b2d-4266-8b78-cbc58ad7212d), which supersedes the module and identity sections of this record.

48) **The support design is kept in full.** The simplified estate needs far less hardware in steady running (about one card, part of the time, once Papers Past is embedded), but the scheduler, the nine-rule card protocol, the hardware profiles and automatic takeover all stay as designed. Arthur: "we have less jobs but we might expand what we are doing... let's keep the capabilities we have identified as having value." Spare cards go to finishing Papers Past sooner, a larger reading model, and reading scanned documents with two models to flag disagreements.

### Page-reading models to trial (researched 11 October)

GLM-OCR stays the incumbent. Four models that were not in the 22 September trial are worth running against it. Nothing found was released after that trial; the newest date from July and August. Scores are the developers' own unless noted, and no public benchmark measures invented text, which is the test that decided September.

| Model | Size | Released | Licence | Published score | Why trial it | Caution |
| --- | --- | --- | --- | --- | --- | --- |
| [TeleOCR](https://huggingface.co/bbsai/TeleOCR) (was NaviDC-OCR) | 1.2B | 17 Aug 2026 | Apache 2.0 | 96.87 on OmniDocBench v1.6, tables 97.05 | Top published score; reads photographed and bent pages | Runs on llama.cpp only through a community conversion; tables come out in a tag format that needs converting; 70.85 on real degraded pages |
| [OvisOCR2](https://huggingface.co/Abiray/OvisOCR2-GGUF) | 0.8B | Jul 2026 | Apache 2.0 | 96.47 to 96.58 on OmniDocBench v1.6 | Smallest; one Markdown page out, the same shape GLM-OCR gives | Community conversion; no data on poor scans |
| [Chandra OCR 2](https://huggingface.co/datalab-to/chandra-ocr-2) | 5.3B | 16 Mar 2026 | Weights free only under US$2M revenue or funding | 85.8 on olmOCR-bench; tables 92.1 | Strongest published claim on handwriting and forms | Licence must be read before selling; old scans are its weakest category (51.1) |
| [Infinity-Parser2-Pro](https://huggingface.co/infly/Infinity-Parser2-Pro) | 35B | 11 May 2026 | Apache 2.0 | 87.6 on olmOCR-bench, the highest listed | The large option a spare card allows; a different family, so a true second reader | English and Chinese only; weak on rotated tables; a general model of this size is where September's rejected candidate put a total among the rows |

Not worth a trial now: PaddleOCR-VL-1.6 (rejected in September for looping and an invented sentence), DeepSeek-OCR 2 (lower scores), Unlimited-OCR (needs an unmerged llama.cpp build and loops on dense pages), MinerU 2.5 Pro (a whole toolkit with extra licence terms), Xiaomi-OCR-0 (no published benchmark).

Trial method, as in September: the same real pages plus a set of legal documents; scored against known figures; any invented text or loop is a failure; each quantised build is compared once with the original weights.

49. **The trial of these four models is a plan step, and Chandra OCR 2 is in** (Arthur, 11 October: "we have no revenue currently so chandra is in"). GLM-OCR is the incumbent each is measured against. Chandra's licence goes on the before-selling legal list (ruling 2): its weights stop being free above US$2M in revenue or funding, and use that competes with its maker's own service is restricted.

50) **The model trial runs first, over the election documents, as the scheduler's live trial** (Arthur, 11 October). It comes before the legal-documents work.

### The trial as the scheduler's first job

The name stays "the scheduler": a registry of what each job needs, a planner that decides who gets what, and a worker on each box.

One run answers two questions, so it is done in two passes to keep them apart.

1. **GLM-OCR alone, through the scheduler.** It should reproduce the readings the old estate already has. A difference here is the scheduler's fault, not a model's.
2. **The four challengers added.** Five models over the same pages forces the cards to swap, which is the behaviour under test.

| What the run proves about the scheduler | How it shows |
| --- | --- |
| One model per card at a time, every swap recorded | The swap ledger matches what the cards actually held |
| A swap pays for itself; a small job never waits for ever | The small models are not starved behind the 35B one |
| Long work is cut into pieces that record progress | Stopping a worker mid-run loses at most one piece |
| Either box can take the work | One box's worker is stopped on purpose and the other finishes |
| The hardware profile is probed, not typed | A box missing a program a model needs is never given that job |
| Peak memory is recorded per job | The profile for each model is filled from this run |

| What the run proves about the models | How it is scored |
| --- | --- |
| Faithful reading | Invented text or a loop is a failure, as in September |
| Correct figures | Donor rows and totals against figures already known: the Commission's own totals and the frozen site's published figures |
| Scans with no text layer | The returns that failed in the old estate for that reason are in the page set |
| Agreement between readers | Where two models of different families agree and where they differ |

The run reads the captured documents and writes to its own scratch tables. It publishes nothing and does not touch the frozen site. Its result chooses the page reader, and the second reader, for the rebuilt Follow the Money.

### Three conditions on the trial (Arthur, 11 October)

1. **The document profiles come first.** A profile says what a document is, which pages go to the page reader, at what resolution, and how its tables are laid out. The 22 profiles in `data-layer/docreview/profiles.jsonl` move into the new repository before the trial. The trial swaps only the page reader a profile names and holds everything else fixed.
2. **A reading is tied to the document's bytes, never to its name.** Last time readings were attached to the wrong documents. The record: the corpus was 4,020 files but 3,325 distinct documents; 424 returns were held under two names and the recogniser matched neither; one return, byte-identical under two names, would have filed 1,469 rows ($40.07m) twice. Every reading in the trial is recorded against the file's hash, the page number, the model, its build and the profile version. The page set is drawn from distinct hashes, and the known answers are joined by hash.
3. **Text or scan is decided per page.** Some PDFs mix scanned pages with pages that carry text. A whole-document test called such a file readable while its declaration page was an image, so the return read as having no total. The rule already in the profiles: a page with under 50 characters of text goes to the page reader, and a page with a text layer stays with the text reader, which outranks any page reader. Of the 56 live party returns, 24 were all text, 23 had an image first page, and 9 were full scans.

What these add to the trial:

- **The page set covers every shape:** all text, image first page, full scan, and handwritten.
- **Scores are per page,** so one bad page cannot hide inside a good document.
- **Text pages are a free answer key.** A page with a text layer is rendered to an image and given to each page reader; the text layer is the known answer. September's choice of GLM-OCR was made this way, and it needs no one to label anything.
- **A figure read from pixels is weaker evidence than one read from a text layer,** and is recorded as such. Where the two disagree, the pixel reading is the first suspect.

### The plan is written (11 October, late)

The step-by-step plan for another Fable agent is [QueryNZV4 Build Plan](https://claude.ai/code/artifact/b9f69ed6-d378-4ffc-a1d0-88c7208b35c7). It carries the model split (Fable for contracts, the scheduler, links and the integrator; Opus for lanes, templates and most of the Papers Past ingest; one measured comparison on the charities lane). It supersedes this record wherever they differ.

Writing and checking it found four things this record has wrong:

- **The freeze must keep one chat-model server and the gateway.** This record says to stop "the two chat-model servers and their gateway". Follow the Money's document reading calls the gateway on port 8090, which passes to the `querynz-agent-llm` server. Both stay.
- **NZME is still being captured.** The news scraper list has `nzherald.co.nz` as ready, so the kept news jobs fetch it. The freeze takes it out.
- **The release script publishes unless told not to.** `ops/pi_release.py` needs `--dry-run` for any comparison run, and its own comparison checks donor-page totals only.
- **The embedding rate is better than recorded here.** A test on 18 September, with the server's prompt cache off, did about 80 short texts a second on one card, against the 25 a second and 40 days quoted above.

51. **Passwords and API keys are rotated as part of the plan, and the long-running security cards are brought into it** (Arthur, 12 October: "We really need to rotate passwords and api keys. this needs to be in the plan too"). This replaces old ruling 270, which deferred every rotation to a later hardening pass. It is track H of the build plan: the inventory brought up to date; a search for where secrets have leaked; wave one, the keys that work from outside the local network, starting with the deploy token for the public site; wave two, the database passwords, in one planned sitting with Arthur present; and the other security cards (admin rights on node1, the container for unattended work).

52) **An interface that shows the connections between registers** (Arthur, 12 October: "I would like an interface that lets me see the connections between registers... run a search and see the results across registers displayed in panes like our Miller boards"). It is a fifth product shape, the board: one search across every register, each followed link opening a pane to the right, so the row of panes is the connection. It is step 4.9 of the build plan, built as soon as the first lanes and the links exist.

53. **The build starts next week, and Follow the Money runs alongside as an exported product fed only by the declared-donations feed** (Arthur, 12 October: "the only feed that matters is the declared donations feed so we can carve that out to run alongside as part of this plan"). The frozen product is therefore a small named set of old jobs, the carve-out: the declared-donations feed, the three readers it calls, the publisher, the daily release, the feedback drain, and the database and copies they stand on. The old capture jobs keep collecting for the new estate until new lanes take over. Every other old job is a candidate to stop, with proof. This replaces the earlier "keep everything but the press graph" freeze (rulings 17, 28 and 32 are narrowed by it). Three further additions made the same morning: the session working in the old repository is wound up before the freeze; the watcher reads the public site's feedback daily; and the copy of the plan in the new repository is the master.

## Gaps to fill before a plan

A review of this document and the risk register on 10 October, by two reviewers who had not seen the discussion. One read only the two documents. The other checked them against the doctrine, the rulings, the Muster 4 pre-pass, the earlier use-case programme and your run sheet. I then confirmed the findings below against the files. Nothing here has been fixed yet; the rest of this document still reads as it did before the review.

### What this document got wrong or missed

- [x] **An earlier use-case programme already exists.** Settled: its ten cases and three expansion cases join the plan. See "The full use-case set" below.
- [x] **The commercial model in the strategy is not the one written here.** Settled: the partner model is an enhancement, the plan assumes customers, and billing is out.
- [x] **The first build step contradicts the pre-pass.** Dissolved: order is free in this planning.
- [x] **"Lanes in parallel" breaks the one-queue rule.** Dissolved: parallel work is allowed. The technical caution stays: two lanes that land through one shared rebuild of the register tables are not independent.
- [x] **The rebuild is larger than the method allows.** Dissolved with the old method.
- [x] **Step 5 would publish connections about named people before the legal advice.** Deferred with the legal work. The one place it returns is the live public site: showing a new person-level connection there is a publishing decision to raise at that time.
- [ ] **Stage 0 disagrees with itself.** Still true of the sections below. It is fixed when the plan is written.
- [ ] **Smaller errors of fact, still uncorrected below.** The Insolvency Register interface is parked on outside approval and carries a daily removals-polling duty for good. Ruling 131 holds tribunals and WorkSafe enforcement as well as courts, but rulings 310 and 311 already released court judgments for cases, parties and outcomes, and ruling 314 shelved that build as a tangent. Ruling 213 deferred foreign registers and removed-company shareholdings. The terminal architecture treats occupational registers as a lookup tier.

### Rulings a plan cannot be written without

- [x] **What this is.** A capability build-out under new operating rules.
- [x] **The business model.** Plan as if customers exist; partners are an enhancement.
- [x] **Doctrine.** Press is demoted entirely for now. The build treats people and connections as first-class. The doctrine documents themselves are not yet amended; that belongs with the new operating rules.
- [x] **Person connections and the legal advice.** Deferred until after the build and before selling.
- [x] **The identity error bar.** Not needed to start. The build measures and records the error rate by name band on every run; the number is ruled later, with data, before anything is sold or a new person-level connection goes on the public site.
- [ ] **The service cut.** Now mine to propose in the plan.
- [ ] **Held legal sources.** Court judgments are already released by rulings 310 and 311, with the build shelved. Tribunals, employment and environment court decisions, coroners and WorkSafe enforcement are still held under ruling 131, which asked for a revisit per source "with intention". Six use cases now ask for them. Not blocking the plan; it decides how far those six can go.
- [ ] **Follow the Money's scope.** Whether the award join, pre-2019 awards or a councils tier ever appear on the public site. The capability is built either way. Not blocking.
- [ ] **The pre-election freeze.** My proposal stands until you rule. Not blocking.
- [ ] **Daily company changes**, against your standing word on the monthly import. Blocks only the monitoring use case's freshness.

### Facts to establish

- [x] **The state of the August use-case endpoints today.** Dissolved: plan first, harvest after.
- [x] **Licence terms for commercial reuse.** Deferred with the legal work. Approvals that stop data being collected at all stay on the list as acquisition gaps.
- [x] **Demand.** Dissolved: plan as if customers exist.
- [ ] **The six measurements in the risk register.** None has been run. They are the first build task for identity, not a precondition for the plan.
- [ ] **An answer set for register rows**, with its size, sampling and who labels it.
- [ ] **Whether an outside figure exists for each stage gate.**
- [ ] **Live row counts**, in place of the catalogue minimums quoted here.
- [ ] **A verdict per reusable piece.** Folded into the harvest.

One item from "Still to verify" is already answered: the earlier requirements document records the award notices as keyed on business number.

### Design not yet specified

- [ ] **A stable row key**: what makes a row the same row across re-reads, amendments and nightly rebuilds. The takeover test cannot run without it.
- [ ] **"Reproduces the published site"**: compared at what grain, over how many days, to what tolerance, signed off by whom.
- [ ] **A published view and a manifest**: owner, shape, versioning, and how licence terms are enforced.
- [ ] **A connection**: which link types, how dated, how hubs and nominees are treated.
- [ ] **Where the shared machinery sits.** The document reader, page recogniser, model client, fetch gate, release pipeline and orchestrator are in none of the five module kinds.
- [ ] **The lane template.** Five lines leaves out what the standing rules require of every lane: a watcher row, a timer, the one switch, a place in the job manifest and a paired correctness check.
- [ ] **Risks not carried over from the risk register.** A donor-to-award join shown weeks before an election is the "coincidence shown as cause" risk and has no presentation rule. Undated links, hubs, the error rate by name band, and the loss of the address rule's evidence after 18 November have no gate on the path.

### What any plan here must contain

- [x] **The pre-pass products the old operating method requires.** Dissolved with the old method. Three are worth harvesting: a decision register mapping each ruling to the step it blocks, a conflict register, and a baseline checked against the live system.
- [ ] **New operating rules and principles** for this way of working.
- [ ] **Sizes**, and a stop rule for a rebuilt module that never matches.
- [ ] **Capacity.** How many sessions run at once now that parallel work is allowed, and your hours.
- [ ] **Goals as measurements.**
- [ ] **What Follow the Money itself needs before 7 November**, weighed against the build. The candidate list is unreachable and both Hansard lanes are challenged.
- [ ] **What is out of scope.** Press is now explicit. The rest is not listed.
- [ ] **A home for the plan.** The new operating rules will say where.

### Operating baseline

- [ ] **The deploy token.** Run sheet section AL records that the token the daily release uses was pasted into a transcript twice. The continuity point rests on that release.
- [ ] **11 red board checks, no tests on push, one page recogniser, both boxes on Wi-Fi.** Which of these must be fixed first is not decided.

## The full use-case set

The ten August cases, the three expansion cases, and the ones added in this discussion, merged into fifteen. The numbers are used in the tables that follow. The last column is where earlier work exists to harvest; its present condition has not been checked, by your instruction.

| # | Use case | Who uses it | The question it answers | Earlier work to harvest |
| --- | --- | --- | --- | --- |
| 1 | Follow the Money | Reporters, the public | Who funds parties and candidates, and what followed | The live product |
| 2 | Legal counterparty and conflict check (due diligence) | A law firm partner before taking a client | Who is behind this company, and does acting for them conflict with anyone we act for | Legal flow with a printable memo; conflicts endpoint; the June lawyers' tool pages |
| 3 | Banking: the director history | A credit analyst | Every company the controlling mind has touched, and how each ended | Banking flow; person view |
| 4 | Agriculture counterparty risk | An agribusiness credit manager | What the record says about the people behind a rural trading company | Agriculture flow; the four-rule company rule set |
| 5 | Business credit and monitoring | Trade credit teams | Has anything changed for the companies I am exposed to | Watchlists and feed |
| 6 | Insurance underwriting | A commercial underwriter | The real safety and solvency record behind a proposal | Mock-up only |
| 7 | Construction: subcontractor vetting and phoenix detection | A head contractor's procurement lead | Is this the failed firm again under a new name | Mock-up; a first probe of the phoenix join |
| 8 | Recruitment: board pre-appointment screen | An executive search consultant | Is there anything in the public record we should know | Recruitment flow; the seven-rule person rule set; report builder |
| 9 | Government procurement integrity | An agency procurement lead | Are shortlisted suppliers linked to our staff, to each other, or to donors | Mock-up; a four-row checklist |
| 10 | Tender and award intelligence | Bidders | Who wins what, from whom, and who is behind them | The award notices table, loaded and unread |
| 11 | Healthcare operator governance | An aged-care investor or regulator analyst | Who runs the homes, and how has it gone | Mock-up only |
| 12 | Property developer due diligence | An investor or apartment buyer | Who is really building this, and what happened to their last projects | Mock-up only |
| 13 | Beneficial ownership and AML checks | Compliance teams and AML providers | Who ultimately owns or controls this, and are they exposed or sanctioned | Ownership-chain endpoints and page; the roll-up through holdings |
| 14 | The post-settlement governance map | Iwi organisations, Crown agencies, reporters | The whole entity web of one post-settlement body, with its office holders | Benchmark questions only |
| 15 | Lobbying: who is in the room | Reporters, integrity bodies | Movement between public office and industry | An endpoint that nothing calls; mostly press-derived |
| 16 | History search | Historians, family and iwi researchers, reporters, Treaty researchers | Everything Papers Past holds on a person, place, event or phrase, despite misread print and old spellings | The search service's keyword, drift, facet and salience tools; the semantic index; the research agent |

Riding on these with no new machinery: vetting bidders and conflict checks (2 and 9), grant-maker checks (10), Follow the Money for councils (1), board screening (8), contractor vetting (7), and a domestic list of politically exposed persons (13).

## Data acquisition gaps

Three piles, in order of cost. "Serves" gives use-case numbers from the table above. Figures are the repository's own, mostly from August and September, and not live counts.

### In hand and unread

Nothing to acquire. Each needs a reader or a rule.

| Data held | What it carries | Serves | What is missing |
| --- | --- | --- | --- |
| Award notices and their category and region tables | 29,874 awards from 2014, keyed on business number | 1, 9, 10 | Any reader, and a scheduled refresh (by hand each quarter today) |
| The company insolvency file | Insolvency type, appointee names and firms, appointment and vacated dates | 3, 4, 5, 7, 8 | Read only as background for name matching |
| Vanished-row history, 16 tables | Trading names, industry classification and roles as they change, kept since 16 August 2026 | 3, 5, 6, 7 | No rule reads it. Nothing before August 2026 |
| Commerce Commission cases and FMA warnings | 112 cases and 16 warnings with parties and categories parsed | 5, 6, 8 | Nothing reads the parsed fields (C397) |
| Disqualified directors | A deterministic derive already written | 3, 5, 7, 8 | Its tables have no definition (C395) |
| Retirement villages file | The schema carries the statutory supervisor's name and appointment date. The August requirements said it did not; the contents need a look | 11 | A reader; supervisor churn needs history |
| Charity annual returns | 421,633 returns | 11, 13, 14 | No typed derive |
| Charity officers | About 260,000 roles; the person key is empty on 58,591 | 8, 11, 14 | Identity |
| WorkSafe releases | Release texts already collected | 6, 7 | A derive of prosecution facts from the text. The official interface gives totals only |
| Council minutes | 24 councils on one meeting platform | 12, 15, councils tier of 1 | No derive of attendance or resolutions |
| Overseas investment decision summaries | Collected | 12, 13 | No derive of applicant, vendor and price |
| Parliamentary speeches | 32,875 speeches by 125 members, all matched | 1, 15 | A participation register exists; nothing joins it to interests |
| Land titles | Companies matched; individuals held back | 12, 13 | The industry derive and the takedown service |
| Māori business identifiers, Australian business numbers, global entity identifiers | Loaded | 13, 14 | Used only to prevent false matches |

### Captured or built, then held or shelved

| Source | Where it stands | Serves | What reviving it takes |
| --- | --- | --- | --- |
| Court judgments | Collected. Released for cases, parties and outcomes by rulings 310 and 311. The build was shelved the same day as a tangent (ruling 314); the register is fed by nothing. 145 documents were in scope | 2, 3, 6, 7, 8, 12 | Picking the shelved build back up |
| A free parsed case-law interface (OpenLaw) | Key in hand and tested; about 47,000 parsed cases; no lane built | 2, 3, 6, 7, 8, 12 | Building the lane |
| Tribunals, employment and environment courts, coroners, WorkSafe enforcement | Held under ruling 131. The Ministry of Justice sources are paused until a permission letter is answered; the letter is drafted and unsent | 6, 7, 11, 12 | A revisit per source, and the letter |
| High Court and Court of Appeal back-catalogue | The host drops automated requests | 2, 12 | The same letter |
| Securities register, Insolvency Register and financial service providers interfaces | Waiting on outside approval since 19 September | 3, 4, 5, 7, 13 | The approval. The insolvency interface brings a daily removals check for good |
| Sole traders, partnerships and trusts | Not in the monthly file. Reachable one at a time through the business-number interface, which ran once in August | 4, 5, 13 | A standing fetch by number |
| Company filings: liquidators' reports, financial statements | A filings table exists; whether it is filled is unconfirmed | 3, 5, 7 | A look, then a reader for the attachments |
| Stock exchange announcements | Nothing collected; terms need written permission; letter drafted | 5, 13 | The letter |
| Waitangi Tribunal reports | 200 held under ruling 99 | 14 | A ruling naming the use case |

### Not acquired

| Source | Serves | Route as last recorded |
| --- | --- | --- |
| Limited partnerships register | 13 | Free public register |
| Sanctions lists (Foreign Affairs, United Nations, Police designations) | 13 | Published lists |
| Overseas ownership data (UK, open beneficial-ownership data, Australia) | 13 | Free bulk; deferred by ruling 213 |
| Licensed building practitioners | 6, 7, 12 | Public register; carded, never built |
| Health and Disability Commissioner decisions | 11 | The open alternative to the practitioners' tribunal, which is blocked |
| Live open tenders, agency contract disclosures, council procurement | 9, 10 | Public; the standing permission covers award files only |
| Grants: gaming-machine, Lottery, regional development, tertiary funding | 10, 1 | Published files; two are carded (C333, C334) |
| Alcohol licences | 5 | A national spreadsheet each quarter |
| Local election returns, councillors' interests, council pay | Councils tier of 1; 15 | Council by council (C332 for pay) |
| Iwi and hapū directory, settlement commitments database, Māori Land Court | 14 | Two are public; the court needs registration |
| Building consents; official MPI and animal-tracing prosecution records | 12, 4 | No bulk route known |
| Ministerial diaries | 15 | Public; on the later list |

### How far each use case gets

- **On held data now:** 8 recruitment, 4 agriculture, 2 legal without litigation, 3 banking without securities, and the domestic half of 13 ownership.
- **With reading of data already in hand:** 9 government, 10 tender, 7 construction, 5 monitoring at monthly grain.
- **Needing acquisition or a held source released:** 6 insurance, 11 healthcare, 12 property, 14 post-settlement map, the overseas and sanctions half of 13.
- **Mostly parked with press:** 15 lobbying.

The sources that open the most use cases are, in order: court judgments and tribunals (six), the securities and insolvency interfaces (five), the change history of companies at finer grain than monthly (four), and the building practitioners register (three).

### What demoting press removes

Keyword search over journalism other than Papers Past is restored (ruling 8 above). That brings back, at keyword strength: coverage recall for insurance, healthcare and property, and the journalism search for due diligence.

Still parked with the press graph: family links between suppliers and staff in procurement, press-derived appointments for lobbying, press ownership claims in beneficial ownership, and anything that needs meaning-based search over current journalism. Each product says "not held" for these.

## History search (use case 16)

Deep search of Papers Past with every tool available.

**What is held.** 4,648,837 Papers Past articles are in the corpus, about 2.1 million of them in the semantic index when ruling 203 was made. A further 86 million items are in the archive on the boxes (Arthur, 10 October) and have never been ingested (C323). I cannot see the boxes from this session, so its location and format there are not recorded here.

**What is not there.** Every person, claim and mention drawn from Papers Past was deleted on your word of 27 September, and a board check keeps it that way. I have read "every tool" as every search tool. Rebuilding people and claims from Papers Past would reverse that deletion; say if you want it.

| Tool | State | What it adds for history |
| --- | --- | --- |
| Full-text keyword search | Built, but reads only the title and first 1,500 characters (C543) | Must read the whole column; old newspaper columns run long |
| Matching that tolerates misread print | Not built | The scans turn Auckland into "Ancklaud". Without this, most deep searches miss |
| Old and variant spellings, names without macrons, initials | Pieces exist in the name folds and the nickname pairs | One query finds a person under every form the papers used |
| Date, newspaper and region filters | Built as facets | Narrowing by place and decade |
| Change over time and distinctive terms | Built (drift and salience) | When a subject rises and falls; what words mark a period |
| Meaning-based search | Built; covers under half of what is held and none of the 86 million | Finds a subject when the words differ |
| Reprint detection | A hand-run near-duplicate scan exists | Nineteenth-century papers reprinted each other; collapse the copies |
| Old place names | The official place-name file is loaded (54,667 names) | Places by former and Māori names |
| An agent that searches in rounds | The research agent exists with a different toolset | Follows leads across many searches and reports with citations |
| Compound-word splitting | Written, wired to nothing | Old compounds and run-together words |

**Acquisition and capacity gaps.** Ingesting the 86 million items. A full-text index at that size is far beyond the present one, so the search engine choice needs sizing. Embedding 86 million items is weeks of graphics-card time at the rate measured in August.

### Ingesting the archive: finding each catch exactly

Your instruction: as ingestion catches, identify exactly where, as we meet it. This is how the ingest is built to do that.

- **Named stages, each with its own count.** Every stage records items in, items out, and items set aside with a reason. In must equal out plus set aside, on every batch.
- **A catch log.** One line per catch: the stage, the item, its place in the archive file, the reason, and the first failing example kept whole.
- **Small batches first.** Ten thousand, then a hundred thousand, then a million, so a catch is met on a small set. A batch that does not reconcile stops the run.
- **Nothing set aside silently.** A run that sets aside more than a stated share stops and says which stage. The record already holds the lesson: one build in August stored 3.4 million of 10.65 million rows and reported nothing.

Where the record says to expect catches, stage by stage:

| Stage | Catch to expect | From |
| --- | --- | --- |
| Reading the archive | Format, encoding and truncated files. Unknown until the first batch is read | Not recorded |
| Overlap with what is held | 4.65 million articles are already in the corpus, so the same item can arrive twice; reprints between papers also collide | C323 |
| Landing in the corpus | Table growth copies to the standby, and the nightly off-site copy is already 368 GB and is re-sent whole on any failed attempt | Lessons file; C321 |
| Keeping it out of the graph | Today only a status value keeps Papers Past out of extraction, not a rule. The search-only policy has to be in place before the first batch lands | Board check T7.69; C323 step 1 |
| Keyword index | The present index reads 1,500 characters and its rebuild is a load event on the serving database. At 86 million items it needs sizing first | C543 |
| Meaning-based index | It is built whole in memory. At 6.4 million articles it takes 33 to 38 GB on a 62 GB box and is already at the limit. It cannot be built that way at this size | C550 |
| Serving | Filters, change-over-time and distinctive-term queries have only run at the present size | Not measured |

### Building the full meaning index

Agreed 11 October. The present method cannot reach this size.

| Limit | Today | At about 91 million items |
| --- | --- | --- |
| Memory | The index is built whole in memory: 33 to 38 GB for 6.4 million articles | Roughly 500 GB; the boxes have 62 GB |
| Storage | Vectors sit in a database table at about 4 KB each | About 350 GB more on the primary, the standby and the off-site copy |
| Time | Best recorded rate is about 25 items a second on two cards | About 40 days |
| Coverage | Title and first 1,500 characters only | Whole documents are required (ruling 23) |

**The build**

1. **Measure the first batch.** Lengths, the share that is adverts or tiny notices, and how much is reprints. This decides what gets a vector.
2. **Read whole documents.** A long column is split into passages and each passage gets its own vector, so nothing past the lead is invisible. This raises the vector count; the first batch says by how much.
3. **Speed up embedding before the long run.** The model uses 0.7 GB of a 34 GB card. Many copies per card, or larger batches, should raise the rate a great deal. Unmeasured on these cards; it is the first experiment.
4. **Embed in shards by newspaper and year, into files on the hard disks.** At half precision the set is about 190 GB before passages. Each shard has its own count and catch log, and a stopped run resumes at the next shard.
5. **Share the cards through the scheduler.** Embedding is a queue job that yields to document reading and to interactive use. Embedding a search query already runs on the processor and needs no card; what needs a card at query time is the search agent and the page reader.
6. **Build a compressed index.** Each vector is squeezed to about 64 bytes, so the whole set fits in under 10 GB of memory. It grows shard by shard, so search works while the run continues.
7. **Re-check the top candidates exactly** against the full vectors. On hard disks this step takes seconds, not milliseconds. That is acceptable for deep search to begin with; the re-check store moves to fast disk if it proves too slow.
8. **Serve it as its own small process**, blended with keyword results.
9. **Prove recall first** against exact search on a one-million sample.

The vectors stay out of the off-site copy because they can be regenerated, and get a second local copy because regenerating costs weeks. The present 6.4 million article index can move to the same design, which frees about 30 GB on each box (C550).

**Rights.** Copyright on Papers Past varies by title and date. I could not read its copyright guide today; the site turned my request away. As far as I know, older material carries no known restriction and several publishers have licensed in-copyright titles for non-commercial use only. That needs checking before history search is sold, and it bears on NZME below.

## The capture test: legality and politeness

Replaces the old capture rules (ruling 10 above). A robots file, an "ai-train" signal, or a guess at what a publisher would prefer no longer decides anything. Two things decide. This is my reading of the law for planning, not legal advice; I am not a lawyer.

**Legality: four questions per source**

1. **Access.** Is the page open without getting past a lock? Fetching a public page is one thing. Getting past a login we do not hold, a challenge, or a block is the conduct the Crimes Act computer-access offences are aimed at, and the copyright changes due by May 2028 tighten the ban on getting around digital locks. Our own paid accounts are access we hold, though their terms may limit what we do with it.
2. **Copying.** Storing a page is making a copy. New Zealand has no text-and-data-mining exception and no general fair use; fair dealing covers research or private study, criticism and review, and news reporting. Facts are free; the wording is not. Government releases are mostly openly licensed.
3. **Contract.** Terms of use bind most clearly where we accepted them, as with an account. Terms on a page we merely visited are less certain, but they are where disputes start.
4. **Personal information and statutory limits.** The Privacy Act applies to what we collect about people even when it is public. Some registers limit by statute what a search may be used for.

**Politeness**

- Slow, low-concurrency, off-peak collection, with caching so nothing is fetched twice.
- A stated crawl delay is honoured as a request about load.
- A direct request from a publisher to stop is honoured. That is stated intent, not inferred.

**Where I stop.** Solving challenges and using credentials that are not ours stay out, and I will not plan them. That is the legality test applied, not the old rule kept: a challenge or a login is a lock, not a wish.

**Timing.** You ruled that legal work follows the build. Legality of collection cannot wait that long, because the collecting happens during the build. So the build carries a one-page position per class of source, written from this test, and the lawyer's review of those pages comes before selling.

**What this reopens.** Sources stopped only by a robots file or a signal: the Ministry of Justice tribunal and court sources paused on 15 August (employment, environment, three professional tribunals, coroners), the Environmental Protection Authority, the health practitioners' tribunal, and one news outlet. Their use in the build still turns on the ruling-131 hold listed above.

**What it does not reopen.** The High Court back-catalogue, which drops automated requests outright. Outlets behind a challenge that a real browser does not pass. The legal-information site that requires an agreement. And fyi.org.nz, which you excluded by name in ruling 321; I have left that in place as a specific ruling.

## NZME: what is legal

**Dropped (ruling 12).** NZME is out of the build, so none of its mastheads appear in keyword search or anywhere else, and the build approach at the end of this section no longer applies. The analysis is kept as the record of why. Two loose ends: the job that collects NZME's archive is recorded as still enabled, and the copies already held remain on the boxes. Stopping the one and deciding about the other are for the working session.

Facts for your decision. I am not a lawyer, and this wants a lawyer's eye before anything from NZME is sold.

**What is held.** Fourteen mastheads, collected back toward 1998 and held with no model run over them (ruling 115).

**What NZME's terms say.**

- The NZ Herald terms of use page as it reached me today is marked "Updated May 2015". It gives access "only for your personal use". It says a user must not "archive the Material" and must not "form a database whether electronically or otherwise by systematically downloading or storing all or any of the Material". It says "no content may be reproduced, published or transmitted in any manner without the prior written consent of NZME".
- That page had no clause on machine learning. Ruling 115 quotes NZME terms barring use for "machine learning and/or AI ... and/or commercial purposes". So a second, newer text exists somewhere. Which document governs, and its date, needs pinning down.

**How the four questions come out.**

| Question | Position |
| --- | --- |
| Access | Public pages, no lock passed. The access offences are unlikely to be the issue. |
| Copying | Holding the full text is copying. No mining exception covers it, and recent reporting says the government is not adding one in the current round of changes. Research fair dealing is a thin cover for a service that is sold. |
| Contract | The terms forbid exactly what the hold is: an archive and a database. Whether terms we never accepted bind us is uncertain. |
| The machine-learning clause | A keyword index is not machine learning, so keyword search stays inside the hold's own definition. Meaning-based search and entity extraction are machine learning and stay off NZME. |

**What a keyword search may show.**

| What is shown | Exposure |
| --- | --- |
| Headline, masthead, date and a link | Lowest. We point at their page and show none of their text. |
| A short extract around the matched words | Some. It turns on whether the extract is a substantial part of the article. |
| The full text | Infringement without a licence. |

**Routes to a clean position.**

- **A licence from NZME.** The letter is drafted and unsent.
- **A media-monitoring licence.** As far as I know, New Zealand's newspaper publishers license press monitoring through a joint agency, and commercial monitoring firms operate under it. A keyword search over news sold to clients is close to that business. Unverified today.
- **Papers Past for the historic Herald.** As far as I know the Herald's older issues are on Papers Past under a non-commercial licence. That would serve history search for research use, not a sold service. Unverified today.

**How I would build while that is open.** Keyword search across the other outlets, with NZME included as headline, date and link only, tagged so it can be cut in one step. No model touches NZME, as now. The licence question goes to the lawyer with the rest before selling.

The same copying question applies to every commercial outlet in the keyword search, not only NZME. NZME is the one whose terms say it most plainly.

Sources read today: [NZ Herald terms of use](https://www.nzherald.co.nz/nz/terms-of-use/LE3ABZBLNLAWAQLS6BRNVZPCWQ/); [Sprintlaw on web scraping in New Zealand, May 2026](https://sprintlaw.co.nz/articles/is-web-scraping-legal-in-new-zealand-essential-compliance-guide/); [Asia IP on the 2026 copyright amendments](https://asiaiplaw.com/article/new-zealand-announces-amendments-to-copyright-law); [Hugh Stephens on the 2026 changes](https://hughstephensblog.net/2026/06/29/copyright-developments-in-new-zealand-going-in-the-right-direction/); [Victoria University on AI and copyright exemptions, September 2025](https://www.wgtn.ac.nz/news/2025/09/ai-companies-want-copyright-exemptionsfor-nz-creatives-the-market-is-their-best-protection); [AJ Park on copyright and AI, 2023](https://www.ajpark.com/insights/nz-copyright-and-ai/).

## Parked and retired work to draw on

Found by a search of the retired folders, the parked cards, the disabled jobs, the older repositories and the ideas backlog. Staged files outside the repository were not visible to this search.

| Item | What it gives | For | Note |
| --- | --- | --- | --- |
| Courts register and its graph feed | Case, party and outcome rows from judgments, with a takedown lever | 2, 3, 6, 7, 8, 12 | Built; fed by nothing |
| Earlier court pipeline | Provenance by numbered paragraph | The same | Its own note: port from it, do not resurrect it |
| Geometric table reader | A second opinion on scanned tables | Every scanned source | Retired 25 September; needs a recogniser that returns word positions |
| Row-pairing check for numbered tables | Refuses a table whose columns have drifted | Any tabular filing | Experimental; wired to nothing |
| Holdings module | Positions, and who held each for how long | 15, 8 | Retired with the older graph code |
| Enterprise nodes | A group above the legal entity | 5, 13 | Built in July; seeded with one group |
| Roll-up through holdings | Exposure carried up an ownership chain | 13 | Live for Follow the Money only |
| Earlier resolvers for positions, events and people by affiliation | A start on matching things that are not people | 13, 14 | Imports deliberately broken |
| Earlier audit checks and accuracy scorer | A deterministic graph audit and a scorer | The harvest itself | The current repository has no successor |
| Flows, report builder and rule sets | Legal, Banking, Recruitment and Agriculture flows; the printable memo; eleven rules | 2, 3, 4, 8 | Built in August on the older graph |
| Ownership-chain page and endpoints | Owners upward, holdings downward | 13 | Built |
| One graph across companies, societies, charities and Gazette | The register graph page from the second generation | Connections | In the older repository |
| Judgment and case inspector pages | From the June lawyers' tool | 2 | In the oldest repository |
| Source prototyping bench | Scrape a new source and inspect the result without landing it | Every new lane | Nothing runs it; one import is broken |
| Retired capture scripts | Award recovery, interests editions since 2006, candidates 1999 to 2023, charity financials | 1, 9, 10, 11 | Kept, runnable by hand |
| Archive survey and back-catalogue walker | Depth for any source | Lanes | Hand-run |
| Research agent, web-only baseline, gap miner, benchmark sweep | A scorecard per use case against the usual means | Every use case | Live units |
| Scheduler and executor | Who gets a graphics card, when | Parallel work | Built; not armed |
| Second-generation scraper service | Ten scrapers with sample outputs; seven already ported | Lanes | Parts of it solve challenges and scrape a blocked legal site. Those parts stay dead |
| Eight drafted letters | Permission and terms requests | Courts, exchange, press, company terms | All unsent |

## The four use cases

Each is sold in New Zealand today. What each provider sells was confirmed from its own site; prices and market sizes were not found.

| Use case | Who pays | Sold today by | What the estate would supply | What it tests |
| --- | --- | --- | --- | --- |
| Anti-money-laundering checks on companies and trusts | Law firms, accountants, real estate agencies, finance companies | [First AML](https://www.firstaml.com/nz/) | Ownership chains, directors and shareholders joined across entities, domestic politically exposed people | Person identity and chains through companies |
| Business credit reports and monitoring | Any firm extending credit to another business | [Centrix](https://www.centrix.co.nz/business/) | The public half: insolvencies, director histories, disqualifications, regulator actions | Dates and change over time |
| Tender and contract-award intelligence | Suppliers bidding for government and council work | [TenderLink](https://illion.tenderlink.com/tendering-for-suppliers) | Award notices joined to who owns and directs the winners, and to donations and appointments | The company-side join, built first |
| Due diligence on a company and its people | Buyers, investors, lenders, boards and law firms before a deal, hire or contract | Law firms, and investigation firms such as [The Investigators](https://theinvestigators.co.nz/services/legal-investigations/commercial-due-diligence-research), as one-off reports | One report across every register: ownership, the directors' other companies and failures, insolvency, regulator actions, land, political exposure | The whole estate at once, and namesakes above all |

All four have established sellers. Due diligence is the broadest: it needs nearly everything the other three need, and it was the project's first product idea in June 2026. The estate's likely edge is the connections between registers, which none of them sells.

## Proposed order

Arthur's proposal of 10 October 2026: build the feasible parts of the first three use cases from easiest to hardest, on the way to due diligence. It is a proposal, not yet a ruling.

1. **Tender and award intelligence.** Needs only the company-side join on the business number.
2. **Business credit and monitoring.** Adds dates and change over time.
3. **Anti-money-laundering checks.** Adds person identity and ownership chains.
4. **Due diligence.** The sum of the three, plus a keyword search of the journalism corpus for articles about the entity under review.

**Follow the Money comes before all four.** It is the first product built on the new modules and it stays live while that happens. The four use cases above keep their order behind it.

Four conditions go with it:

- **Feasible parts only.** Where a source is missing, the product says so; it does not guess.
- **One outside figure each.** Every use case names a published figure it must agree with before it counts as built.
- **Press is retrieval, not assertion.** Results are labelled as articles mentioning a name, and narrowed by requiring a company or role from the registers in the same article.
- **It sits beside Follow the Money.** Joining award notices to donors serves both the tender use case and the site.

Two prerequisites: the full-text search index (run sheet §AR, Arthur's to fire), and a licence answer on indexing the held NZME titles for a paying customer.

## The path

Each stage adds a capability, brings in the sources that capability can use, and unlocks the use cases that depend on it.

&#91;embedded content: the path · 5 stages, 5 gates\]

Read each row left to right: the sources a stage brings in, the capability they feed, and the use cases that capability unlocks. A stage does not hand over to the next until one figure from outside the estate agrees with ours. Four dated jobs sit outside this order and run regardless: the legal advice backstop on 1 November, the election on 7 November, sealing director addresses before 18 November, and the Tenancy and real-estate capture windows.

### Building toward Follow the Money first

Stage 0 is not groundwork done away from the product. It is Follow the Money moved onto the new modules, one part at a time, with the site live the whole way. This fits the path to the Muster 4 pre-pass, which already orders Follow the Money's work as reading, then register, then serving, then leaving the box. Each module is taken out of that work as its part of the order is done.

| Step | What is built | Proven on | Pre-pass work it comes out of | Cards |
| --- | --- | --- | --- | --- |
| 1 | Shared keys | Follow the Money's own donor and party names | Register | C357, C344, C167 |
| 2 | The reader contract | The party and candidate returns | Reading | C409, C411, C418 |
| 3 | Electoral returns as the first lane on the template | The published donation and expense figures | Reading, then register | C467, C116 |
| 4 | Identity | The donor ledger; its existing judgments move untouched | Register | C339, C342, C345 |
| 5 | Connections | The company behind a donor, the people behind the company, then what came out: award notices joined on business number | Register, then serving | C194, C224 |
| 6 | Follow the Money served from the new modules | The public site | Serving | C132, C156 |

Step 5's award join is the first new thing a reader of the site sees, and it is the same join that opens tender and award intelligence. Stage 1 starts from a product that already runs on the new parts.

**Continuity rules**

- **The daily release keeps running from the current chain.** Nothing in this plan pauses it, and its reading queue is not held up for the rebuild.
- **New modules are built beside the chain, not inside it.** They read the same documents and write their own tables.
- **A module takes over one job at a time.** It takes over only after it reproduces what the site publishes, with every difference explained by a named card.
- **The instruments already exist.** The release pipeline refuses to publish when a donor page's total falls against the day before, and the register is checked against the Commission's own table, which it matched to the cent on $14,560,581.38 on 10 October.
- **Each switch is undone by one change.** The old path is disabled and kept, as the retirement rule already requires.
- **Fixes made to the live chain meanwhile are carried across by their tests.**
- **Proposed: no switch of anything that feeds the public site before the election on 7 November.** Build beside it until then. This one is a suggestion and yours to rule.

This settles point 8 of the intake rule below: the path is fitted to the pre-pass order, not set against it.

## Sources on the path

Each source sits at the earliest stage that can use it. Most of this list comes from the project's own source survey of 18 August and its ideas backlog; none of it was rechecked against the publishers today, so treat "how obtained" as the last known position.

| Source | Stage | How obtained | Serves |
| --- | --- | --- | --- |
| Companies register, award notices, electoral returns, Gazette, charities register | 0 | Already held | Everything after |
| Live open tenders | 1 | Public, government tender site | Tender and award intelligence |
| Agency contract disclosures | 1 | Public, agency by agency | Tender and award intelligence; vetting bidders |
| Council procurement on other platforms | 1 | Public, council by council | Tender and award intelligence; Follow the Money for councils |
| Gaming-machine grants | 1 | Public, society by society | Grant-maker checks |
| Lottery grants | 1 | Public, government release | Grant-maker checks |
| Regional development funding (card C333) | 1 | Public, government release | Grant-maker checks; Follow the Money "what came out" |
| Charities data feed | 1 | Free bulk feed | Grant-maker checks |
| Local election returns, 2025 | 1 | Public, council by council | Follow the Money for councils |
| Daily company changes | 2 | Free bulk or interface, Companies Office | Business credit and monitoring; phoenix detection |
| Insolvency Register | 2 | Public register | Business credit and monitoring; phoenix detection |
| Disqualified directors (card C395) | 2 | Public register | Phoenix detection; contractor vetting |
| Regulator actions, read into a register (card C397) | 2 | Public, regulator by regulator | Business credit and monitoring; contractor vetting |
| Licensed building practitioners | 2 | Public register | Contractor vetting |
| Alcohol licences | 2 | Public, per licensing authority | Business credit and monitoring |
| Emissions trading register | 2 | Public register | Business credit and monitoring |
| Petroleum and minerals permits | 2 | Public register | Business credit and monitoring |
| Personal Property Securities Register | 2 | Paid, one lookup at a time | Business credit and monitoring |
| Filed financial statements | 2 | Inquiry drafted, not sent | Business credit and monitoring |
| Sanctions lists (Foreign Affairs, United Nations, Police designations) | 3 | Free, published lists | AML checks; board and executive screening |
| Limited partnership partners | 3 | Public register | AML checks; conflict checks |
| Financial service providers register | 3 | Public register | AML checks |
| Councillors' interests registers | 3 | Public, council by council | Conflict checks; politically exposed persons list |
| UK ownership data | 3 | Free, overseas | AML checks |
| Open beneficial-ownership data | 3 | Free, overseas | AML checks |
| Offshore leaks database | 3 | Free, overseas | AML checks; board and executive screening |
| Australian registers | 3 | Overseas, partly paid | AML checks; contractor vetting |
| Shareholdings of removed companies | 3 | Held in part; depth to confirm | AML checks; phoenix detection |
| Full-text index of the press corpus | 4 | Build from what is held | Due diligence |
| Court judgments | 4 | Needs a ruling (131 holds the legal estate) | Due diligence |
| Overseas Investment Office decisions | 4 | Built, switched off | Due diligence |
| Land titles | 4 | Licence limits use for individuals | Due diligence |
| Ministerial and mayoral diaries; chief executives' gifts and expenses | 4 or later | Public; on the later list | Due diligence; Follow the Money |

## Further use cases

Eight more that fall out of the same stages without new machinery. The buyers are my suggestions of who has the problem, not confirmed demand.

| Use case | Stage | What it answers | Likely buyer |
| --- | --- | --- | --- |
| Vetting bidders | 1 | Who is this supplier, what else have they won, who is behind them | Agency and council procurement teams |
| Grant-maker checks | 1 | Is this applicant a real, current body, and what other public money has it had | Gaming societies, community trusts, council grant teams |
| Follow the Money for councils | 1 | Who funded each councillor and mayor, and what did their donors win from the council | The public, local newsrooms; same product, new tier |
| Phoenix detection | 2 | Has a failed company reappeared under the same directors or address | Creditors, insolvency practitioners, trade suppliers |
| Contractor vetting | 2 | Is this builder licensed, solvent, and free of regulator action | Homeowners, developers, insurers |
| Board and executive screening | 3 | What has this person directed, owned, and been removed from | Recruiters, boards, investors |
| Conflict checks | 3 | Does a decision-maker have a declared or registered interest in the other party | Councils, Crown entities, law firms |
| Domestic politically exposed persons list | 3 | Who in New Zealand holds or held public office, and who are their companies | AML providers and their reporting-entity clients |

The first three need only the company-side join, so they arrive with tender and award intelligence. The last three publish connections about named people, so they wait on the person-identity gate and on the legal advice.

## Building it in modules

&#91;embedded content: module kinds · 4 in a chain on 1 shared base\]

Five kinds of module, with imports running one way. Adding a source never touches identity, adding a person rule never touches a source, and a product can be deleted without loss. A sighting is one register row naming a party, with its evidence.

| Module | What it owns | What it hands on | First built | Starts from |
| --- | --- | --- | --- | --- |
| Shared keys | Nothing; pure functions | Name key, address key, business-number and organisation folds | Stage 0 | The key functions now defined in at least nine places across six packages |
| Source lane, one per source | Its documents and its own register rows | Rows with date and evidence; sightings to identity; one outside check figure | Stage 1, then one per source | `gazette_register` and `courts_register`, which already have this shape |
| Identity | The ledger of judgments and the key view | A key, a candidate, or an abstention for each sighting | Stage 0 for companies, stage 3 for people | `donor_anchors`, `roster_folds`, `person_identity` and `folds`, lifted out of `registers` |
| Connections | A regenerated view of links | Who is linked to whom, with dates and evidence; from stage 2, what changed when | Stage 1 | New |
| Product, one per use case | Its pages and saved lists only | Answers to its users | One at each stage | `pi`, which is already close |

### Why change the cut

V3's rule is sound: a service is a package that owns its state, declares a contract, and has a test holding the boundary. It works where a service has one job and one store, as the graph writer, the model gate and the document reader do. It strains in three places, measured on the repository at commit `2d3874e` (10 October, 11:12):

- **Services cut by layer, not by job.** `registers` is about 14,800 lines in 39 files, owns roughly fifty tables and carries a 55 KB spec. `query` is another 15,400 lines and 57 routes. A change to one register means reasoning about all of it.
- **The largest body of code is outside the structure.** `ops` is about 47,500 lines across 157 top-level scripts with no spec. Thirty-one of them write to the database and seven write straight into the registers tables. Most source fetching lives there.
- **Shared logic has no home.** The two party-name folds disagree on six of 78 labels, and the product layer imports identity internals from `registers` though its spec says pure helpers only.

By the project's own count on 8 October, 21 of 24 services carry a spec and 8 fill in every section.

### Rules that make it hold

- **One-way imports, tested.** Keys, then lanes, then identity, then connections, then products. A product never imports from a lane. One test enforces the direction.
- **One template for lanes.** The thirty-odd sources on the path are the same job repeated. A lane's spec is five lines: the source, what it owns, what it emits, its outside check, its unit.
- **Lanes in parallel.** Lanes do not depend on each other, so each can be one session's queue, as the one-queue-per-service rule already allows.
- **No rewrite of `registers`.** Stop adding to it, lift identity out, and treat what remains as the electoral-returns lane.
- **`ops` shrinks by attrition.** A fetch script moves into its lane when that lane is next touched; `ops` keeps operations only.

### Products as exportable services

Each use case is a service that can run apart from the estate, and can be exported complete to another environment, without the estate holding two copies of its code or its data.

**What a product is made of**

- **Its own code:** pages, queries and rules.
- **A manifest:** the list of published views it reads, each with its licence terms and how often it must be refreshed.
- **Its own state only:** accounts, saved lists, usage.
- **The shared keys** as a pinned dependency, not a copy.

|  | Running inside the estate | Exported |
| --- | --- | --- |
| Code | The product's code | The same code |
| Data | Reads the published views directly | Reads a copy of exactly the views in its manifest, rebuilt from the estate on a schedule |
| Its own state | Kept in the product's own tables | Goes with it |
| Source of truth | The estate | Still the estate. The copy is rebuilt, never edited |

Follow the Money already works this way. It is built as a snapshot from the registers, checked by 15 gates, published to an outside host, and runs there without the estate. The first product on the new modules is therefore also the first proof of this point.

**Rules**

1. **A product reads only the views named in its manifest.** Never the inside of a lane or of identity. Today the Follow the Money app imports identity internals from `registers`; that goes.
2. **A product never writes into the estate.** It writes its own state and nothing else.
3. **Every row a product reads has a stable key.** Donation rows are renumbered every night today, which breaks both citations and any exported copy.
4. **Export is tested, not assumed.** Build the bundle, start it with no connection to the estate, and run the product's acceptance checks. A product that only passes inside the estate is not exportable.
5. **Withdrawals reach every copy.** A suppressed name (24 hours), a correction (5 working days) and the director address seal after 18 November all bind an exported copy as much as the estate. So an export needs either a refresh channel back to the estate or a recorded handover of those duties.
6. **Licences travel with the data.** Land title data on individuals may not be publicly indexed, press text waits on the NZME licence answer, and award notices need attribution. The manifest carries the terms for each view.
7. **No second copy of logic.** If a product needs a result the estate computes, such as a fold or a match, it gets the result as a column in a view, not a copy of the function.

**Open:** whether "another environment" means a second place this project hosts, or a handover to another party. Rules 5 and 6, and the privacy advice still owed, read differently in each case. Leaving the box at all is card C133.

This is a proposal. The three words of ruling 328 stand; what changes is where the lines between services are drawn, and that is Arthur's ruling.

## What already exists, and what it brings with it

Every piece the path could reuse, with the problems the repository's own records say it has and the cards that already know about it. Read at commit `2d3874e` (10 October, 11:12) from the open, parked and closed card registers, each service's spec, the lessons files and the Muster 4 pre-pass. "None documented" means nothing was written down, not that nothing is wrong. The last column is my recommendation, not a ruling.

### The module plan is mostly cards you already hold

The five module kinds are not new work beside the card register. About twenty-five open cards already describe them, raised at different times and filed under different queues:

| Module kind | Open cards that already are this work |
| --- | --- |
| Shared keys | C357 (seven divergent name folds), C344 (one address module) |
| Source lanes | C409 (one document-reader service), C411 (reader ground truth), C116 (register writers outside the package), C104 (no replayable table definitions), C201 and C202 (capture depth and breadth), C395 (disqualification register), C397 (regulator enforcement register), C330 to C336 (seven register-class feeds, C333 being regional development funding), C212 (capture-windowed sources), C403 (source-drift audit) |
| Identity | C339 (the fold over the whole director roster, GO under ruling 221, unbuilt), C342 (one resolved-roster view every join reads), C345 (review threads as a judgment table), C350 (region as a supporting leg, blocked), C159 (read the 22 corroborated donors) |
| Connections | C338 (address as a link), C194 (shareholder residue and limited partnerships), C224 (business-number anchoring for bankruptcies and court parties), C326 (legal form on organisations) |
| Products | C133 (leaving the box: serving box, TLS, domain), C132 (shape for a customer), C543 (search index width), C329 (completeness gate against publicdata.co.nz), C349 (acceptance runner for the wider app) |

Two parked cards belong with them: C353 (every entity's addresses as one view) and C348 (eleven reads that ignore which version of a judgment they are reading).

### Data already held

- **Company side:** about 1.1 million directorships, 1.5 million shareholdings, 720,000 registered offices, 330,000 trading names, and about 65,000 groups of companies sharing an address. These are the catalogue's minimum counts, not live counts.
- **Awards:** 29,874 government award notices from 2014 onward.
- **Trouble:** Gazette insolvency appointments, about 60,000 bankruptcies, director prohibitions, WorkSafe enforcement.
- **Officers and owners:** about 260,000 charity officers, trust boards, incorporated-society officers, land title owners (companies matched, individuals held back).
- **Public office:** about 9,500 Gazette public appointments, MPs' interests, MP and ministerial expenses, the electoral returns.
- **Not held:** sole traders, partnerships and trusts. The monthly company file covers companies only; the record says no bulk file will ever supply the others.

Two corrections to the path above. Stage 2 is further along than drawn: director prohibitions and insolvency appointments are already derived from the Gazette, so the Insolvency Register is mainly the outside check. And the press keyword search exists but reads only the title and first 1,500 characters of each article (C543).

### Shared keys

| Piece | Problems it carries | Cards that know about it | Recommendation |
| --- | --- | --- | --- |
| Name folds (several copies across `registers`, `query`, the graph writer and the document reader) | Seven divergent folds; one drops macrons, so Rāwiri and Rawiri differ. One fold is kept as three deliberate copies held equal by a test. The two party-name folds disagree on 6 of 78 labels and neither contains the other; the fuzzy rule folds New Labour Party into Labour at 0.88. | Open: C357, C467 (part), C167 (part: 371 nickname pairs stated by filers; merging on them cannot work). Closed: C457 (a strip-order bug in all three copies; 50,447 keys re-keyed), C480 (a fold existed and one page never called it, so 104 donors were published under more than one name), C367, C189, C118 (ruling 360: the director register is the given-name authority). | Take the rules, write one function. Do not promote any existing copy. |
| Address keys | The street key returns nothing for PO boxes and garbled text. An older key dropped street numbers under three digits; 160 folds were withdrawn for it. Only 482,733 of 759,477 registered offices carry a postal-address id. One address holds 1,060 companies, and address alone once grouped 25 ministers at Parliament. | Open: C344 (triaged, not started), C338. Parked: C353. Closed: C426. | Build as C344. Address never carries a match alone. |

### Source lanes: capture

| Piece | Problems it carries | Cards that know about it | Recommendation |
| --- | --- | --- | --- |
| Fetch gate (permission and pacing per host) | 35 older fetchers still bypass it, held by a ratchet. They include the config-driven document fetcher, Gazette capture and the charities client. | Closed: C220, C549 (Python's robots reader was over-permissive; 4 forbidden pages quarantined), C547, C535, C554 and C557 (hosts adopted without a permission row). | Take. No new lane may be added to the bypass list. |
| Landing contract | Five older entry points register a document before landing it, so a failed landing is never retried (half fixed). A second landing path is unresolved. | Closed: C218. | Take the one wrapper only. |
| Config-driven document fetcher | Not on the fetch gate. 70 of 73 sources have no archive walk. | Open: C201. Closed: C216. | Take after it is on the gate. |
| Headed browser for walled government sites | A challenged page is dropped, so fewer pages come back than were asked for. Both Hansard lanes are challenged today, and the 2026 candidate list has not been reachable. | Open: C524 (your ask, runsheet §AN), C151 (part), C168 (in progress). Closed: C370, C215, C528. | Take. A challenged read stays a failed read. |
| Coverage scan | For 86 of 222 source-and-weekday pairs the sparse test reduces to "published at all". | Closed: C541, C538, C500. | Take as is. |
| Charities lane | Its client is not on the fetch gate, its documented host no longer resolves, and it still imports a module marked "do not run". Officers land with no person key. Its timer had never fired at the 7 September audit. | Closed: C361. Parked: C303. | Take the idea (verbatim copy, then derive). Not the code template. |
| Award notices | Loaded by wiping and reloading, refreshed by hand each quarter, with no scheduled job found. The catalogue marks the typed derivation as pending. | None found beyond a "refresh card" note in the source list. | Take the data. A scheduled job and a derive are stage 1's first task. |
| Gazette register | Its schema file has drifted from the real tables. Its gate is soft: it records a failure and still exits clean. 35,938 parser abstains, 90.8% of them one celebrant format (reader built, wiring open). Existing rows owe a re-derive after two name fixes. | Open: C226 (part), C224, C222. Closed: C399, C183, C347, C432 and C434 (node1 blanked return totals nightly for 17 days). | Take after C224, which is stage 1's join. |
| Courts register | The feed has no scheduled job; extraction waits on your ruling on 131; about 67 documents quarantined; the suppress lever defaults to the old graph. | Open: C199 (your ruling), C063 (part). | Leave until the ruling. |
| Disqualified directors | The derive writes three tables that have no definition anywhere, in a schema the cutover dropped. | Open: C395. | Build as C395. |
| Regulator actions | 112 Commerce Commission cases and 16 FMA warnings are parsed and nothing reads them. The Act section is empty on all 128. | Open: C397. | Build as C397. |
| Register catalogue and count minimums | Seven live writers of register tables sit outside the package. The tables are created piecemeal in code, with no replayable chain. | Open: C116 (part), C117 (one part is yours), C104. Closed: C083 (a wipe-and-reload can serve a reader zero rows). | Take the catalogue. Settle C104 before adding thirty lanes. |
| Amended filings | Two rules only. "Prefer the amendment" is wrong in at least one case. Unmatched pairs are reported for a ruling. | Closed: C442, C446, C515, C517. | Take as is. |
| Publisher link | No link is served when the publisher's page was never captured. | None found. | Take as is. |

### Source lanes: reading documents

| Piece | Problems it carries | Cards that know about it | Recommendation |
| --- | --- | --- | --- |
| Page recogniser | The only one, with nothing behind it. Killed for memory on 28 September and now capped at 6 GB; a 12.4 GB run timed out against the cap. It had never actually run until 24 September. | Closed: C412, C417, C494. Open: C550 (part). | Take. It is a single point of failure for every scanned source. |
| Document reader and its checks | One reader since 25 September, so no automatic second opinion. Only 30 of 101 party returns match the total they declare. 264 of 844 stored reads fail their own stated total; tables of 6 to 20 rows pass 48% of the time. No scheduled job runs it. | Open: C418 (part), C411 (part), C461. Closed: C463, C433, C445, C422. | Take the checks and the answer-set method. Reader accuracy is unsolved; C411 is the instrument. |
| One reader contract | There is none: 11 text-extraction calls in 4 shapes across 9 files, and two duplicated converters. | Open: C409 (blocked on C411). | This is the lane template's reading half. Build as C409. |
| Profiles and corrections | A profile is pinned to the code both ways for one form only. 379 of 381 corrections are marked machine-agreed, not person-confirmed. 16 corrections reach no page. | Open: C186 (part). Closed: C448, C450, C424. | Take. Make the reader run from the profile as part of C409. |
| Model client | For most jobs it records a wrong model and carries on; requested and served matched in 13.8% of 334,763 calls. | Closed: C413. Open: C454 (your call). | Take, with refusal turned on for every new lane. |

### Identity

| Piece | Problems it carries | Cards that know about it | Recommendation |
| --- | --- | --- | --- |
| Donor matcher | Weights are hand-set. One rule accepted by a rounding margin (now pinned). The audit sample of 22 is unread. A withdrawn match once supported new ones. | Open: C159 (yours), C377 (part), C350 (blocked: "a pass rule needs an arm, not a sum"). Parked: C348. Closed: C112, C113. | Take the ledger and the two rules. Not the weights. |
| Director-record folds and their watch | Built for donor and MP names only; the whole 1.19 million rows is unbuilt. 857 of 5,314 folds were contested at the first run. | Open: C339, C342, C165. Closed: C340, C341. | Build as C339 and C342. This is stage 3. |
| Ordered resolver | None documented. | Closed: C343. | Take as is. |
| Verdicts and review threads | The only verdict is "hold", tied to a weights version. Threads are still a file. | Open: C345 (first piece landed). Closed: C458, C428, C430 (six rules for only asking what a person can answer). | Take. Re-key verdicts to rule and evidence. |
| Review page | Comments only by ruling 324; its routes are untested. | Closed: C109. | Take as is. |
| Hand-labelled answer set of 207 | Scores 134 of 207. It labels names in press text, not register rows. A rebuild takes 40 to 90 minutes. | Open: C233. | Take the method. Stage 0 needs its own set. |
| Company shareholder anchoring | Done by name because the business number is empty on all 1.58 million rows. 26,857 rows have no match; limited partnerships are unrecovered. | Open: C194. | Take. C194 is on the path at stage 3. |
| Press-graph merge judge | Contradicts itself on 10,813 names; 1,310 merges ran on one. Its test set of 13 cannot carry its own threshold. | Open: C429 (yours), C540 (part), C404. | Leave, with the press graph in maintenance. |

### Connections

| Piece | Problems it carries | Cards that know about it | Recommendation |
| --- | --- | --- | --- |
| Directorship, shareholding, office and shared-address views | An ended role is dated to the day the file was imported, not the day it ended. That is the gap stage 2 has to close. | Open: C326. Closed: C192 (of 151 name-matched directorships, 15 had a supporting link). | Take. Real dates need the daily change feed. |
| Exposure build | Served with no reader since 30 September. | None found. | Take the idea. |
| Vehicles build | None documented. Ruling 253 governs: a company stays its own donor and ownership is a note, never summed. | Closed: C378. | Take as is. |
| Land title owners | Individuals are held with no matching. The takedown service the licence obliges is parked. | Open: C351. Parked: C388. | Stage 4, and C388 first. |

### Products

| Piece | Problems it carries | Cards that know about it | Recommendation |
| --- | --- | --- | --- |
| Follow the Money app | A parsed return total is held for under half the party-years since 2019. The donor picker cuts its list before folding names, so a donor can lose its page when others gain money. | Open: C132, C156 (part). | Take as the pattern for a product. |
| Release pipeline | Every gate reads one output. On 3 October a fold took $8,024,342 across 110 donors off the site and eleven gates passed it. None of fifty board checks asserts the value of an answer a user sees. | Closed: C497, C521, C518, C469. | Take, and give each product one check against a figure from outside. |
| Citation resolver | Donation citations point at row numbers that are renumbered every night. | Closed: C346, C106, C526, C184. | Take. Every lane must give rows a stable key. |
| Rules that must cite | The company rule set is unbuilt and there is no hostile test set (spec dated 16 August). | Closed: C121. | Take the idea. The rules need rework for credit. |
| Watchlists and feed | The acceptance check is "to build". Table changes run from the product's entry point. | Open: C349. | Take with care. |
| Press keyword search | Reads the title and first 1,500 characters; 77.5% of articles are longer. | Open: C543 (yours to fire; never during a serving session), C323. | Prerequisite for stage 4. |
| Rate limit | Its spec calls it a courtesy bar, not a control. | Closed: C085, C126. | Not enough for strangers. See C133. |
| Gap miner | Its web fetch is described as the strongest injection channel in the estate, and it is not on the fetch gate. | Closed: C086. Open: C188. | Take for internal use only. |

### Orchestration

| Piece | Problems it carries | Cards that know about it | Recommendation |
| --- | --- | --- | --- |
| Era orchestrator | Jobs it pauses do not restart themselves. It reads another service's log format. Its resume and exit defects closed on 5 and 6 October. | Closed: C016, C017, C034, C026. Parked: C014, C019. | Take the pattern. It needs generalising beyond press re-reads. |
| Work queue | One item per claim. None else documented. | Open: C010 (3 GB per worker; specific to press extraction). | Take as is. |
| Fleet control (job registry, scheduler, executor, run history) | Nothing runs the scheduler on a clock; queue depth is not measured; a three-job collision at 03:30 is open. Five jobs now record their runs, so the spec's statement that none do is stale. Wrapping one job broke it for eight days. | Closed: C415, C416, C488, C414. Parked: C021. | Take run history now, the scheduler later. |

## Infrastructure

### Built

| Piece | Problems it carries | Cards that know about it |
| --- | --- | --- |
| Primary database, standby and floating address | One failover drill is recorded (24 August); the address move has not been re-drilled. Restarting the address job aborts. The failure log records and nothing acts on it. Both boxes reach the internet over Wi-Fi. | Open: C054, C221g (a cable; yours). Parked: C390. Closed: C380 (cold restart in 39 seconds). |
| Off-site backup and restore | Of 368 GB sent each night, 146 GB has no way to be rebuilt. The restore rehearsal passes at 90% of the primary, not equality. Rehearsed restore times: 17 minutes for the registers, 315 minutes for the graph. | Open: C321, C322 (part). Closed: C046, C059, C449. |
| Job manifest across the two boxes | The moves of database-adjacent jobs to node1 are part done. | Open: C316, C393. Closed: C436. |
| Daily board | 11 of 73 checks were red on 10 October. Unit test suites run only when someone runs them. | Closed: C529, C498. |
| Monthly company register import | By hand, monthly. No daily change run has ever completed, though one is designed. Your word of 19 September is on the record: it is yours, it is scheduled, and nothing should re-raise it as a card. | Closed: C531. |
| Sealed address store | Built and not yet fired. The board goes red on 4 November without a seal. | Open: C232 (yours to fire before 18 November). |

### Not built

| Need | Cards that know about it |
| --- | --- |
| Live serving to customers (hosted box, TLS, domain) | C133, open. The pre-pass places it last, after the product is worth showing a stranger. |
| Customer accounts, keys, metering, billing | None found. |
| One-sitting rotation of every password and key | C087, open, yours to run. The record calls it stop-the-world. C102 (the walk-away container) sits beside it. |
| Daily company changes | The design exists. Stage 2 needs it, which is in tension with the standing word on the monthly import. That is yours to rule. |
| One home for register table definitions | C104, open. |
| Tests on every push | None found. C511 (the overhaul) touches it. |

## Intake rule: reuse without importing the old problems

Two risks sit in everything above. A piece can bring its defects with it, and a piece can be rebuilt without what its cards already learned. These rules are a proposal for holding both.

1. **Each piece gets a verdict before it is used.** One of four: take as is, take after a named card closes, take the idea and rebuild, or leave. The recommendation columns above are a first pass. Nothing is reused on the strength of existing.
2. **Reuse through a contract, never by copy.** The seven name folds are what copying produced. A module either imports the one function or does not use it.
3. **A reused piece passes one check against outside truth before a lane depends on it.** The release pipeline passed eleven gates on a wrong site because every gate read our own output.
4. **The cards travel with the piece.** When a piece moves into a module, its open cards are re-homed to that module's queue, and the lessons its closed cards filed are read first. The tool for that exists: `ops/lessons_for.py --paths` prints every lesson filed against a set of files, and ruling 359 already requires it at planning.
5. **A card the new design answers is closed as superseded, with a pointer.** It is not left open beside the work that replaces it. The first table in the section above lists the candidates.
6. **New lanes never join an old debt list.** No new fetcher on the gate's bypass list, no new writer of register tables outside its own package, no new table without a definition in one home.
7. **Lanes run in parallel only if each owns its tables and its derive.** The pre-pass already records the hazard (its conflict C-2): two changes landing through one derive that wipes and reloads the register tables make the cause of a moved figure unknowable. A lane that shares a derive is not independent.
8. **The pre-pass order stands until you change it.** It puts Follow the Money's reading work first and the register feeds after it. The path in this document would have to be fitted to that order or replace it, and that is your ruling.

### Rebuild or move

Flagged as important to the plan (Arthur, 10 October). Whether to rebuild a piece or move it depends on where its value sits.

| Treatment | Pieces | Why |
| --- | --- | --- |
| Rebuild, with the old code as reference | Shared keys, the lane template and reader contract, identity, connections | Their defects are structural: seven copies of a fold, hand-set weights, one package doing ten jobs. Patching carries the shape forward. They are also small. |
| Move as is, behind a new contract | The fetch gate, the headed browser, the amended-filings rules, the judgment contract, the per-form parsers and profiles, the release pipeline | This code is mostly edge cases paid for one at a time. A rewrite would relearn them, which is what the lessons file was created to stop. |
| Leave in place until it is replaced part by part | The Follow the Money chain | It is live. See the path-critical points. |

In the project's three words: redeploy units, rebuild the boundaries between services, and decide module by module.

### What the cards are for

The cards fall into three kinds, and each kind is worth something different.

| Kind of card | Examples | In a rebuild | In a redeploy |
| --- | --- | --- | --- |
| A fact about the outside world | The Commission's form changed its part letters three times. Address alone grouped 25 ministers at Parliament. Python's robots reader is over-permissive. | Fully useful, more than the old code. It is a requirement whatever the code looks like. Mostly closed cards. | Useful as a warning not to break the fix. |
| A defect in the old structure | Seven folds. Writers outside the package. 35 fetchers bypassing the gate. | Becomes one line of acceptance, then is closed as superseded. | It is the to-do list. |
| An operating scar on a specific job | Wrapping one job broke it for eight days. node1 blanked totals for 17 days because it lacked the page reader. | Applies almost unchanged, because a new lane still runs as a scheduled job on the same two boxes. | Applies unchanged. |

The cards cited in this document have not been sorted into these kinds one by one. The split is a reading of the ones pulled for the tables above.

### Three rules for a rebuild

1. **Carry the tests first.** The old tests are the lessons in a form that runs. The new module passes them before it replaces anything, except tests that only pin the old structure.
2. **Never rebuild the data.** Judgment ledgers, corrections, profiles and answer sets move across untouched.
3. **Account for every difference.** Run old and new over the same real rows. Each row where they disagree must be explained by a named card saying the old answer was wrong. An unexplained difference is a regression.

The third rule is what forces the cards to be read, and it shows which old behaviour was a fix and which was a fault.

### What this section does not cover

- The card register moves daily. Anything raised or closed after 11:12 on 10 October is not here.
- The problems listed are the documented ones. A piece with "none documented" has not been audited by this pass.
- Card ids were checked to exist in the registers. The one-line descriptions are mine and shorter than the cards.

## Gaps for anti-money-laundering checks

Held today: companies with directors and shareholders, charities and their officers, society officers, and domestic politically exposed people (MPs, ministers, candidates, Gazette appointments).

| Gap | What it blocks | Can it be closed? |
| --- | --- | --- |
| Trusts | Seeing who is behind a trust | No. New Zealand has no public trust register. Sellers today collect the trust deed from the client. |
| Overseas owners | Any chain that leaves New Zealand | Partly. Only the global legal-entity register (GLEIF) is held. Foreign company registers are candidates; terms to check first. |
| Sanctions lists | Screening | Yes. The MFAT Russia list, the UN lists and the Police terrorist designations are public and not captured. |
| Foreign politically exposed people | Screening | Not as things stand. The main open source is licensed non-commercial, which the commercial ruling (113) excludes. |
| Limited partnership partners | Who is behind a partnership | Likely yes. The register is public; partner detail is not captured. |
| Shareholdings of removed companies | Ownership history | Open since 19 August. The bulk feed drops them; per-company filings or our own snapshots going forward are the options. |
| Identity documents | Verifying the individual | Out of scope. Not a public record; a partner's tool would do this. |

## Gaps for business credit and monitoring

Held today: Gazette bankruptcies and insolvency appointments, director prohibitions, and charity financials.

| Gap | What it blocks | Can it be closed? |
| --- | --- | --- |
| Daily company changes | Monitoring. The companies register arrives as a monthly bulk file imported by hand, and the API has no change feed. | Partly. A more frequent bulk pull, or the register's own change-notification watchlists, are the options. |
| Security interests (PPSR) | Who holds security over a business | Only as a lookup. The register is public but searched one record at a time; there is no bulk. |
| The Insolvency Register | Bankruptcies and no-asset procedures at source | Yes. It has a free API and is not captured. |
| Court judgments | Debt and liquidation proceedings | Needs a ruling. Judgments are captured, but the whole legal estate is held under ruling 131, and the permission letter to the Ministry of Justice is drafted and unsent. |
| Filed financial statements | Financial health | Unknown. The inquiry to the Companies Office is drafted and unsent. |
| Regulator actions | Adverse history | Yes. Commerce Commission, FMA and WorkSafe are captured but not read into a register (card C397). |
| Disqualified directors | Banned persons | Yes. The derive runs; the register has no home yet (card C395). |
| Payment defaults | Credit behaviour | No. This is private bureau data. |

## Gaps for tender and award intelligence

Held today: 29,874 government award notices from 2014 onward, and minutes from 24 councils.

| Gap | What it blocks | Can it be closed? |
| --- | --- | --- |
| Live open tenders | Alerts on new opportunities | To verify. Only awards were found in the estate. The government tender site is public. |
| Procurement outside the government tender site | Coverage of councils, council companies and state-owned enterprises | Partly. Other council platforms are surveyed but unbuilt. Private tender portals fall under the robots and terms rules. |
| Contract values | Sizing a contract or a supplier's book | Partly. Award notices often omit them; agencies' own contract disclosures are not captured. |
| Grants and funds | Public money that goes out other than by contract | Yes. Regional development funding and similar are carded, not built (card C333). |

## Gaps for due diligence

A due diligence report needs nearly everything in the two tables for anti-money-laundering and credit, plus the gaps below.

| Gap | What it blocks | Can it be closed? |
| --- | --- | --- |
| Court judgments and litigation | The core of any due diligence report | Needs a ruling. Same hold as above (ruling 131). |
| Adverse media | Reputation | A capability gap, not a source gap. The corpus is held, but press is parked and search reads only a title and the first 1,500 characters (card C543). |
| Tribunal and disciplinary decisions | Adverse history of a person or firm | Partly. Tenancy and Real Estate Authority decisions expire from public view after three years, so late capture means no capture (card C212). Other professional bodies are not captured. |
| Occupational licences | Whether someone is licensed to do what they claim | Yes in principle. Builders, real estate agents and financial service providers have public registers; none is held. |
| Land holdings of individuals | A person's assets | Limited by licence. Title owners are held, with individuals' rows held back under the LINZ personal-data licence. |
| Criminal history | Character | No. It is not a public record. |

## Gaps across all four

Four gaps sit under every use case.

- **The identity service.** None of the four works without knowing that a person in one register is the person in another.
- **The legal-estate hold.** Ruling 131 keeps court judgments out of extraction. It matters most to credit and due diligence.
- **Licence terms for commercial reuse.** Each source's terms need reading against a paid product, the LINZ personal-data licence first.
- **Regulated ground.** Credit reporting has its own rules, anti-money-laundering checks must rest on sources a regulator accepts, and any report about an individual falls under the Privacy Act. Legal advice comes before selling.

## Still to verify

- [ ] Whether the ultimate-holding-company field from the companies register is loaded.
- [ ] Whether live open tenders are captured, or only awards.
- [ ] Whether the award notices' supplier table carries business numbers.
- [ ] How complete the Gazette liquidation and receivership derive is.

This page lives outside the repository. For any of it to bind the work, the working session needs to card it.

## Ruling 54: keep the new estate quick to work on (12 October)

The new estate is built so that a prompt gets an answer quickly, and that speed is measured. Arthur: "I want to be able to easily work on the new estate. It takes a long time to get an output from a prompt on the old estate. Is there a way we can design to keep things nimble?" On hearing the seven rules below: "do it".

**What was measured on the old estate.** Sizes are from the read-only copy at commit `2d3874e`. Session times themselves were not measured.

| What a session reads or runs | Size |
| --- | --- |
| The orientation file | 13 KB |
| The operating method it points to | 42 KB |
| The lessons: ten section files and an index | About 700 KB. One section is 160 KB, and the search tool prints sections whole |
| The open card register | 88 KB |
| The rulings file | 335 KB |
| The day-log, which every close adds to | 1.6 MB for September; 1.1 MB for October by the 10th |
| Test files | 585 |
| Document checks before every push | 40 |
| Rebuilding the answer set after a change | 40 to 90 minutes |
| One release | About 25 minutes |

On top of the reading, every prompt was treated as a full card: lessons searched twice, four questions answered twice, a day-log entry and a pushed commit, even for a question.

**The seven rules**

| Rule | What it means | Where it sits in the build plan |
| --- | --- | --- |
| 1. Three weights of session | A question session is read-only, with no card and no ceremony. A fix session changes one module, and its merge request is its whole record. A build session runs the full process | "Three weights of session" |
| 2. A limit on required reading | The plan is split into one file per step and track. A question session reads about 10 KB, a fix session about 43 KB, a build session about 77 KB | "What to read, and how much" |
| 3. Nothing that grows is read whole | One file per card, lesson and decision. The lessons search returns at most eight rules. The status file is overwritten and kept to a page. There is no day-log | "Lessons", "Picking up", "Closing a piece of work" |
| 4. Two tiers of checks | A fast tier, aimed at under a minute for one module, on a small sample with stored model readings. The full tier is run by the integrator at the merge, and all of it nightly | "Two tiers of checks" |
| 5. Rebuild only what changed | One document or one day's file is re-read without rebuilding the rest. The same for links, groups and search tables | Register rule 10 |
| 6. Data questions come from the published tables and the board | Sessions look at data through one command, on a login that can only read, with a 30-second and 200-row limit. A longer query gets ten minutes, one at a time | "Three weights of session"; step 0 |
| 7. It is measured | Two hooks time every prompt. The checks board shows the typical and the worst wait for each weight. A check fails when required reading passes its limit | "Keeping the work quick"; step 1b |

**What it costs.** Question and fix sessions check the lessons less than a build session does, so a lesson can be missed. The integrator's full checks at the merge are the backstop. No hard limit is loosened: a question session obeys every one.

**Found on the way.** The build plan had itself grown to 190 KB, and every brief told its session to read it. That was the old mistake repeated. The plan is now split in step 1.1, and only the first founding session reads it whole.

**Three things that differ from what Arthur was first told.** The orientation file is one page plus the hard limits, 10 KB in all, and not one page: the limits bind even a session that only answers questions, so they stay in front of every session. Step 0 gains two logins and a small second database for Arthur to create: a read-only login for sessions, a read-only login for products, and the sample database. And the tools themselves are a new piece of work, step 1b, done inside step 1.

**Two independent reviews, and what they changed.** The first found 25 problems in the first draft. The three most serious were about safety: a question session was held read-only by the file-edit hook alone, its login could read home addresses, and a "longer question" would have run through a path that could write. The second review checked the fixes and found 12 more, two of them serious: any session could have added a job to the list the safety hook lets a session stop, and a question session could still have reached home addresses through the old databases.

As the plan now stands:

- The hooks refuse a question session every edit, commit, push, job control and any credential file but its own. Its login can only read, and is never granted the tables that hold a person's home address, or the seal.
- A question session has no login to the old databases, because they hold home addresses. Until a lane for the data is merged, a question about old data goes to a build session.
- The list of old jobs that may be stopped sits outside git, only a founding session may write it, and the hook names every carve-out job as never stoppable.
- Each session fills its own copy of the sample, and each module keeps its own sample list as hashes and keys only, so parallel sessions cannot disturb each other and no personal data enters git.
- The merge gate loads only the modules a branch touches, and a source that is down no longer fails an unrelated merge.
- The limits were re-set from measured sizes: the core file is 24.7 KB against a limit of 27, and step 1 is 26 KB against 28.

The fixes for the second review have not been read by a third reviewer, and nothing has been tried on the boxes.

**The numbers are starting guesses.** The budgets and time targets are set from judgment, not from measurement. After the first week of timings the integrator proposes real ones in the decision queue.

## Models seen on 13 October: the KDnuggets article

Arthur sent [10 Hugging Face Models Worth Knowing in 2026](https://www.kdnuggets.com/10-hugging-face-models-worth-knowing-in-2026) (KDnuggets, Vinod Chugani, 12 October 2026). Three of its ten models bear on the plan, one is optional, and the rest do not apply. Nothing below is in the plan yet; it waits on Arthur's word. The article is newer than Claude's own knowledge, so the figures are the article's, and no model card was read.

| Model | What the article says | Bearing on the plan | Recommendation |
| --- | --- | --- | --- |
| Qwen3.8-27B | The default open base model of 2026; reads images and video as well as text; Apache 2.0; about 16 GB at 4-bit | A challenger for the text reader, which is Qwen 3.6 35B today. Fits one card. Community llama.cpp files exist. Another Qwen, so it cannot be the second page reader from a different family. It may be slower per page than the current model, which uses only part of itself for each word | Add to the step 3 trial, scored on the same answer keys, with speed measured |
| Qwen3-Embedding-0.6B | 596 million parameters; leads the open-weight MTEB leaderboard at its size; Apache 2.0; needs an instruction prefix on queries | The embedding model must be chosen before 86 million Papers Past items are embedded, because changing afterwards costs weeks. The article itself still names bge-m3 for mixed keyword-and-meaning search, which supports the current choice | Add a side-by-side to the one-million recall proof in step 7.4, on old newspaper text and te reo |
| ModernBERT-base | An encoder for classification and name tagging; 8,192-token context; Apache 2.0; meant for fine-tuning on labelled data | The broad name index over Papers Past (ruling 43) has no stated method. A small tagging model is far faster than a chat model over millions of articles. It needs labelled examples, which the registers and place names could supply, and is English-trained, so Māori names need testing | Note as an option in step 7.5 |
| Gemma 4 (31B) | Google, April 2026; Apache 2.0; third on a text leaderboard at launch | A different family from Qwen and from GLM-OCR, so a possible independent second text reader or reviewer | Optional |
| DeepSeek-V4.1-Flash | 552 billion parameters, MIT | Far too large for four 34 GB cards, and hosted use breaks hard limit 10 (no text leaves the boxes) | No |
| SAM 3, DINOv3, FLUX.2 klein | Image segmentation, vision features, image generation | No use in the estate | No |
| Whisper large-v3-turbo | Speech recognition | No audio source is in the plan | No, unless an audio source is added |
| all-MiniLM-L6-v2 | The common embedding baseline; short inputs | Older and English-only; bge-m3 and the Qwen embedding both exceed it | No |

**What this would change in the plan if Arthur agrees:** step 3's model table gains a row and a text-reader comparison; step 7.4 gains an embedding comparison before the long run; step 7.5's name-index row names a method.

## Notes from Arthur, 16 October

Given in the old repository's last session, after the plan was pushed. In his words: (1) *"the core architectural change we are making is we are creating a rich spine made of multiple joined registers"*; (2) *"once we have the multiple joined registers we can use them for name resolution for press"*; (3) *"instead of the deterministic extraction using a large register of names, I would like to experiment with ModernBERT-base for name resolution. I am also interested in other things it can do."* The build plan carries them: the first at the top of "What we are building", the second under "Deliberately not built", the third as track D.2, the name-resolution experiment, with the joined registers as its answer key. None opens a new step; the third earns one only by its measurement.
