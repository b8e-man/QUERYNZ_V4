# QueryNZV4 Build Plan

Oct 11, 2026 · @arthur falls

This is the complete set of instructions for building QueryNZV4, written for a Fable agent that has not seen the discussion behind it. Follow the steps in order; each says what to do, why, how to know it is done, and what to hand Arthur.

## Read this first

### Who you are

You are a Fable agent running in Claude Code on node2, started by Arthur. You have not seen the two days of discussion that produced this plan. This document is your whole brief. It is self-contained on purpose: do not go looking for another plan.

The old repository carries its own orientation file (`CLAUDE.md`), doctrine and operating method. Those were written for a different way of working: one queue at a time, one muster, Arthur ruling each step. **Where they conflict with this plan, this plan wins.** The exception is the section "Hard limits" below, which nothing overrides.

**Which copy of this plan is the master.** From the day it is saved, `docs/PLAN.md` in the new repository is the master copy. Once step 1.1 has split it, the files under `docs/plan/` are the master and `docs/PLAN.md` is their index. Either way it changes only by Arthur's ruling, recorded in `docs/decisions/rulings.md`, and the integrator makes the edit. The document it was first written in is a snapshot and may fall behind.

### What to read, and how much

**Read only what your work needs.** Arthur's ruling 54 (12 October): "I want to be able to easily work on the new estate. It takes a long time to get an output from a prompt on the old estate." A session there read hundreds of kilobytes of doctrine, lessons and logs before it could answer. This document is itself about 200 KB, so it is split, and required reading has a limit.

**The first founding session reads this document whole, once.** In step 1.1 it splits the document into the files below. From then on no session reads all of it.

| File | Holds, by the headings of this document | Limit |
| --- | --- | --- |
| `CLAUDE.md`, at the top of the repository | Up to 3 KB of orientation written in step 1.1, then "Hard limits" whole. Claude Code loads it unasked | 10 KB |
| `docs/PLAN.md` | The index: this section, under the title lines that stand above "Read this first" | 5 KB |
| `docs/plan/core.md` | "Who you are", "Who Arthur is", "What you may decide, and what you may not", and "How the work runs" except its last three headings | 27 KB |
| `docs/plan/limits.md` | "Hard limits". Their one home; a check fails if the orientation file's copy differs | 7 KB |
| `docs/plan/step-0.md` to `step-7.md`, and `step-1b.md` | One step each, with its brief | 28 KB each |
| `docs/plan/tracks.md`, and `track-a.md` to `track-h.md` | The opening paragraph of "Tracks alongside", then one track each | 28 KB each |
| `docs/plan/design.md` | "What we are building" | None |
| `docs/plan/reuse.md` | "Reusing the old code" | None |
| `docs/plan/map.md` | "Where everything is", "Words used in this plan", "The order of work", "Which model does what", "Size, and what each step asks of Arthur" | None |
| `docs/plan/reference/` | The four reference sections, one file per third-level heading | None |
| `docs/plan/headings.md` | Written by the split: every heading and step number, with its file. Search it to follow a cross-reference such as "see step 1.10" | None |

**What each kind of session reads before it starts.** A kilobyte here is 1,000 bytes. "Three weights of session", in `core.md`, says what the weights are.

| Session | Reads | At most, about |
| --- | --- | --- |
| Question | The orientation file. Then only what the question needs | 10 KB |
| Fix | The orientation file, this index, `core.md`, and the spec of the one module it changes | 43 KB |
| Build | The same, then its step file (for a track, `tracks.md` and its track file), `docs/status.md`, its own status file, and the specs of the modules it touches | 77 KB |
| Integrator | The orientation file, this index, `core.md`, `docs/status.md`, and the requests waiting in the inbox | 45 KB and the requests |

`design.md` and `reuse.md` are read when a brief names them, or when the work is a new lane, link rule or product shape. `map.md` says where everything is and what the words mean: look there first when a path, a box or a term is unknown. Otherwise all three are looked up, not read through.

**A check holds the limits.** It runs in the fast tier and fails when a file passes its limit. So a rule added to `core.md` has to fit, which usually means another rule is cut, merged, or turned into a check a machine runs. Every ceremony on the old estate was added for a good reason and none was ever taken away. The limits are starting figures; change them by ruling once sessions have been timed.

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

## Hard limits

These are never traded for convenience, speed or a passing test. If a step in this plan seems to require breaking one, stop that piece of work and put it in the decision queue marked "no default".

**Secrets**

1. **Credentials live in `~/.querynz/*.env` and nowhere else.** Never in the repository, a brief, a log, a card, a commit message or a chat reply. If you see one in a file or a transcript, do not repeat it; note where it is and tell Arthur.
2. **The deploy token for the daily release has been exposed in a transcript twice.** Replacing it is the first item of track H: Arthur issues the new one and puts it in place himself. Do not print, move, copy or re-create it. Nothing in the new estate uses it.
3. **Bypass-permissions mode is never used on the bare box.** Sessions run on a reviewed list of allowed commands, set up in step 1.

**What may be collected**

4. **Capture is judged on legality and politeness.** Four questions per source: is the page open without getting past a lock; is storing it lawful copying; what terms did we accept; what does privacy law or the register's own statute limit.
5. **A robots file is no longer a permission decision** (ruling 10: legality and politeness, "not inferred intent"). It is read for one thing, a stated crawl delay, which is honoured. The old fetch gate refuses on a robots file for most hosts; the new estate's copy replaces that refusal with the rules in this section.
6. **Never solve a challenge or CAPTCHA, never use a login that is not ours, never get around a block.** A headed browser that is shown no challenge may read a page; shown one, it stops. A challenged read is a failed read. Log it and move on.
7. **Be polite:** slow, low-concurrency, off-peak, cached so nothing is fetched twice. A publisher's direct request to stop is honoured.
8. **Two sources are out by name:** fyi.org.nz (old ruling 321) and every NZME masthead, the NZ Herald included (ruling 12). Neither is captured, indexed or read.
9. **Before a new class of source is captured, write its one-page legal position** from the four questions. A lawyer reviews those pages before anything is sold.

**What may leave the boxes**

10. **No text leaves the boxes for a cloud model** (old ruling 172). Every model used by a job, for reading, embedding, review or answering questions, runs on the boxes.
11. **A session is the one exception that already exists, whatever its weight.** You read code, and samples of data, in order to build, to check, and to answer Arthur's questions. Keep it to samples. Never pass a register or the corpus through a session in bulk. Never print a person's home address or a suppressed name into a session, a card, a lesson or a log. The exact wording of this limit is in the decision queue.
12. **A web search by the review agent carries a name and a public role at most.** Never an address, and never anything from the sealed store.
13. **Nothing built here is opened to strangers or sold** until Arthur says so. Every product's surface listens on the local network only. Legal work comes after the build and before selling (ruling 2).
14. **No new connection about a named person goes on the public site** without Arthur's decision at that time.

**What may be shown**

15. **A person's home address is never shown or extractable.** No published table and no export carries one. A company's registered address is shown.
16. **A suppressed name is suppressed on every surface;** the row and the money stay.
17. **Papers Past is searched, not mined.** No people, claims or links are built from it. Its name index stays inside the history product and never feeds the links.

**What may be deleted**

| Class | Examples | Rule |
| --- | --- | --- |
| Cannot be regenerated | Captured documents, decisions, ledgers, corrections, document profiles, answer sets, anything a person typed | Never deleted. Withdrawn or quarantined |
| Can be regenerated | Registers, links, groups, indexes, scratch tables, build output | Deleted freely. A lane wiping and reloading its own tables is the design |
| Quarantined | Anything set aside | Kept for a fixed period, then removable on Arthur's word with a logged line |

18. **The old estate's data is deleted only when Arthur agrees the new estate has consumed it.**

**The frozen product**

19. **The old repository takes no commit after the freeze tag** except an emergency fix: the daily release is broken, or a published figure is wrong. That is Arthur's word each time.
20. **The daily release keeps running throughout.** Nothing in this plan pauses it.
21. **Nothing that feeds the public site is switched before the election on 7 November 2026.** Build beside it until then. This stands until Arthur rules otherwise.
22. **This plan authorises exactly three kinds of change to the old estate:** stopping old jobs that are outside the carve-out, with proof (step 1.4), and the freeze commits (step 1.5). Both may be done before the election, because the proof shows the site does not change. The third is rotating passwords and keys under track H, which changes credential files and restarts jobs but never the old repository; each sitting is on Arthur's word. Everything else that would touch the old estate's jobs, its database server settings or its files, including the off-site copy, takeover and any drill, is built and rehearsed beside it. It is applied to the live database server or the old jobs only on Arthur's word, and not before the election.
23. **Every job the new estate installs carries the prefix `qv4-`.** The installer never changes or removes a job without that prefix. A new build of the model server is installed beside the old one, never over the program the frozen product's two servers use.

**Machinery**

24. **The safety hook and the scope hook stay on** in every session.
25. **A graphics card holds one model profile at a time.** Jobs that share that profile may share its slots. Every swap is recorded.
26. **The review agent may search the web only for evidence that two rows are different people.** It never confirms a link from the web, because web presence favours the prominent.

## What we are building

An estate of New Zealand public records that does five things: it **copies** public registers, **builds** registers where none exists, **links** rows across them, **answers** questions from them with a citation, and **checks** itself. Everything else is support.

This is a capability build-out. Plan and build as if customers exist for every use case. Billing, accounts and metering are out. The first product is Follow the Money, rebuilt on the new estate and compared with the frozen site.

**The core architectural change** (Arthur, 16 October): a rich spine made of multiple joined registers. Everything above — the links, the products, the board — is a view of that spine, and the spine is what later work resolves against. See "Notes from Arthur, 16 October 2026" in the reference section.

### 1 and 2. Registers: copied and built

| Kind | What it is | Examples |
| --- | --- | --- |
| Copied | Someone else's register, held as a copy and kept fresh | Companies with directors and shareholders; charities and officers; tender awards; the Register of Political Parties; LINZ title owners and place names; MPs' declared interests |
| Built | A register that exists nowhere, assembled from notices or filed documents | Insolvency appointments, director prohibitions and public appointments from the Gazette; donations and party returns from Electoral Commission filings; regulator actions; court judgments |

Rules every register follows:

1. **The captured document is kept unchanged.** It is the only thing that cannot be rebuilt.
2. **Every row is rebuilt from its documents.** A wrong row is fixed by fixing the reading or adding a correction, never by editing the row.
3. **Every row has a stable key,** the same across re-reads, amendments and nightly rebuilds. For a copied register the key is the source's own identifier for that row (a company number with a role identifier, a charity number with an officer identifier), so it survives each new monthly file. For a built register it is the document's hash with the page and the place on the page; an amended filing is a new document whose rows point back to the rows they replace. A key never depends on a row number or a file name, because both change.
4. **Every row cites its document:** the file's hash (a fingerprint of its bytes), the page, and the place on the page.
5. **Each register has one owner in the code:** one lane, one set of tables, one test set. No two lanes land through a shared wipe-and-reload.
6. **A reading that fails its own check publishes nothing,** not a number.
7. **Every lane has one figure checked against the outside world,** such as the source's own total.
8. **Nothing is set aside silently.** Every lane keeps a catch log, and items in must equal items out plus items set aside.
9. **A register goes back as far as its source does.** The 2019 window belongs to the Follow the Money template alone; no lane inherits it.

**Rule 10, added by ruling 54: a register rebuilds in parts.** One document, or one day's file from the source, can be read again and its rows replaced without rebuilding the rest, and one register rebuilds without touching another. A lane's wipe and reload is the full path and this is the quick one. The same holds downstream: links, groups and search tables are recomputed for the keys that changed. The check that the quick path and the full path agree is a rolling one: each night the next register in turn is rebuilt whole into a staging schema, compared and dropped. The Papers Past archive is checked on a sample of items and never rebuilt whole. The old estate's answer set took 40 to 90 minutes to rebuild after any change.

### 3. Links

There is no stored person. There are three tables, and a person is what you get by reading them together.

| Table | What it holds | Who writes it |
| --- | --- | --- |
| Links | A pair of rows that join, the rule that joined them, the evidence, and a grade: confirmed or near | The joining rules, on every rebuild |
| Decisions | A remembered ruling on a pair, one of three: "the same", "not the same", or "contested" (the link drops to near). Each records who or what made it and on what evidence. Only ever added to | The review agent, corrections, suppressions; the old estate's judgments, copied across |
| Groups | Rows gathered into people by following confirmed links, minus the decisions. Rebuilt whenever either table changes; never edited | Nobody: it is computed |

Organisations need none of this where a register gives them an official number. The number is the link.

**How a link is made**

- **One shared reading of names and addresses.** "J. A. Smith", "John Adam SMITH" and "Smith, John" come out the same everywhere, and so do addresses. One function, imported, never copied. Macrons are kept.
- **Two rules confirm a link between person rows** (old ruling 221): the same first, middle and last name; or the same first and last name at the same street address.
- **A busy address needs a middle name:** an address shared by more than 50 companies counts only when the full name carries a middle name (old ruling 217). Address alone never confirms.
- **Everything else makes a near link,** shown as a possible namesake with the reason it is only near.
- **Joining a politician to a company role is stricter.** An MP's or candidate's name found on the director register counts only with a supporting link, whatever the name similarity: a shared directorship, a shareholding, or a company that person declared. Of 151 name-matched MP directorships in the old estate, 15 had one. The rest are kept and labelled as namesakes.
- **A joint filed name is one donor. A parent and its subsidiary are a group, not one party.**
- **These rules are exact for Follow the Money.** For the wider estate they are the starting point, revisited only after the first measurements and only by Arthur's ruling.

**How a link is unmade**

- **Every confirmed link is watched** for signs it covers two people: appointments in different regions at once, a very common full name, a bankruptcy on one row while the other keeps appointing, donor rows from far-apart addresses in one year.
- **A review agent reads the evidence and splits the link if it cannot trust it.** Splitting is the safe direction.
- **A split is a decision added, then a rebuild.** Nothing is deleted and nobody edits a group by hand.

**Two settings are ruled from measurement, and each has a default until then.** Build both as settings, not as code.

- **How far a chain of links is trusted** (A joins B, B joins C). Default: a group follows chains of confirmed links, as the old folds did, and any group the watch flags is contested as a whole. Follow the Money needs this default to reproduce the frozen site.
- **How much doubt each step through a person adds** to a multi-step connection. Default: a connection that passes through more than one person is listed as near, never confirmed.

### 4. Products: four shapes

The sixteen use cases sit on four shapes. A shape is built once; a use case is a template on it. A fifth shape, the board, serves no single use case.

