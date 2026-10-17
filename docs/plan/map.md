### Where everything is

This plan was written from a read-only copy of the old repository at commit `2d3874e` (10 October 2026, 11:12 NZDT) and without sight of the boxes. **Anything it says about live state is to be measured before it is relied on. Where the boxes differ from this plan, the boxes win; record the difference.**

| Thing | Where |
| --- | --- |
| node1 | 10.0.0.1. Normally holds the primary database role and the floating database address 10.0.0.10 |
| node2 | 10.0.0.2. Build sessions run here. Holds the standby database — **the PRIMARY since the 17 October failover; node1 is down and rejoins as the standby** — capture jobs, the Follow the Money app (port 8300) and its publisher (8301) |
| Third machine | The voter for database takeover. Its address is not known yet; record it in the baseline when it exists |
| Old repository, live | `/home/user/Git Repos/QueryNZ_V3` on node2 (note the space in the path); node1 mirrors it every 15 minutes. **The frozen product runs from this folder.** Touch it only for the changes this plan names |
| Old repository, reference copy | A second clone at the frozen tag, at a path with no space such as `/home/user/qnz3-ref`, made in step 1. Read old code, carry old tests and run comparisons from this copy, never from the live folder |
| New repository | QueryNZV4 at `/home/user/querynzv4`. Working copies for sessions sit under `/home/user/querynzv4-work/` |
| This plan | `docs/PLAN.md` in the new repository. Arthur saves it there before the first session |
| Captured documents | Inside the live old folder, under `var/staging/`: for example `ec-donations` (3,091 return files at one count), `ec-financials`, `ec-expenses`, `ec-promoters`, `ec-party-register`, `party-constitutions`, `party-sites`, `mp-expenses`, `linz`. The frozen product reads them too. The new estate reads them and never writes there |
| Databases | PostgreSQL 18.3. Three old databases on one server: `extractions` (the press graph), `incoming_news` (the news corpus), `nzbn_canonical` (the registers). The new database is `querynz_v4` |
| Credentials | `~/.querynz/*.env` on each box. Nowhere else, ever |
| Local models | The chat model is Qwen 3.6 35B (served name `qwen3.6-35b-a3b-q4km`). The embedding model is bge-m3. The page reader is GLM-OCR, under `/home/user/models/vision-glm-ocr/`. Find the other model files in the baseline |
| The frozen product | followthemoney.nz, a static site on an outside host, released daily by the `ftm-release` job |
| How an alarm reaches Arthur | The old estate sends a phone notification through ntfy, using an address kept in ops/config/alert-channel.env in the live old folder and not in the repository. New jobs reuse it by reading that file when they run, never printing it. Every failure is also written to `var/audits/unit_failures.jsonl`. Confirm in the baseline that a test notification reaches him |
| Old cards | `data-layer/docs/MUSTER_2_CARDS.md` (open) and `MUSTER_2_CARDS_CLOSED.md` |
| Old lessons | `docs/doctrine/LESSONS.md`, one file per section under `docs/doctrine/lessons/`, searchable index at `lessons/INDEX.md` |
| Old rulings | `docs/records/DECISIONS.md` (numbered to 360). Rulings 1 to 54 cited in this plan are from the October discussion and are listed at the end |

### Words used in this plan

- **Register:** a table of rows about people, organisations or events, where every row points to the document it came from.
- **Lane:** the code that captures one source and reads it into its register. One lane, one source.
- **Page reader:** a model that turns a page image into text. **Text reader:** the step that turns text into rows; today it is the local chat model.
- **Link:** a recorded join between two rows, with its rule, evidence and grade. **Decision:** a remembered ruling on a pair of rows. **Group:** rows gathered into one person by following links.
- **Fold:** the old estate's word for joining two rows as one person or donor. In the new estate a fold is a confirmed link.
- **Shape:** one of four kinds of product. **Template:** one use case on a shape.
- **Scheduler:** the one service that places every job on a graphics card or on the processor.
- **Profile** has three meanings, so this plan always says which. A **document profile** describes one kind of document: how to recognise it, which pages need the page reader, how its tables are laid out. A **hardware profile** is what a box has. A **model profile** is a model plus its settings on a graphics card.
- **Card** (work item): one small file describing a blocker, a finding or an idea. **Graphics card** is always written in full, or as "card 0" to "card 3" where the context is hardware.
- **Board** has two meanings. The **card board** lists work items. The **checks board** is the daily run of checks on data and jobs.
- **Published table** and **public site** are different things. To publish a table is to make it readable by products inside the estate. Putting anything on the public site, followthemoney.nz, is Arthur's decision.
- **Live:** anything outside a session's own scratch schema, and any installed job.
- **Lesson:** something the project paid to learn, filed where it bites.
- **Catch log:** one line for every item a job could not process, with the stage and the reason.
- **Checkpoint:** the stop after a product is built, where it is tested and its failures carded.
- **Frozen site:** the old Follow the Money, kept running unchanged as the reference.
- **The seal:** on 18 November 2026 directors' home addresses begin to be suppressed on the companies register. The seal is an encrypted, access-logged copy of those addresses as published before that date, kept for matching and never shown. Firing it is Arthur's job.

