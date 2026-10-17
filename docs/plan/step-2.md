## Step 2: the scheduler, first build

**Goal.** One service that places every job on a graphics card or on the processor, on either box, and survives the loss of one box's worker.

**Why now.** The page-reader trial in step 3 is its first real job, and every later step queues work through it. The simplified estate needs far less hardware in steady running, but Arthur ruled that the full design is kept because the work may grow (ruling 48).

**Model.** Fable. Several sessions, one at a time, each continuing from `docs/status.md`.

### What Arthur asked for

- Either box can take over from the other after an unplanned shutdown, in either direction.
- Everything is held on both: code, services, data.
- Both boxes do work all the time. Neither is a spare.
- Every task is placed by one service. With four graphics cards, four work; with two, two work.
- Each graphics card is set up for the job it is doing: which model, with what settings. A card full of one model is not also handed another.
- Each box has a hardware profile. A job that speeds up with more memory goes to the bigger box with more parallel workers, and runs smaller on the other when that box is away.

### What exists to build on

Extend the old fleet service; do not bring in a general cluster manager. Two boxes and four cards with model-specific settings is a narrow problem.

| Part | Exists in the old repository | Missing |
| --- | --- | --- |
| What each job needs | `ops/fleet/jobs.py` and `config/job_types.yaml`: model, context, slots, measured memory, priority per job type | Processor-only jobs; memory per worker |
| Rules for sharing a card | `ops/fleet/schedule.py`: five rules, a pure function, fully tested | Never run against a real queue |
| Changing what a card holds | `ops/fleet/control.py`: swaps a card's model and settings, rehearsal mode by default | Nothing calls it on a clock |
| Job history | `ops/fleet/runs.py` and the wrapper `ops/fleet/runjob.py`; five old jobs record their runs | Peak memory; every job |
| Seeing the hardware | `ops/fleet/probe.py` reads node2 only | node1; disks; installed programs |
| Queue depth | Nothing | Needed before the planner can decide |
| Taking over a dead box's jobs | A lease-and-token pattern in `ops/extract_queue.py` | Not applied to jobs in general |

### Do

**2.1 One job queue, kept in the new database,** so it moves with the database when a box is lost.

**2.2 A worker on each box.** It probes its own box at start and on a clock, reports what it has, and pulls the most urgent job it can run. Losing a box means one worker stops pulling.

**2.3 The hardware profile is probed, never typed.** Cores, memory, each graphics card and its memory, each disk and its free space, and **the programs installed**. A typed profile goes stale the day hardware changes.

**2.4 Every job declares what it needs:** a model profile or the processor only, memory per parallel worker, a deadline, a query time limit, whether it can share a card, and optionally "prefers the most memory".

**2.5 Parallelism is worked out, not fixed.** The number of workers a job gets on a box is what fits in that box's free memory after a reserve for the database and the standing services.

**2.6 A hard ceiling per job.** A job that outgrows what it declared is stopped; the box is not. The run record keeps each job's peak memory, and a job whose peak passes its declared cost is flagged so the figure is corrected.

**2.7 A graphics card holds one profile at a time.** A profile is a model plus its settings. Jobs matching the loaded profile run together up to its stated slots. Every swap is written to a ledger with its reason.

**2.8 Leases.** A running job holds a lease it must keep renewing. If its box dies the lease lapses and the other worker takes the job. Jobs are cut into pieces that record progress, so little is redone.

**2.9 The graphics cards the carve-out holds are reserved.** `querynz-agent-llm` (the chat model the declared-donations feed reads with) holds a card on node2. `querynz-vision-ocr` (its page reader) runs on both boxes and is not pinned to a card, so each box has a reservation. Both run outside the scheduler. Register the cards they hold as fixed reservations the planner never evicts; the baseline says which cards those are. `querynz-gpu-gateway` is also part of the carve-out but holds no card. The scheduler therefore starts with fewer than four free cards; that is expected.

**2.10 An alarm from the other box.** If one worker goes silent, the other raises it, through whatever channel the baseline found reaches Arthur. node2 once went down for four days and nobody knew.

**2.11 One installer** puts the same code, job files and model files on both boxes, and copies the credential files from box to box directly, never through the repository. It installs only jobs with the `qv4-` prefix and never changes or removes any other job. It installs a new build of the model server beside the old one, never over it.

**2.12 The clock belongs to the scheduler.** A job that runs on a timetable has its timetable in the queue, not in a timer on one box. So when a box is lost the survivor runs the job with no hand step. In the old estate, enabling a job on the surviving box was done by hand.

**2.13 Standing services are jobs too.** The apps and model servers each carry a wanted count and a priority, so a surviving box starts whatever is missing in order of importance, within what one box can carry.

**2.14 A re-read is a job type.** Re-reading a set of documents after a reader, a document profile or a rule changes is queued like any other bulk job, cut into pieces, and compared with what it replaces before it lands. Nobody fires it by hand (ruling 45).