| Shape | What it does | Use cases |
| --- | --- | --- |
| Published site | Publishes totals and pages from a fixed set of registers, on a schedule | 1 Follow the Money |
| Subject report | Starts from one person or organisation and reports what the registers hold: confirmed connections, then near connections | 2 Legal counterparty and conflict check; 3 Banking director history; 4 Agriculture counterparty; 5 Business credit and monitoring; 6 Insurance underwriting; 7 Construction and phoenix detection; 8 Recruitment board screen; 11 Healthcare operator governance; 12 Property developer due diligence; 13 Beneficial ownership and AML |
| Register scan | Asks one question of every row and lists the answers | 9 Government procurement integrity; 10 Tender and award intelligence; 14 Post-settlement governance map; 15 Lobbying |
| Archive search | Finds documents by keyword, by meaning, and by the names in them | 16 History search over Papers Past; keyword search over other journalism; 17 Discourse (the press graph's return, scoped: who said what about a subject, aimed at whom) |
| The board | One search across every register, shown as a row of panes that grows to the right as each link is followed | None of its own. It is the way to look at the estate itself (ruling 52; step 4.9) |

A template holds five things:

- **Which published tables it reads.** This is also all it is allowed to read. Each is listed with its licence terms, any attribution it requires, and how often it must be refreshed.
- **Its sections,** in order. A template may include a section headed "articles mentioning", fed by keyword search over journalism. It retrieves; it asserts nothing.
- **Its own rules:** warning flags, and patterns such as a failed company restarted under a new name.
- **Its known-limits page:** what the product cannot see, stated to the reader.
- **Its owner and version.**

Monitoring is a subject report run again when one of its registers changes.

Rules for every product:

1. **A product reads only the published tables its template names.** Never the inside of a lane.
2. **A product never writes into the estate.** It writes its own state only. When a product wants a record refreshed, it raises a request and the lane that owns the record does the work.
3. **Export is tested, not assumed.** A use case is exported as its shape, its template and a copy of the tables it reads. Build the bundle, start it with no connection to the estate, and run its checks.
4. **Withdrawals reach every copy:** a suppressed name within 24 hours, a correction within 5 working days, and the director-address seal. So an export needs either a refresh channel back to the estate or a recorded handover of those duties.
5. **Licences travel with the data.** Award notices need attribution. Land title data on individuals may not be publicly indexed.
6. **No second copy of logic.** If a product needs a result the estate computes, it gets the result as a column, not a copy of the function.
7. **Every product's surface is a web app on its own port, reachable on the local network only.**

Rules for everything a product shows:

- Every figure links to the document it came from.
- A blank says whether it means "none found" or "not held".
- A total states what it leaves out.
- An unreadable name is shown as unreadable, never hidden, guessed or ranked.
- A figure read from pixels is weaker evidence than one read from a text layer, and is marked as such.

### The Follow the Money template's own settings

These bind that one template and nothing else. They are what make the rebuilt site match the frozen one, so none of them moves. **They are as the frozen site stands at the freeze tag, not as this plan was first written:** the old repository moved after `2d3874e` (the race definition, ruling 361; the party page's selector; the published search's aliases), and the baseline of step 1.3 records the tag. Where this list and the frozen site differ, the frozen site wins.

**Scope**

- Calendar 2017 onward, whole (ruling 364, 17 October): every figure from 1 January 2017; **2017 is not a race (ruling 366, the same night)** — the races are 2020, 2023 and 2026, and 2017 to polling day is in the whole-window figures only; (364's text, superseded on this point: the 2017 election is a race of its own, and 23 September 2017 splits 2017's named rows between the 2017 and 2020 races by each donation's own date (ruling 363). Earlier rows are kept and never published; every Part A line's date is read.
- Seven front-page parties: National, ACT, Labour, Green, NZ First, Te Pāti Māori, Opportunity. Other parties' data is kept and served, not worked.
- A renamed party is the same party.
- A race is every calendar year after the election before it, up to and including its own (ruling 361, 16 October), inside the window: 2020 is 2018–2020 for return totals and from 24 September 2017 (the day after the 2017 election) for named donors (ruling 363); 2023 is 2021–2023; 2026 is 2024–2026. 2017 is not a race (ruling 366): 2017 to polling day is in the whole-window figures only. Every figure the selector governs is cut by it: the card figures, the party page's figures, donor roster, broadcasting allocation and size map, and the home page's four bars, the electorate map, list and totals.
- No press-reported row.

**Money**

- A donation is from the donor the Commission filed it under. A wholly-owned company keeps its own row; ownership is a note and is never added to the owner's total.
- If a return covers the money, the return is the record. A separate large-donation disclosure of the same gift is never added.
- The headline is all donations: the return's declared total. Named donors come second.
- One figure per party-year, with its basis named. A party's own committees and branches are not outside donors.
- Where our reading and the Commission's figure differ, the Commission's is the headline, linked to the Commission's own page.

### 5. Checking

Without checks a wrong answer looks the same as a right one.

| What is checked | How |
| --- | --- |
| A register | Row counts against the source's own totals; sums against official figures where they exist; freshness; every row has a citation |
| A reading | The catch log. Each document that could not be read is named, with the stage it stopped at |
| The links | Error rate measured by how common the name is, on test pairs the registers themselves supply |
| The review agent | Scored on those same test pairs before it may split anything on its own |
| A product | Tested when built. What fails becomes a card and a line on its known-limits page |
| Follow the Money | Compared figure by figure with the frozen site. Every difference is explained by a card |

### How the code is laid out

Three kinds of module, with imports running one way, held by one test.

| Folder | Holds | May import |
| --- | --- | --- |
| `keys/` | The one reading of names, addresses and official numbers. Pure functions, no database | Nothing |
| `support/` | The scheduler, the document reader, the model client, the fetch gate, the landing wrapper, the document profiles, the release pipeline, the installer | `keys` |
| `registers/<lane>/` | One lane each: capture, reading, its tables, its outside check, its catch log, its short spec | `keys`, `support` |
| `links/` | The joining rules, the three tables, the watch, the review agent | `keys`, `support`, published register tables |
| `products/<shape>/` and `products/templates/` | The four shapes and one template per use case | `support`, published tables |
| `checks/` | The checks board and the comparison with the frozen site | `support`, published tables |
| `cards/`, `lessons/`, `docs/` | One file per card and per lesson; the plan, the decisions, the status file | Not code |

**A published table** is a view in a schema named `pub`, owned by the lane or by `links`. It is the only thing a later module may read. A test in the merge gate fails if any module imports from, or queries, the inside of another.

### Deliberately not built

- The press graph as it was: people and claims drawn from journalism at large. Parked. It returns SCOPED, as use case 17 Discourse (Arthur, 17 October) — one subject at a time, after links, with the joined registers as what its names resolve against (Arthur, 16 October: once the registers are joined, "we can use them for name resolution for press"). Until step 4 is closed nothing resolves a press name.
- A stored person record, or any graph database.
- Billing, accounts, metering.
- Anything from NZME or fyi.org.nz.
- The later list: mayoral diaries, chief executives' gifts and expenses. (Ministers' diaries came off it on 17 October — use case 15.)

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
- **The scope hook is the fence.** It reads the scope file in the working copy and refuses an edit outside the folders named there. Always allowed: the session's own files in `cards/`, `lessons/`, `docs/status/`, `docs/decisions/queue/` and `merge-requests/`. Generated files are never allowed. **No scope file means refuse everything.** The integrator and the founding sessions get a scope file that names the whole repository. Outside the repository, a session may write only under its scratch folder.
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

### Reusing the old code

Whether to rebuild a piece or move it depends on where its value sits.

| Treatment | Pieces | Why |
| --- | --- | --- |
| Rebuild, with the old code as reference | The reading of names and addresses, the lane template, the reader contract, the links, the product shapes | Their faults are structural: seven copies of one name function, hand-set weights, one package doing ten jobs. They are also small |
| Move as it is, behind a new contract | The fetch gate, the headed-browser code, the amended-filing rules, the per-form parsers and document profiles, the release pipeline without its deploy step, the scheduler's registry, rules and ledger | This code is edge cases paid for one at a time. A rewrite would relearn them |
| Never rebuild | Decisions, corrections, document profiles, answer sets | They are data. They move across untouched |

Three rules for a rebuild:

1. **Carry the tests first.** The old tests are the lessons in a form that runs. Run them from the reference copy, never from the live old folder. The new module passes them before it replaces anything, except tests that only pin the old structure.
2. **Account for every difference.** Run old and new over the same real rows. Each cause of disagreement gets one card saying which side is right. One card per cause, not per row.
3. **Stop rule.** If a rebuilt module still has unexplained differences after its second full comparison, stop. Card the residue and put the choice in the decision queue.

Four rules for anything reused:

1. **A verdict before use:** take as is, take after a named fix, take the idea and rebuild, or leave. The reference section gives a first verdict for each piece.
2. **Reuse through one imported function, never by copy.**
3. **One check against the outside world** before anything depends on it. The old release pipeline passed eleven gates on a wrong site because every gate read our own output.
4. **No new member of an old debt list:** no fetcher that bypasses the fetch gate, no table without a definition in one place, no writer outside its own lane.

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

## Step 0: what Arthur does before building starts

None of this can be done by a session. Arthur has said the hardware items will be done before the build. Nothing in steps 1 and 2 depends on them technically; step 3 needs the disk, and track A needs the third machine.

- [ ] **Create an empty private repository named QueryNZV4** on the GitHub account, clone it on node2 to `/home/user/querynzv4`, and give node2 push access.
- [ ] **Save this plan as `/home/user/querynzv4/docs/PLAN.md`.**
- [ ] **Create the database logins for the new estate** and put their connection details in `~/.querynz/v4.env` on both boxes. The first owns one database, which Arthur creates, `querynz_v4`, on the existing server, with a cap of 20 connections and a five-minute limit on any query. The second can only read the three old databases, and its address is the standby's. Two more logins and a second, small database, added by ruling 54, are in the table under this list.
- [x] **Check the alarm address exists:** the file `ops/config/alert-channel.env` in the live old folder, which sends a phone notification when a job fails. Present (checked 17 October). The watcher that guards the frozen site through the election depends on it.
- [ ] **Mount node2's second 4 TB hard disk.** The Papers Past archive, its index files and the model files need the room.
- [x] **Fit the spare 64 GB of memory in node2.** DONE 17 October: node2 reads 125 GB. (The same sitting took node1 down — see "Notes from Arthur, 17 October" item 5 — so today node2 holds the primary role as well; the plan's "primary stays on node1" is the target state, restored only by track A's fail-back on Arthur's word.)
- [ ] **Set up the third machine and put it on the network,** with its own path to each box. It only votes on which box holds the database, and holds no data. Any always-on computer will do.
- [ ] **Allow for model downloads over the satellite link:** roughly 80 GB for the four trial models, each fetched once and copied from box to box over the local link. The session runs the downloads off-peak; it needs to know there is no data cap in the way.
- [ ] **Start the first session in `/home/user/querynzv4`,** on Fable, and paste the step 1 brief. Start it in that folder and not in the old repository: a session started in the old folder loads the old orientation file and the old hooks, and this plan overrides both. This first session has no fences yet, so it will ask before each command. It builds the fences and stops; every later session starts with them loaded.

* [ ] **Wind up the session now working in the old repository.** Let it finish or drop what it has in flight, and tell it that the old repository takes no commits after the freeze tag. Two sessions changing the old estate at once is how the frozen site gets broken.

**The logins and databases in full.** Ruling 54 adds the last two rows and the sample database. Arthur creates both databases and every login, so that no login of the new estate can create a database or a login on the server that feeds the frozen site.

| Login | May | Limits | Its details go in |
| --- | --- | --- | --- |
| Owner | Own `querynz_v4` and `querynz_v4_sample` | 20 connections; five minutes a query | `~/.querynz/v4.env`, as `QV4_OWNER_URL` |
| Old-estate reader | Read the three old databases, at the standby's address — **until node1 is rewound there is no standby: point it at node2 (the primary) for now and move it when the standby exists** | 5 connections | `~/.querynz/v4.env`, as `QV4_OLD_READ_URL` |
| Session reader | Read, in the two new databases, what the owner grants it. Step 1.8 grants everything except the tables that hold a person's home address, and the seal | 5 connections; 30 seconds a query unless `bin/q --long` asks for ten minutes | `~/.querynz/v4-read.env`, as `QV4_READ_URL` |
| Product reader | Read the published tables only. The board and every product surface use it | 10 connections | `~/.querynz/v4-read.env`, as `QV4_PRODUCT_URL` |

Two dated jobs of Arthur's sit outside the build and do not move for it. They are listed with their dates under "Dated jobs" at the end: the privacy-advice backstop (1 November), and sealing the director addresses (before 18 November, with the old checks board going red on 4 November).

Rotating passwords and keys is now part of the build, as track H. It will ask Arthur for about five minutes at a provider for each key, starting with the deploy token for the public site, and for one planned sitting to change the database passwords.

## Step 1: set up, freeze, and fix the seams

**Goal.** A new repository with its fences working, the old product frozen and still releasing, the press-graph jobs stopped, and the table shapes agreed so later sessions can work in parallel.

**Why first.** Parallel work only holds when the seams are fixed. Everything after this step builds on the shapes written here, so one session at a time writes them and nothing fans out until the step closes.

**Model.** Fable. This step takes several sessions, one after another. Each reads `docs/status.md` and carries on.

### Do

**1.1 Create the repository's fences.** Do this first, so everything after has a home.

- The folder layout from "How the code is laid out", and `docs/status.md`.
- **Port the two hooks; do not just copy them.** The old safety hook is `.claude/hooks/denylist.py` and the old scope hook is `.claude/hooks/session_scope.py`. Both are switched on in the old `.claude/settings.json`. The old scope hook reads its scope from `data-layer/docs/sessions/CURRENT`, has old paths written into it, allows everything when that file is missing, and allows any write outside the repository.
- **The new scope hook:** reads the scope file in the working copy; refuses everything if there is none; allows the always-allowed paths from "Starting a session"; and outside the repository allows writes only under the session's scratch folder. Test all four.
- **The new safety hook keeps the old refusals and adds four:** running `pi_release.py` without `--dry-run`; running `pi_cloudflare.py` or any other deploy tool; stopping, disabling or restarting any job without the `qv4-` prefix unless that job is on the step 1.4 stop list set out below, and never a job in the carve-out; and any write under the live old folder outside the commits of step 1.5.
- **The safety hook refuses wiping a table from the shell.** Keep that. A lane wipes and reloads its own tables through its own code, in one transaction.
- **The list of allowed commands** in `.claude/settings.json`. Start from the old list and change it: add the git commands a session needs (push, merge, worktree, clone); allow job control only for `qv4-` jobs; allow remote commands on node1 only through the installer and the probe; and do not allow a bare web-fetch command, because every fetch goes through the fetch gate. No bypass. List what it allows, in plain words, in your end-of-session note.
- **The launcher,** `bin/start-session`.
- **The merge gate:** one command that runs every test and the one-way import test and refuses on a failure. Prove it by trying to merge a branch with a failing test.
- The card and lesson file formats and the generators for the card board and the lessons index.
- `docs/decisions/queue.md` and `docs/decisions/rulings.md`. Copy rulings 1 to 54 and the waiting decisions from the end of this plan into them.
- The orientation file, set out below.

**Also in 1.1: split the plan and write the orientation file.** Both are safe file work, and every later session starts lighter for them.

- **The split script holds an explicit table of every heading and the file it goes to,** as "What to read, and how much" lays out, and fails on a heading it does not know. It changes no words. The title lines above "Read this first" go to the index. A second-level heading line, and any text between it and the first third-level heading under it, go with the first piece of that section; in the reference folders that is a file named `00-intro.md`. The reference sections split at third-level headings. The two diagram placeholders stay as they are. It also writes `docs/plan/headings.md`.
- **Prove the split:** every line of the original lands in exactly one piece, and joining the pieces in the order the script recorded gives the original back. Some files are made of pieces that do not sit together in this document.
- **The orientation file,** `CLAUDE.md`, in 3 KB: what the estate is, in five lines; the three weights and what each reads; the rules for a question session in full, because it reads nothing else; the few paths every session needs (the main checkout, the live old folder that is not to be touched, the reference copy, the inbox); and where the index, `map.md`, the status file and the card board are. Then the hard limits whole, copied from `docs/plan/limits.md`.
- **`bin/start-session --main founding`,** so that the next founding session starts with a scope file.
- **The stop list for step 1.4,** `/home/user/querynzv4-work/live/stop-list.md`, outside git. The safety hook reads it and lets only a founding session write it. The hook also names every job in the carve-out, one by one, and refuses to stop any of them whatever the list says.

**Then stop.** The first session ends when 1.1 is merged, because hooks and the allowed-command list load only when a session starts. Steps 1.4 and 1.5 touch the live estate and are never run by a session that started without the fences.

**1.2 Make the reference copy of the old repository.** Clone it to `/home/user/qnz3-ref` and give it its own Python environment; the live folder's environment points back at the live code. From now on, read old code and run old tests there. The live old folder is the running product: running tests or scripts in it can write into its `var/` folder or its live tables. Many old tests write a test row and, when they find themselves on the standby, advise pointing at the primary. Never do that. A carried test that writes runs against a scratch schema in `querynz_v4` only.

**1.3 Measure the boxes.** Write `docs/baseline.md` from what is actually there, and list every place it differs from this plan.

- Hardware on each box: cores, memory, each graphics card and its memory, each disk with its size and free space, including the volumes that hold the database and its change log.
- Programs on each box that jobs depend on: the text-extraction tools, each build of the model server, the model files. The two boxes have differed before without anyone knowing.
- The three old databases: size, and row counts of the main tables.
- Every scheduled job on each box: enabled or not, last run, last result.
- **Which graphics card each of the frozen product's model servers holds,** and the address the reading jobs actually call. The reading scripts read `~/.querynz/*.env` first, so confirm the value in force matches the default, without printing either file. The gateway's own status page answers which server it routes to.
- **The old checks board:** which checks are red, and for each, whether it touches the daily release. Eleven of 73 were red on 10 October. A red is acted on only if it touches the release.
- **How a failure reaches Arthur today,** if it does.
- The old repository's current commit. It has moved since `2d3874e`.
- The captured documents under `var/staging/`: each folder, its file count, its size.
- The Papers Past archive: where it is, its size, its format. The record says about 86 million items, on the boxes, never ingested.
- Three facts never confirmed: whether the ultimate-holding-company field of the companies register is loaded; whether live tenders are captured or only awards; how complete the Gazette's liquidation and receivership rows are.

**1.4 Carve out what the frozen product needs, and stop the rest with proof.** This is one of the authorised changes to the old estate (hard limit 22). The frozen product must not notice. **Build the watcher of 1.6 before you start this,** and make the NZME commit of 1.5 before the first batch.

1. Write the list of jobs you intend to stop into the stop list of step 1.1, the file the safety hook reads, and note it in `docs/status.md` before stopping any.
2. **Learn what normal change looks like first.** Each release is a folder under `var/pi-snapshot/v/` in the live old folder, named by its time, with `current` pointing at the live one. They are written once and kept, so nothing needs copying. Compare two existing consecutive versions file by file and note what always changes: dates, stamps, new filings.
3. Stop and disable the jobs in two or three batches, on both boxes. After each batch, wait for one scheduled daily release to run green before the next. The old checks board will show red for the stopped jobs until the commit in 1.5; that red is expected.
4. After the last batch, compare the new day's version folder with the last one before the stops, **file by file, across all ten kinds of page data**. The release script's own comparison checks donor-page totals only; it is not enough.
5. If you need an extra release to compare, run `ops/pi_release.py --dry-run` and never without that flag: without it the script publishes to the public site. Even the dry run restarts the publisher on port 8301 and writes a version into the live folder, so run it well clear of the scheduled release.
6. **Do not force a document through the live reading path.** Check the path instead: the gateway on port 8090 has a status page that shows which server it routes to and which model answers. Then watch the first real filing that arrives after the stop.
7. Any difference beyond the normal change you measured means a stopped job was needed. Switch it back on and record which.

**Arthur's ruling 53 (12 October):** "We will build this next week and just keep Follow the Money running as an exported product. The only feed that matters is the declared donations feed, so we can carve that out to run alongside as part of this plan." So the frozen product is no longer "everything the old estate runs, minus the press graph". It is a small, named set of jobs: the carve-out. Everything else in the old estate is either collecting for the new estate or a candidate to stop.

**The carve-out: what keeps the public site current. Keep, and watch.**

| Job | What it does for the site |
| --- | --- |
| `ec-disclosures`, daily at 03:30 on node2 | The declared-donations feed. With a headed browser on the desktop it collects the Commission's declarations of donations over $20,000, reads the new files, and rebuilds the donation registers. In the same sitting it fetches again any annual or candidate return that arrived cut short |
| `querynz-gpu-gateway`, `querynz-agent-llm`, `querynz-vision-ocr` | The readers that feed calls: the gateway on port 8090, the chat model behind it, and the page reader for declarations filed as images |
| `querynz-pi-publisher`, `ftm-release` at 06:15, `ftm-feedback-drain` hourly | Builds each day's version of the site, checks it, publishes it, and collects what readers send through the site's form |
| The database, its standby and floating address; `offsite-push`; the change-log archive jobs; `querynz-deploy-node1`; `querynz-residue-mirror` | What the above stand on, and the copies of them |

**Still collecting, for the new estate.** These only capture. They do not touch the site. Each keeps running until the new lane for its source takes over capture, because a gap in collecting cannot always be filled later.

`newsscrapers` and `newsscrapers-daily` (with NZME taken out), `gazette-capture`, `hansard-forward`, `legislation-backfill`, `comcom-capture`, `fma-capture`, `enforcement-capture`, `companies-office-capture`, `courts-capture`, `tribunals-capture`, `querynz-charities`, `society-officers`, `parties-capture`, `party-sites-recapture`, `linz-titles-pull`, `mp-expenses`, `minister-expenses-capture`, `motu-repec-capture`, `pdfpipe`, `docpipe-daily`, `querynz-coverage`.

**Candidates to stop, each with the proof above.**

| Group | Jobs |
| --- | --- |
| The press graph | `v3-extract`, `querynz-extract-fleet`, `querynz-crawler`, `querynz-mint-lane`, `querynz-research`, `querynz-sweep`, the `querynz-llm@` instances, `nzme-archive-backfill` |
| The news meaning index | `querynz-embed-backfill`, `querynz-embed-burst`, `querynz-embed-index`, `querynz-embed-index-ship`, `querynz-embed` |
| Rebuilds and feeds the declarations do not pass through | The nightly chain on node1 (`gazette-derive`, `registers-derive`, `gazette-feed`), `feed-parties`, `mp-tenure-derive`, `hansard-register`, `hansard-reprocess`, `companies-office-derive` |
| Old apps and their helpers | `querynz-pi-web` (the local copy of the product), `querynz-api`, `querynz-serving-precompute`, `querynz-feed-filters`, `querynz-paper-images`, `querynz-ec-results`, `robots-audit`, the reference downloads |
| The old checks board | `v3-audit`, once the watcher of 1.6 covers the carve-out |

**Two cautions on that list.** The sweep is the only thing that checks the old checks board ran, which is why the watcher comes first. And `registers-derive` also rebuilds the return totals the site shows: stopping it freezes those totals as they stand, which is what the ruling intends, but prove that the declarations still reach the site without it before leaving it off.

**The proof now has a positive half.** Besides "nothing changed that is not new data", show that a newly published declaration appears on the public site the morning after the Commission lists it, with only the carve-out running.

**1.5 The freeze commits and the tag.** This is another authorised change. Two small commits to the old repository, made in the live old folder on its main line, each staging only the files named here. That folder always has other changed files in it, because a kept job rewrites a tracked report every day; leave those alone.

- **First commit, before any job is stopped: NZME taken out of news capture.** `ingestion/newsscrapers/registry.py` lists `nzherald.co.nz` as `ready`, so the kept news jobs would go on fetching it. The registry's status values are `ready`, `blocked:credentials`, `blocked:antibot` and `blocked:robots`; the scrapers skip every blocked value. Add a value `blocked:ruling` and give it to `nzherald.co.nz` and to `businessdesk.co.nz`, which NZME owns. Check the list `HELD_SOURCE_DOMAINS` in `ingestion/news/review_sources.py` for the other NZME mastheads (`newstalkzb`, `gisborneherald`, `oneroof`, `driven`) and confirm nothing fetches them. Check the source lists for fyi.org.nz the same way. The two other paywalled outlets, `nbr.co.nz` and `newsroom.co.nz`, are not captured either.
- **Second commit, after the last batch of stops:** `ops/systemd/MANIFEST.json` updated to show which jobs are now disabled, so the old checks board does not stay red for jobs stopped on purpose.
- **Each commit must pass the old pre-push gate.** `hooks/pre-push` runs `ops/units_manifest.py --check` and three test files, and its document checks may ask for an old-style day-log entry for the change. If it does, write the smallest entry it accepts, in the same commit. Regenerate what it asks to be regenerated.

Then tag the second commit as the frozen version, record the tag in `docs/baseline.md`, confirm node1's mirror has reached the tag, and move the reference copy to it. From here the old repository takes no commit without Arthur's word.

**1.6 Build the watcher for the frozen product, and the first checks board. Do this before 1.4.** A small `qv4-` job that checks each day that `ftm-release` ran and was green and that `v3-audit` ran, and sends the alarm if not, through the ntfy address in the old estate's alarm file. At each release it also records the version's name and a listing, by path and hash, of the captured-document folders; step 4.5 builds from those listings. Then the new checks board in `checks/`: it starts with that one check, grows with every lane, and alarms if it has not itself run. Someone must be watching the release through the election; this is that someone.

**The watcher also reads the site's mail.** Readers send corrections and requests to suppress a name through the form on the public site. `ftm-feedback-drain` collects them hourly into a file in the live old folder. The old working session used to see them; nobody does now. So the watcher checks that file each day and sends the alarm when something new has arrived, and the integrator puts it to Arthur the same day. A suppression request carries a 24-hour clock and a correction five working days.

**1.7 Bring the reference material across,** read-only, under `reference/`. Things that will be added to get a live home as well.

| What | From (reference copy of the old repository) | Live home in the new repository |
| --- | --- | --- |
| The lessons, as the starting set | `docs/doctrine/LESSONS.md`, `docs/doctrine/lessons/`, with the tools `ops/lessons_for.py` and `ops/lessons_index.py` | New lessons go in `lessons/`; the search covers both |
| The document profiles | `data-layer/docreview/profiles.jsonl` (versioned; the newest line per profile is current) | `support/profiles/`, added to and never rewritten |
| The corrections a person or a check made to readings | `data-layer/docreview/corrections.jsonl` | Beside the profiles; moved untouched |
| The extraction rulebook, parked with the press work | `data-layer/docs/DEFECT_TAXONOMY.md`, `HEALING_SYSTEM.md`, `ERA4_RULES.md`; the healing rules and tests in `data-layer/healer/`; `data-layer/reconciliation/reconciliation/defects.py` and `guards.py`; lessons sections 2, 5 and 8 | `reference/rulebook/` only. Parked |
| The old cards | `data-layer/docs/MUSTER_2_CARDS.md`, `MUSTER_2_CARDS_CLOSED.md` | None. Context only |
| The earlier use-case work | `data-layer/docs/USE_CASE_PROGRAMME.md`, `USE_CASE_REQUIREMENTS.md` | Checklists feed the checkpoints |
| The old rulings | `docs/records/DECISIONS.md`, `docs/doctrine/RULED_DEFAULTS.md` | None. Context only |

**1.8 Set up the new database,** `querynz_v4`, with the login from step 0, reached through the floating address. One schema per lane, one for links, one per product, a `pub` schema for published tables, and a scratch schema per session. The old nightly off-site job copies only the three old databases, and changing it would be a change to the frozen estate. So install a small job of your own that dumps the new database each night and sends it off-site under its own name, until track B replaces it. Its decisions and run records cannot be regenerated.

**The sample database and the grants.** Arthur made `querynz_v4_sample` in step 0; give it the same schemas. In both databases, a person's home address is kept only in schemas whose names end `_private`: each lane's own, and each session's scratch one. Grant the session reader everything except those schemas and the seal, with default grants so that later tables follow. Grant the product reader the `pub` schema only. The nightly dump skips the sample, because it is refilled from its lists.

**1.9 Write the contracts.** Each is a short document plus a test.

| Contract | What it fixes | Take from |
| --- | --- | --- |
| The reading of names, addresses and official numbers | One function each. Macrons kept. For telling a person's name from an organisation's, the director register is the authority for given names. Nicknames are never merged on. One party-name function | The old estate has seven divergent name functions and address keys in at least five files; take the rules and their tests, promote no existing copy |
| The document store | A document is its bytes. It is keyed by hash; its names are attributes. One landing wrapper. For web pages, the hash is taken after removing what changes on every fetch | `ingestion/landing.py`; the old estate held 424 returns under two names |
| The register row | The stable key; the document hash, page and place; the dates as filed; the reader and document-profile version; whether read from text or pixels; a person's home address held apart, in the lane's private schema | Old donation rows were renumbered nightly, which broke every citation |
| Dates | An ended role carries the day it ended, not the day the file was imported | The old company views dated endings to the import day |
| The lane | Capture, read, tables, published views, outside check, catch log, run record, five-line spec, how its rows appear in a pane of the board, re-reading one document or one day's file alone, and its documents in the sample database | `data-layer/gazette_register` and `data-layer/courts_register` already have nearly this shape |
| The reader | One way to turn a document into text and rows: per page, text layer first, page reader for image pages, run from the document profile, every reading stamped with its model and settings, stored by the document's hash, and replayable without the model | The old estate had 11 text-extraction calls in 4 shapes across 9 files |
| The model client | Every call names its model and refuses an answer from a different one. Local addresses only | `data-layer/modelgate/modelgate/client.py` |
| The document profile | The fields a profile carries and how a new version is added | `data-layer/docreview` |
| Links, decisions, groups | The three table shapes; the three verdicts; who or what made each decision; the two trust settings | The old estate's ledgers of judgments |
| A template | Published tables read, with terms and refresh; sections; rules; known-limits page; owner and version | New |
| A job | What it needs: a model profile or the processor only, memory per worker, deadline, query time limit, whether it can share | `config/job_types.yaml` |

**1.10 Move the shared machinery into `support/`,** each piece with its old tests carried first.

- **The fetch gate,** from `ingestion/fetchgate.py`, with its robots refusal replaced as hard limit 5 says: record the robots file, honour a crawl delay, and refuse on the named sources, on a challenge or block, on a publisher's request, or where no one-page position is on file.
- **The landing wrapper,** rebuilt and not moved. The old one stores an article's text, not a document's bytes; the new one stores bytes, keyed by hash.
- **The model client,** with refusal on for every lane.
- **The document reader,** from `data-layer/docread`, behind the reader contract.

**Where a new lane gets its documents.** Until the public site is switched, the old capture jobs stay the only regular fetchers for the sources they cover, so nothing is fetched twice. A new lane's documents come one of three ways, and the lane's spec says which:

| Case | What the lane does | What its rows cite |
| --- | --- | --- |
| The old estate holds the file | Copy it by hash, read-only, from the old `var/staging/` folders into the new document store. Take only captured files; some of those folders also hold derived output (`pageread/`, `residue/`, `index/`, `archive/`), which is not a document | The file's hash, page and place |
| The old estate kept only text or parsed rows, not the file | Export those rows once to a dated file in the new document store and treat that file as the document. Mark every row from it "taken from the old estate's tables; original not held" | The export file's hash, plus the source's own identifier or address for the item |
| The old estate holds nothing usable, or the source was never captured | One polite capture of its own through the new fetch gate into the new document store, after its one-page position is written | The file's hash, page and place |

**After 1.10, do step 1b,** the quick-work tools. It has its own section after this one. Then do 1.11, which is their first real use.

**1.11 Build one thin slice end to end.** Take the party returns that have a text layer (the document profile `ec-party-return-text`; 24 of the 56 live returns were this shape). Read them from the captured files, write rows under the row contract, publish one table, and print one plain page from it. No page reader and no scheduler are needed. The test is narrow on purpose: for each of those returns, the declared total in the new table equals the total the frozen site shows for that party and year, or the difference has a card.

**The slice is also the first proof of the fast tier.** Its tests run on the sample database, calling no model, in under a minute.

### Done when

- [ ] An edit outside a session's scope is refused, and a branch with a failing test is refused by the merge gate.
- [ ] `docs/baseline.md` exists and its differences from this plan are listed.
- [ ] The carve-out is named and watched, every other old job is either still collecting or stopped with proof, a new declaration has reached the public site with only the carve-out running, and the daily release has run green since.
- [ ] The old repository is tagged, with NZME out of its news capture.
- [ ] The watcher for the frozen product is running and has raised a test alarm that reached Arthur.
- [ ] Every contract has a document and a passing test, and the shared machinery in `support/` passes its carried tests.
- [ ] The thin slice matches the frozen site's totals for the same returns, or each difference has a card.
- [ ] The reference material is in place and the lessons index builds.

* [ ] The plan is split, its pieces rejoin to the original, and every file is within its limit.
* [ ] Step 1b is closed.

### Brief to paste

```text
You are a founding session for QueryNZV4, running as Fable on node2,
started in /home/user/querynzv4. If the folder docs/plan/ does not
exist yet, you are the first: read docs/PLAN.md in full, do 1.1, and
stop when 1.1 is merged. Otherwise read docs/PLAN.md, which is now
the index, then the files it names for a build session on step 1,
then docs/status.md, and continue where it stops. Do step 1 only, in
this order: 1.1, 1.2, 1.3, 1.6, the first commit of 1.5, 1.4, the
rest of 1.5, 1.7 to 1.10, step 1b (stop when it is built), then 1.11.
Work alone. The only changes you may make to the old estate are
stopping old jobs outside the carve-out, with proof (1.4), and the
freeze commits (1.5), and never in a session that started without
the hooks. Never touch a job in the carve-out. Obey the hard limits.
Put questions for Arthur in the decision queue with a default and
keep working. Update docs/status.md at every close. Finish by telling
Arthur in plain words what closed, what is carded, what waits on him,
and whether step 1 is finished or needs another session.
```

## Step 1b: the quick-work tools

**Goal.** The tools that keep the estate quick to work on (ruling 54): light sessions, a fast tier of checks on a small sample, and a timer on every prompt.

**When.** Inside step 1, after 1.10 and before 1.11, by a founding session using the step 1 brief. The thin slice of 1.11 is the first real use of these tools. **Model.** Fable.

### Do

**1b.1 The weight in the fence.** The launcher writes the session's name and weight into the scope file. For the weight "question", the scope hook refuses every edit inside the repository, the always-allowed paths included, and the safety hook refuses any command that commits, pushes, merges, runs the installer, controls a job, or names a credential file other than `~/.querynz/v4-read.env`. Outside the repository a question session may write only its scratch folder and `inbox/cards/`; a fix or build session, its scratch folder and `inbox/merge-requests/`. For every weight but founding and integrator, the scope hook refuses `.claude/`, `bin/`, `docs/plan/`, the orientation file and any scope file. The hooks are a fence. The wall is the session reader, which cannot write whatever a session does.

**1b.2 `bin/ask`.** It makes a throwaway working copy of the main line at `/home/user/querynzv4-work/ask-<time>`, with a question scope file and a scratch folder beside it, removes copies more than a day old that no session is using, and prints the folder to start in and the rules for a question session. There is no brief.

**1b.3 `bin/fix <module folder>`.** It accepts only a module folder: `keys/`, `links/`, or one folder under `support/`, `registers/`, `products/` or `checks/`. It refuses a folder held by a build session, meaning one named in the scope file of a working copy that `bin/start-session` made and the integrator has not yet removed. It reopens an existing copy whose request was refused. It makes the working copy `fix-<module>-<n>`, a branch, a scope file and a scratch schema. The integrator removes a working copy, fix or build, once its last request is merged.

**1b.4 `bin/q`.** One command for looking at data in the two new databases: the session reader, 30 seconds, 200 rows. `--long` allows ten minutes, takes a lock so that only one runs at a time, writes the full result to the scratch folder and shows the first 200 rows. `--old`, for fix and build sessions only, reads the old databases through the old-estate reader under the same limits. A question session has no route to the old databases, because they hold home addresses.

**1b.5 The inbox.** `/home/user/querynzv4-work/inbox/`, outside git. It holds `merge-requests/`, which the launchers link into every working copy, and `cards/` for notes from question sessions. The integrator commits a copy of each finished request under `docs/merges/`.

**1b.6 The sample.** Each module keeps `sample.list` in its own folder: document hashes and source keys, never bytes or rows. One command gathers the lists and fills a named scratch schema in `querynz_v4_sample`, through the code of the branch it is run from. Tables that hold a person's home address go in a schema whose name ends `_private`, there as everywhere. The first list is the thin slice's, in 1.11. The integrator's own fill, from the main line, is what other sessions read as published tables.

**1b.7 The two tiers.** Two commands. The fast tier takes a module or the whole repository, fills the session's sample, replays stored readings, fails on an unmarked slow test, and records its own time. The merge gate of 1.1 becomes the full tier at a merge. It loads only the modules the branch touches into a staging schema of the real database, and on a pass moves those tables into place, so nothing is loaded twice. A load expected to take more than ten minutes runs as a scheduler job that writes its result into the request, and before 7 November it stays inside the bulk-loading limit under "Shared things on the boxes". The nightly run goes on the checks board of 1.6.

**1b.8 The reading-limit check,** in the fast tier: each file against its limit in the index, each status file against 3 KB, and the orientation file's limits against `docs/plan/limits.md`.

**1b.9 The timer.** Two hooks, on the events Claude Code raises when a prompt is submitted and when the session stops. Each adds one line to `/home/user/querynzv4-work/times/session-times.jsonl`: the session's name and weight from the scope file, the event, and the time. Never the prompt. A checks-board job reports the typical and the worst wait for each weight over seven days, and trims the file to 30 days.

**1b.10 The lessons search.** One command, over the first line of every file in `lessons/` in the main checkout and the old estate's one-line index brought across in 1.7. It returns at most eight rules, one line each, with the file to open. Test it on the eight real pairs the old tool was measured on; the old tool found five.

**Then stop.** Hooks load only when a session starts, and a session cannot start another. Arthur starts one question session with `bin/ask` and asks it anything. The next founding session does 1.11 and then works through the list below.

### Done when

- [ ] The question session Arthur started gave its answer, and its two lines are in the times file.
- [ ] The hooks, run against a question scope file, refuse an edit, a commit and the owner's credential file, and allow a note in `inbox/cards/`.
- [ ] `bin/fix` refuses `.claude/hooks`, and refuses a folder a build session holds.
- [ ] Two fills of the sample from different branches, run at the same time, do not disturb each other.
- [ ] A test not marked slow that sleeps for six seconds fails the fast tier.
- [ ] The reading-limit check fails on a file made one byte too long.
- [ ] The thin slice's tests pass in the fast tier, and the checks board shows the first timings.
- [ ] The lessons search returns at most eight rules, and its recall on the eight pairs is recorded.

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

## Step 3: the page-reader trial over the election documents

**Goal.** Choose the page reader, and a second reader from a different family, for the rebuilt Follow the Money. Prove the scheduler on a real job while doing it.

**Why here.** Five models over the same pages forces the graphics cards to swap, which has only ever run in rehearsal. The election documents come with known answers. The result is needed by step 4.

**Model.** Fable sets up the page set, the scoring and the first pass. Opus can run the second pass.

### The models

GLM-OCR is the incumbent. It was chosen on 22 September because it invented nothing; it even reproduced a filer's typo. The old estate recorded the question as settled for electoral returns. Arthur has reopened it (rulings 49 and 50).

| Model | Family, for choosing a second reader | Size | Licence | Why it is in | Caution |
| --- | --- | --- | --- | --- | --- |
| GLM-OCR (incumbent) | Zhipu | 1.3B; 4.8 GB on a card; 4.4 seconds a page | MIT | The reference | Files at `/home/user/models/vision-glm-ocr/`; served today by `querynz-vision-ocr` on port 8032 |
| [TeleOCR](https://huggingface.co/bbsai/TeleOCR), formerly NaviDC-OCR | Qwen 2.5 base | 1.2B | Apache 2.0 | Top published score on the main document benchmark; reads photographed and bent pages | Served here only through a community conversion; tables come out in a tag format that needs converting; weaker on degraded pages |
| [OvisOCR2](https://huggingface.co/Abiray/OvisOCR2-GGUF) | Qwen 3.5 base, small | 0.8B | Apache 2.0 | Nearly the same score, smallest; one Markdown page out, the same shape GLM-OCR gives | Community conversion; no data on poor scans |
| [Chandra OCR 2](https://huggingface.co/datalab-to/chandra-ocr-2) | Qwen 3.5 base, mid | 5.3B | Weights free under US$2M revenue or funding; use that competes with its maker's own service is restricted | Strongest published claim on handwriting and forms | In by ruling 49. Its licence goes on the before-selling legal list. Weakest on old scans |
| [Infinity-Parser2-Pro](https://huggingface.co/infly/Infinity-Parser2-Pro) | Qwen 3.5 base, large | 35B | Apache 2.0 | Highest score on the other main benchmark | English and Chinese only; weak on rotated tables. September's rejected large model put a printed total in among the rows |

For the second reader, GLM-OCR is one family and every Qwen-based model is another. Two Qwen-based models agreeing is weaker confirmation than GLM-OCR agreeing with one of them.

Already rejected and not to be re-run: Qwen2.5-VL-32B (one of three on controls) and PaddleOCR-VL-1.6 (repeated one line eleven times and invented a sentence). Looked at on 11 October and left out: DeepSeek-OCR 2 (lower scores), Unlimited-OCR (needs an unmerged build of the model server and loops on dense pages), MinerU 2.5 Pro (a whole toolkit with extra licence terms), Xiaomi-OCR-0 (no published benchmark). No public benchmark measures invented text, which is the test that matters here.

### Three conditions from Arthur

1. **The document profiles come first.** The trial runs under the existing profiles and swaps only the page reader a profile names. Everything else is held fixed.
2. **A reading is tied to the document's bytes, never to its name.** Last time readings were attached to the wrong documents. The old corpus was 4,020 files but 3,325 distinct documents; 424 returns were held under two names; one return, byte-identical under two names, would have filed 1,469 rows ($40.07m) twice. Record every reading against the file's hash, the page number, the model, its build, its settings and the profile version. Draw the page set from distinct hashes. Join the known answers by hash.
3. **Text or scan is decided per page.** Some files mix scanned pages with pages that carry text. A whole-document test once called a return readable while its declaration page was an image, so it read as having no total. The rule in the profiles: a page with under 50 characters of text goes to the page reader; a page with a text layer stays with the text reader, which outranks any page reader.

### Do

**3.1 Get the models onto both boxes.** Download each once, off-peak, and copy it to the other box over the local link through the installer. Use each model in the form the boxes' model server can load, with its image projector file. For each model fetch two levels of compression and compare them on twenty pages, because community conversions vary; keep the smaller only if it reads the same. If a model needs a newer build of the model server, install that build beside the old one (hard limit 23).

**3.2 Serve each as a scheduler profile.** Use each model's own documented prompt and input format; these models are trained on specific prompts and do poorly on generic ones. Temperature 0. Record every setting. If a model cannot be served on these cards within two days of trying, card it, record why, and carry on without it.

**3.3 Build the page set,** from distinct hashes of the captured election documents.

- Every shape: all text, image first page, full scan, handwritten, two-column donor tables. Of the 56 live party returns, 24 were all text, 23 had an image first page and 9 were full scans; across all 125 staged party returns, 84 had no usable text layer.
- Every kind: party donation returns, loan returns, party and candidate expense returns, large-donation disclosures, party financial statements.
- The returns that failed in the old estate for want of a text layer.
- Three named cases as fixed tests: NZ First 2023 (a first pass found parts B and C and not A, and stated $202,639.75 for a party that spent $1,513,080.37); ONE Party 2020 (a pixel reading gave $30.43 against a true $30,433.35); the Māori Party 2020 (the text layer's $301,517.96 is right and the Commission's published $241,986.42 is wrong).

**3.4 Build the answer keys.** None needs a person.

- **Text pages as a free key.** Render a page that has a text layer to an image at the document profile's resolution and give it to each page reader. The text layer is the answer. This is the only key that can show invented text directly.
- **Each return's own printed total.** Every return prints one, so a reading's rows can be summed against it.
- **Declared totals from outside:** the Commission's own published table, and the frozen site's figures. The old register matched the Commission's table to the cent on $14,560,581.38 on 10 October. **Known exceptions, where the Commission's table is wrong and must not be used as the key:** its 2020 figures for the Māori Party and Advance NZ, which give Part A alone.
- **The old answer set** in `data-layer/docread/docread/gold.py`. Use only entries a person confirmed; 379 of the 381 stored corrections are machine-agreed and are not truth.

**3.5 Pass one: GLM-OCR alone, through the scheduler.** Use the same build and the same settings the old estate used, as recorded in its readings. Matched by hash and page, it should reproduce the readings the old estate already holds. A difference here points first at the scheduler or the harness, not the model. Try twice to remove each difference; then card what remains, with its likely cause, and go on to pass two. Some old readings were attached by file name and will not match for that reason alone.

**3.6 Pass two: add the four challengers.** Queue all five over the same page set as bulk jobs, with one small urgent job injected part-way to exercise the queue rules.

**3.7 Score per page.** Amounts and tables are scored after the text reader has turned each page reader's text into rows, using the text-reader profile from step 2.15, the same for every page reader.

| Measure | Rule |
| --- | --- |
| Invented text | On a text page used as a key: any run of five or more words in the reading that is not on the page fails the page. On a true scan there is no page key, so invention is judged three ways: an amount that appears in no other reader's output and breaks the printed total; a row that only one family of reader produces; a name that matches the form's own printed example or instructions |
| Loops | The same line three or more times in a row, where the text layer or the other readers show it once, fails the page. Genuinely repeated donor rows are not loops |
| Amounts | Every money amount exact, to the cent |
| Tables | Row count and column alignment. The row-number column sits outside the ruled border on these forms, and readers disagree on whether it belongs |
| Completeness | A part not read is not a part that is zero. A reading holding two of three parts has missed one |
| Agreement | Where two readers from different families agree, and where they differ |

**3.8 Decide.**

- A challenger replaces GLM-OCR only with zero invented-text and loop failures across the set and a better score on amounts.
- The second reader is the best model from a different family with zero inventions.
- If no challenger qualifies, GLM-OCR stays alone and the lack of a second reader is carded.
- Record the choice as a new version of each profile, and the whole trial in `docs/trials/page-readers.md`.

### What the run proves about the scheduler

| Proof | How it shows |
| --- | --- |
| One model per card at a time, every swap recorded | The swap ledger matches what the cards actually held |
| A swap pays for itself; a small job never waits for ever | The small models and the injected urgent job are not starved behind the 35B one |
| Long work is cut into pieces that record progress | A worker stopped mid-run loses at most one piece |
| Either box can take the work | One box's worker is stopped on purpose and the other finishes |
| The profile is probed, not typed | A box missing a program a model needs is never given that job |
| Peak memory is recorded | Each model's profile is filled from this run |

The run reads the captured documents and writes to its own scratch tables. It publishes nothing and does not touch the frozen site or its two model servers.

### Done when

- [ ] Pass one reproduces the old readings, or each difference has a card.
- [ ] Every model has a score per shape, or a card saying why it could not be served.
- [ ] Every scheduler proof in the table above has passed and is recorded.
- [ ] The primary reader and the second reader are chosen and written into the profiles.
- [ ] The lessons are filed.

### Brief to paste

Launcher: `bin/start-session trial support/trials support/profiles docs/trials`

```text
You are a build session for QueryNZV4 on node2, in the working copy
the launcher made for you. Read docs/PLAN.md, then docs/status.md and
your own status file, and continue where it stops. Do step 3: the
page-reader trial over the election documents, as the scheduler's
first real job. Search the lessons for reading documents, document
profiles and page readers first. Key every reading to the file's hash
and page, never its name. Decide text or scan per page. Run GLM-OCR
alone before adding the challengers. Write only to scratch tables;
put nothing on the public site; leave the frozen product's servers
alone. Push your branch and raise a merge request for each finished
piece. Update your status file at every close. Finish by telling
Arthur which reader won, which is the second reader, what is carded,
and whether step 3 is finished.
```

## Step 4: Follow the Money rebuilt

**Goal.** Follow the Money running on the new estate and reproducing the frozen site, with every difference explained by a card.

**Why first among the products.** Arthur's ruling 15. It is also the one product with known answers for every part: the Commission's own totals for the registers, the frozen site for the pages.

**Models.** Opus for each lane. Fable for the links, the published-site shape, the comparison and the integrator. This is the first step that fans out: three sessions plus the integrator.

### What the frozen site is

- A static site on an outside host, with search running in the reader's browser and one small hosted function that takes feedback. With both boxes off it stays up as at its last release.
- It publishes ten kinds of page data, listed in `data-layer/pi/pi/snapshot_paths.py`: home, parties, electorates, pickers, subject, electorate, donor, board-member, size-bands, cite.
- The daily release (`ops/pi_release.py`, run by `ftm-release`) regenerates everything, runs its gates, and flips the site only on green. Publishing is in `ops/pi_cloudflare.py`; feedback is drained by `ops/feedback_pull.py`.

Holes already on record. Reproduce the frozen site first; then each of these is a finding card, not a silent fix.

- The donor list is cut at 1,500 before names are folded, so a donor can lose its page.
- A parsed return total was held for under half the party-years since 2019 at one count; measure it again.
- The announced-candidates tier is empty, and the 2026 candidate list has never been captured: the Commission's pages are behind a challenge.
- Parliament's Hansard pages have been behind a challenge since about 5 October; the Hansard register is held at 23 September. No technical route will be sought. The unlock is a permission request, which is Arthur's.
- No electorate candidate has a vote count: the results site refuses automated reads.

### Do

**4.1 Build the lanes, in parallel.** Each lane re-reads from documents already captured, taken by hash from the old `var/staging/` folders, read-only. Nothing is re-fetched that is already held, and until the public site is switched the old capture jobs stay the only fetchers for their sources. Decisions and corrections are copied across untouched. Each lane holds everything its source holds, back to the source's start; only the Follow the Money template applies the 2019 window. The folder name for each lane is listed under the briefs below.

Which of the three cases in step 1.10 each lane starts from, as far as the old repository shows. Confirm each in the baseline.

| Lane | Starts from |
| --- | --- |
| Party returns, candidate returns, disclosures, party finance, party register, party rules | Files held under `var/staging/` |
| MPs' and ministers' expenses; LINZ titles | Files held under `var/staging/` |
| Gazette notices; Hansard | Text rows in the old news database, no file. Export once |
| Companies and the other entity types | The monthly file Arthur downloads. Find where the raw files are kept; if only the loaded tables survive, export once |
| Charities | Parsed straight into tables from the register's own data feed; no file was kept. One capture of its own, shared by both builds of this lane |
| Society officers; MPs' interests | Find out in the baseline |

| Lane | Kind | Notes |
| --- | --- | --- |
| Charities register and officers | Copied | **Build this one twice, once with Fable and once with Opus, against the same tests, in two folders (charities-a and charities-b) from one shared set of captured files so nothing is fetched twice. Record the comparison and keep one.** The old lane's client bypassed the fetch gate and its host no longer resolves; take the idea (verbatim copy, then read), not the code |
| Companies, directors, shareholders, addresses, and the other entity types | Copied | The monthly file is downloaded by hand by Arthur and is not to be raised as outstanding. Sole traders, partnerships and trusts are not in it |
| Register of Political Parties, and party lifecycle | Copied and built | Renames come from registration windows: four are known. A renamed party is the same party |
| Party donation and loan returns | Built | The core lane. Uses the readers chosen in step 3 and the profiles. See "Electoral Commission forms" in the reference section before writing a line |
| Candidate returns | Built | Totals come from the Commission's own spreadsheet, joined on year, electorate and surname. Amended returns are republished under a different file-name pattern |
| Large-donation disclosures (over $20,000) | Built | Build this lane first. It is the one feed the frozen site still depends on, and once it reproduces the old feed it can take that feed over, on Arthur's word. The Commission states which declaration an amendment replaces; never infer it. Its listing often shows a challenge to plain requests. A headed browser that is shown no challenge may read it; shown one, it stops |
| Party expense returns, broadcasting allocation, party financial statements, promoters, party rules | Built | Each has a profile |
| Candidates, electorates, who sits in the House | Built | Electorate names join 72 of 72 to Stats NZ's. Boundary shapes need a key that is Arthur's to place |
| MPs' declared interests; MPs' and ministers' expenses | Copied from published files | The interests register renumbered its categories in 2018: key on the heading, not the number. Every edition reprints the rules after the last member |
| Gazette: party events, public appointments, insolvency, prohibitions | Built | The old lane's gate records a failure and still exits clean; do not carry that. 90.8% of its 35,938 unread notices are one celebrant format |
| Incorporated-society officers | Copied through the per-entity interface | A seventh of the societies each night, the party societies first |

**4.2 Build the links.**

- Take from the old estate the ledger and the two rules, not the hand-set weights. The pieces are in `data-layer/registers/registers/`: `donor_anchors.py`, `roster_folds.py` (the folds and the watch), `person_identity.py` (ordered resolution, never fused), `folds.py`.
- **Copy the old decisions across exactly as they are, into their own table, and never edit them.** Beside them, build a mapping from each old decision to the new stable keys of the two rows it was about. The old row numbers changed every night, so map by content: the names, the document, the amount or the role. A decision that cannot be mapped is carded, not guessed. The old verdict "hold" maps to "contested".
- Company shareholders are matched by name because the official number is empty on all 1.58 million rows; 26,857 had no match.
- Run the six first measurements and record them. None has ever been run:

1. How often a full name repeats, by how common the name is.
2. Addresses shared by many companies.
3. The error rate of the two confirming rules. No person labels this. Measure it on the test pairs from 4.3, and have the review agent read 100 confirmed links drawn at random with their evidence; report both figures and say plainly that the second is an agent's judgment.
4. How often each rule can fire at all, per register.
5. Company names to official numbers: the share that match exactly one company alive on the donation date.
6. The shape of the groups: sizes, and any group that contradicts itself.

- The error rate is recorded by name band on every rebuild. The acceptable number is ruled later by Arthur, with this data, before anything is sold or a new person-level connection goes on the public site.

**4.3 Build the test pairs from the registers.** No person labels them.

- **Known to be two people:** two directors with one name on one company at the same time; two candidates with one name standing in different electorates at one election.
- **Known to be one person:** the same role carried from one monthly company file to the next under the source's own role identifier; the same officer across a charity's successive annual returns under the source's own officer identifier; a candidate across an original and an amended return.
- **Size and sampling:** aim for at least 200 pairs of each kind in each name band (rare, middling, common), drawn at random within the band. Say so where a band cannot supply that many.
- **Use:** score the joining rules on them at every rebuild, and score the review agent on them before it acts alone (track C).

**Hold the director addresses from before 18 November.** The monthly company files captured before that date are documents and cannot be regenerated. Confirm the last one before 18 November is in the document store on both boxes and in the off-site copy. Add a check that fails if an address published after that date, where a director has substituted a service address, is used to confirm a link. The home addresses themselves are used for matching only and appear in no published table.

**4.4 Build the published-site shape and the Follow the Money template.** Move the release pipeline behind the new contract with its gates, **without its last steps**. The new pipeline stops when it has written a version folder. It has no deploy step, holds no deploy token, does not drain the live site's feedback, and serves its preview on ports other than 8300 and 8301. The old scripts have the frozen product's publisher job name and both of those ports written into them, and restart that job. Cut every one of those ties. Left in, the new pipeline would restart the frozen publisher and build the "new" site from the old app, and the comparison would pass while testing nothing. Add one gate that checks a figure from outside the estate, the Commission's own published table: on 3 October a fold took $8,024,342 across 110 donors off the old site and eleven gates passed it, because every gate read our own output.

**4.5 Compare with the frozen site.**

| Question | Answer |
| --- | --- |
| At what grain | Every published file of the ten kinds, figure by figure |
| Same inputs | At each frozen release the watcher records the version's name and a listing, by path and hash, of the captured-document folders. The new estate builds each day from that listing, so timing is not counted as a difference |
| Over how long | Seven consecutive daily releases |
| Tolerance | None on money. A difference is a difference |
| Each cause of difference | One card, saying which side is right and why. One card per cause, not per figure: rebuilt links over the whole director register will move many folds for a few reasons |
| A clean day | No difference without a card, and no card saying the new side is wrong |
| Passing | Seven clean days in a row |

**4.6 Checkpoint.** Run the product's checklist. Card what fails. Write the known-limits page. Fix, accept or drop each finding.

**4.7 Export test.** Build the bundle, start it with no connection to the estate, and run the product's checks.

**4.8 Do not switch the public site.** The rebuilt product replaces the frozen one only on Arthur's decision, not before 7 November, and by one change that can be undone. The old chain is disabled and kept.

**4.9 Build the board: the way to see connections across registers** (ruling 52). Arthur: "I would like an interface that lets me see the connections between registers. One problem is the difficulty visualising the data. It would be good to be able to run a search and see the results across registers displayed in panes like our Miller boards."

&#91;embedded content: the board · four panes, one path\]

**What it is.** A search box and a row of panes that grows to the right. The first two estates had this and called it the Miller board.

- **One search across every register at once.** The first pane lists the results grouped by register, with a count for each. A register that is not held says "not held".
- **Clicking a result opens a pane to its right:** the row, its fields, its source document, and its links grouped by register. Confirmed links come first and near links after, each with the rule that made it and the reason it is only near.
- **Clicking a link opens the next pane.** The row of panes is the path walked, left to right, so a connection across three or four registers is visible at once.
- **A person pane shows the group:** every row gathered as that person, by register, with the links that hold the group together, and the possible namesakes listed apart. A contested link shows its decisions.
- **A pane can be pinned, and a path can be saved.** From step 5 on, "report from here" opens a subject report on that row.

**It is a fifth shape, and it serves no single use case.** It is the way to look at the estate itself, for a customer and for the builder. It reads published tables, links and groups only. It creates nothing: no link is made by looking. Every pane cites its document, and every rule for what a product may show applies, home addresses above all.

**How it is built.**

- **A search table across registers,** published by `links`: one entry for every name, address and official number in every register, under the one shared reading, pointing at its row. It is rebuilt with the registers.
- **Each lane says how its rows appear in a pane,** as part of its spec: the title, the fields shown, the dates, the citation. A new lane's rows then appear on the board with no change to the board.
- **Take the mechanics from the earlier boards:** the panel chain in the oldest repository's `frontend/src/pages/SearchPage.tsx` with its `NzbnPanel` and `PersonPanel`; and in the old estate, `gui/src/pages/IndustryPage.tsx` and `gui/src/components/DossierView`. They are React and TypeScript.
- It lives in `products/board/`, on its own port, on the local network only.

**Why here.** It is the fastest way to see whether the links are right, so build its first version as soon as the first lanes and the links exist, before the comparison in 4.5. It grows with every lane after that, and in step 7 archive-search results become a pane too.

**Done when,** for this first version: a search for a known donor opens, across four panes, its returns, the company behind it, that company's directors, and one director's other companies, each pane citing its document.

### Done when

- [ ] Every lane has its five-line spec, its outside check passing, and a reconciling catch log.
- [ ] The Fable and Opus builds of the charities lane are compared and the result is a lesson.
- [ ] The six measurements are recorded.
- [ ] The comparison has run seven days with no difference lacking a card.
- [ ] The checkpoint is done and the known-limits page exists.
- [ ] The export test passes.

### Briefs to paste

For each lane (change the lane name and folder):

```text
You are a build session for QueryNZV4 on node2, running as the model
docs/briefs/next.md names, in the working copy the launcher made for
you. Read docs/PLAN.md, then docs/status.md and your own status file,
then the lane contract and the row contract. Build one lane only:
<lane>, in registers/<lane>/. Get its documents the way step 1.10
says for its case; fetch nothing the old estate already holds. Search
the lessons and the reference notes for this source before writing
anything. Give every row a stable key and a citation. Keep a catch
log that reconciles. Find one figure from the source itself to check
against. Work in your scratch schema; edit nothing outside your
folder; never touch the old estate's jobs, folders or primary
database. Push your branch and raise a merge request. Finish by
telling Arthur what closed and what is carded.
```

Lane folder names for this step: `charities-a`, `charities-b`, `companies`, `parties`, `party-returns`, `candidate-returns`, `disclosures`, `party-finance` (expenses, statements, promoters, rules), `candidates-house`, `interests-expenses`, `gazette`, `society-officers`.

For the links, the shape and the comparison:

```text
You are a build session for QueryNZV4, running as Fable on node2, in
the working copy the launcher made for you. Read docs/PLAN.md, then
docs/status.md and your own status file, and continue where it stops.
Do the part of step 4 named here: <links, in links/ | published-site
shape and Follow the Money template, in products/site/ and
products/templates/ftm/ | the board, in products/board/ | comparison
with the frozen site, in checks/>. The two confirming rules are exact
and are not yours to change. Copy the old decisions untouched and map
them beside. Record the six measurements. The new release pipeline has
no deploy step and never touches the frozen product's publisher job
or its ports. Do not switch the public site. Push your branch and
raise a merge request. Finish by telling Arthur what closed, what is
carded and what waits on him.
```

## Step 5: subject reports, legal documents and company monitoring

**Goal.** The subject-report shape, ten templates on it from easiest to hardest, the legal sources read in, and company records kept as fresh as the official interface allows.

**Why this order.** Ten of the sixteen use cases are subject reports, and four of them run on data already held.

**Models.** Fable for the shape, the legal-document research and the monitoring design. Opus for lanes and templates.

### Do

**5.1 Build the subject-report shape.** One builder:

- It starts from one row, a person or an organisation, chosen by the user.
- It walks confirmed links outward and lists near links beside them, each with its reason.
- It fills the template's sections from the registers the template names.
- It applies the template's own rules and flags.
- Every statement carries its citation. Every blank says "none found" or "not held".
- It can print as a memo.

Harvest from the old estate, as ideas and tests more than code: the August flows for Legal, Banking, Recruitment and Agriculture; the report builder and printable memo; the seven-rule person set and the four-rule company set in `data-layer/flags`; the ownership-chain page; the checklists in `data-layer/docs/USE_CASE_REQUIREMENTS.md`. They were built on the old graph.

Presentation rules for every report, because these are the ways a true link misleads:

- **Every connection is dated.** An undated hop is marked as undated.
- **Hubs are flagged:** professional directors, nominees, the Crown, an address with a thousand companies.
- **A nominee is not an owner.** A role is shown as the register states it.
- **Coincidence is not shown as cause.** Two facts sit side by side with their dates; the report does not join them with "because".
- **Absence is not a finding.** "No connection found in the registers held" is the most a report can say.

**5.2 Templates, in this order.** Each ends with a checkpoint.

| Order | Use case | Runs on | Waits on |
| --- | --- | --- | --- |
| 1 | 8 Recruitment board screen | Held data | Nothing |
| 2 | 4 Agriculture counterparty | Held data | Nothing |
| 3 | 3 Banking director history | Held data | The securities register for the full picture |
| 4 | 2 Legal counterparty and conflict check | Held data | Court judgments, from 5.4 |
| 5 | 13 Beneficial ownership and AML, domestic half | Ownership chains through held shareholdings | Sanctions lists, limited partnerships, overseas data |
| 6 | 7 Construction and phoenix detection | The insolvency file, disqualified directors, the change history | The building practitioners register |
| 7 | 5 Business credit and monitoring | Monthly grain at first | 5.5 for freshness; the insolvency and securities interfaces |
| 8 | 6 Insurance underwriting | WorkSafe releases, regulator actions | Courts and tribunals |
| 9 | 11 Healthcare operator governance | Retirement villages file, charity returns | Health and Disability Commissioner decisions |
| 10 | 12 Property developer due diligence | Company side of land titles, overseas investment decisions | Building consents, courts |

The templates for use cases 2, 6, 11 and 12 gain an "articles mentioning" section once the journalism keyword search of step 7.6 exists. Template folders are `products/templates/<number>-<short-name>/`, for example `products/templates/08-recruitment/`.

**5.3 Lanes this step adds.** Read what is already held before acquiring anything.

| Held and unread | What it gives | Note |
| --- | --- | --- |
| The company insolvency file | Insolvency type, appointees, dates | Read today only as background |
| Change history, 16 tables | Trading names, industry and roles as they change | Kept only since 16 August 2026 |
| Commerce Commission cases and FMA warnings | 112 cases and 16 warnings, parties parsed | The Act section is empty on all 128 |
| Disqualified directors | A derive already written | Its three tables have no definition anywhere |
| Charity annual returns | 421,633 returns | No typed read |
| Retirement villages file | Statutory supervisor name and date | Contents need a look |
| WorkSafe releases | Release texts | A read of prosecution facts from the text |
| Overseas investment decision summaries | Applicant, vendor, price | No read |
| Land titles | Company owners matched | Individuals are held back under the licence. The licence obliges amending or deleting on request, so the takedown service is built before any individual's row is used |

| To acquire, all free and public | For |
| --- | --- |
| Sanctions lists: Foreign Affairs, United Nations, Police designations | 13 |
| Limited partnerships register | 13 |
| Licensed building practitioners | 6, 7, 12 |
| Health and Disability Commissioner decisions | 11 |

Waiting on outside approval since 19 September, and not to be worked around: the securities register, the Insolvency Register and the financial service providers interfaces. The insolvency interface brings a daily removals check for good. Until they arrive, the templates that want them say "not held".

**5.4 The legal documents.** Arthur's ruling 18: these sources are in. They were held because they need good profiles and good reading, not because they were unwanted. Easiest first.

1. **The parsed case-law interface (OpenLaw).** The key is in hand and tested; about 47,000 cases, already parsed, so no page reading. Build the lane.
2. **The court judgments already captured.** The courts register exists in `data-layer/courts_register` (parse, derive, suppress) and is fed by nothing; 145 documents were in scope. A consolidated appeal names several parties in one line: emit one row per party and role. Repoint its suppress lever, which defaults to the old graph.
3. **Research how legal documents are structured,** and write it up before building further: neutral citations, parties, outcomes, numbered paragraphs. An earlier pipeline kept evidence by numbered paragraph; port the idea, do not resurrect the code. Write a profile per court format.
4. **Repeat the page-reader trial on scanned legal documents.** The September and step 3 results cover electoral returns only.
5. **Tribunals, employment and environment courts, coroners.** They were paused on a robots signal, which no longer decides anything. Apply the capture test and write the one-page position. A permission letter to the Ministry of Justice is drafted and unsent; sending it is Arthur's. Capture of an open page does not wait for the letter. It waits only where the site blocks or challenges.
6. **Not reopened:** the High Court and Court of Appeal back-catalogue, which drops automated requests; the legal-information site that requires an agreement.

**A court's suppression order binds every product.** A name a court has suppressed is suppressed on every surface.

**5.5 Company monitoring** (ruling 19).

- The monthly import stays as it is.
- **Whenever a product looks an entity up, the estate checks that entity against the official business-number interface.** The product does not do this itself, because a product never writes into the estate. It raises a request; the companies lane makes the call, lands the answer as a document, and rebuilds that entity's rows from it. The interface has no change feed, so this is the deepest it allows. It answers in about 0.6 seconds per entity; the access key is in the credentials folder and was last used in August.
- Each difference is stored as a dated change. This is what finally gives an ended role its real end date.
- Watched entities are checked on a schedule, not only on lookup.
- Sole traders, partnerships and trusts are not in the monthly file and are reachable only this way, one at a time.
- An exported copy of a product does not call the interface. It is refreshed from the estate.

### Done when

- [ ] The shape passes its tests and prints a memo.
- [ ] Each of the ten templates has had its checkpoint and has a known-limits page.
- [ ] The OpenLaw lane and the courts register are fed and checked against a figure from their source.
- [ ] The legal-document research note and its profiles exist.
- [ ] A lookup updates the register from the interface, and the change is dated.

### Briefs to paste

```text
You are a build session for QueryNZV4 on node2, running as the model
docs/briefs/next.md names, in the working copy the launcher made for
you. Read docs/PLAN.md, then docs/status.md, and continue where it
stops. Do the part of step 5 named here: <the subject-report shape,
in products/report/ | the template for use case N, in its folder
under products/templates/ | the lane for <source>, in
registers/<lane>/ | the legal-document research, in docs/research/ |
company monitoring, in registers/companies/>. A template may read
only the published tables it names. Date every connection, flag hubs,
never show coincidence as cause. Run the checkpoint when a template
is built: test it, card what fails, write the known-limits page. Push
your branch and raise a merge request. Finish by telling Arthur what
closed and what is carded.
```

## Step 6: register scans

**Goal.** The scan shape and four templates on it. A scan asks one question of every row, such as "which suppliers share a director with a donor?", and lists the answers with their citations.

**Why after step 5.** A scan needs the groups built for every person, and the two trust settings. Both settings have defaults (see "3. Links"), so this step does not wait for a ruling. Put the measurements from step 4 and your recommendation to Arthur in the decision queue before this step starts; if he has not ruled, build on the defaults and keep them as settings.

**Models.** Fable for the shape and the multi-step rule. Opus for lanes and templates.

### Do

**6.1 Build the scan shape.** A scan is a saved question, the registers it reads, the trust rule it applies to chains, and a list out. Every line in the list carries its citations and its grade. A scan re-runs when its registers change.

**6.2 Templates, in this order.** Each ends with a checkpoint.

| Order | Use case | Runs on | Note |
| --- | --- | --- | --- |
| 1 | 10 Tender and award intelligence | 29,874 award notices from 2014, keyed on official business number, held and never read | Needs a reader and a scheduled refresh; the file is refreshed by hand each quarter today |
| 2 | 9 Government procurement integrity | Awards joined to directors, shareholders and donors | A donor-to-award join is the plainest case of coincidence shown as cause. It stays off the public site unless Arthur decides otherwise |
| 3 | 14 Post-settlement governance map | Charity officers, Māori business identifiers, company roles | Needs the iwi and hapū directory and the settlement commitments database, both public. The Māori Land Court needs registration. 200 Waitangi Tribunal reports are held under an old ruling that asks for a named use case: put it to Arthur |
| 4 | 15 Lobbying | Gazette appointments, MPs' interests, the Hansard register, ministers' diaries | Arthur, 17 October: four products in order — (a) the ministers' diary register (a built register from the monthly proactive-release PDFs; no dependency, so it can go into the registers milestone early); (b) who each minister met and what those people and organisations represent, resolved against the spine, so after links (and the first real job for track D.2); (c) the legislation join — minister ↔ portfolio ↔ bill ↔ Hansard speech, with the meetings beside it by date, and an "articles mentioning" section that retrieves and asserts nothing; (d) discourse, which is its own product, use case 17. Ministers only: backbench MPs publish no diary. The template will still say "not held" often |

**6.3 Sources this step adds.** All public.

- Live open tenders, agency contract disclosures, council procurement on other platforms.
- Grants: gaming-machine societies, Lottery, regional development funding, tertiary funding.
- Council minutes from 24 councils on one meeting platform are held with no read of attendance or resolutions.
- Local election returns and councillors' interests, council by council.

**6.4 A question for Arthur, not blocking.** Whether the award join, pre-2019 awards or a councils tier ever appear on the public Follow the Money site. The capability is built either way.

### Done when

- [ ] The two trust settings are ruled, or their defaults are recorded as in force.
- [ ] The award notices are read, refreshed on a schedule, and checked against the source's own count.
- [ ] Each of the four templates has had its checkpoint and has a known-limits page.

### Brief to paste

```text
You are a build session for QueryNZV4 on node2, running as the model
docs/briefs/next.md names, in the working copy the launcher made for
you. Read docs/PLAN.md, then docs/status.md, and continue where it
stops. Do the part of step 6 named here: <the scan shape, in
products/scan/ | the template for use case N, in its folder under
products/templates/ | the lane for <source>, in registers/<lane>/>.
A scan lists what the registers show with dates and citations; it
never says one fact caused another. Nothing from this step goes on
the public site. Run the checkpoint when a template is built. Push
your branch and raise a merge request. Finish by telling Arthur what
closed and what is carded.
```

## Step 7: archive search

**Goal.** History search over the whole of Papers Past with every search tool, and keyword search over other journalism.

**Why it can start early.** Most of it is machine time. The embedding run begins as soon as the scheduler works and runs beside steps 4 to 6.

**Models.** Opus for the ingest. Fable for the index design and the recall proof.

### What is held

- 4,648,837 Papers Past articles in the news corpus, about 2.1 million of them in the old meaning index.
- A further archive of about 86 million items on the boxes, never ingested. Find it in the step 1 baseline.
- Every person, claim and mention drawn from Papers Past was deleted on Arthur's word on 27 September. It stays that way.

### Do

**7.1 Put the search-only rule in place before the first batch lands.** In the old estate only a status value kept Papers Past out of extraction. In the new estate it is a rule with a test: nothing from this archive can reach the links.

**7.2 Ingest the archive so that every catch is found exactly where it happens.** This is Arthur's instruction.

- **Named stages, each with its own count.** Items in, items out, items set aside with a reason. In must equal out plus set aside, on every batch.
- **A catch log.** One line per catch: the stage, the item, its place in the archive file, the reason, and the first failing example kept whole.
- **Small batches first:** ten thousand, then a hundred thousand, then a million. A batch that does not reconcile stops the run.
- **Nothing set aside silently.** A run that sets aside more than a stated share stops and says which stage. One old build stored 3.4 million of 10.65 million rows and reported nothing.

| Stage | Catch to expect |
| --- | --- |
| Reading the archive | Format, encoding, truncated files. Unknown until the first batch |
| Overlap with what is held | 4.65 million articles are already in; reprints between papers also collide |
| Landing | Table growth copies to the standby and swells the off-site copy |
| Keyword index | Needs sizing at this scale before an engine is chosen. Measure the first batch, then decide and record why |
| Meaning index | Cannot be built in memory at this size; see 7.4 |
| Serving | Filters and change-over-time queries have only run at the present size |

**7.3 Read whole documents.** The old keyword index read only the title and first 1,500 characters; 77.5% of articles are longer. Index the whole text.

**7.4 Build the meaning index.** The old method needs about 500 GB of memory at this size.

1. **Measure the first batch:** lengths, the share that is adverts or tiny notices, and how much is reprints. This decides what gets a vector.
2. **Split long columns into passages,** each with its own vector, so nothing past the lead is invisible.
3. **Speed up embedding before the long run.** The model (bge-m3) uses 0.7 GB of a 34 GB graphics card. Many copies per card, or larger batches, should raise the rate a great deal. Keep the server's prompt cache off: the prompts are unique, and with the cache off one card did 2.73 times as much in the same 90 minutes, 437,328 short texts, about 80 a second. The record's older figure of 25 a second and 40 days predates that test. Whole documents split into passages are more and longer texts, so measure before estimating.
4. **Embed in pieces by newspaper and year, into files on the hard disks,** at half precision. Each piece has its own count and catch log, and a stopped run resumes at the next piece.
5. **Share the graphics cards through the scheduler.** Embedding is bulk work that yields to document reading and to live questions.
6. **Build a compressed index:** each vector squeezed to about 64 bytes, so the whole set fits in under 10 GB of memory. It grows piece by piece, so search works while the run continues.
7. **Re-check the top candidates exactly** against the full vectors on disk. Seconds, not milliseconds, is acceptable for deep search to begin with.
8. **Serve it as its own small process,** blended with keyword results.
9. **Prove recall first** against exact search on a one-million sample.

The vectors stay out of the off-site copy, because they can be regenerated, and get a second copy on the other box, because regenerating costs weeks. The figures above assume one vector per item; passages will raise them, and the first batch says by how much. The old meaning index over news stops being rebuilt when the press jobs stop in step 1. Only its Papers Past part is rebuilt, in this design. The memory the old index holds is freed when the old app that loads it is stopped.

**7.5 Build the search tools.**

| Tool | State in the old estate | What it adds |
| --- | --- | --- |
| Matching that tolerates misread print | Not built | The scans turn Auckland into "Ancklaud". Without this most deep searches miss |
| Old and variant spellings, names without macrons, initials | Pieces exist | One query finds a person under every form the papers used |
| Date, newspaper and region filters | Built | Narrowing by place and decade |
| Change over time, and distinctive terms | Built | When a subject rises and falls |
| Reprint detection | A hand-run scan | Nineteenth-century papers reprinted each other; collapse the copies |
| Old place names | 54,667 official names loaded | Places by former and Māori names |
| Compound-word splitting | Written, wired to nothing | Old run-together words |
| A broad name index | New (ruling 43) | Which names appear in which articles: people, towns, roads, organisations. A search aid only. The method is decided by the measurement in track D.2 (ModernBERT-base against the deterministic path) |
| An agent that searches in rounds | A research agent exists with other tools | Follows leads across many searches and reports with citations |

**7.6 Keyword search over other journalism** (ruling 8).

- News capture keeps running. Every NZME masthead is excluded from the index and from capture; what to do with the NZME copies already held is a question for Arthur.
- Show the headline, masthead, date, a link, and a short extract around the matched words. Never the full text.
- Paywalled outlets are not captured and are never forged.
- No meaning index and no people or claims are built from current journalism while the press work is parked.

**7.7 The history-search template and its checkpoint.** Copyright on Papers Past varies by title and date; add it to the before-selling legal list.

### Done when

- [ ] Every ingest batch reconciles, and the catch log names each catch.
- [ ] The keyword index covers whole documents.
- [ ] Recall is proven on the one-million sample and recorded.
- [ ] The meaning index covers the archive, with its count against the archive's count.
- [ ] A test proves nothing from Papers Past can reach the links.
- [ ] The checkpoint is done and the known-limits page exists.

### Brief to paste

```text
You are a build session for QueryNZV4 on node2, running as the model
docs/briefs/next.md names, in the working copy the launcher made for
you. Read docs/PLAN.md, then docs/status.md, and continue where it
stops. Do the part of step 7 named here: <ingest, in
registers/papers-past/ | keyword index or meaning index or search
tools, in products/search/ | journalism keyword search, in
products/search/>. Papers Past is searched, never mined: build no
people, claims or links from it. Start with small batches; stop a
batch that does not reconcile; log every catch with its stage and its
place in the archive. Queue all graphics-card work through the
scheduler. Push your branch and raise a merge request. Finish by
telling Arthur what closed and what is carded.
```

## Tracks alongside

These run beside the numbered steps. Each is one session's work at a time and counts toward the three build sessions. The brief for a track is the step 5 brief with its task line changed to "Do track X", and its folder is: A `support/takeover/`, B `support/offsite/`, C `links/review/`, D `support/rules/`, E `registers/<source>/`, H `support/security/` and `docs/security/`.

### Track A: automatic takeover

**Starts when** the third machine is on the network. **Model:** Fable.

- **Primary and standby are roles, not boxes.** The primary role normally sits on node1. If it lands on node2 the scheduler reserves memory for it there.
- **Today takeover is by hand:** about 45 minutes, with every privileged line typed by Arthur. One drill is on record (24 August: back in 2 minutes 37 seconds, nothing lost) and a cold-restart drill passed in 39 seconds on 15 September. The floating address's move has not been drilled again since, and restarting the job that holds it aborts. The runbook is `docs/runbooks/FAILOVER_DRILL.md` in the old repository.
- **With two boxes, neither can tell "the other died" from "the link dropped".** The third machine votes, which is what makes automatic takeover safe.
- **Build:** automatic promotion on the voter's word; the floating address moves with the role; the survivor starts whatever standing services are missing, in order of importance, within what one box can carry (size that set to 62 GB); a box that returns rejoins as the standby, catches up its files, and its worker starts pulling again.
- **A two-way file copy** for what the database does not carry: captured documents, the Papers Past archive, model files, index files.
- **Build and rehearse it beside the live database, on a scratch pair of database instances.** The live database feeds the frozen site. No change to its settings and no drill on it happens before the election, and after the election only on Arthur's word (hard limit 22).
- **Then drill it on the live pair in both directions,** on Arthur's word, before calling it done.
- **Open:** whether each write waits for the standby before it is confirmed. The default is that it does not, because everything above capture can be rebuilt.
- **Privileged setup** on either box may need Arthur's hands. Queue it; do not work around it.
- **What the 17 October failover taught (old ruling 365; old lessons 1-ops-the-estate, 2026-10-17 block).** node1 died after a RAM install and the takeover to node2 was done by hand in 45 minutes. The floating-address model held: no writer was edited. Everything around it was manual, and track A must build these five in, each with a check on the board rather than a line in a runbook: (1) promotion that needs no password — a root-owned promote job that runs as the database user; (2) the floating-address job asks the wire (`arping`) before adding the address and refuses if anything answers; (3) a returning box never starts as a second primary — on boot it asks whether the address is held elsewhere and, if so, comes up as the standby or not at all, with no static per-box marker deciding; (4) the access rules file (`pg_hba`) is generated from one source for both boxes and diffed nightly — the standby lacked the line for reaching itself through the floating address; (5) nothing names the other box by its address: the four old jobs that did (`wal-archive-mirror`, `querynz-residue-mirror`, `querynz-verdict-sync`, `querynz-deploy-node1`) had to be stopped by hand — a job names a role or checks the peer and skips cleanly. Two more for the hardware baseline: a box that holds a role needs a way to see its firmware (node1's display has never worked, and a RAM change is the commonest road to a "press F1" screen), and the boxes are serviced one at a time, the standby streaming again before the primary is touched. **Track A starts from the real state, which is inverted from this plan's baseline: node2 is primary, node1 is down and will rejoin as the standby after a rewind.** A watcher for a box pings the box's own address, never the floating one.

Boot lessons already paid for: the standby failed at boot because its log disk mounted 14 seconds after it started; mount the hard disks so a missing disk does not block the boot; the floating address must come up after the network; user-level jobs on a box need lingering enabled to run without a login. The record asks for an uninterruptible power supply, and both boxes reach the internet over Wi-Fi; both are Arthur's.

### Track B: the off-site copy

**Starts** after step 1. **Model:** Opus, reviewed by the integrator.

- **Ruling 21:** the off-site copy stores changes, with a weekly full checkpoint. It has to be efficient.
- **Today** 368 GB is dumped every night and re-sent whole after any failed attempt, over a satellite link. Of that, 146 GB has no way to be rebuilt.
- **Build the new copy as new `qv4-` jobs beside the old one. The old nightly job keeps running, untouched, until a restore from the new copy has been rehearsed and passed.** Retiring the old job is then a change to the old estate, so it is Arthur's word and not before the election.
- **Sort the data by the delete rule.** What cannot be regenerated goes first and always: captured documents, decisions, corrections, document profiles, answer sets, and anything a person typed. Human review notes were once in no backup at all.
- **What can be regenerated stays out,** unless rebuilding it costs more than storing it. The vectors stay out and get a second local copy.
- **The press graph database keeps changing after the freeze,** while two old jobs, `feed-parties` and `gazette-feed`, still write to it. They are candidates to stop in step 1.4. Once they are stopped with proof, nothing writes to the press graph: take one last full copy and remove it from the nightly copy. Until then it stays in. The database itself is never dropped without Arthur's word.
- **Rehearse a restore to equality,** not to "90% of the primary", and record the time it took.

### Track C: the review agent

**Starts** with the links in step 4. **Model:** Fable.

- **Its job:** read each watched link's evidence and split the link if it cannot trust it. Arthur is not in this loop.
- **Three verdicts, matching the decisions table.** *Not the same:* that decision is added and the groups rebuild. *Contested:* the agent cannot trust the link; it drops to near, and products show it as a possible namesake. *No reason to doubt:* the link stays confirmed and the review is recorded.
- **It runs on the boxes,** as a bulk job through the scheduler, on the review-and-questions model profile (the local Qwen model). Nothing it reads is sent to a model off the boxes.
- **It may search the web only to find evidence that two rows are different people.** A query carries a name and a public role at most (hard limit 12), goes through the fetch gate, and every web citation must be a page it actually fetched in that run.
- **Build on what exists:** `data-layer/research/research/merge_refuter.py` (the refute-only agent with web search), `data-layer/research/research/webtools.py`, and the timed screen-then-re-read pattern in `data-layer/healer/healer/crawler.py` and `reread.py`.
- **It must be measured before it acts alone.** The old one was tested on 13 hand-labelled cases, where about 196 "different" cases are needed to measure it to within 0.05. Use the test pairs from step 4.3, which need no labelling.
- **The pass mark, as a default until Arthur rules:** on the pairs known to be one person, it wrongly splits fewer than 1 in 100. Splitting is the safe direction, so no minimum is set on how many of the known-different pairs it catches; report that figure. Until it passes, its verdicts are recorded and not applied.

### Track D: the rulebook and the rule-learning loop

**Starts** after step 1. **Model:** Opus for rules, Fable to review them.

- **Arthur's ruling 46:** "Just as we automatically build document profiles, we also built rules for understanding the press graph and errors we encountered via the healer. We should maintain this process and also capture the existing extraction lessons and rules too."
- **Captured** in step 1 under `reference/rulebook/`. Parked, searchable, not running.
- **The loop in the new estate:** the catch logs and the review agent's splits supply the cases. An error seen often is named as a class and carded with examples. A build session writes a rule for it with a test against real rows. The rule applies to new readings and to rows read before it existed.
- **The doctrine worth keeping:** a rule that cannot decide leaves the row alone; every action is reversible and written down with the rule's name; no rule decides on the shape of a name alone.
- **Profiles for new kinds of document are proposed automatically.** Four lessons bind that: ask which profile a reading belongs to before writing a reader; a profile written after its reader is a description until it is pinned to the code both ways; a profile that claims a document it will not read is worse than none; an unassigned document may only mean a misspelt marker.

**D.2 The name-resolution experiment** (Arthur, 16 October: *"instead of the deterministic extraction using a large register of names, I would like to experiment with ModernBERT-base for name resolution. I am also interested in other things it can do"*). An experiment, not a lane: a session fine-tunes ModernBERT-base (local, so hard limit 10 holds) to tag names in text and resolve them to register rows, with the joined registers as the answer key — a name that matches exactly one row by the shared reading is a labelled example, and the test pairs of step 4.3 give the hard cases. It is scored against the old deterministic path (the name index and the register-of-names lookup) on the same documents, and the result is written up as `docs/trials/name-resolution.md` with a second page listing what else the model is good for here (classification of notices by type, the Papers Past name index of 7.5, document-profile recognition). It runs on the scheduler like any model job, touches no product, and publishes nothing; it earns a step only by the measurement. **Starts** when the first lanes and the shared reading exist (step 4). **Model:** Fable to design the key and the scoring; Opus to run it.

### Track E: capture the windowed sources now

**Starts** as soon as the lane contract exists. **Model:** Opus.

Tenancy Tribunal and Real Estate Authority decisions are public for three years only. Capture them now and hold them; the reading comes in step 5. Apply the capture test and write the one-page position first. Capture of an open page does not wait for the unsent permission letter; it stops only where the site blocks or challenges. The old estate never captured these, so the new lane does its own fetching through the new fetch gate.

### Track F: consuming and retiring the old data

- Keep a list, `docs/old-estate-consumed.md`, of each old table and file store and which new lane has consumed it.
- **Nothing old is deleted without Arthur's word.**
- The press graph is parked, not consumed. Whether to move it off the primary to free space is a question for the decision queue.

### Track G: the before-selling list

Not worked now; kept current in `docs/legal/before-selling.md` so the lawyer's review has one place to start.

- The one-page legal position for each class of source.
- Chandra OCR 2's licence, if it wins the trial.
- Copyright on Papers Past, by title and date.
- The LINZ licence for personal data and its takedown duty.
- Each source's terms for commercial reuse.
- Privacy law for any report about a person; credit-reporting rules; what sources an AML regulator accepts.
- The acceptable error rate for links, to be ruled by Arthur with the measurements.

### Track H: security hardening, and rotating every password and key

**Starts** when step 1 closes. **Model:** Fable. **Launcher:** `bin/start-session security support/security docs/security`

**Arthur's ruling 51 (12 October):** "We really need to rotate passwords and API keys. This needs to be in the plan too." It replaces old ruling 270, which put off every rotation to a later hardening pass. The long-running security cards of the old estate are gathered here.

**Why this is a track and not a step.** Most of the doing is Arthur's: only he can issue a new key at a provider or change a database password. The session's job is to make each of those a five-minute task with no guesswork, and to prove it worked.

**Rules for this track. They are hard limit 1 applied.**

- **A secret is never typed, pasted, confirmed or printed** in a session, a card, a log or a chat. A secret reaches a transcript the moment someone confirms it. Two earlier rotations of the deploy token failed for exactly this reason: the replacement was pasted into a transcript too.
- **Arthur copies each new value from the provider's page straight into the credential file** on the box, and tells the session only that it is done. Not through chat, and not through anything a session can see.
- **A session never reads the credentials folder,** except one variable at a time inside a command that uses it without showing it.
- **Every check prints a verdict only:** "works" or "refused".
- **Every rotation ends with two proofs and a note:** the new value works, the old value is refused, and the date is written in the inventory.
- **Anything the frozen product uses is rotated well clear of the daily release,** and followed by a `--dry-run` release.

**H.1 Bring the inventory up to date.** The old estate names every secret, never its value, in `docs/runbooks/CREDENTIALS_INVENTORY.md`. Walk it row by row against the file names and variable names on both boxes and against the job files and code that read them. Write the result as `docs/security/inventory.md`: each secret, where it lives, what reads it, whether it can be used from outside the local network, and whether it is known to be exposed. Two files there have never been explained, `x.env` and `sync.env`; ask Arthur to confirm or delete them.

**H.2 Find where secrets have leaked, and report places only.** Look in: the old repository's history; the Claude settings files on the boxes, which once carried a database password inside allowed commands; the saved session transcripts on the boxes; shell history; the system journal, where an API key once leaked through a client's logging. Report the file and line, never the value. Anything found counts as exposed and is rotated. Clean out what can be cleaned.

**H.3 Write one short runbook per secret,** for Arthur: where to go at the provider, exactly which permissions to grant, which file and variable to put it in, and what to tell the session when done.

**H.4 Wave one: secrets that work from outside the local network.** Do these as soon as the runbooks exist. None needs a job stopped.

| Secret | Why it is in wave one | Arthur does | The session proves |
| --- | --- | --- | --- |
| The deploy token for the public site | It has been exposed twice, and whoever holds it can change what followthemoney.nz serves, during an election | Creates a new token with the same narrow permissions and nothing else, copies it straight into the credential file, revokes the old one | `ops/cloudflare_token_check.py`, which prints verdicts only; then a `--dry-run` release; then the next scheduled release is green |
| The business-number interface key | It passed through chat when it arrived | Issues a new key at the provider | One lookup works; the old key is refused |
| The LINZ data key | It is on both boxes and reaches an outside service | Issues a new key | A dry run of the weekly titles pull |
| The off-site storage key | It reaches outside storage | Issues a new key in the storage console and revokes the old | The next nightly copy succeeds |
| The cloud model keys | No job may use a cloud model, so they should not exist on the boxes | Revokes them at the providers and removes the lines | The model client's test that no lane can call out |
| Subscriber logins for NBR and BusinessDesk | Those outlets are no longer captured | Removes them from the boxes | Nothing reads those variables |
| The alarm address | Anyone who has it can read or send the alarms | Makes a new private address, updates the file and the phone | A test alarm arrives |
| The keys the boxes use for GitHub | A new repository is being added | Issues a key for the new repository; reviews the old ones | A push works |

**The off-site backup passphrase is a special case.** Every existing backup needs the old passphrase to restore. If Arthur changes it, both are kept in his password manager with their dates, and a restore of an old backup is rehearsed before the old one is forgotten.

**H.5 Wave two: the database passwords.** Three roles: the application role that every old job connects as; the replication role, which is still the placeholder it was created with; and the read-only role the public app uses. Tighten the database's access file in the same sitting, so each role may connect only from where it is used.

- **This is stop-the-world for the old estate.** The application password sits in every old job's connection settings and in about fourteen installed override files. Every one must change together, and every job restart.
- **It is the third kind of change to the old estate this plan authorises** (hard limit 22). It changes credential files and running jobs, never the old repository.
- **The session prepares everything first:** the list of every file that holds each password, by name only; one script that takes the new value from Arthur at a prompt, sets the role's password and rewrites every file without showing it; the order of restarts; and the proof afterwards.
- **Rehearse on a scratch pair of database instances.** Rotating the replication password once forced the standby to be rebuilt from scratch, 326 GB.
- **The proof afterwards:** every kept job starts; the standby is streaming; a `--dry-run` release is green; the watcher is green; the old passwords are refused.
- **When:** Arthur chooses the sitting and is present for it. The default is the first quiet day after the election, because the database is reachable only from the local network and the sitting restarts everything the frozen site depends on. If he wants it sooner, it can be done any day well clear of the daily release.
- The new estate's own logins were created fresh in step 0 and are not part of this.

**H.6 Make rotation cheap from now on.** In the new estate every job reads its secrets from one named file, through one function, when it starts. The installer copies those files from box to box and never through the repository. So a rotation is: Arthur writes one file, the installer copies it, the `qv4-` jobs restart. Carry the old test that fails if any job file holds a secret. The inventory gives each secret a date; rotate everything on it at least once a year and at once when exposed.

**H.7 The other long-running security cards.**

| Card | What it is | In this plan |
| --- | --- | --- |
| Admin rights on node1 | The admin-rights file on node1 was never redone, so commands that need no password on node2 still ask on node1 | Arthur's, at the box. The runbook from H.3 covers it |
| A container for unattended work | Sessions may run without asking permission only inside a sealed container, never on the bare box. Never built | Build it after wave two. Until then no session runs with permissions bypassed (hard limit 3) |
| Text from outside treated as instructions | A model that reads fetched web pages or documents can be told things by them | Carry the old rule: a tool that writes is offered to a model only when the user's own request needs it, and fetched text is data, never instructions. It binds the review agent |
| The request limit on the apps | A courtesy limit, not a control | Enough while products listen on the local network only. Revisit before selling |
| Leaving the box: a public host, encryption in transit, a domain | Needed before any product is opened to strangers | Outside this build. It belongs with selling |

**Done when**

- [ ] The inventory is current and every row has a rotation date or a reason it has none.
- [ ] The leak search has run and every place it found is cleaned or listed.
- [ ] Every wave-one secret is rotated, with both proofs recorded.
- [ ] The database passwords are rotated in one sitting, the proof is green, and the access file is tightened.
- [ ] The test that no job file holds a secret passes in the new repository.

## Reference: the old estate

Every piece worth reusing, where it lives in the old repository, the faults its own records admit, and a first verdict. "None documented" means nothing was written down, not that nothing is wrong. Paths were checked at commit `2d3874e`.

The old structure strained in three places, which is why the cut changes: `data-layer/registers` is about 14,800 lines in 39 files owning some fifty tables; `ops` is about 47,500 lines across 157 scripts with no spec, 31 of which write to the database; and shared logic had no home.

### Names, addresses and capture

| Piece | Where | Faults on record | Verdict |
| --- | --- | --- | --- |
| Name functions | Copies in `registers`, `query`, the graph writer and the document reader | Seven divergent copies. One drops macrons, so Rāwiri and Rawiri differ. The two party-name functions disagree on 6 of 78 labels; a fuzzy rule folds New Labour into Labour. One page never called its fold, so 104 donors were published under more than one name | Take the rules and tests. Write one function |
| Address keys | In `registers` | The street key returns nothing for PO boxes. An older key dropped street numbers under three digits; 160 folds were withdrawn for it. One address holds 1,060 companies | Rebuild. Address never confirms alone |
| Fetch gate | `ingestion/fetchgate.py` | 35 older fetchers bypass it. The standard robots reader in Python is over-permissive and must not make permission decisions | Take. No new lane bypasses it |
| Landing | `ingestion/landing.py` | Five older entry points register a document before landing it, so a failed landing is never retried. Five of thirteen writers bypassed the wrapper | Take the one wrapper only |
| Headed browser | `ingestion/newsscrapers/browserfetch.py, ingestion/hansard/scraper.py; the lock helper is ingestion/browser_profile.py` | A challenged page is dropped. After an unclean exit the browser leaves a lock that blocks every later launch; clear it only if its owner is dead | Take. A challenged read stays a failed read |
| Coverage scan | The `querynz-coverage` job | For 86 of 222 source-and-weekday pairs the test reduces to "published at all". When half the sources are thin on one day, it is our outage, not theirs | Take as is |
| Charities lane | `ingestion/charities` | Client not on the fetch gate; its documented host no longer resolves; officers land with no person key; its timer had never fired at one audit | Take the idea, not the code |
| Award notices | `ingestion/gets`; tables `bulk.gets_*` in `nzbn_canonical` | Loaded by wipe and reload, refreshed by hand each quarter, no scheduled job, never read | Take the data |
| Gazette register | `data-layer/gazette_register` | Its schema file has drifted from the real tables. Its gate records a failure and still exits clean. 35,938 notices unread | Take after fixing the gate |
| Courts register | `data-layer/courts_register`, `ingestion/courts` | Fed by nothing; about 67 documents quarantined; suppress lever points at the old graph | Take in step 5 |
| Disqualified directors | `ingestion/companies_office` | The derive writes three tables that have no definition anywhere | Rebuild the tables, take the derive |
| Regulator actions | `ingestion/comcom`, `ingestion/fma`, `ingestion/worksafe` | 128 records parsed and read by nothing; the Act section is empty on all | Build the read |
| Amended filings | `registers/supersede.py` | "Prefer the amendment" is wrong in at least one case; unmatched pairs are reported | Take as is |
| Table definitions | `schema/nzbn_canonical.sql` and code | Tables were created piecemeal with no replayable chain; seven writers sat outside the package | New estate: every table defined in one place |

### Reading documents

| Piece | Where | Faults on record | Verdict |
| --- | --- | --- | --- |
| Page reader | The `querynz-vision-ocr` job; GLM-OCR | The only one, with nothing behind it. Killed for memory once; capped at 6 GB. It had never actually run until 24 September because of a code bug | Take. Step 3 gives it a second |
| Document reader and checks | `data-layer/docread` | One reader, so no automatic second opinion. 264 of 844 stored readings failed their own stated total. Tables of 6 to 20 rows passed 48% of the time. Table size predicts failure; text or scan does not | Take the checks and the answer-set method |
| One reader contract | None | 11 text-extraction calls in 4 shapes across 9 files | Build in step 1 |
| Profiles and corrections | `data-layer/docreview`, `profiles.jsonl` | A profile is pinned to the code both ways for one form only. 379 of 381 corrections are machine-agreed. 16 corrections reach no page | Take. The reader runs from the profile |
| Model client | `data-layer/modelgate/modelgate/client.py` | For most jobs it recorded a wrong model and carried on | Take, with refusal on for every lane |
| Geometric table reader | `data-layer/docread/retired/geometry.py` | Retired 25 September; needs a reader that returns word positions | A possible second opinion on tables |
| Row-pairing check | `ops/party_return_rows_pairing.py` | Experimental | Refuses a table whose columns have drifted; worth wiring into scoring |

### Links and products

| Piece | Where | Faults on record | Verdict |
| --- | --- | --- | --- |
| Donor matcher | `registers/donor_anchors.py` | Hand-set weights. One rule accepted by a rounding margin. A withdrawn match once supported new ones | Take the ledger and the two rules, not the weights |
| Director folds and the watch | `registers/roster_folds.py`, `folds.py` | Built for donor and MP names only; the whole 1.19 million director rows were never done. 857 of 5,314 folds were contested at first run | Rebuild over the whole register |
| Ordered resolver | `registers/person_identity.py` | None documented | Take as is |
| Verdicts and review threads | `registers/review_verdicts.py`, `review_comments.py` | The only verdict is "hold", tied to a weights version. The comment route once took the author's name from the caller | Take as decisions; re-key to rule and evidence |
| Old answer set | `data-layer/candidate_register/truthset` | 207 hand labels of names in press text, not register rows | Take the method only |
| Company views | In `registers` | An ended role is dated to the day the file was imported | Rebuild with real dates |
| Ownership notes | `registers/vehicles.py`, `exposure.py` | Exposure has had no reader since 30 September | Take the rule: ownership is a note, never summed |
| Land title owners | `registers/linz_title_owners.py` | Individuals held with no matching; takedown service parked | Step 5, takedown first |
| Sealed address store | `registers/sealed.py` | Built and not yet fired | Arthur fires it before 18 November |
| Follow the Money app | `data-layer/pi` | Imports the inside of `registers`; the donor list cut before folding | The pattern for a product; rebuild on the shape |
| Release pipeline | `ops/pi_release.py`, `pi_snapshot.py`, `pi_cloudflare.py` | Every gate reads our own output | Move without its deploy step and without its ties to the frozen publisher (step 4.4); add one outside check |
| Flags and rule sets | `data-layer/flags` | Seven person rules and four company rules exist; there is no hostile test set | Take the idea |
| Watchlists and feed | In `query` | Acceptance check never built | Take with care |
| Search service | `data-layer/corpus_search`; `data-layer/query/query/semantic.py`; `ops/embed_articles.py`, `ops/build_embed_index.py` | Keyword index reads 1,500 characters. The meaning index is built whole in memory: 33 to 38 GB for 6.4 million articles on a 62 GB box | Take the tools; rebuild both indexes |
| Research agent, gap miner | `data-layer/research` | Its web fetch is the strongest injection channel in the estate and is not on the fetch gate | Internal use only |

### Machinery

| Piece | Where | Faults on record | Verdict |
| --- | --- | --- | --- |
| Scheduler parts | `ops/fleet/`, `config/job_types.yaml` | Nothing runs it on a clock; queue depth unmeasured | Extend in step 2 |
| Work queue with leases | `ops/extract_queue.py` | Specific to press extraction | Take the pattern |
| Re-read orchestrator | `ops/era_cutover.py` | Jobs it pauses do not restart themselves | Take the pattern for the re-read job type |
| Old checks board | `tests/test_invariants.py`, run daily by the `v3-audit` job | 11 of 73 red on 10 October. None of fifty checks asserted the value of an answer a user sees. It was once dead for days while every row read nominal. Its only watcher is the sweep job | Rebuild in `checks/`; the new board alarms if it has not run |
| Old card board | `ops/board.py` | None documented | Replaced by the generated board |
| Job manifest | `ops/systemd/MANIFEST.json`, checked by `ops/units_manifest.py` | Jobs were once installed nowhere, or on one box only | Generated in the new estate |
| Hooks | `.claude/hooks/denylist.py`, `session_scope.py`, switched on in `.claude/settings.json` | The scope hook reads an old path for its scope and allows everything without it | Port, do not copy (step 1.1) |
| Lessons tools | `ops/lessons_for.py`, `ops/lessons_index.py` | Retrieval recall measured at 5 of 8. The search prints whole sections, up to 160 KB at a time | Take the one-line index. Write a new search over it and the new lesson files (step 1b) |
| Database, standby, floating address | Runbook in `docs/runbooks/` | Takeover by hand; one drill | Track A |
| Off-site backup | The `offsite-push` job | 368 GB nightly; restore rehearsed to 90% | Track B |
| Citation resolver | In `data-layer/pi` | Donation citations pointed at row numbers that changed nightly | Take, on stable keys |
| Rate limit | In `data-layer/query` | A courtesy bar, not a control | Not enough for strangers |

### Old databases

| Database | Size in August | Holds |
| --- | --- | --- |
| `nzbn_canonical` | 21 GB | The registers. `public.entities`, `director_roles`, `shareholder_roles` and their history tables; `bulk.*` (insolvency, award notices, other entity types, retirement villages); `charities.*`; `gazette.*`; `mp_interests.*`; `parties.register` |
| `incoming_news` | 25 GB | The news corpus, Papers Past articles included, and the old article vectors |
| `extractions` | 211 GB | The press graph. Parked |

### The boxes, as last recorded

Measure all of this in the baseline; it is here so you know what to expect.

|  | node1 | node2 |
| --- | --- | --- |
| Processor | 16 cores, 32 threads | The same |
| Memory | 62 GB | 62 GB, with the spare 64 GB to be added |
| Graphics cards | Two Radeon R9700, 34 GB each | Two Radeon R9700, 34 GB each |
| Disks | Two hard disks of 3.6 TB (`/mnt/hdd1`, `/mnt/hdd2`), a fast disk at `/mnt/ssd`, the system disk | One 2 TB fast disk, two 4 TB hard disks (one at `/mnt/hdd`, one to be mounted), the system disk |
| Normal role | Primary database, the floating address, database-side jobs | Build sessions, capture jobs, the old apps, the standby database |

- **Network:** a 10-gigabit link joins the boxes. Each reaches the internet over Wi-Fi, behind a satellite connection that allows outbound traffic only.
- **System:** Fedora 44. Every job is a user-level scheduled job, installed by copy, with a manifest saying which box runs it. 75 jobs were on record.
- **Graphics cards are AMD, not Nvidia.** The model server that works on them is llama.cpp's. Software that assumes Nvidia cards will not run as documented.
- **The old serving app held a 27 GB index in memory on node2,** which is why node2 was recorded as tight. That app is outside the carve-out, so the memory is freed if step 1.4 stops it.

### Parts that stay dead

- Anything in the older scraper service that solves challenges or scrapes the legal-information site that requires an agreement.
- Tesseract as a reader. It invents plausible names instead of failing ("Chaistopher Yaakin", $820,500), the one error a reader cannot detect in itself.
- The press-graph merge judge, which contradicted itself on 10,813 names.
- The old capture rules as policy. Cards written under them keep their facts and lose their policy.

### Parked and retired work to draw on

Arthur's ruling 6: parked and retired work is a resource. None of it runs today.

| Item | Where | For |
| --- | --- | --- |
| Groups above the legal entity (enterprises) | `data-layer/claim_graph/claim_graph/enterprises.py` | 5, 13 |
| Exposure carried up an ownership chain | `data-layer/query/query/exposure_rollup.py` | 13 |
| Flows, report builder, printable memo, rule sets | `data-layer/flags`; `gui/src/useCases.ts`; the August flows on the older graph | 2, 3, 4, 8 |
| Ownership-chain page and endpoints | In `data-layer/query` | 13 |
| A bench for trying a new source without landing it | `ingestion/explore` | Every new lane |
| Retired capture scripts: award recovery, interests editions since 2006, candidates 1999 to 2023, charity financials | `ops/retired/` | 1, 9, 10, 11 |
| Archive survey and back-catalogue walker | `ops/archive_survey.py`, `ops/coverage_backwalk.py` | Depth for any source |
| Research agent, web-only baseline, gap miner, benchmark sweep | `data-layer/research` | A scorecard per use case; internal use only |
| A second reader used in one audit | `ops/donor_pairing_audit.py` | The two-readers idea in step 3 |
| A holdings module, earlier resolvers for positions and events, an earlier audit and accuracy scorer, a one-graph register page, judgment inspector pages | The older repositories on the same GitHub account | Ideas only; some have deliberately broken imports |
| Eight drafted letters, all unsent | Arthur's run sheet, `data-layer/docs/ARTHUR_RUNSHEET.md` | Courts, the stock exchange, press, company terms |

## Reference: registers and use cases

Counts are the old catalogue's, mostly from August and September. Measure them in the baseline before quoting them.

### Held: registers that are copied

| Register | What is held | Note |
| --- | --- | --- |
| Companies | About 1.19 million director rows, 1.58 million shareholder rows, 759,477 registered offices, 330,000 trading names | Monthly file, downloaded by hand. About 65,000 groups of companies share an address |
| Other entity types | 59,981 societies (26,901 registered, 130,475 officer rows), 4,114 limited partnerships with no officers by structure, trust boards, 2,922 public sector bodies, retirement villages | Government departments are in the public-sector file, not the companies register |
| Charities | About 260,000 officer roles; 421,633 annual returns | The person key is empty on 58,591 officer rows |
| Tender awards | 29,874 notices from 2014, with supplier, category and region tables | Never read |
| Register of Political Parties | The current roll | 78 of 86 annual returns owed by today's 14 parties for 2019 to 2025 are held |
| LINZ | Title owners; 54,667 official place names | Individuals' title rows are held back under the licence |
| MPs' declared interests | 21 editions | Categories renumbered in 2018 |
| Reference lists | World place names, Wikidata, overseas organisations, Māori business identifiers, Australian business numbers | Used only to prevent false matches. One download is 103 GB over the satellite link |

### Held: registers that are built

| Register | Built from | Note |
| --- | --- | --- |
| Insolvency appointments, about 60,000 bankruptcies, director prohibitions, about 9,500 public appointments, party events, celebrants | The Gazette, 208,304 notices | Appointments begin in 1999. Notices are walked through a date-ordered index, so a paging checkpoint is valid only for a closed year |
| Donations, returns, expenses, party finances, promoters, party rules | Electoral Commission filings | See the forms notes in the next section |
| Candidates; who sits in the House | Commission files; Gazette vacancies | 2,078 electorate candidates held for 2017 to 2023 |
| Who spoke in Parliament | Hansard | 32,875 speeches by 125 members. Held at 23 September |
| MPs' and ministers' expenses | Quarterly workbooks | Public money, not the politician's |
| Regulator actions | WorkSafe, Commerce Commission (112 cases), FMA (16 warnings) | Parsed, unread |
| Court judgments | 145 documents in scope | Register built, fed by nothing |

### Not held

| Source | Serves use cases | Route as last recorded |
| --- | --- | --- |
| Securities register, Insolvency Register, financial service providers | 3, 4, 5, 7, 13 | Interfaces awaiting outside approval since 19 September |
| Parsed case law (OpenLaw) | 2, 3, 6, 7, 8, 12 | Key in hand; lane unbuilt |
| Tribunals, employment and environment courts, coroners | 6, 7, 11, 12 | Capture test, then a lane. Permission letter unsent |
| Sole traders, partnerships, trusts | 4, 5, 13 | One at a time through the business-number interface. There is no public trust register |
| Company filings: liquidators' reports, financial statements | 3, 5, 7 | A filings table exists; whether it is filled is unconfirmed |
| Sanctions lists; limited partnership partners | 13 | Free, public |
| Overseas ownership data | 13 | Free bulk; deferred by an old ruling |
| Licensed building practitioners | 6, 7, 12 | Public register |
| Health and Disability Commissioner decisions | 11 | Public |
| Live tenders, agency contract disclosures, council procurement | 9, 10 | Public |
| Grants: gaming-machine, Lottery, regional development, tertiary | 10, 1 | Published files |
| Local election returns, councillors' interests, council pay | 1 (councils), 15 | Council by council |
| Iwi and hapū directory, settlement commitments, Māori Land Court | 14 | Two public; the court needs registration |
| Stock exchange announcements | 5, 13 | Terms need written permission; letter drafted |
| Building consents; primary-industry prosecutions | 12, 4 | No bulk route known |
| Never available |  | Payment defaults (private bureau data); criminal history; identity documents |

Also not held, lower priority: alcohol licences (a national spreadsheet each quarter); paid securities lookups, one at a time; the emissions trading and petroleum permit registers; the offshore-leaks database; Australian registers; shareholdings of removed companies, which the bulk file drops; occupational registers; foreign politically exposed people, whose main open list is licensed for non-commercial use only. Reopened by the capture test and awaiting a lane: the Environmental Protection Authority and the health practitioners' tribunal.

### The sixteen use cases

| # | Use case | Who uses it | The question | Shape | Step |
| --- | --- | --- | --- | --- | --- |
| 1 | Follow the Money | Reporters, the public | Who funds parties and candidates, and what followed | Published site | 4 |
| 2 | Legal counterparty and conflict check | A law firm partner before taking a client | Who is behind this company, and does acting for them conflict with anyone we act for | Subject report | 5 |
| 3 | Banking: director history | A credit analyst | Every company the controlling mind has touched, and how each ended | Subject report | 5 |
| 4 | Agriculture counterparty risk | An agribusiness credit manager | What the record says about the people behind a rural trading company | Subject report | 5 |
| 5 | Business credit and monitoring | Trade credit teams | Has anything changed for the companies I am exposed to | Subject report, re-run on change | 5 |
| 6 | Insurance underwriting | A commercial underwriter | The real safety and solvency record behind a proposal | Subject report | 5 |
| 7 | Construction: subcontractor vetting and phoenix detection | A head contractor's procurement lead | Is this the failed firm again under a new name | Subject report | 5 |
| 8 | Recruitment: board pre-appointment screen | An executive search consultant | Is there anything in the public record we should know | Subject report | 5 |
| 9 | Government procurement integrity | An agency procurement lead | Are shortlisted suppliers linked to our staff, to each other, or to donors | Register scan | 6 |
| 10 | Tender and award intelligence | Bidders | Who wins what, from whom, and who is behind them | Register scan | 6 |
| 11 | Healthcare operator governance | An aged-care investor or regulator analyst | Who runs the homes, and how has it gone | Subject report | 5 |
| 12 | Property developer due diligence | An investor or apartment buyer | Who is really building this, and what happened to their last projects | Subject report | 5 |
| 13 | Beneficial ownership and AML checks | Compliance teams | Who ultimately owns or controls this, and are they exposed or sanctioned | Subject report | 5 |
| 14 | Post-settlement governance map | Iwi organisations, Crown agencies, reporters | The whole entity web of one post-settlement body, with its office holders | Register scan | 6 |
| 15 | Lobbying | Reporters, integrity bodies | Movement between public office and industry; who ministers met, what those people represent, and the legislation and press beside each meeting | Register scan | 6 |
| 17 | Discourse | Reporters, researchers, campaigners | One public subject ("Three Waters") over time: what was said, who said it, and who it was aimed at — speaker, stance and target read from journalism and resolved against the spine | Archive search | after 4 |
| 16 | History search | Historians, family and iwi researchers, reporters | Everything Papers Past holds on a person, place, event or phrase, despite misread print and old spellings | Archive search | 7 |

Riding on these with no new machinery: vetting bidders and conflict checks (2 and 9), grant-maker checks (10), Follow the Money for councils (1), contractor vetting (7), and a domestic list of politically exposed persons (13).

What parking the press work removes, and each product says "not held" for: family links between suppliers and staff, press-reported appointments for lobbying, press ownership claims, and meaning-based search over current journalism.

## Reference: facts and traps the old cards paid for

Each line cost the old estate real time. They are requirements whatever the new code looks like. Figures are as the cards last stated them.

### Electoral Commission forms

- **Donation bands are set by law and changed with the 2023 returns.** Up to $1,500 may be anonymous. $1,500 to $5,000 is reported only as an aggregate ($1,500 to $15,000 before 2023). $5,000 and over is itemised by name ($15,000 before 2023). Over $20,000 is disclosed within 10 working days ($30,000 before 2023).
- **The un-itemised band is one total per return and is the biggest block** (National 2023: $6.00M of $10.38M).
- **Only Part A names donors.** Part G is the aggregate under the threshold and Part F is protected by law, so money there has no donor to find.
- **Part G is three aggregate categories, not a table of rows.** A part's total read as a donation double-counts money; drop it.
- **The form changed its part letters three times:** (A+C+D+F+G), (A+C+D+E), and 2019's (A+B+C+D+E).
- **The declaration page is not always page 1 and not always text.** One total was on page 9. Totals appear as bare integers, "$2370", "0" or "Nil". Summing the parts recovers a missing total.
- **Missing totals were parser faults, not page-reading faults.** Arthur was right about this before the cards were.
- **The donor's name and street address sit in separate columns under one heading.**
- **A return can have inserted continuation sheets** ("page 6.1"). One held the nine largest donations, $546,222.92.
- **The form prints an example address,** which was once read as the fourth-largest donor.
- **The blank form prints "NIL" and "$0.00",** which a reader quoted as the answer on 27 returns that declared $279,002.25.
- **Every return prints its own total,** so every reading can be scored against it.
- **A row-band table model emitted one donation two or three times** (one Part A read 3.37 times its printed total).
- **Extract text with layout kept.** Without it tables break apart, label on one line and number elsewhere.
- **Candidate totals come from the Commission's own spreadsheet** with no link to the return files. Joining on year, electorate and surname matched 373 of 391.
- **The Commission republishes amended candidate returns under a different file-name pattern.** A file-name search missed 10 returns worth $445,786.58.
- **The Commission states, by date, which declaration an amendment replaces.** Nine are amended; one reads "amendment withdrawn", so its original stands.
- **A large-donation disclosure exists only because one donation passed $20,000.** A row below that floor is a damaged reading. The Commission links an image, not a PDF, for 11 of 271.
- **The Commission's table of large declarations leads with the date it received the declaration,** weeks after the party received the money. Show both dates.
- **The Commission can be wrong.** Its 2020 table gives Part A alone as the total for two parties. The headline rule still stands: its figure, linked to its page, with ours beside it.
- **Parties have filed annual financial statements since the 2023 financial year.** Some also file on the Incorporated Societies Register; National and ACT do not.
- **Third-party promoters are a separate class.** Referendum advertising is held beside election advertising and never added to it.
- **List-seat outcomes are in the Commission's own list rows.**

### Capture

- **A challenge page must be detected whatever the vendor,** and recorded as a failed read. Never as thin content, an empty answer, or a reason to retry quickly. Retry a challenged government host daily at most.
- **The Commission's large-donation listing, its candidate pages and the results site sit behind challenges.** A real headed browser that is not challenged may read them; one that is challenged has failed. Archive copies of the same pages were 212-byte shells.
- **A browser job must start after the graphical session,** or it fails every time.
- **Party websites:** the http, https and www spellings are one page, and every response carries fresh tokens, so raw byte hashes never match. For web pages, hash the content after removing what changes on every fetch.
- **Dates must be read from the page markup at landing.** The stripped text often does not carry one. A grant record's "Year: 2020" is a funding year, not a publication date.
- **Gazette notices are walked through a date-ordered index.** A paging checkpoint is valid only while the year's count is unchanged.
- **The Reserve Bank's site returns an empty shell even to a browser.** Its old status said "ready" while landing nothing.
- **Two paywalled outlets are stopped and never forged.**
- **One catalogue site's terms forbid bulk reading without permission.** Read terms, not only the robots file.
- **The electoral roll is off-limits.**
- **Large downloads over the satellite link need a bounded retry.** One reference file is 103 GB.

### Names and matching

- **A nickname map of 371 filer-stated pairs is sound, and merging on it finds nothing:** 1.27 times a shuffled map. Never merge people on a name alone.
- **Address alone once grouped 25 ministers at Parliament.** One address holds 1,060 companies.
- **The Commission's form prints the donor's address on 98% of rows.** Likely aliases are proposed where filed names share a street address and a distinctive word; nothing folds automatically.
- **No fold across a period where an address was substituted.** Director address suppression begins on 18 November 2026.
- **A bare acronym can be a registered trading name** (NZTA is a trading name of NZ Talent Alliance Limited). "All capitals and short" is not a safe test.
- **Government departments are not in the companies register.** Its 98 department-shaped names are companies.
- **A consolidated court appeal names several parties in one line.** One row per party and role.
- **Of 151 name-matched MP directorships, 15 had a supporting link.** One MP's count fell from 24 to 2.

### Databases and jobs

- **Every job's database address names the floating primary, never a box.** Old register code silently defaulted to the local machine, which on node2 is the read-only standby.
- **A wipe and reload inside one transaction never shows a reader zero rows.** With each statement committed separately, it does.
- **Database connections run out.** An old fleet took 97 of 100. Reserve some for serving and refuse to start beyond the rest.
- **Exit codes mean something:** 0 clean, 3 wrote with counted problems, 1 nothing written. A job once reported success daily because its script ended on a print statement.
- **A job's deadline must be longer than its work and shorter than its interval.** One job was killed 55 times in a week.
- **A deliberate stop must not raise the failure alarm,** and a dependent job waits for its server's health check.
- **The model server hangs for about 45 seconds after a stop signal.** Stop it with a 20-second limit and then a hard kill.
- **A memory limit above what the box has free is not a control,** and a killed run under-reports its peak.
- **Swap fullness says nothing about memory health.** Read the kernel's memory-pressure figures.
- **Before moving a folder, check the repository, the job files and the settings for anything that names it.** One move caused an unclean reboot and a missed backup.
- **Job changes are installed on both boxes and parity is checked.** node1 once ran pre-incident settings six days after the fix was written.
- **The standby once started at boot without streaming and piled up 2.7 TiB of change log.** Change-log volume fell from 244 GB a day to about 3.4 GB after tuning; read it as a daily series, not an average.
- **A refused privilege request was once read as "folder absent",** so a clean-up reported success for weeks while doing nothing.
- **An options string inside a connection string silently discards the environment's settings,** time limits included.
- **One transient error failed a whole 25 GB upload.** Retry each part with a pause.

### Measuring

- **Two numbers agreeing is not a catch** if the instrument could have got that number from what it already held.
- **A count in a description is a claim like any other.** Measure it.
- **A sample of neighbouring rows lies.** One said 96.6% where the truth was 51.1%.
- **A check that tests a key against itself always passes.**
- **A figure a person read off a page needs a home in the repository.**
- **An author's name supplied by the caller is not evidence of authorship.** The server stamps who wrote a record.

## Reference: dated jobs, open decisions, rulings

### Dated jobs

These sit outside the build and do not move for it.

| Date | Job | Whose | Note |
| --- | --- | --- | --- |
| 1 November 2026 | Backstop for the privacy-law advice | Arthur | Deferred with the legal work, but the date is on record |
| 4 November 2026 | The old checks board goes red if the director addresses are not sealed | Arthur seals; the build watches | Fourteen days before the law changes. Confirm in the baseline that a red old board does not stop the daily release; the record says it only reports |
| 7 November 2026 | General election |  | The frozen site's busiest period. Nothing that feeds it is switched before this |
| 18 November 2026 | Director address suppression begins. Seal the copy of addresses as published before it | Arthur fires it | The address-matching rule depends on that sealed copy. From 1 November every end-of-session note says whether it is done |
| No date | Rotate the deploy token for the daily release | Arthur | It has been exposed twice. It is the first item of track H |
| Now | Capture Tenancy Tribunal and Real Estate Authority decisions | Build, track E | Three-year window |

### Decisions waiting on Arthur

Copy these into `docs/decisions/queue.md` in step 1. Every one but the last five has a default, so none stops the build.

| Decision | Default, used until he rules | Blocks |
| --- | --- | --- |
| Accept or change the operating rules in this plan | They apply as drafted | Nothing |
| The reading limits and time targets of ruling 54 | As drafted, then re-set from the first week of session timings | Nothing |
| The wording of hard limit 11: what a session, itself a cloud model, may read | As written: samples yes, bulk no, never home addresses or suppressed names | Nothing |
| How far a chain of links is trusted | Chains of confirmed links are followed; a flagged group is contested whole | Nothing |
| How much doubt a step through a person adds | More than one person in the path makes the connection near | Nothing |
| Whether one graphics card is kept free for live questions | No card is kept empty | Nothing |
| Whether each database write waits for the standby | It does not | Nothing |
| What counts as an emergency fix to the frozen site | The release is broken, or a published figure is wrong | Nothing |
| No switch of the public site before 7 November | Keep | Nothing |
| The review agent's pass mark | It wrongly splits fewer than 1 in 100 pairs known to be one person | Nothing |
| Whether any confirming rule beyond the two is tried | A candidate rule may be measured on the test pairs; none is applied without a ruling | Nothing |
| When the database passwords are rotated (track H, wave two) | The first quiet day after the election, with Arthur present. Wave one does not wait | Wave two only |
| What to do with NZME copies already held | Keep, quarantined, unread | Nothing |
| Whether the parked press graph moves off the primary database | Leave it where it is | Disk and memory only |
| Whether the award join or a councils tier appears on the public site | Not shown | Nothing |
| Whether "another environment" for an exported product means a second host of ours or a handover to another party | A second host of ours | Nothing until an export leaves |
| How an alarm reaches Arthur, if the baseline finds no channel | A line at the top of `docs/status.md` and in the end-of-session note | Nothing |
| **When the rebuilt Follow the Money replaces the frozen one** | **No default. Arthur's decision** | Step 4.8 only |
| **A named use for the 200 Waitangi Tribunal reports** | **No default. They stay held and unread** | Depth of template 14 |
| **The acceptable error rate for links** | **No default. Ruled with the measurements** | Selling only |
| **The drafted, unsent permission letters:** Ministry of Justice, the Office of the Clerk (Hansard), the stock exchange, the Companies Office (filed statements), and four others on the run sheet | **No default. Sending is Arthur's** | The sources behind each |
| The key for electorate boundary shapes; an uninterruptible power supply; a network cable in place of Wi-Fi; a one-sitting change of every password and key, which the record calls stop-the-world | Arthur's to do | The electorate map; reliability |

### Rulings in force from the October discussion

Given by Arthur between 10 and 12 October 2026. Copy them into `docs/decisions/rulings.md` and number on from 55.

**Three points that govern everything**

- Follow the Money does not stop, and the build goes toward it first.
- Rebuild the shape, move the scar tissue, and make the cards account for every difference.
- Every use case can be exported whole, without heavy duplication of code or state. Since ruling 47 an export is a shape, a template and the tables it reads.

**10 October**

1. This is a capability build-out. Plan as if customers exist. Billing, accounts and metering are out.
2. Legal work comes after the build and before any service is sold.
3. The partner model is an enhancement, not the frame.
4. Order and parallel work are free. New operating rules replace the old method.
5. The ten August use cases join the plan.
6. Parked and retired work is a resource to draw on.
7. Press is demoted entirely for now.
8. Keyword search is back for journalism other than Papers Past.
9. History search is a use case, with every search tool.
10. The capture rules are abandoned. Collection is judged on legality and politeness.
11. Superseded by 12.
12. NZME is dropped, every masthead.
13. The Papers Past archive is on the boxes. Each ingest catch is identified exactly where it happens.

**11 October**

14. Work is parallelised as far as it can be. The lessons flow and the card board are kept. The backlog is not allowed to pile up, but not at the cost of the work.
15. Follow the Money is the first thing recreated in the new estate. After it the order is the planner's, as set out in this plan.
16. Each product is tested when built. Gaps and failures are carded, not necessarily fixed.
17. The live Follow the Money is frozen and kept as a working, exported product.
18. The held legal sources are in. Research legal document extraction and try newer page readers. Easiest first.
19. Company monitoring goes as deep as the official interface allows: poll on lookup and update from the differences. The monthly import stays.
20. The Papers Past meaning index lives on the hard disks for now.
21. The off-site copy stores changes, with a weekly checkpoint.
22. Four graphics cards, switched between jobs by the scheduler.
23. Papers Past is read whole.
24. The build method for the full meaning index is agreed.
25. A new repository. The old one stays as it is, running the frozen product.
26. The old two-closures rule is dropped. Three kinds of card replace it.
27. One short spec per module, checked at the merge.
28. Stopping the press-graph jobs is a plan step.
29. The three-way delete rule is agreed. The safety hook stays.
30. Build sessions run on node2, each in its own working copy: three plus the integrator to start.
31. The two boxes are peers and one service schedules every job. A third machine makes database takeover automatic. Each box has a hardware profile. The spare memory goes in node2; the primary database role normally stays on node1.
32. The frozen Follow the Money keeps its daily data refresh.
33. The old cards are not carried over. All are read for context, with care.
34. The standing product rules were gone over one by one (see 39 to 43).
35. Arthur starts each build session on node2. The plan gives a short brief for each.
36. The new estate's data lives beside the old at first. The old is deleted once properly consumed.
37. Lanes re-read from documents already captured. Judgments and corrections are copied untouched.
38. The new repository is named QueryNZV4.
39. The Follow the Money money and scope rules belong to that product only.
40. The two confirming rules stay exact for Follow the Money. The wider estate starts with them; they are revisited only after measurement, by Arthur.
41. Arthur is not in the review loop. A suspicious link is reviewed by an agent and split if not trusted. Reports list near connections.
42. A company's registered address is shown. A person's home address is never shown or extractable, and is still used for matching.
43. Papers Past gets a broad name index as a search aid: people, towns, roads, organisations. It never feeds the links.
44. A graphics card runs one model on one kind of job at a time. The scheduler may swap it and records every swap.
45. Re-reads no longer wait for Arthur. The scheduler runs them.
46. The rule-learning process is kept, and the old extraction lessons and rules are captured.
47. The design is simplified: five parts, no stored person, four product shapes.
48. The support design is kept in full, because the work may grow.
49. The four page readers are trialled. Chandra OCR 2 is in.
50. The trial runs first, over the election documents, as the scheduler's live trial, under three conditions: profiles first, readings tied to bytes, text or scan decided per page.

**12 October**

51. Passwords and API keys are rotated as part of this plan, and the long-running security cards are brought into it (track H). This replaces old ruling 270, which deferred every rotation.

52) An interface that shows the connections between registers: one search across all of them, with the results and each followed link shown in panes side by side, like the Miller boards of the earlier estates. It is a fifth product shape, the board (step 4.9).

53. The build starts next week. Follow the Money keeps running as an exported product, and the only feed it still needs is the declared-donations feed, which is carved out to run alongside (step 1.4).

54) The new estate is kept quick to work on: three weights of session, a budget on required reading, nothing that grows read whole, two tiers of checks on a sample database, registers that rebuild in parts, data questions answered from the published tables, and the wait measured ("Keeping the work quick").

**Old rulings this plan still relies on,** by their number in `docs/records/DECISIONS.md`: 172 (no text to a cloud model), 203 (Papers Past is a search corpus), 217 (busy address), 220 (the watch on links; its "on Arthur's word" is replaced by ruling 41), 221 (the two confirming rules), 253 (ownership is a note), 193, 277 and 357 (the return is the record), 321 (fyi.org.nz), 333 and 347 (2019 onward), 349 (a renamed party), 351 and 356 (seven parties), 355 (no press row), 361 (a race is every year since the election before it, cut at the window; it replaced 358 on 16 October), 360 (for telling a person's name from an organisation's, the director register is the authority for given names).

### What this changes in the old terminal document

`docs/doctrine/TERMINAL_ARCHITECTURE.md` (20 August) already describes this design: registers as the spine, and people as a view rebuilt from decisions. Five of its statements are changed by the rulings above. Amending the document itself is Arthur's.

| It says | Now |
| --- | --- |
| Capture is robots-absolutist and ask-first | Legal and polite |
| Arthur is the deliberate bottleneck on judgments | An agent reviews and splits |
| No era is fired by anything but Arthur | The scheduler runs re-reads |
| Products are built for partner entrepreneurs | The use cases drive the build |
| Mentions and claims from journalism are a layer of the store | Parked with the press work |

### Notes from Arthur, 16 October 2026

Given in the old repository's last session, for the founding session. His words, then where each lands.

1. *"the core architectural change we are making is we are creating a rich spine made of multiple joined registers."* — Stated at the top of "What we are building". It is the design's one sentence; a session that has read nothing else should have read that.
2. *"once we have the multiple joined registers we can use them for name resolution for press."* — Recorded under "Deliberately not built": press stays parked, and when it returns its names resolve against the spine, not against a register of names of its own.
3. *"instead of the deterministic extraction using a large register of names, I would like to experiment with ModernBERT-base for name resolution. I am also interested in other things it can do."* — Track D.2, the name-resolution experiment, with the joined registers as its answer key, scored against the deterministic path; ModernBERT-base was first noted on 13 October (the KDnuggets article) as an option for the Papers Past name index, and that row in 7.5 now points at D.2 for the measurement.

### Notes from Arthur, 17 October 2026

Given in the old repository's last session, after the four closes of that day.

4. *"1. read all the MPs diaries and schedules 2. identify who they are meeting and the organisational/industry connections the people represent 3. Connect that to legislation and also media mentions 4. explore media subjects and who they are targeted at. For example, three waters — what was the discourse, who was targeted by the discourse, who was doing the targeting."* Clarified: the diaries are **ministers'** (only ministers publish them; monthly proactive-release PDFs, collectable under old ruling 242), and the fourth is **its own product**. Where each lands: 1 to 3 are use case 15 Lobbying, products (a) to (c) in the step 6 order table — the diary register first, in the registers milestone, since it depends on nothing; the meetings' affiliations and the legislation join after links, because they resolve names against the spine. 4 is use case 17 Discourse, on the archive-search shape: the press graph's return, scoped to one subject at a time, reading speaker, stance and target from journalism and resolving them against the spine — so it also waits for step 4. Keyness over time (what was said, when) exists in the old estate today and is the retrieval half; the assertion half is new. Hansard is held to 23 September behind a challenge and the Office of the Clerk letter is unsent — Arthur's, and it gates product (c).

5. *"we need to be able to automatically survive a failover so please record everything we have learned from this."* (17 October, 22:50, after the failover.) — Old ruling 365. Recorded as the five build rules at the end of track A, the hardware baseline notes beside them, and the lessons block in the old repository; track A starts from the real state (node2 primary).

### The later list

Not in this build: mayoral diaries, chief executives' gifts and expenses, and the press graph at large (it returns one subject at a time as use case 17). Ministers' diaries are in: use case 15, product (a).