### Which model does what

| Work | Model | Why |
| --- | --- | --- |
| Step 1's table shapes and contracts | Fable | Every later session builds on them |
| The scheduler | Fable | A subtle fault shows up weeks later as a lost job |
| The link rules and the review agent | Fable | Judgment more than code |
| The integrator | Fable | Reads every merge |
| A register lane, once it has a brief, a table shape and tests | Opus | Careful, not hard |
| A template on a shape that exists | Opus |  |
| Most of the Papers Past ingest | Opus |  |
| A question or fix session | Either | Both are timed in the first week, and the quicker one that answers well becomes the default |

**Measure it once.** In step 4, give both models the same first register lane (the charities copy) against the same tests, and record the result as a lesson. Adjust this table from the measurement.

A session with a short brief, one module and tests that can fail does well on either model. A session without them drifts on either.

### Size, and what each step asks of Arthur

These are rough, for planning his time. Replace them with measured figures as steps close.

| Step | Size | Asks of Arthur |
| --- | --- | --- |
| 0 | An afternoon of his own time, plus the hardware | All of it |
| 1 | Several sessions, one at a time | Start each; answer the queue |
| 2 | Several sessions | Start each; privileged setup if a job needs it |
| 3 | A few sessions and days of machine time | Start each |
| 4 | The largest step: about a dozen lane sessions, then at least seven days of comparison | Start sessions from `docs/briefs/next.md`; decide the switch |
| 5 | Ten templates and about a dozen lanes | Start sessions; send the letters he chooses to |
| 6 | Four templates | Rule the trust settings, or let the defaults stand |
| 7 | A few sessions and weeks of machine time | Start sessions |
| Track H | Two or three sessions of preparation; the rotating itself is short | About five minutes at a provider for each wave-one secret, and one planned sitting of an hour or two for the database passwords |

## The order of work

&#91;embedded content: order of work · 7 steps, 7 pieces alongside\]

The drawing shows the order; the table below says the same thing for a reader without the drawing, and adds what each session needs.

| Session | Earliest start | Needs first | Model |
| --- | --- | --- | --- |
| Step 1, the founding session | Step 0 done | The plan saved in the new folder; the database login | Fable |
| Step 2, the scheduler | Step 1 closed | The job contract | Fable |
| Tracks B, D and E | Step 1 closed | The lane contract (for E) | Opus |
| Track A, takeover | The third machine on the network | Rehearsal only before the election | Fable |
| Step 3, the page-reader trial | Step 2 closed | The second disk; the model downloads | Fable, then Opus |
| Step 7.1 to 7.4, Papers Past ingest and embedding | Step 2 closed | The second disk | Opus; Fable for the index |
| Step 4, lanes | Step 3 closed | The readers chosen | Opus |
| Step 4, links, shape, comparison | Step 3 closed | The first lanes merged | Fable |
| Track C, the review agent | Step 4's links exist | The test pairs | Fable |
| Step 5 | Step 4.4 built. The seven-day comparison in 4.5 may still be running | The links | Fable and Opus |
| Step 6 | Step 5's shape built | The trust settings, or their defaults | Fable and Opus |
| Step 7.5 to 7.7, search tools and the template | Step 7.4's recall proof |  | Opus |
| Track H, security and rotation | Step 1 closed. Wave one as soon as its runbooks exist | Arthur at the providers; a sitting with Arthur present for the database passwords | Fable |
| Step 4.9, the board | The first lanes merged and step 4's links exist | Each lane's pane description | Fable for the shape; Opus for panes |

Step 1 is done by one session at a time. When it closes, the integrator role begins. Tracks and the Papers Past ingest may run beside steps 2 and 3. From step 4, three build sessions work at once, and track sessions count toward the three. Tracks F and G are lists kept current throughout, so they are not drawn.