**2.15 The new estate's own model profiles.** Create at least these, on cards that are not reserved:

| Model profile | Model | Settings to start from | Used for |
| --- | --- | --- | --- |
| Text reader | Qwen 3.6 35B (`qwen3.6-35b-a3b-q4km`) | Two requests at once, 50,000 tokens each, about 25 GB on a card, temperature 0 | Turning text into rows; the old job type was called `document-read` |
| Review and questions | The same model | Start from the old `reasoning` settings | The review agent; answering questions in products |
| Embedding | bge-m3 | Prompt cache off; many copies per card | Search |
| Page reader | GLM-OCR, then whatever step 3 chooses | One request at a time, 300 dots per inch pages | Image pages |

### The nine rules for sharing the graphics cards

Rules 1 to 5 exist in `ops/fleet/schedule.py` and came from Arthur's ruling of 22 September. Rules 6 to 9 are new.

| # | Rule | What it handles |
| --- | --- | --- |
| 1 | A job whose queue is empty gives its card up at once | Idle cards |
| 2 | A job keeps its card for up to one hour while it has work, then others get a turn | Long jobs blocking others |
| 3 | At the end of a turn the card finishes what is in flight and takes nothing new. Nothing is killed | Half-finished readings |
| 4 | Waiting jobs take turns in priority order; a job that has had a turn goes to the back | Starvation behind a busy job |
| 5 | A swap must pay for itself. A card already holding the right model is taken at no cost | Small jobs causing swaps |
| 6 | A small job never waits for ever: if its queue stays too short to justify a swap, it gets one after a set maximum wait. Start at 30 minutes | Small jobs stuck behind rule 5 |
| 7 | Long jobs are cut into pieces of a few minutes, each recording its own progress | Long jobs that cannot be interrupted |
| 8 | Three classes: someone is waiting; due by a time; whenever. A waiting person goes first, a due job next as its time nears, bulk work fills the rest | Deadlines and live questions |
| 9 | A bulk job takes every free card but gives cards back when others queue. The swap cost in rule 5 is the measured load time of each model, not a fixed number | One job holding every card |

**Whether one card is kept free for live questions is undecided** (ruling 22). The recommendation, and the default until Arthur rules: no card is kept empty. While any product is being served, one card holds the review-and-questions profile, takes bulk work for that same profile, and keeps part of its slots for live questions. Embedding one search query runs on the processor and needs no card.

### Traps the old estate paid for

- **Identical code on two boxes is not identical capability.** node1 lacked the page-reading program and blanked the return totals every night for 17 days with the board green. This is why the profile records programs.
- **A wrong model was served and nobody was told.** Of 334,763 model calls, the model asked for was the model that answered in 13.8%. Every lane in the new estate refuses an answer from the wrong model.
- **Wrapping one old job in the run recorder broke it for eight days,** on an unquoted path with a space in it. The new repository's path has no space; quote paths anyway.
- **A job killed at its deadline leaves its database query running.** Hence the query time limit.
- **Memory has run out before.** On 23 September node1 ran out outright and the database's next request triggered the kill. On 28 September the page reader was killed for memory and is now capped at 6 GB.
- **Both hardware clocks hold local time,** 13 hours ahead of UTC in summer. Store and compare times in UTC.
- **Three jobs collided at 03:30** in the old timetable. A queue removes the cause; check it did.

### Done when

- [ ] The old planner tests pass, and new tests cover rules 6 to 9.
- [ ] A worker on each box has registered a probed profile, programs included.
- [ ] A job needing a program only one box has is never given to the other.
- [ ] A swap happens for a real job and the ledger matches what the card actually held.
- [ ] A worker stopped mid-job loses at most one piece, and the other box finishes the job.
- [ ] A job that passes its memory ceiling is stopped and the box stays up.
- [ ] Stopping one worker raises an alarm from the other box.
- [ ] The reserved cards of the frozen product were never touched.

* [ ] A job on a timetable runs on the surviving box with no hand step when the other worker is stopped.
* [ ] The four model profiles in 2.15 load on cards that are not reserved, and the text-reader profile reproduces a reading the old estate holds.
* [ ] A re-read of ten documents is queued, runs in pieces, and is compared with what it would replace.

### Brief to paste

Launcher: `bin/start-session scheduler support/scheduler support/installer support/profiles`

```text
You are a build session for QueryNZV4, running as Fable on node2, in
the working copy the launcher made for you. Read docs/PLAN.md, then
docs/status.md and your own status file, and continue where it stops.
Do step 2: the scheduler's first build. Extend the old fleet service
(ops/fleet in the reference copy of the old repository) rather than
starting again; carry its tests first. Search the lessons for
scheduling, memory and model serving before you write anything. Never
touch the frozen product's servers or the cards they hold. Push your
branch and raise a merge request for each finished piece. Update your
status file at every close. Finish by telling Arthur what closed,
what is carded, what waits on him, and whether step 2 is finished.
```

