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
| `querynz-pi-web`, the product's own instance on port 8300 | The release's search gate (`ops/pi_search_gate.py`) compares the snapshot's browser search with what this instance finds; without it the release ran red (18 October, found by a release run by hand after batch 2). The same program as the publisher, bound to the box's network |
| The database, its standby and floating address; `offsite-push`; the change-log archive jobs; `querynz-deploy-node1`; `querynz-residue-mirror` | What the above stand on, and the copies of them |

**Still collecting, for the new estate.** These only capture. They do not touch the site. Each keeps running until the new lane for its source takes over capture, because a gap in collecting cannot always be filled later.

`newsscrapers` and `newsscrapers-daily` (with NZME taken out), `gazette-capture`, `hansard-forward`, `legislation-backfill`, `comcom-capture`, `fma-capture`, `enforcement-capture`, `companies-office-capture`, `courts-capture`, `tribunals-capture`, `querynz-charities`, `society-officers`, `parties-capture`, `party-sites-recapture`, `linz-titles-pull`, `mp-expenses`, `minister-expenses-capture`, `motu-repec-capture`, `pdfpipe`, `docpipe-daily`, `querynz-coverage`.

**Candidates to stop, each with the proof above.**

| Group | Jobs |
| --- | --- |
| The press graph | `v3-extract`, `querynz-extract-fleet`, `querynz-crawler`, `querynz-mint-lane`, `querynz-research`, `querynz-sweep`, the `querynz-llm@` instances, `nzme-archive-backfill` |
| The news meaning index | `querynz-embed-backfill`, `querynz-embed-burst`, `querynz-embed-index`, `querynz-embed-index-ship`, `querynz-embed` |
| Rebuilds and feeds the declarations do not pass through | The nightly chain on node1 (`gazette-derive`, `registers-derive`, `gazette-feed`), `feed-parties`, `mp-tenure-derive`, `hansard-register`, `hansard-reprocess`, `companies-office-derive` |
| Old apps and their helpers | `querynz-api`, `querynz-serving-precompute`, `querynz-feed-filters`, `querynz-paper-images`, `querynz-ec-results`, `robots-audit`, the reference downloads |
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

- [x] An edit outside a session's scope is refused, and a branch with a failing test is refused by the merge gate. DONE 18 October (1.1 merged, 5c1e5f2).
- [x] `docs/baseline.md` exists and its differences from this plan are listed. DONE 18 October (node2 only; node1 is out of the plan by ruling 55).
- [ ] The carve-out is named and watched, every other old job is either still collecting or stopped with proof, a new declaration has reached the public site with only the carve-out running, and the daily release has run green since.
- [ ] The old repository is tagged, with NZME out of its news capture.
- [x] The watcher for the frozen product is running and has raised a test alarm that reached Arthur. DONE 18 October: `qv4-checks-board` 07:30 and `qv4-checks-heartbeat` 09:00/21:00 on node2; the test alarm sent again at 14:1x on 18 October reached Arthur, confirmed in session.
- [x] Every contract has a document and a passing test, and the shared machinery in `support/` passes its carried tests. DONE 18 October (eleven contracts in docs/contracts/; fetch gate, landing, reader and model client in support/ with 599 tests green).
- [x] The thin slice matches the frozen site's totals for the same returns, or each difference has a card. DONE 18 October (22 of 22 sample returns equal; on the full load 23 party-years equal and the one difference, Labour 2020 original against amendment, is carded).
- [x] The reference material is in place and the lessons index builds. DONE 18 October (corrections kept outside git until they have a private home).

* [x] The plan is split, its pieces rejoin to the original, and every file is within its limit. DONE 18 October.
* [x] Step 1b is closed. DONE 18 October (its last item closed with 1.11).

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

