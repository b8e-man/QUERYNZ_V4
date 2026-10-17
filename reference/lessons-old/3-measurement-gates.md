> Part of [LESSONS](../LESSONS.md) — living memory, one section per file
> since 2026-10-04 so that "read the relevant section" is a thing a reader
> can do. The rules of the file, and why it exists, are in LESSONS.md.

## 3. Measurement & gates

- **A predicate with two consumers belongs in neither of them.** The rules
  deciding whether a gold candidate is still worth asking a person about lived
  inside the page that drew it, which was fine while one surface read it. The
  moment a second consumer appeared, a rule held in one and not the other
  stopped being a difference and became a trap: it does not fail loudly, it
  puts unanswerable questions in front of a person and looks like it is
  working. One of those rules withdrew 2,687 of 4,706 cells. **Extract the
  predicate the day the second consumer is written, and prove the move by
  IDENTITY — every figure the old caller quoted, unchanged.** (2026-09-28,
  C460.)

- **A MEASURED REFUSAL NEEDS A GUARD, BECAUSE THE ARTEFACT THAT SURVIVES IT
  LOOKS USABLE.** C167, closed 2026-10-10. The nickname map is sound — 371
  pairs the FILER stated, written `Formal (Nickname) Surname` so the document
  asserts both, screened of 26 organisations, 3 titles and 164 non-shapes, and
  carrying te reo equivalents no bought-in list has (David↔Rawiri, Peter↔Pita,
  James↔Hemi). Merging on it is refused by measurement: 33,989 same-surname
  pairs against a SHUFFLED-MAP null of 26,713, a **1.27x lift**, which is no
  signal (#c20929). What then sits on disk is a clean, well-documented,
  plausible-looking map of 371 real pairs with no consumer — and the next
  reader who finds it will not re-run the null model, they will wire it in.
  **SO THE REFUSAL GOES IN A TEST, NOT ONLY IN A DAY-LOG.** The guard asserts
  that NOTHING imports the file, and says why in its own failure message, so the
  day something does the argument has to be made again with a measurement
  rather than by someone noticing a useful-looking file. The warning also
  travels INSIDE the artefact, beside the data, because a reader who opens the
  JSON is the reader who needs it.
  Generally: when a measurement says "do not build this", the deliverable is
  the evidence AND the guard. A negative result with no enforcement is a
  positive result on a delay.

- **A SCREEN IS NOT INSTALLED UNTIL EVERY WRITE PATH ASKS IT, AND THE PATH
  THAT HARD-CODES THE COLUMN THE SCREEN DECIDES WILL BE HOLDING THE LARGEST
  ROW.** C464, closed 2026-10-10. The screen itself was right: built
  2026-10-09, 25 tests, **zero false positives in the whole history**, and
  `line_kind` answers `furniture` for every one of the rows in question when
  asked directly. The nightly derive then ran at 03:35 and **7 rows worth
  $120,062.78 were still typed `name`** — led by `TOTAL FOR PART A` at
  $98,561.77, 82% of the money in one row, which is #8a634c's shape exactly.
  Every one carried `row_basis = agreed, reconciled = false`: the signature of
  `load_reviewed`, whose INSERT read
  `line_kind, reconciled, row_basis) VALUES (…,'name',false,%s)`. One column,
  one literal, and the screen was unreachable from the path that loads what a
  PERSON confirmed.
  **THE TEST THAT WOULD HAVE CAUGHT IT IS NOT A TEST OF THE SCREEN.** C464's 25
  tests all exercise `line_kind`, and `line_kind` was never wrong. What was
  missing is a test of the LOAD — a part total handed to `load_reviewed` and
  asserted absent from the insert — which is why the five new ones assert on
  `c.inserts` and one asserts the literal `'name'` is not in the SQL at all.
  Verified end to end rather than by unit test alone: re-ran the derive and the
  count went **7 rows / $120,062.78 to 0 / $0.00**, with the disclosure side
  unmoved (281 live, 6 sub-floor, 0 impossible dates).
  **AND "A RE-DERIVE REMOVES THE MONEY" IS A PROMISE, NOT A STATE.** The card
  said exactly that on 2026-10-09 and the re-derive had RUN, twice, without
  removing it. A card that records what a future run will do should name the
  run and the number to check, because otherwise the next reader believes the
  sentence instead of the register.

- **A TABLE CELL ENDS AT AN UNESCAPED PIPE, AND THE REGISTER CARRIES ONE IN
  DATA.** C171, 2026-10-10. The card register is a markdown table read
  POSITIONALLY — owner at cell 4, size at 5, status at 6 — and C171's own
  finding is a donor filed as `N S| Management Limited`. The pipe is in the
  DATA, so that row was EIGHT cells in a seven-column table: every consumer
  read its status from the wrong cell and the remainder sat orphaned in an
  eighth. It read True by luck, because the pipe happened to fall in the last
  column. Three rows in the closed register have it mid-row, where luck runs
  out: **C381 reads `Claude` as its status**, and C384 and C551 carry one
  inside backticks — markdown does not care that a pipe is in inline code.
  **ESCAPING IT IN THE DOCUMENT FIXES NOTHING UNTIL THE READER HONOURS THE
  ESCAPE**, which is why `\|` and a `(?<!\\)\|` split landed in the same
  commit, in `muster_audit.split_cells`, with `board.py`, `four_questions.py`
  and `test_arthur_owed.py` pointed at it — four readers of one row, which is
  the same count that gave three different open counts (#7ca4cc).
  **AND THE WIDTH IS MEASURED FROM THE ROWS, NEVER READ FROM THE HEADER.**
  Against the header the check reported **149 findings** in the closed
  register, every one false: its 16 header lines name six columns and 313 of
  its rows carry a seventh (`use case`) that the live register has always had —
  the rows are right and the headers were never updated. That register is also
  genuinely BIMODAL, 313 rows at seven against 86 at six, so no single width is
  correct for it. The check now takes the MODE of a document's own rows and
  REFUSES to speak where fewer than 95% agree: one real finding in the live
  register, one in the parked, nothing in the closed. A checker that reports
  149 false positives is worse than no checker, and it would have buried the
  one row that mattered.

- **A CORRECTION KEYED ON THE PRE-STATE BECOMES UNPLACEABLE THE MOMENT IT IS
  APPLIED — SO ITS REPORT FILLS WITH PERMANENT FALSE ALARMS AND A REAL ONE
  HIDES AMONG THEM.** C186, 2026-10-10. `docreview.corrections` addresses a row
  by WHAT THE REGISTER CURRENTLY HOLDS, deliberately: the EC form prints a row
  number, `registers.party_donations` does not carry one, and guessing which
  stored row is which printed row double-counts donations. The cost of that
  correct choice was never measured. An `amend` that names `$51,828.90` and
  sets `$11,826.30` matches nothing once it has run, so the loader reported it
  as *"0 rows match"* for ever. Measured on the live ledger: **35 "unplaced"
  corrections, of which 18 had already been applied, 7 are genuinely absent
  from the register and 10 change something other than an amount.** Eighteen
  standing false alarms is how the seven hide — and the seven are the real
  finding, a figure a person read off the page that the register holds nowhere
  (#dcaa40: an instrument that cannot tell a leak from a correction will report
  the correction).
  **THE THIRD STATE IS "SATISFIED" AND IT HAS TO BE REPORTED, NOT DROPPED.**
  Nothing matches the old values AND exactly one row of that document already
  holds the new ones: the correction is done, not unplaceable. Quietening an
  alarm moves a signal (#624a50), so `satisfied` is counted and listed in the
  same report rather than filtered away, and two rows already holding the new
  value stays REFUSED — picking one is the double count the addressing scheme
  exists to prevent. Live effect: unplaced **35 → 16**.
  **AND CHECK WHAT THE LEDGER DECLARES BEFORE BLAMING THE LOADER.** The same
  rows read `row_basis = agreed` where a person had read the page, which looked
  exactly like a tier lost in application — so the fix shipped with a comment
  saying the register *"held only TWO `confirmed` rows while a person had
  confirmed twenty"*. It had not: **379 of the 381 corrections DECLARE
  `agreed`** and the loader was faithful to every one. The tier assertion added
  here is a measured no-op (`retiered` 0) kept for the first `confirmed` amend,
  and whether Arthur's own page-readings should have been written `confirmed`
  is a question about the LEDGER that runsheet §AS already owes him. A defect
  in the thing that WRITES a record and a defect in the record are not the same
  defect, and the second one is not the loader's to repair.

- **A GENERATED REGISTER'S FIGURES ARE MEASURED; THE PROSE BESIDE THEM IS NOT —
  AND THE PROSE IS WHERE THE IMPACT CLAIM LIVES.** C467, 2026-10-10.
  `RETURNS_FLAWS.md` is generated from the register at run time and gated by
  `--check`, so every COUNT in it is true by construction. Its §5 narrative is
  a hand-written list inside the generator, which `--check` compares only to
  itself, and it said of an unresolved party label: *"any consumer reaching for
  `party_canonical` drops those returns silently."* Measured when the fix
  landed: the labels live in `party_return_totals.party_label`, the only
  consumer of `party_canonical` is `pi_residue.returns_held`, and that reads
  `party_donations.party`, which carries none of them — **175 (party, year)
  pairs before and after, nothing gained or lost.** The flaw was real and the
  hazard worth closing; the IMPACT sentence was never measured, and a drift
  gate over a generated document cannot catch a claim that was wrong the day it
  was written. So a narrative bullet states what it has measured, says ZERO
  when the live effect is zero, and a fix is recorded as latent rather than
  claimed as a repair — the alternative is a register that reads as a list of
  live defects and is partly a list of hazards.

- **`n_live_tup` IS NOT THE DENOMINATOR, AND A NEVER-ANALYSED TABLE'S COUNTER
  CAN BE 293x WRONG.** Nothing but VACUUM or ANALYZE corrects `n_live_tup`, so
  the tables it lies about most are exactly the ones a maintenance check exists
  to find. Measured 2026-10-10 on the primary: `v3.alias` 90,262 against
  26,495,281 actual rows (293x), `v3.detector_signals` 73,431 against
  12,063,503, `v3.extract_queue` 52 against a planner belief of 5,640,263. Two
  costs, in opposite directions. A dead/live RATIO built on it read 11.9 and
  looked like catastrophic bloat on a table whose real ratio was 0.04 — and
  autovacuum, which uses `reltuples`, was correctly leaving it alone, so an arm
  built on that ratio would have red for ever on sound tables. And the census
  of never-analysed tables filtered `n_live_tup > 100_000`, so all four of the
  largest never-analysed tables in the schema read BELOW the threshold and were
  omitted — 10 GB of them, found every week by a check that named them never.
  Filter on SIZE, which is measured; ask autovacuum's OWN formula
  (`threshold + scale_factor * reltuples`, per-table reloptions honoured)
  rather than a ratio you picked; and report both row figures, because their
  disagreement is the finding.
- **A safeguard mutation testing cannot kill is not a safeguard — delete it.**
  A party matcher stripped a list of filing-tree words before matching. Removing
  the strip killed no test, and the reason was not a gap in the tests: none of
  those words collided with anything the matcher looked for, so the code decided
  nothing. Shipping it would have told the next person the hazard was handled.
  **A surviving mutant is either a missing test or dead code, and the difference
  is worth five minutes to establish.** (2026-09-28, C460.)


- **`x IN (…) OR y IN (…)` is not two semi-joins — split it into two
  statements.** The OR defeats the hash semi-join, so every row of the outer
  table linearly scans a MATERIALISED copy of the inner list, once per branch.
  *Paid for by:* 2026-09-27, the Papers Past withdrawal. The `entity_merges`
  count — 2.1M rows against 2.3M ids — was still running at eighteen minutes;
  EXPLAIN put it at **cost 64,462,499,455**. Rewritten as a UNION of two
  joins: **1,327,983**. The same shape was in the `claims` DELETE, 18M rows,
  where it would have hung the transaction rather than a count. A row matching
  both columns is removed by the first statement and simply absent for the
  second, so two statements are exactly equivalent.

- **Write the plan, not the sentence.** Twice in one script I wrote SQL that
  read like the English of what I wanted and planned like nothing I would have
  chosen: a correlated `NOT EXISTS` per entity (cost 268M, 59 minutes) and
  then the OR above (cost 64.5 BILLION). *Paid for by:* 2026-09-27. Both were
  found by a live run stalling, not by reading the code, and one was found
  only because the slow statement happened to be a count. **EXPLAIN every
  statement in an irreversible run before firing it** — it costs seconds and
  it is the only reading that sees what the database will actually do.

- **A keyword sweep finds the word, not the fact — read the hits before you
  carry them.** *Paid for by:* 2026-09-27, the identity queue. Looking for
  pairs disproved by a death date, I matched `evidence_text ILIKE '% died %'`
  on the A side and got ten. **Nine were somebody else's death** — *"the
  figures, released by Labour Minister Kate Wilkinson, show that 30 people
  died from accidents at work"*. One real death-of-the-subject claim in ten.
  Had I reported the ten, nine records would have been separated on evidence
  that says nothing about them. Sibling of *two numbers agreeing is not a
  catch*.
  · 2026-10-06 (C062), the same rule inside a GATE: T7.60 reports how many
  lanes ask for the proxy pool, and the first enumerator matched
  `heavy\s*=\s*True` and returned four files — the one real caller, a
  DOCSTRING in `_fetch.py` explaining the flag, and two test files. An arm
  whose job is to state a population cannot report a number that counts prose,
  so the enumeration is an AST walk for a `Call` with `heavy=True` as a keyword
  (and the skipped test files are NAMED, never silently dropped). The same cut
  then attributed the asker to every unit running `-m courts.*`, which named
  `courts-extract` — a unit whose module never imports the asker — so
  attribution is by bounded import REACHABILITY. **An arm that sends someone to
  fix an uninvolved unit is worse than no arm**, and both errors were the gate
  matching a NAME where it needed a FACT.

- **Open the page.** Twice in one hour Arthur reported a surface broken that
  every instrument I had called healthy, and both times one render found it.
  *Paid for by:* 2026-09-27. First the concern badge that could only draw on a
  box already open; then *"I cant scroll"* — `ReviewPage` was the only page in
  the app with no overflow class, 4,201px of queue clipped into a 692px frame
  by `main`'s `overflow-hidden`, four pairs of eighteen reachable. Neither is
  visible in a test suite, a route probe, or the bundle. A surface is not
  delivered until it has been looked at, and the cheap way to look is a
  headless render that can fail.

- **A feature proven by grepping the bundle is a feature nobody has seen.**
  Render the page and look at it before reporting a surface delivered.
  *Paid for by:* 2026-09-27, ruling 353. Arthur said the reviewer had none of
  the changes he asked for. Everything I could check said otherwise: the
  routes returned live data, the served `index.html` was `no-store`, the
  bundle's `last-modified` matched the build, and every string I searched for
  was in the JavaScript. All true, and the thing he wanted still was not
  there — the amber "N concerns" badge read its count from a thread that is
  only fetched when the box is OPENED, so it could only ever draw on a box
  that was already open. Six concerns were invisible on a collapsed queue of
  eighteen. One headless render found it in a minute. The page-level counts
  request that fixes it was already built and already deployed; nothing
  called it.

- **A check conditioned on finding something passes when the thing is gone.**
  Ask the store how many there should be, then count what the surface drew.
  *Paid for by:* 2026-09-27, the same hour. The first version of
  `ops/review_smoke.py` verified the concern panel *if any pair was badged*.
  I mutated the counts request away, rebuilt, and the check went green with
  zero badges on a queue the ledger says carries six — the exact defect it
  had just been written to catch. Zero read as "nothing to flag" rather than
  "the badge is broken". It now reads `items_with_concerns` from
  `/api/er/comments` first and fails when the page under-draws. Sibling of
  *a check that cannot fail is not a check* above, and the fourth appearance
  this week of a guard that quietly passes.

- **A check that cannot fail is not a check — ask what it would look like if
  the thing under test were broken.** "Run it and watch it refuse" is only
  evidence against a host that publishes something to refuse.
  *Paid for by:* 2026-09-21, C221. Its acceptance was a live dry run against
  web.archive.org watching for a refused path. The archive publishes NO
  robots.txt — it 404s — so under ruling 78 nothing there is disallowed, the
  run refused nothing, and it would have refused nothing whether the fix
  existed or not. It closed on C220's chokepoint test and on C115 showing the
  same gate refusing Wikipedia, which is a host that does ban things.

- **A detector reads the STRUCTURE it judges, never the text around it.** If
  the thing being detected is a structure, the detector reads the tree; a
  substring search over source is a detector a docstring can flip either way,
  and a gate that reads prose argues with the prose. Derive from facts the repo
  already maintains — a directory, a section heading, an AST — not from English.
  A code-stripper must drop DOCSTRINGS and keep STRING LITERALS: when a test
  asserts ABSENCE, ask what its stripper removed; when it asserts PRESENCE, raw
  text is fine.
  *Paid for by:* 2026-09-19, three times in one day — the clock-column gate
  counted its own explanatory prose as a violation, the retype-boundary gate
  read the route's comment naming the tables `remediate` writes, and the
  precompute gate read the job's comment quoting its own GROUP BY · two of
  those "fixes" then used a `tokenize` loop that blanks EVERY string token, and
  SQL lives in string literals, so "this job holds no `SELECT` of its own"
  became unfailable — the over-correction is worse, because a false positive
  argues with you and a vacuous test agrees with you (the version that survives
  both is AST-based, as `ingestion/tests/test_parties_capture.py` already did
  that morning) · 2026-09-19, the KIND gate (ruling 313): comparing each INDEX
  hook's own kind word against its section reported 32 disagreements, five of
  them the SENTENCE and not the subject — `ARTHUR_RUNSHEET`'s hook says its
  *lower sections* are "a record", `concerns-archive` matched the word inside
  "issues-ledger"; shipped, it would have been exempted within the week ·
  2026-09-20, the shared-DSN gate: asking whether the word `environ` appeared
  in a function's source flagged EVERY correctly migrated module in the estate,
  because the docstring written for them the same hour says "The environment's
  value", and the refusal check matched `exit(` inside `dsn_or_exit(`, i.e.
  inside the DELEGATION · 2026-09-04, twice: the hook's destructive-CLI rule
  matched the word in a heredoc'd DECISIONS row and the credential rule matched
  a path mentioned in a Python string — judge the command HEAD after stripping
  sudo/env, judge quoted remote programs as commands of their own (`ssh host
  '…'`, `bash -c '…'` recurse), never regex a whole line for a word ·
  2026-08-22 (B1): the permission hook blocked the doc-edit commit that
  described it, within minutes of going live — a guard that pattern-matches
  words will stop the people writing about the guard, so match the STATEMENT
  shape and keep each false positive as a test case (second bite: once live,
  the classifier refused the agent's edits to the hook file itself, so a loose
  rule cannot be tightened by the agent that found it; whether hooks fire under
  bypassPermissions is recorded as unverified, ruling 37).

- **A gate keyed on a NAME cannot enforce a rule about a VALUE — write the
  detector against the thing the rule names.**
  *Paid for by:* `test_dsn_import_shape.py` forbade the code supplying a DSN
  value and looked only at variables ending `_DSN`, so it read past
  `data-layer/register_env.py` for two days — three
  `postgresql+asyncpg://querynz@localhost:5432/...` literals under the names
  `EXTRACTIONS_URL`, `INCOMING_NEWS_URL`, `NZBN_CANONICAL_URL`, and
  `INCOMING_NEWS_URL` is what four other live modules call the backlog. Found
  only because homing the shared accessor was the one reason anyone opened that
  file · the same shape in prose: a gate that forbids one bad SHAPE is not a
  gate for the property. The honest-UA gate grepped for "Mozilla/" and a
  headless-browser call, so any other declared USER_AGENT passed and was
  stamped on every request (2026-09-04, audit A20); it now asserts that every
  declared User-Agent carries the contact address unless the module is an
  argued exception. **Write gates positively: "every X has Y", never "no X
  looks like Z."**

- **A new test is not evidence until it has FAILED against the code it
  indicts.** A test that can only pass is a claim, not a measurement, and it is
  worse than no test because it occupies the space where a real one would go.
  The check is cheap: `git show HEAD:<file>` into a scratch copy, an env
  override, or break the thing on purpose and put it back.
  *Paid for by:* 2026-09-19, three times in one day on three files — the
  console precompute gate and the query retype boundary (their stripper deleted
  the text they searched), and three of the eleven scope-hook cases (the fake
  repo lacked the directories that make a literal look like a path) ·
  `entity_status IS DISTINCT FROM 'Removed'` running against all-lowercase
  statuses and leaving 30,568 dead societies in the live tier — a predicate
  that silently matches nothing looks exactly like one that works · 2026-09-04:
  `era_cutover.py` had said since 08-22 that it "halts if the fleet reports
  failures above the threshold", while the wave phase checked only that three
  fleet passes exited 0 and `max_failures_pct` was read by nothing; the same
  audit found 0 of 25 units carrying the OnFailure the manifest doc described.
  **Read the code, not the docstring, when listing what protects an era** · a
  test that reads a GENERATED document passes whenever the document is current,
  including when the generator that wrote it has since been broken (found
  2026-09-19 by mutating the generator and watching two tests stay green) — a
  test about what a generator PRODUCES has to run the generator · an acceptance
  rec that cannot fail: PI-41b read `… and A or B`, Python binds `and` tighter,
  the trailing `or` detached the conjunction and B matched the route's own
  basis literal, so it passed on any board; PI-33 compared a filtered subset
  `<=` its superset; PI-37 asserts only identities the server computes in the
  same pass (audit 2026-09-03; now pinned in
  tests/test_ux_run_political_influence.py — a rec predicate is a conjunction,
  an AST test refuses a top-level `or`, recs pin VALUES within bands, and a rec
  whose predicate cannot be shown failing on a fixture is not a rec) · a
  mutation harness that counts only `FAILED` misses the mutations that break
  COLLECTION: planting an import-time resolve took pytest to rc 2 with `ERROR …
  during collection` and the harness reported the suite had MISSED it
  (2026-09-20) — a verification tool inherits every blind spot it was built to
  find.

- **A gate tested with fakes certifies the shape you faked; a gate that can
  reach production is the worst false gate of all.** A worker's connection is a
  SIBLING of its caller's — same DSN, same search_path — never a fresh default,
  and any test that exercises a write path must be able to prove where the
  write went. A test that exercises a lane also exercises its TELEMETRY.
  *Paid for by:* 2026-08-22, per-worker connections opened with
  `store.connect()` went to the configured production graph while the test
  drove a throwaway schema — six rows landed in production `review_decisions`
  during a suite run (reverted within the hour; keys._worker_connect) ·
  2026-08-22 (B4 T1): the worker-isolation fix and its crawler twin were green
  on fakes, and the CLIs pass a `ReconnectingGraph` wrapper with no `.info`, so
  the first live crawler cycle under `healer.cli` died at 09:40 on exactly that
  — keep a live run in every batch's acceptance
  (`tests/test_sibling_connection.py`) · 2026-09-19: the gate written for the
  crawler's new finder state called the finder against a throwaway schema, and
  the finder wrote those counts into the real `var/audits` state file where the
  board reads them — the next morning's board would have reported a cleanup
  "stalled" at five entities. When a function acquires a side effect outside
  the database, every existing test of it becomes a writer to that destination:
  redirect the path in a fixture and prove it by deleting the real file and
  re-running the suite · a TTL memo leaks the same way across test fakes
  (2026-09-08, C155: memoising `_elected_spans` / `_mp_affiliation` /
  `_mp_interest_roles` for 600 s turned three green query tests red) — a memo
  needs a per-test clear in conftest the moment it is introduced.


- **An exemption in a gate is a filed defect wearing a different hat.** When
  writing "X is exempt because Y", check whether Y is a bug.
  *Paid for by:* 2026-09-19 — `tests/test_dsn_import_shape.py` banned
  from-imports of DSN constants with exactly one exemption, `TESTKIT_DSN`,
  exempt *because* it fell back to a localhost literal and so could not turn an
  import into a refusal. The fallback was itself a filed row; paying the row
  emptied the exemption set.

- **Check the instrument before believing its output — and when a score
  moves, suspect the instrument before the system.** A measurement is not
  evidence until the thing that measured it has been tested against something
  already known. Sample the AUDITOR, not just the audited. Before filing a
  measurement, ask what else would produce this number.
  *Paid for by:* 2026-09-20, the muster audit — `ops/muster_audit.py` reported
  **91 broken references** on its first run and **14** after two bugs in the
  tool were fixed, a **73% false-positive rate**, and the errors were not
  random: it resolved paths by BASENAME, so `claim_graph/merge.py` "resolved"
  to a different `merge.py` three packages away, and its arm pattern was
  `T7\.\d+` while `T7.2b` exists, so it counted 49 arms where the board has 50.
  Both numbers would have been quoted as fact · a resolver gate reporting
  106/207 because the grader's name match failed on comma display forms
  ("Peters, Rt Hon Winston") — fixing the grader, no weights touched, gave the
  true 127 · an LLM reviewer that systematically over-flagged correct
  canonicalisation, where the harness's own bugs surfaced only under human
  spot-check · a signal that counts the thing it is judging is not a signal:
  the first `common-name` check counted the roster's records of the exact full
  name, which is the folded group itself, and flagged 71% of folds (2026-09-06;
  dropped, regions-apart + bankruptcy-within-bar stayed at 16%) · three
  findings filed and self-corrected within two days — an "extractor drops
  pre-modifier objects" diagnosis (it already looked left), a conclusion from a
  recency-biased 4,000-row sample, and a 24-shard slowdown blamed on memory
  bandwidth when it was core oversubscription · and the fix needs measuring
  too, even when it is obviously right: the narrowed ESTATE-clock gate scan was
  correct about the row that motivated it and produced 21 new false "none"s,
  known within a minute only because the generator prints its own totals
  (2026-09-19). **A change that improves the case in front of you is a
  hypothesis about the other cases.**

- **Green is not throughput: audit the filter against the queue's shape, and
  never let an absence read as completion.** A job that exits 0 having done
  nothing is the failure mode monitoring misses. A done-signal computed from
  "stale" rows cannot see ABSENT rows; a skip-list over completed work needs a
  status filter; an empty reference table degrades every deterministic lookup
  to a silent no-op, so assert ROW COUNTS at startup, never "table exists";
  abstains must never read as progress; and "returns something" is not
  "working" — check freshness and coverage, not a non-zero count.
  *Paid for by:* v2, an extract job firing every 30 minutes for DAYS while its
  `length BETWEEN 500 AND 9000` test excluded 100% of the standing queue
  (re-derived in 2026-08-20's watcher doctrine as the data tier) · v2 again, a
  source landing rows continuously while its discovery only ever surfaced a
  month-stale slice · a sweep driver looking for "a log row whose build is
  stale" when a requeued article has no log row at all — it announced "nothing
  left to sweep" with 100,282 eligible articles unextracted · the drain
  skipping everything in `extraction_log` regardless of status, so an ERRORED
  article counted as done and was never re-offered, and because stats counted
  only `status='ok'` the hole was invisible (→ now T7.9) · `nzbn_canonical`
  bootstrapped schema-only (8 MB, zero rows), so NZBN matching ran one empty
  lookup per org entity for WEEKS, linking nothing, with no error anywhere ·
  heal loops counting abstains as work and looking like they were converging
  when nothing was moving (2026-08-14) · and its inverse, which cost one false
  alarm: a queue count is a top-up equilibrium, not a progress metric — finders
  refill what the judge drains, so a flat number means healthy flow and
  progress is the `judged_at` rate (2026-08-18).

- **A degrade nothing downstream reads is a lie with a variable name, and the
  lie travels up one level at a time.** When a degrade flag is set, find every
  consumer of the record in the same change, or do not set it — and follow the
  status all the way to the pixel. A type error cannot catch a rule that
  believes it looked.
  *Paid for by:* 2026-09-19 — `entity_flags_view` catches a register failure,
  sets `rec["register_down"] = True` and returns, correct for a serving route
  that must not 500 because a second database is away; no rule read the key, so
  three of four returned `clear` over an assembly that was never filled, and a
  company in receivership was served "no gazette insolvency events on the
  subject or any entity sharing an officer with it". The rulepack's own
  docstring forbids it and its contract enforces greens structurally — a
  `clear` must carry `sources_held`, which the rule supplied from a constant.
  Fixing the rules was not enough: `build_report`'s verdict was `worst or
  "clear"`, so a document whose every check was blocked still answered `clear`
  while the prose beside it said "3 check(s) blocked (declared)" — prose is not
  the verdict, the badge reads the verdict — and one level further the GUI's
  colour map falls back to GREEN for a value it does not know, so a new honest
  status renders as reassurance.






- **Never cite a POSITION in a document that is still being written, and never
  key a judgment to a row id something regenerates.** Cite the text, the
  heading or the file; bind a judgment to a STABLE content key (source sha +
  row hash); a derive that regenerates a table re-runs the passes that judge
  it, in the same run; a serving join across tables keyed by id ALSO matches
  the natural key; and a pass that keeps judgments by content key must RE-POINT
  their ids at the rows that now carry the key, every run. Git is an oracle for
  what a document MEANT — before rewriting a stale reference by judgement,
  check whether the repo can still say what it pointed at.
  *Paid for by:* 2026-09-19, three instances in one day — `ops/retired_register.py`
  cited its evidence as `file:LINE` and one row cites LESSONS.md, the file this
  project appends to the day it learns something, so every append shifted the
  ordinal and the pre-push gate failed on a document whose substance had not
  changed; the bootstrap gate read a comment as a directive; and the card
  register cited `L<n>` of the issues-ledger, which had been SPLIT three days
  after the cards were written, so **141 of 163 citations named the wrong
  DOCUMENT**. All 163 were repointed exactly, with nothing guessed, from the
  ledger as it stood at the citing document's own commit · a repair that cannot
  run twice is a repair nobody can verify: the first pass wrote its marker into
  the very lines its fingerprints were taken from, so a second pass placed 98
  of 163, and stripping the marker broke the already-present guard — both found
  by running it again, neither by reading it · 2026-09-06:
  `press_appointments.sample_claim_id` stopped resolving after era 5 and the
  review showed "article link not resolved" on every press leg — claim ids are
  row ids until the document-scoped key lands (TERMINAL L3), so cite the
  DOCUMENT and re-find the current claim at read time (C346, and `/api/cite`
  must follow) · 2026-09-03, donor anchors: `registers.party_donations` was
  re-derived on 2026-08-28 with fresh serial ids while `registers.donor_anchors`
  kept pointing at the old ones, so every party-donation row served as
  "name-matched" for six days and the ledger's ids collided with
  `candidate_donations` ids — nothing on the page said so, the anchored count
  simply fell to zero. **Met again 2026-09-05** with rules 1–3 in place,
  because the serving join was still by `donation_id`
  (`donor_anchors._rebind_ids`: 29,785 re-pointed). The acceptance runner
  (PI-11b "anchored ≥ 10") caught it both times — run it after every derive,
  not only after code.

- **A record of the world is stale the moment the world moves, and only the
  box knows which way.** A row that claims a state of the world costs one
  command to check. A row is read from the LEFT, so closed rows lead with their
  state (`**DONE …** — was: …`). A hand-set value under a COMPUTED field has a
  life of days: find the clock that writes that column, and put the change in
  the rule it runs. A board red at 06:45 can be green by 14:00 with nobody
  touching it. A declaration outranks an inference, and a real timer outranks
  both.
  *Paid for by:* 2026-09-19 — two queue rows both said "waiting on Arthur": one
  had been done six days earlier and never closed, the other had been struck as
  moot and was not; neither error was visible from any document, because the
  runsheet, the queue plan and the day-log all agreed with each other and
  disagreed with the machines. T7.24 read as a live red for four hours after
  its repair because the closing sentence sat at the end of a 600-character
  cell · `source_policy.llm_tier` is computed by rule (104) and recomputed
  every Monday by `robots-audit.service`, so a council tier written by hand
  would have read correctly all week and silently reverted — and not to NULL
  but to `llm`, which is *permission granted* (measured: with the new rule off,
  all 24 council hosts compute to `llm`) · 2026-09-19, the ESTATE clock
  column's fourth false reading: `ops/set_parking.py` turned from hand-run into
  GATE the moment a test named its path in order to read its DOCSTRING, and the
  narrowed-scan fix was reverted in favour of changing the precedence — `gate`
  is grep's opinion about what a test file means, a marker in the docstring is
  the author saying what fires this · 2026-08-23: T7.10's six dirty names were
  gone by the time the hygiene pass ran (0 changes, dry run) because the
  crawler's own screens had taken them — re-run the arm before acting on a
  stale board line · 2026-08-23: a stale runsheet made Arthur re-decide five
  decided things, so when a ruling lands the line that asked for it is edited
  in the same commit (ruling 30's discipline).



- **A documented limit that produces WRONG answers is a defect wearing a
  limit's clothes.** Writing a limit down makes it honest, not harmless; the
  test is which direction it fails in. A limit that MISSES things is a tripwire
  being a tripwire; a limit that FLAGS the wrong thing teaches people to work
  around the guard.
  *Paid for by:* 2026-09-19 — the scope hook's docstring said "a relative
  target resolves against the repo root, not the shell's cwd", stated plainly,
  tested, and read for months as a known edge; it was refusing writes to files
  inside the open brief because of a `cd` it did not model, and the proof was
  already in the tree: `"finders" + "." + "json"`, `ROUTES = "routes" + ".py"`,
  string assembly written for no reason but to get past it.

- **When a fact is written down twice, the second copy is the defect waiting
  to happen.** Delete the copy; it is the cheaper half of the fix by a
  distance.
  *Paid for by:* 2026-09-19, the KIND gate — all 32 disagreements existed
  *because* the kind was recorded in the section heading AND repeated in the
  hook.

- **"Built" means EXECUTED against the real surface.** CLI verbs parsed by a
  test, pins that execute, services restarted in the close (MO §4, ruling 87).
  A ledger or plan CLAIM is not runtime truth: before a card becomes a batch,
  read the code it names.
  *Paid for by:* 2026-08-23 — three "built" claims with green tests had never
  been executed: `seed-ids` was a dispatch line with no function (plan-mode
  rehearsal executes nothing), the coverage spot fix was pinned by a source
  grep and had crashed every live `/subject` call since it shipped, and the
  query service was serving week-old code; the era fire and the acceptance
  runner found all three within an hour · 2026-08-29 → 2026-09-04: the Muster 1
  remaining-work plan took THREE passes because passes 1–2 planned from what
  cards and docs SAID — a "RED gate", an "unbuilt" balancer, a "3 GB/shard"
  floor — and pass 3 probed the code and found each one false or already done
  (the 2026-09-04 collect then measured 47 of 227 open cards stale, moot or
  duplicate). MO §3.6(c) says probe the STACK; this widens it to the code a
  card names · 2026-09-06: adding a status to a catalog is adding it to the
  test that lists the allowed statuses — ruling 194 set `status="withdrawn"` in
  the morning and the catalog test was red until an unrelated evening run found
  it, so the package's tests run in the same commit as the package's data
  change.

- **Serving must say WHICH judgment version it serves, and a "done" skip rule
  keys on the INPUT's content hash, not on the output existing.** Identity is
  the bytes, not the path.
  *Paid for by:* 2026-09-06 — the review read every weights version live at
  once, so the 1.7 cards stood beside the 1.8 ones (filter to the current
  version or withdraw the superseded run; C348) · 2026-08-23: the EC page-read
  skipped 20 of the 26 re-downloaded returns because each had a JSON, read from
  the truncated 1 MiB bytes, that looked done — the sha in the JSON was the
  tell and nothing compared it.

- **Exact means a key, not a score; and a pass rule needs an ARM, not a sum.**
  Identity between two records is the same street number + street name,
  everything else tolerated. Weights rank; only a named arm carries — say which
  signals may carry before tuning any weight. Corroboration counts DISTINCT
  SOURCES and excludes denied/withdrawn modality, because a denial is a second
  mention, not a second source.
  *Paid for by:* 2026-09-06 (ruling 221) — the address leg scored token
  overlap, so a shared postcode and suburb word gave 20% and "74 St George's
  Bay Rd" vs "74 St Georges Bay Road" gave 67% (the tokeniser dropped numbers
  under three digits and split the apostrophe), and Arthur read both as wrong
  on the same card; the old text key had also folded 160 roster records that
  met only on care-of / postcode wording · the same ruling: three weak legs
  (unique name, co-donation, press) summed past the floor and corroborated
  donors nobody could defend · 2026-09-06 (rulings 215–218): 1,427 of 3,358
  first folds rested on law/accounting-firm hubs (> 50 companies) — weight an
  address by the size of its group, and let an exact longer name carry the
  weight a hub cannot.



- **A rule the estate learns does not reach the substrate by itself — name the
  shared infrastructure explicitly when a rule goes out.** Shared test
  infrastructure is nobody's service and is swept last. And where a shared
  module LIVES is decided by what may import it, not by what it does.
  *Paid for by:* 2026-09-19 — "a DSN carries no default, because the wrong
  database ANSWERS" was learned in August and applied one package at a time,
  while `testkit.fixtures`, imported by every DB-backed suite in the repo,
  still carried a localhost literal with a comment recording the 61
  `ReadOnlySqlTransaction` errors it had already caused · 2026-09-04 (Muster 2
  B4, audit A47): the role password sat as the DEFAULT in 52 tracked files, in
  three alembic.ini files and as `PGPASSWORD=`/`PASSWORD '…'` in four bootstrap
  scripts — every one "just a default", none scanned, and the unit-file
  credential gate could not see them; defaults now name role and host only, so
  a bare shell fails LOUDLY on auth instead of silently reading the dead
  standby (`tests/test_doc_drift.py` scans every tracked
  `.py/.sh/.conf/.service/.env/.ini`; fixture placeholders pass; rotation stays
  Arthur's, ledger 1631) · 2026-09-04: the query suite failed 9 tests on a
  column the canonical register DB had carried for ten minutes, because its
  bare-shell default DSN reached the stalled hot standby (in_recovery since
  09-02) — the runner's env (ruling 165) points at db-primary and the same tests
  pass, so a suite that needs the canonical must refuse a connection that
  answers `pg_is_in_recovery()` true (testkit's dbguard shape); green-on-a-copy
  is the A06 class · 2026-09-20 (ruling 308(a)): the obvious home for one DSN
  accessor was `v3/dsn.py`, and four packages — console, extractor, query,
  candidate_register — each carry a boundary test banning an import of `v3`,
  query's saying the service must not import THE FACTORY; homing it there meant
  widening four bright lines to admit one module, so it went into its own
  zero-dependency package at the bottom and all four boundary tests passed
  untouched. **The tests were the design review; they had been written before
  anyone asked.**

- **Removing a default can DELETE a test instead of failing one — count the
  collection, not the failures.** A FROM-import resolves at import time (an
  attribute access does not); a module-level constant other modules import IS
  an interface, however much it looks like configuration; and `tests/` at the
  repo root is not inside any package you are grepping. A failing test
  announces itself; an absent one does not.
  *Paid for by:* 2026-09-19, the night the estate took 39 localhost DSN
  defaults out — two settle tests lost 13 tests to a removed module-scope env
  write; `ops/tests/test_resweep_reconcile.py` stopped collecting when
  `extractor/settings.py`'s `from claim_graph.settings import GRAPH_DSN` met a
  value that now resolves on access; and `registers.metrics.DSN`, deleted after
  grepping the PACKAGE, broke twenty test modules at collection and a board arm
  the package grep never saw. Gated by `tests/test_dsn_import_shape.py` ·
  2026-09-14 (S6): `evidence_for_model` read as unused across the packages and
  was nearly deleted, and `tests/test_evidence_gate.py` at the repo root
  imported it — a name is dead only when the root `tests/` are grepped AND the
  root suite runs green without it (`tests/test_dead_code_gone.py` pins the
  dead set).

- **A mechanical migration can introduce the defect it removes, and the gate
  will not see it.** Import a shared helper under a PRIVATE alias — an
  unaliased import also joins the importing module's public API. And a
  distribution's directory must not be spelled like the module it ships.
  *Paid for by:* 2026-09-20 — inserting `from estate_dsn import dsn` into a
  module whose own accessor is NAMED `dsn` shadows the import: the `def` wins,
  `return dsn(name)` calls itself, and three service packages recursed to the
  stack limit while the 308(a) gate passed all three, because a function
  calling itself reads exactly like delegation; a DB-backed test three packages
  away said `RecursionError`, and `registers/tests/test_sealed.py` caught the
  public-API half by asserting that surface exactly · the same day,
  `data-layer/estate_dsn/estate_dsn.py`: any process with `data-layer/` on its
  PYTHONPATH finds the DIRECTORY first and imports it as an empty NAMESPACE
  package, so the real module never loads — `ImportError: cannot import name
  'dsn_or_exit' from 'estate_dsn' (unknown location)`, and "unknown location"
  is the tell. `ops/tests/test_unit_entrypoints_import.py`, which runs each
  unit's `python -m <module>` in a subprocess with that unit's own PYTHONPATH,
  failed 21 of them including `gazette-derive` and `hansard-register`. The
  directory is hyphenated now, which Python cannot import under any
  circumstances. **An installed package passing `import x` in YOUR shell says
  nothing about the shell the unit runs in.**

- **A standing rule with no gate is a rule that will be broken, and you can
  predict which one.** Audit the rule list against the hook rules; a rule that
  cannot be gated is written down as ungated rather than trusted.
  *Paid for by:* 2026-09-20 — in one session I broke exactly two standing
  rules, `pgrep -f` and `--amend` after a push attempt, and
  `.claude/hooks/denylist.py` contains **zero** occurrences of `pgrep`, `pkill`
  or `amend`. Force-push, `rm -rf`, `psql -f` and `/proc/<pid>/environ` are all
  covered thoroughly and none of those was broken. **Unmeasured compliance
  decays under time pressure.**

- **A register whose rows name nothing cannot be audited, and two registers
  with no link means closing one does not close the other.** A row that names
  no evidence is marked UNCHECKABLE when it is written, so the number is
  reported rather than discovered a month later; status, evidence and history
  do not share one cell.
  *Paid for by:* 2026-09-20 — **403 of 637** card and plan rows name no file,
  no unit and no board arm, and three reasonable parsers over the same file
  gave three different open counts (63, 49, 43) · the same day: all fourteen
  service queues had "had a pass" while **173 cards stood open**; the queue
  register closed 151 rows against 27 opened while the card register moved
  separately at about 5 a day, so the estate could report every queue done and
  be nowhere near done.

- **When the find rate reaches the close rate, the plan's shape is wrong, not
  its order — promise an ORDER and publish the measured rate.** Deeper auditing
  finds faster than it fixes, which is the audit working; a plan that promises
  a clearing date is making a promise about something it does not control.
  *Paid for by:* 2026-09-20 — 7 rows closed, 7 opened.

- **A collect is not a plan, and the difference is eight products.** MO §3
  wants a surface matrix, a conflict register, a pull-forward list, a decision
  register mapped to what each ruling blocks, cross-queue invariants, a probed
  doc-vs-reality baseline, a re-pass after any ruling, and a concurrency map.
  **A list is a plan only when it says what may run beside what, and what would
  collide.**
  *Paid for by:* 2026-09-20 (ruling 318) — asked for "the new muster items" I
  produced a counted, verified list of 272 and presented it as a plan; Arthur
  asked whether the MO had been applied to it and it had not. Six products were
  missing or half-done, including clause (c), the runtime-stack PROBE, which
  exists precisely because a stale default and a misleading variable name were
  once read as current fact. The one conflict I had found — A1 committing per
  merge while A2 indexes the table every merge writes — turned up in a LESSONS
  re-read, not in any structure.

- **Keep the "verified fail-closed — do not re-audit" list in the audit
  RECORD, not in the plan.** The next audit reads the record as its before; a
  muster-scoped document is nobody's before.
  *Paid for by:* Muster 1 pre-pass §6 (2026-08-28), re-paid 2026-09-04 — the
  08-28 audit verified five gates genuinely fail-closed (research robots, the
  evidence/citation gate, gazette dedupe + namesake floor, the donations
  stated-total floor, the FLEET watcher) and wrote "do not re-audit" where
  nobody read it; the next audit re-verified all five.

- **A setting that must agree across units has ONE home and ONE writer — and
  an arm that asks the UNITS, not the file.**
  *Paid for by:* 2026-09-04 — the era flag set lived in three places (a fleet
  knob file, hand-installed drop-ins, the era manifest), and the drop-ins set
  only ERA3, so the standing tick and docpipe stamped v3-det-1.9 through the
  whole of era 5 while the fleet stamped 2.2 and every gate read the fleet. Now
  `era-flags.env` is written by the era close (ruling 166), the lanes and the
  launcher read it, and T7.32 asks `extraction_log` what actually got stamped
  (→ pre-pass K3; audit A01).

- **The identity behind a rate limit must be one the client cannot type.**
  *Paid for by:* 2026-09-04 (audit A37) — the product limiter keyed on
  X-Forwarded-For from any peer, so a fresh header bought a fresh bucket, and
  the test that "proved" the limiter sent the spoofed header itself. Now the
  peer is the client unless it is a named trusted proxy
  (`PI_TRUSTED_PROXIES`), buckets are evicted, the headers travel on a 500, and
  /api/health has its own bucket, a cache, and checks the REGISTER store the
  product serves — it had been checking the backlog it never reads. A limiter
  test must spoof from an UNTRUSTED peer and expect the 429.

- **sudo NOPASSWD:ALL plus an open 1025–65535 firewall range is "no floor".**
  The denylist hook is a tripwire on spellings; the box's floor is sudo scope
  and the zone the factory ports answer on. Identify before ruling — a port is
  not a threat until named.
  *Paid for by:* 2026-09-04 (audit A08/A48, ruling 173); both narrowed by files
  Arthur installs (`ops/production/sudoers-querynz`, `firewalld-lan.sh`,
  runsheet §AG), and the unknown listener on :27500 was passimd, Fedora's fwupd
  cache.

- **A destructive launcher's guards are exercised on the target box before the
  human runs it.** A guard that builds a pattern from a lookup FAILS CLOSED
  when the lookup is empty and compares resolved values, never a glob; a
  `--check` mode runs the read-only preamble on the actual box; a prompt names
  the exact string to type.
  *Paid for by:* 2026-09-06, disks_format.sh — the root-disk guard read btrfs's
  `/dev/nvme0n1p3[/root]`, got an empty parent, and its `case /dev/$root_disk*`
  matched EVERY device; and the confirm prompt said "type the device name" so
  Arthur typed the label and it aborted. A guard is verified by execution, not
  by reading — and a human's time spent on my defect is the cost.

- **The fleet disagrees with itself on ~6% of verdicts** at the production
  config (94% label agreement across three pairings). Rules are induced from
  that corpus, so the churn bounds how sharp any rule can be. → B4b's dense
  validation pass (ruling 27).

- **A comparison names its PREDICATE, the way an exhibit names its source.**
  Before reporting that a count has moved against the number a card was written
  at, re-derive it by CALLING the production function the card used — the SQL
  pre-filter AND the Python predicate that is the authority over it. SQL that
  looks equivalent is not, and the difference is invisible in the answer: both
  numbers are real, they just count different populations, and the alarm lives
  entirely in the gap.
  *Paid for by:* 2026-09-21, C241 — I flagged the glue-seam count as "4,189, UP
  from 3,882, where the card's criterion says it falls" and put it to Arthur as
  a finding. 4,189 was the raw shape; 3,882 was the shape minus OCR debris and
  abstains. Like for like it was 3,772 vs 3,882 — down, as predicted. In the
  same sitting my hand-rolled versions of these predicates returned 56,688
  "seams" (real: 1,108) and 328,120 "anonymised persons" (real: 194): off by
  15× and 1,700×, and both plausible enough to have been reported.

- **When a rule has an instrument, write the row in the shape the instrument
  reads — then RUN it and confirm the number moved.** A compliance the counter
  cannot see is not compliance, and it fails silently in the safe-looking
  direction: the budget never debits, so nothing ever complains.
  *Paid for by:* 2026-09-21 — ruling 323's `ops/card_balance.py` finds an
  opened card by the token `raised <date>` / `ruled <date>` in its live row. I
  opened C406 and C407 writing "Arthur 2026-09-21" in the source column
  instead, so the balance read 4 opened where the truth was 6. I would have
  gone on opening cards against a budget that never debited them.

- **Never `open(path, 'w')` in the same expression that reads `path`.** Python
  evaluates the `open(...,'w')` first, which TRUNCATES the file; the read that
  follows returns empty, and the write "appends" to nothing.
  *Paid for by:* 2026-09-21 —
  `open(c,'w').write(open(c).read() + rows)` replaced 275 lines of
  MUSTER_2_CARDS_CLOSED.md with 3. `card_balance.py` caught it one command
  later by reporting 3 closures where it had just said 21; restored from
  `git show HEAD:`. The instrument noticed, not me.

**A GENERATIVE MODEL CANNOT BE THE STRUCTURE AUTHORITY.** Ask a transcriber
for a table and it decides, per page, what counts as one. Never anchor a
parser on a field the model may or may not emit; take STRUCTURE from geometry
(ruling lines, cells by coordinate) and CHARACTERS from the model, and pair
them so they can disagree. Two readers that share an engine share their
mistakes, so agreement between them means nothing — diversity is the whole
mechanism, not a nicety.
  *Paid for by:* 2026-09-23 — GLM-OCR read National 2017 page 3 with zero
  character errors and kept the form's row-number column; on page 2, identical
  layout, same model, temperature 0, it dropped that column. An explicit
  prompt instructing it to emit the number changed nothing on either page. The
  audit's parser anchored on the number, so 528 of 554 documents (95.3%)
  yielded no rows and the night's headline figure rested on 26 documents, not
  554. Fixed by `data-layer/docread`: Table Transformer for the rows, the
  transcriber for the text, and the amount believed from NEITHER without
  agreement.

**RECOVERING ONLY WHAT WAS MISSED LEAVES WHAT WAS WRONG.** A second, more
expensive read triggered by absence never fires on a confident error. If a
field matters, read it twice ALWAYS and treat a difference as a dispute.
  *Paid for by:* 2026-09-23 — a 600 dpi re-read of each money cell recovered
  every amount the page-scale pass missed, and left `$10,088.00`, which that
  pass had read as `088.00`. It parsed, so no recovery fired; an amount two
  orders of magnitude out would have been served clean. Reading the money
  column twice unconditionally costs 0.1 s a cell.

**A CONSTANT TUNED AT ONE SCALE IS A BUG AT ANOTHER.** Any threshold in
pixels, characters or seconds must be derived from the data in hand, not
written down once.
  *Paid for by:* 2026-09-23 — words were grouped into printed lines by a fixed
  12-pixel band, chosen at 200 dpi. Run at 300 it split one line into three
  and returned `$ 000. 50, 00` for `$50,000.00`; two thirds of the money column
  read as nothing at all. The fix is the words' own median height, which the
  page supplies.













- **A queue of dead questions looks exactly like a short queue.** The docread
  review queue held 15,230 open items and 1,438 of them could be answered: the
  rest were a rule whose premise was two readers, disputes naming a reader
  retired the day before, pre-window years, and the stale threshold above.
  Withholding them is right — but withhold with a REASON, count the reasons,
  and print them in the header, or the page a reviewer opens is
  indistinguishable from a corpus the readers agreed on. (2026-09-26.)




- **A mutation that changes no test is dead code or a missing test.** The
  promoter label was read from the anchor AND stripped of its trailing
  `[PDF, 313KB]`; removing the anchor branch broke nothing, because the strip
  alone handled both held pages. Either delete it or state the case it exists
  for — `[PDF]` with no size — as a test. Code kept for a reason no test states
  is code kept for no reason. (2026-09-26, C453.)


- **A line that names a gap goes on naming it after the gap closes.** The
  promoter blind spot still read "not yet parsed into a register" four hours
  after the register loaded, and four other lines did the same thing the day
  before. A sentence about what the estate lacks must be generated from a
  count, never written as prose. (2026-09-26, twice in one day.)

- **Capturing the register did not unblock the claim the register was blocking.**
  A1 was "the one that blocks every coverage claim" for months. Held, it turned
  out to be a snapshot of today's 17 parties — and the parties that make
  coverage hard are the ones no longer on it. What decides a missing return
  from a deregistered party is the registration WINDOW, which was already in
  `gazette.party_events`. Ask what QUESTION a capture answers before ranking it
  as a blocker. (2026-09-26, C455.)

- **A measurement that cannot be trusted is withheld with a reason, not
  published with a caveat.** The party-coverage instrument computes 49 of 108
  party-years missing and will not return it, because the fold reads Māori
  Party and Te Pāti Māori as two parties and a party that filed then reads as
  one that did not. A caveat gets dropped when the number is quoted; a refusal
  does not. (2026-09-26, C455.)

- **Take the measurement that argues the OTHER way before handing a ruling
  over.** C429's owed entry said no further measurement could move the line,
  and carried one number: the judge reproduces its own verdict 0 times in 26.
  True, and only half of it. Nobody had asked what the lane actually merges —
  6,994 of 6,997 join names identical after casefold, and none has ever fused
  two entities both typed `person`. The verdict is unreliable; what it
  executes may not need it to be reliable. A ruling put to a person with only
  the evidence for one side is a guess with a signature. (2026-09-26, C429.)

- **A backlog that grows while a decision waits is an argument in the
  decision.** C429 was written at 79,445 stopped verdicts and 6,738 merges; it
  is 82,631 and 7,001. Quote the live count in the ask, not the count from the
  day the card was written. (2026-09-26.)

- **Put the sample in front of the person; the aggregate hides what they would
  recognise.** I showed ten merges to argue the retype lane was safe. Arthur
  read row three — `Ancklaud` — and said it is a misrendering of Auckland.
  There are 13 live `Auckland` entities, the lane merged none, and it called
  two of them `distinct-entities-ok` at the same 0.95 it merged the garbles at.
  That reversed the reading. 10,813 names carry both verdicts and 1,310
  executed merges sit on one. None of it was visible in the aggregate I had
  already taken. (2026-09-26, C429.)

- **Safe is not right, and a pipeline can be one without asking about the
  other.** The retype lane's dominance test and refuter stop it fusing two real
  people — 0 in 6,997. Neither looks at whether the judge said the opposite
  about the same name somewhere else, so 18.7% of its merges rest on a verdict
  it contradicts. Guards that bound the DAMAGE are not guards on the
  CORRECTNESS. (2026-09-26, C429.)

- **A gate that cannot fail is not a gate.** The candidate expense reading was
  checked by the form's own arithmetic — F + G against the stated total — and
  seven scanned returns read NIL against a Commission figure while passing it,
  because 0 + 0 makes 0. The check can only fail on a document where something
  was found. Ask of every gate: what reading makes it pass while being wrong?
  (2026-09-26, C451 d.)

- **Each false-positive storm names the next narrowing; don't guess two steps
  ahead.** "Is there money on this page the reader missed" fired on every ACT
  return (a count of 10,000 households, a $120 itemised row). Narrowed to the
  declaration page, it fired again (the donations threshold in section 2).
  Narrowed to section 3, it is right. Each cut took minutes because the corpus
  said which numbers were not totals. (2026-09-26, C451 d.)

- **A source file and its import can disagree.** Two edits inside the same
  second left a `.pyc` whose mtime and size still matched, so the interpreter
  reused it: the file said `EXPENSE_SCHEMA = 5`, `ast.parse` of that same file
  said 5, and `import` said 4 — and a background pass had inherited the stale
  module. When behaviour contradicts the source, check the import before the
  logic. (2026-09-26.)

- **`TaskStop` kills the wrapper, not the work; `ps -C python3` cannot see a
  venv.** Three readers ran on the same corpus for half an hour, all writing
  one log, because a 4h38m process from before a compaction had twice been
  recorded as dead. List by full command line and kill by PID. (2026-09-26.)












- **A field whose rule has changed must be rewritten by the new rule, including
  to nothing.** A reading is MERGED into its stored predecessor, so a key the new
  rule leaves unset keeps the old rule's value. `expenses_unclaimed` was written
  only when a figure was found, so twelve 2023 ACT returns still carried $1,500.00
  and $10,000.00 — the DONATIONS threshold and a household count — from a schema
  that read the whole page. Harmless for as long as only the reader consulted the
  field in memory; twelve false refusals the instant a re-gate read it back off
  disk. Declare every derived field at the top of the function that derives it.
  (2026-09-26.)

- **A version field belongs to whoever did the work.** The re-gate stamped
  `expenses_schema` with the reader's constant, which made the re-read selector —
  keyed on that version — skip the 34 readings the re-gate had just touched. A
  pass that ran no reader may not claim the reader's version. (2026-09-26.)

- **A guard that reads a version can disarm itself.** Adding the fossil floor to
  `unclaimed_refusal` meant it consulted `expenses_schema`, and the reader's
  working dict did not carry one — so the live guard would have declined to fire
  on every document while every unit test still passed, because the tests called
  the rule directly. Third instance of this class in two days: when a predicate
  starts reading a new field, the caller that is not a test is the one to check.
  (2026-09-26.)

- **A refusal is a fact, not a sentence.** A reading that ABSTAINS because the
  form gave too little to check and a reading this pass REFUSES to believe both
  write `consistent = None`; the difference lived only in English, in the note.
  So the register's loader could not tell them apart and published Diana
  Burgess's stated 0.00 out of a reading refused precisely because her page
  prints 4,207.19. The guard had been running correctly and changing nothing
  downstream for a day. **When a check can decline for two different reasons,
  the reason is part of the result** — and the component that decides it is the
  one that records it. (2026-09-27.)

- **A refusal is not a disagreement.** Scoring a refused reading against the
  authority counted it as a mismatch, which is a claim that we read something
  and it differed. Nothing was compared. 2023's disagreements fell from 16 to
  13 and 2020's from 52 to 49 by removing comparisons that never happened.
  (2026-09-27.)

- **A gate may not fail on documents the estate has blinders on.** The nightly
  derive exits 1 on 51 sum-check problems, 17 of the 20 it prints being 2011 and
  2014 returns — and ruling 347 says pre-2019 is kept, never worked, and NEVER
  COUNTED AS A GAP. Only 3 of the 20 are in window. A gate whose red light is
  dominated by out-of-scope rows stops being read. (2026-09-27.)

- **A constant the work cannot reach is a constant the work will not obey.**
  `WINDOW_FROM` lived in `query.influence.base`, the SERVING layer, while
  `registers` sits underneath it — so the nightly derive could not read it
  without inverting the dependency and simply did not, failing its gate on 2011
  and 2014 returns for a year ruling 347 says cannot be a gap. Put a rule that
  binds the WORK at the bottom of the stack and let the surface bind upward.
  (2026-09-27.)

- **An equivalent mutation is a dead branch.** `in_window` opened with
  `if year is None: return False`, and removing it killed no test — because
  `int(None)` already raises into the except below. Code no test can
  distinguish from its absence is code that will be trusted to do something it
  is not doing. Delete it or make it matter. (2026-09-27.)


- **`except: return None` makes a broken query indistinguishable from an honest
  answer.** A validator queried `er_merges`; the table is `entity_merges`. The
  bare except turned that into "no such merge", which is exactly what a real
  missing row returns — so the wrong table name survived a live check against
  production. A missing ROW is None; a database that will not answer raises.
  (2026-09-27.)

- **A label map over a table is a truncation you will forget you chose.** The
  same validator built `{merge_id: label}` by walking every merge class at 5,000
  rows each; the `auto` class holds 2,074,700. Slow, and wrong in a way no test
  would show: a merge outside the top 5,000 of its class silently could not be
  commented on. A primary key deserves a lookup, not an index built in memory.
  (2026-09-27.)

- **One store per QUESTION, not one per surface.** Two comment ledgers already
  existed on two review tabs, and a third would have made "what has Arthur said
  about this?" a question with three answers. A reviewer cannot audit what he
  cannot find again, so the subject is a field, not a file. (2026-09-27.)

- **Ask who has to reach it before asking where it belongs.** A review-comment
  store was built in `pi.pages` (the product on :8300), moved to `query` (which
  the console may not import at all), and only then to `registers`, which is
  underneath every surface that needs it. Three placements in one day for one
  module, and `WINDOW_FROM` was the same mistake that morning. The dependency
  direction is the design; the package name is a consequence. (2026-09-27.)

- **Re-export copies; alias shares.** Keeping an old import path alive with
  `from new import *` COPIES module-level state, so patching one name leaves the
  other pointing at the real file. For a module holding a path to a live ledger
  that is not a style question — it is how test writes reach production data.
  `sys.modules[__name__] = real_module` makes both names one object.
  (2026-09-27.)

- **A doctrine test can outlive its doctrine, and it fails silently in a suite
  nobody runs green.** `test_no_review_decision_surface` asserted no `/api/er/`
  route existed; a ruling had reinstated that queue six days earlier, so the test
  had been red ever since and read as "the console suite is just red". A blanket
  ban on a URL prefix cannot tell a READ from a DECISION. Assert what a route may
  DO. (2026-09-27.)

- **A shared fixture belongs at the root, not in whichever directory last got
  caught.** The review ledger was polluted by the PI suite, fixed in
  `data-layer/pi/tests/conftest.py`, and polluted again the same day by the
  console suite — which has no conftest. A guard that protects live data goes
  where every suite inherits it. (2026-09-27.)

- **A 404 body reads as a working page to a check that only counts errors.** A
  render probe reported 22 characters and **zero page errors** on all six routes
  it visited, because it was asserting against `/pi.html` and the product's entry
  is `/`. Nothing threw: there was no JavaScript to throw. `pageerrors == 0` is
  evidence that a page did not break, never that it loaded. Assert a floor on
  what was DRAWN as well. (2026-09-28.)


- **"Is anything waiting in here?" is a question about the STORE, not the
  surface.** Asked to remove four review tabs unless something in them needed
  reviewing, the answer came from each queue's own numbers: identity asked 0
  verdicts of 128 groups because a ruling had dissolved them all, the returns
  tab's 8 open rows were all out-of-scope parties, the corroboration queue had 0
  open questions — and **gold tier held 605 in-scope cells, 11 of them disputed
  readings**. Three of four were safe to remove and the fourth was the most
  valuable queue on the product. A surface with a queue behind it says nothing
  about whether the queue is empty. (2026-09-28.)

- **Deleting a file to tidy up a wrong build broke a live bundle git could not
  restore.** `gui/dist-product` is gitignored AND served, by the query app on
  :8100. Built the wrong target, removed the stray CSS, and took the :8100
  product's stylesheet with it. Gitignored does not mean disposable — it means
  git will not bring it back. (2026-09-28.)

- **A many-to-many alias is evidence a NAME is present, never that an ENTITY is
  the same one.** Resolving approved spellings through `alias_link` proposed
  folding twelve different men — Michael Gerard, James, Sean, Joseph, Gerald,
  Grant, Craig, Terrance, Bruce, Denis, Andrew and Alan SULLIVAN — into one
  `Michael Sullivan`, because each legitimately carries the short surface form in
  prose. Four Warren Lewises and four Graeme Edwardses came with them. The arm
  was added for a good reason (matching `entities.name` only had reported "no live
  entity" for Dame Jenny Gibbs, who is in the graph with 117 mentions), so the fix
  is the distinction and not the removal: one arm answers "is this name present",
  the other "which entity IS this name", and only the second may pick a merge
  target. **Read the rows a derivation produces before applying it** — 40 pairs
  looked like success. (2026-09-28.)

- **An approval and a rejection are not symmetrical, so they cannot reach the
  machinery the same way.** An approved fold is recoverable: a better rule may
  find it later and be right. A rejection is not, because the pairs a human
  refuses are exactly the ones where every mechanical signal points the wrong way
  — one surname, one address, one filed return. So an approval may be a proposal
  awaiting a commit, while a rejection has to be a STANDING REFUSAL that binds
  without being asked. Storing both as "a decision" loses the half that cannot be
  rederived. (2026-09-28.)

- **A guard belongs at the chokepoint every path passes, not on the queue one path
  reads.** A refusal recorded on `er_candidates` would have blocked Splink and
  left the healer's twelve direct `merge_entities` folds free — and the healer is
  the arm that runs every two hours. Count the call sites before choosing where to
  put the check. (2026-09-28.)

- **A boundary test that fails your new code may be right.** `merge.py` is pinned
  to exactly two public functions — "the EXECUTOR: no guards, no scoring, no
  waves" — and three new names broke it. Moving the lookup into its own module
  satisfied the pin and produced the better design; widening the pin would have
  produced neither. The reflex to edit the assertion is the thing to catch.
  (2026-09-28.)

- **An append-only ledger has a LAST row, and that is the verdict.** 147 rows,
  113 ids, and three of them rejected and then re-recorded as abstained four hours
  later with "too hard to tell, we need corroborating information". Reading every
  row as live would have installed refusals their author had withdrawn. Where a
  ledger holds more than one question and no field says which (two surfaces wrote
  this one), infer it EXACTLY — `fold(name) == core` — never by a heuristic like
  "the key is lowercase". (2026-09-28.)

- **A mutation the gate survives condemns the ASSERTION, not the mutation.**
  Drawing a nine-band stacked area, the check was "no two bands share a top
  edge" — and overlaid bands, every one drawn from the axis, have nine different
  top edges, so the mutation passed and the chart would have shipped as nine
  overlapping areas. The assertion had to name the property the shape actually
  has: at the last year each band is one interval and the intervals TILE, base to
  top, from the axis to the plot's ceiling. The reflex to read a surviving
  mutation as "the code was fine anyway" is the failure; a mutation that changes
  the ink and leaves the gate green means the gate was never watching the ink.
  Write the assertion so that the wrong version of the drawing is the one thing it
  cannot accept. (2026-09-29.)



- **A preflight below the thing it guards is not a preflight.** It reads like
  one, it is named like one, and everything it was built to prevent has
  already happened by the time it runs. Three in one day (2026-10-05):
  `embed_articles` called `modelgate.policy_preflight` AFTER connecting to the
  database, so a box with no `V3_DSN` died on the connect and never reached the
  guard built for exactly that (caught only because a test of mine asserted the
  exit text and got `Connection refused`); `extract_fleet` ran its connection
  preflight AFTER the model warm, which is **2.41 GB of VRAM loaded and thrown
  away** to learn the fleet could not have started; and `era_cutover`'s
  died-phase check sat BELOW the "no halted phase" refusal, so the refusal it
  informs could never see it. **Grep the guard's call site and the first line
  of what it protects, and assert the ORDER in the test** — the ordering is the
  whole gate, and nothing about the code's appearance reveals it.



- **A test that sets the state by hand proves the refusal and not the write.**
  The era-manifest `running` marker was asserted by writing the marker in the
  test and checking that a resume refused — which it did, correctly, and
  **deleting the code that writes the marker left all 43 tests green.** The
  half that matters is the half no fixture can stand in for: drive the real
  phase and read the manifest from inside it. Whenever a test supplies the
  precondition, ask which side of the contract is now unasserted.
  (2026-10-05, C034.)

- **Read a published thing back more than once before calling the publish
  failed, and print the gate's failure lines rather than its tally.** The
  release read `SNAPSHOT.json` once, immediately after the flip, so an edge
  cache that had not caught up was indistinguishable from a bad deploy — it
  now retries to a three-minute deadline. And its refusal printed the gate's
  LAST line, which is the gate's summary count, so the one thing a person
  needed (which gate, and why) was the one thing withheld; `_why()` prints the
  lines starting fail/error/refus instead. (2026-10-05, C510.)


- **AN ARM BELOW THE `__main__` GUARD NEVER RUNS, AND THE BOARD PRINTS A COUNT
  THAT SAYS SO.** `tests/test_invariants.py` has TWO collection boundaries and
  both read `CHECKS` at the moment they execute: the `parametrize` decorator
  fixes the pytest view, and `if __name__ == "__main__": sys.exit(main())` RUNS
  THE BOARD — which is how the file is used in production
  (`ops/production/audit-tick.sh` execs `python tests/test_invariants.py`).
  Execution never returns from `main()`, so **every arm defined after that line
  is never registered at all.** On 2026-10-06 the guard sat at line 3090 with
  three arms below it: the board ran **58 of 61**, and **T7.59 — added the day
  before, and reported green — had never run once.** Every board state file
  carried `checks: 58` and nobody compared it to the number of `@check`
  decorators.
  **The test written to prevent this was itself the adjacent check**: it
  compared the `@check` declarations in the source against `CHECKS`, and both
  are complete on IMPORT, so it was green throughout. It asked whether the arms
  were REGISTERED, never whether anything would RUN them. It now asserts three
  counts that fail independently — declared == registered, the
  PARAMETRIZE DECORATOR's own captured list == registered (read from the mark,
  not the session, or a `-k` filter makes the clause pass by deselecting what it
  is about), and the `__main__` guard is the LAST statement in the file. A
  2026-10-04 note had already fixed the pytest half of this and left the script
  half, because it reasoned about the script path instead of measuring it.
  **Of any suite that reports a tally, ask what the tally is a tally OF, and
  compare it to something counted a different way.** (2026-10-06, C058.)

- **A RESUME SKIPS EVERY GATE BELOW ITS RESTART POINT — re-run the ones whose
  answer can change while the work is stopped, and NOT the ones that are
  memory.** `era_cutover` resumes with `for name in PHASES[start:]`, so an era
  that halted anywhere after `preflight` never re-ran it — and the
  ruled-defaults check lives there (ruling 148: *a deviation is a decision,
  never an accident*). The run path already KNEW the ground had moved:
  `env_amendments()` exists to report that the environment changed since the
  era was written, logs it, and then the check that would judge that change
  never ran. **The lazy fix — re-run the whole preflight — is wrong, and
  wrong in an instructive way:** that phase also snapshots `baseline_reds`,
  the board as it stood when the era was FIRED, so the harness can gate on "no
  NEW red". Re-snapshotting on resume would adopt any red that appeared *while
  the era sat halted* as the new normal, turning the gate's own memory against
  it. So the rule is a question per check: **can this answer change while the
  work is stopped, and is it a MEASUREMENT or a MEMORY?** Measurements get
  re-run (the ruled defaults; whether the graph is still a writable primary,
  because a failover can happen during a halt); memory is preserved; expensive
  build checks stay keyed to the repo head, which `launches[]` already records.
  And the guard runs BEFORE `halted_at` is popped — a refusal placed after it
  would clear the halt and then decline to proceed, so the next `--resume`
  would be rejected for having nothing halted. The guard would have destroyed
  the state it exists to protect. (2026-10-06, C026.)

- **A GATE WHOSE RECORDER DOES NOT EXIST SKIPS POLITELY FOREVER.**
  `test_throughput_gate.py` judges a draining fleet against ruling 144's CPU
  floor by reading `var/audits/era5-perf.jsonl` — and **nothing in the repo had
  ever written that file.** The only mention of it anywhere was the test that
  read it: the recording was an ad-hoc shell loop during era 5, it stopped on
  2026-09-02 18:02, and it left no way to repeat itself. The gate had judged
  nothing for over a month and could not have, while the card asking to
  "re-record" named an instrument that did not exist. **The skip was honest and
  that is what made it invisible** — it said "recording stale, no live drain to
  judge", which reads as a quiet period rather than a missing producer. Two
  fixes, and the second is the durable one: the recorder is tracked
  (`ops/fleet_perf_record.py`), and it runs **with every extraction tick**
  rather than only alongside an era wave — the difference between a gate fed by
  somebody remembering and a gate fed by the work itself. Also: the gate's path
  was pinned to `era5`, so any recording made after that era would have been
  invisible to the gate that asked for it. **Of every skipping gate, ask what
  WRITES the thing it reads, and when that producer last ran.** (2026-10-06,
  C002; sibling of the recovery runbook pointing at a script that was gone,
  C279 — a consumer outliving its producer.)


- **A WITHDRAWN JUDGMENT MUST STOP BEING EVIDENCE, NOT JUST STOP BEING SHOWN.**
  `donor_anchors` has carried `withdrawn_at` and a withdraw path for a month,
  and every serving read filtered it — so the feature looked finished. One read
  did not: `_person_context` scores a NEW candidate by asking whether its
  companies are already anchored as donors, and a judgment somebody had
  withdrawn still answered yes. A retracted accept went on corroborating fresh
  ones, which is the auto-executed-verdict mode (*the wrong answer teaches
  itself*) arriving through the one door nobody watches — the inside of the
  judgment pass. **Withdrawal has to undo a judgment's CONSEQUENCES or it only
  hides the row.** The census that found it is the shape to copy: every
  `FROM/JOIN` of the table, each one classified as filtered, deliberately
  unfiltered (a migration, an audit) or a defect — 28 statements, 22 filtered,
  5 exempt with a stated reason, 1 wrong — and the exemptions are now a NAMED
  list that a test fails on when it grows. (2026-10-06, C113.)



- **AN EXCLUSION NOBODY CAN EXPLAIN IS DRIFT, AND "RETIRE IF 0" HAS TO ACTUALLY
  BE RUN.** `_PRESS_EMPLOY_EXCLUDE` was one bare NZBN in a WHERE clause. A
  2026-09-03 audit could not explain it, lifted it into a named constant with a
  comment saying the next audit should retire it if it still matched nothing —
  and there it sat, now looking like knowledge somebody had rather than a
  question nobody had answered. **Naming a thing you cannot justify makes it
  harder to remove, not easier**, because the comment reads as provenance.
  Measured a month later: **0 of 623,551 rows**, the same answer as the day it
  was named. Removed from the query, the constant AND the import — a constant
  left behind is re-adopted by the next person who needs "the exclusion list".
  When you defer a deletion, put the MEASUREMENT in the deferral, not the
  intention. (2026-10-06, C117.)

- **PER-ARTICLE ISOLATION TURNS A TOTAL FAILURE INTO A CLEAN EXIT — SO A RUN
  THAT PRODUCED NOTHING MUST SAY SO.** The standing extraction tick ran
  `ok=0 fail=45 mentions=0 claims=0`, the shard fleet exited 0, the systemd unit
  Finished, and no board arm said anything. The per-article `except` is right —
  one bad document must not stop a drain — and it is exactly what hid a
  `KeyError` that failed EVERY article for **sixteen days**. The fix is one
  branch and it is narrow on purpose: red only when every article failed AND
  there was at least one, because a run with no rows is idle and a run with
  some failures is the isolation doing its job. **Wherever a loop swallows
  per-item errors, ask what the loop reports when it swallows all of them.**
  (2026-10-06, C512.)

- **A BINARY `else` STANDING IN FOR A VOCABULARY IS HANDLED FOR ROUTING AND
  UNHANDLED FOR COUNTING.** `signals.record` bucketed a note with
  `drops if nt.channel == "drop" else sigs` — so anything not `drop` was a
  signal — and then counted it under `nt.channel`, its REAL channel, while the
  read asked for the literal `"signal"`. The contract declares two channels;
  the estate emits three (28 `drop`, 5 `signal`, 1 `rewrite`, the last added by
  C247 on 2026-09-20). That one note bucketed as a signal, counted as a
  rewrite, and `counts[("signal", k)]` raised KeyError. **The same value was
  read two ways, three lines apart** — once as "is it a drop", once as "what
  is it" — and only the first way had a default. Count by the BUCKET you put a
  thing in, not by the attribute you used to choose it; and when a vocabulary
  grows past the branches that read it, the branches are the thing to change.
  (2026-10-06, C512.)

- **AN AUTHORISATION THAT DOES NOT STATE ITS AGE CANNOT BE DOUBTED.** The merge
  drain runs only while a gate artifact says the refuter passed, and
  `refuter_measured()` returned `"b4b-refuter-gate-2026-08-22T042025Z.json
  catch=0.846 …"` — the same sentence at one day old and at **forty-five**,
  which is what it was. `merge_refuter.py` had three commits in the gap. They
  turned out to be endpoint plumbing, so the old measurement did still measure
  the judgment that runs, **but nothing had checked that and the log could not
  have shown it.** A measurement is a claim about a moment; carry the moment in
  the sentence the record quotes, so staleness is legible without anyone going
  to look. Refusing on a CHANGED subject is a fingerprint, and a bigger job
  (C513) — stating the age is the precondition for anyone wanting one.
  (2026-10-06, C260.)

- **A RELATIVE PATH INSIDE A GATE MAKES ITS ANSWER DEPEND ON WHO STARTED THE
  PROCESS.** `GATE_GLOB` defaulted to `var/audits/b4b-refuter-gate-*.json`, so
  the same function returned "authorised" from the repo and **"no full refuter
  gate run recorded" from anywhere else** — which is a skip, and a skip is
  silent. It had never misfired because `querynz-crawler.service` and the era
  orchestrator both happen to run with the repo as their working directory: a
  correctness resting on a coincidence of configuration, one `WorkingDirectory=`
  away from a lane that stops merging and says nothing. Anchor every path a
  gate reads to the repo, never to the caller. (2026-10-06, C260.)

- **A DETECTOR THAT READS ANOTHER PACKAGE'S LOG FORMAT MUST BE PINNED TO THAT
  FORMAT BY A TEST.** `era_cutover.drain_verdict` scrapes the healer's
  `merge drain …` lines so the era record states whether the drain ran. Reword
  the healer's line and the scraper returns "no merge-drain line" — a drain that
  RAN recorded as absent, which is worse than the truncation it was built to
  fix. The test therefore extracts the log format strings FROM `crawler.py` and
  renders them through `%`-substitution, so a rewording fails in the suite
  rather than in an era. Proven by rewording the line and watching it go red.
  **Where a reader and a writer live in different packages, the coupling is the
  thing to test — not the reader's idea of the writer.** (2026-10-06, C260.)

- **A SURFACE MUST SAY HOW CURRENT IT IS, FROM THE DATA AND NEVER FROM THE
  CLOCK.** The declared-donations panel had no `as_at`, so a reader could not
  tell "complete to last Monday" from "stopped updating in June" — and neither
  could Arthur, which is why the question was asked of a panel that was in fact
  current. The freshness line is now the newest declaration HELD. A `now()`-based
  one would have read healthy forever after the feed died, which is the same
  silent-success family as a lane that exits 0 having landed nothing.
  **Every surface that can fall behind states the newest thing it holds.**
  (2026-10-06, C514.)

- **A JOIN KEY YOU DID NOT NORMALISE INVENTS A DEFECT THAT IS NOT THERE.** Twice
  in two hours, on two different cards. Reconciling the Commission's table
  against `donation_disclosures` on `source_file` reported **36 declarations
  missing**; the rows were there, keyed to the capture's HTML name because the
  table — not the scan — was their source. Re-keyed on donor and amount: **zero
  missing**. Then the same shape again: one side stored
  `2026-20k+-donations__M_G_Jones_12_June_2026.pdf` and the other
  `M_G_Jones_12_June_2026.pdf`, which reported **43 orphaned documents worth
  $2.03M**; on normalised basenames it was **8 worth $242,297**, and only one of
  those was real. Both times the wrong number was large, alarming and about to
  be reported. **Before believing a set difference, print one member of each
  side and look at it.** (2026-10-06, C514.)

- **WHEN A FLAG MUST BE HONOURED IN THIRTY PLACES, THE DELIVERABLE IS THE CENSUS,
  NOT THE THIRTY EDITS.** `superseded_at` had to be excluded by every read of
  `registers.donation_disclosures` — 31 of them across 13 files, with no shared
  predicate and no view, in a schema where 37 sites already repeat
  `line_kind = 'name'`. The edits are mechanical; what they lack is any way to
  prove they are ALL done, and "the serving join excludes it" is the kind of
  claim that is usually PARTLY true, which reads as done. So the census came
  first, failing with all 29 names, and the edits turned it green one file at a
  time. **A SHORTCUT THAT LOOKS CHEAPER MUST HAVE ITS BLAST RADIUS MEASURED:**
  renaming the table and serving a filtered view under the old name is one change
  instead of thirty — and a view is absent from `pg_tables`, which drives
  `ops/db_maintenance.py`, while `pg_class` drives the console's row counts and
  `ops/offsite_restore.py`, and `registers/catalog.py` carries the table with a
  row floor. Wider than what it avoided, so it was dropped. Count the reads, then
  count what the clever alternative touches. (2026-10-06, C517.)


- **INSTALL THE WATCH WHILE THE POPULATION IS STILL CLEAN.** C081 asked for a
  reconciliation of `claims.qualifiers->>'ref'` against live register refs,
  because a re-derive TRUNCATEs a register and a parse regression can leave claims
  citing rows nobody holds. Measured before building: 143 of 143 and 846 of 846
  matched, **zero orphans** — so there was nothing to repair, and the temptation
  is to close the card on the measurement. That would throw away the only cheap
  moment: the arm costs two small queries today (989 refs), the firing path can be
  proved by fixture while the live answer is green, and the next regression is
  found by the board instead of by a reader following a citation to nothing. **A
  card that measures clean is not a card with nothing in it — ask whether anything
  would notice if it stopped being clean.** (2026-10-06, C081.)

- **AN ARM READS ITS OWN SUBJECT OUT OF THE WRITER, SO A NEW ONE IS WATCHED
  WITHOUT ANYBODY EDITING THE BOARD.** `register_claims` stamps 13 different
  `register` values and only two carry a `ref`. A list of those two in
  `test_invariants.py` would quietly stop covering the third that somebody adds —
  the arm would stay green over a population it no longer knew about. So T7.63
  parses the writer's own `json.dumps({...})` blocks BY BRACE BALANCE (a
  single-line grep found 4 of 9 in C515, because a qualifier dict wraps), and a
  register whose table is missing is a finding rather than a skip. When the arm
  can find no subject at all it REDS, because that means the writer was reworded
  and the gate has silently lost its job. (2026-10-06, C081.)

- **A GATE THAT ASSERTS LESS THAN ITS DOCSTRING PROMISES WILL BLOCK THE RELEASE
  AND BE RIGHT.** `pi_home_recent` said it checked "the rows are in non-increasing
  date order, **by the same parsed date the API ordered on**" and in fact checked
  `date_iso` — one specific date, hardcoded. When C514 moved the panel's sort to
  the declaration date, the gate refused `ftm-release` every firing and
  followthemoney.nz sat **thirteen hours stale carrying a figure that had already
  been corrected**. The gate was doing its job; the drift was between its words
  and its code. Two things follow. **Where a gate's docstring says it derives
  something, it must derive it** — or say the field it checks. And the cost of a
  gate disagreeing with its subject is not a red line, it is everything
  downstream of the gate. (2026-10-07, C518.)

- **TELLING A RANKING CHANGE FROM A LOSS IS THE DROP-GUARD'S HARDEST JOB, AND
  MINE TOOK AN HOUR.** The release compare reported a donor's total falling
  $4,000 and its page gone. I reached for three explanations before the right
  one — a ruling about party transfers, a transient read, a fold — and each was
  plausible, cheap to believe, and wrong. It was `LIMIT 1500` in the picker
  query, applied BEFORE folding: new declarations pushed the boundary above a
  $4,000 donor. **The row was never lost** — register, donor endpoint and
  electorate race all still served it. The discipline that got there was
  refusing to run `--allow-drop` until every one of the four movements had a
  named cause, and the tell was that the two RISES matched the three
  declarations that had arrived overnight. When a guard fires, account for every
  row it names, including the ones that moved the other way. (2026-10-07, C521.)

- **A DROP-GUARD MUST ASK THE SERVING LAYER, NOT RECOMPUTE THE FIGURE.** The
  release compare blocked on any donor total falling, which was right while a
  fall meant data had gone missing — and wrong once two routine things began
  making totals fall: a supersession (the Commission amends a declaration) and
  the picker's `LIMIT 1500`, applied before folding, so a donor loses its page
  when OTHER donors gain money. The temptation is to recompute the donor's true
  total from the register and compare. **Do not:** the published figure is the
  sum of folds, the open-year rule, ruling 277's scope and the display-name map,
  and a second implementation of it is a second lane computing one quantity.
  Ask the publisher the generator read. `published == served` is a faithful
  build and a real change; `published != served` is the BUILD losing something,
  which is the only case worth blocking; and **"could not be asked" is never
  agreement** — an unreachable publisher must fail closed or the guard becomes a
  rubber stamp exactly when it matters. (2026-10-07, C521.)

- **ONE EVENT IN TWO BUCKETS IS JUDGED TWICE AND THE HARSHER VERDICT WINS.** A
  donor page that VANISHES is both a fall (its total went to zero) and a gone
  page. The first version of this fix processed both lists, so the page the
  change was written to ALLOW came out as `published $0 but the publisher serves
  $4,000 — the BUILD lost this`. A missing page is a COVERAGE question and a
  present page with a smaller number is a FIGURE question; they need separate
  branches and the one event must enter only one. Caught by the test written for
  the case, which is the only reason it did not ship. (2026-10-07, C521.)

- **A CROSS-BOX CLASSIFICATION CANNOT BE ASSERTED ONCE EITHER SIDE'S EVIDENCE HAS
  ROTATED.** `test_the_real_survey_calls_the_2026_09_17_cut_a_SITE_event` failed
  with `['node1'] != ['node1', 'node2']` and the code was right: node2's journal
  horizon had moved to 2026-09-17T20:39:55 — PAST the 09:08 boot — while node1's
  was still 2026-08-22, so only one box could still see the event and `survey()`
  honestly called it ONE BOX. The test's guard skipped only when NEITHER box held
  it, which is the narrower half of the same condition. **Where a verdict is
  reached by comparing two sources, a live-data test of that verdict must skip the
  moment EITHER source loses the evidence** — and say which one, with the
  horizons, so the skip is a fact and not a shrug. The rule itself belongs on a
  fixture, where retention cannot reach it. (2026-10-07, C058's arm.)


- **A RETRY'S BOUND COMES FROM WHAT THE WORK COSTS, NOT FROM WHAT LOOKS TIDY.**
  `querynz-ref-wikidata` fires quarterly and had no `Restart=` at all, so a
  `ConnectTimeout` on 2026-10-05 cost three months of a stale corpus. The obvious
  fix is a handful of retries — and it is wrong here: the unit's own header says
  the dump is **103.14 GB** and that the quarterly cadence is a RULING made on that
  number, because the box egresses over a satellite link. A ConnectTimeout
  transfers nothing, so retrying it is free; a failure after 80 GB is not, and
  systemd cannot tell the two apart. So the burst is **2** — exactly one more
  attempt — and the unit says why, because the next reader's instinct will be to
  raise it. **Read what a lane COSTS before deciding how often it may fail.**
  (2026-10-07, C525.)

- **A DECISION THAT TAKES EFFECT "AT THE NEXT BUILD" IS NOT IN FORCE, AND NOTHING
  IS COUNTING THE DAYS.** Era-5 rule 2 landed the Beehive metonym block as two
  `gazetteer_blocklist` rows on 2026-08-31, and the record says it was *"verified
  through `gazetteer._blocklist()`: both blocked"*. That verified the TABLE held
  the rows. Whether the automaton excludes the form is a different question, and
  its answer was no: this box's `gazetteer.pkl` was built **2026-07-30**, so the
  block has never once been in force. **399 of the 400 claims on the café entity
  were created AFTER the decision was filed, the most recent the morning this was
  found** — five weeks of a defect everyone believed was fixed, because the
  record said "effect lands at the next gazetteer build" and nothing ever asked
  whether that build had happened. A decision whose effect waits on a rebuild
  needs an instrument that reports it as PENDING, with the artifact's build date
  beside the decision's date; otherwise "landed" and "in force" become the same
  word in the record, and only the first is true.
  *Paid for by:* 2026-10-07 (C239), five weeks after 2026-08-31.


- **`ps` TRUNCATES TO THE TERMINAL WIDTH OF WHATEVER STARTED THE PROCESS, SO A
  PROBE THAT PARSES ITS OUTPUT ANSWERS DIFFERENTLY DEPENDING ON WHO ASKED.** T7.66
  reads the live model servers out of the process table — deliberately, because the
  gateway builds its backend list from the unit files and an arm consulting the same
  pair would agree with it by construction. The probe ran `ps -o cmd= -C
  llama-server` and matched `--port (\d+)`. From a wide shell it found four servers
  and passed. Under pytest, **the same box in the same second**, every line came back
  cut at about 80 columns, `--port` had fallen off the end, nothing matched, and the
  arm reported *"NO llama-server is running on node2 — the fleet is down"*. One
  missing `-ww` was the whole difference between a working gate and a confident lie,
  in the direction that matters least: it would have cried outage on a healthy
  fleet, and it would equally have reported "nothing to compare" on a dead one
  before the MANIFEST cross-check was added.
  **So: any `ps` a gate parses carries `-ww`, and better still, read
  `/proc/<pid>/cmdline`, which has no width at all.** The general form is the one
  this estate keeps paying for — *an instrument whose answer depends on the
  environment that invoked it is not an instrument* — and the tell was available for
  free: the same check disagreeing with itself between two ways of running it.
  *Paid for by:* 2026-10-07 (C413), caught only because the arm was run both ways
  within a minute.

- **READ THE WRITER TO LEARN WHAT IT INTENDS; READ THE DATA TO LEARN WHAT IS THERE.
  THEY ARE DIFFERENT QUESTIONS AND THE SECOND ONE IS USUALLY THE ONE ASKED.** T7.25
  claimed "page-regenerated register feeds are idempotent" and watched a hardcoded
  pair, `("worksafe_enforcement", "disclosure_statements")`, while the graph holds
  **fifteen** register families — so the five duplicate `courts` claims C063 was
  raised on were outside its population and nothing could ever have found them. The
  arm had the right idea and the wrong universe. Widening it, I reached for the rule
  that fits the shape — *an arm reads its own subject out of the writer* — and
  brace-balanced `register_claims.py`'s `json.dumps({...})` blocks the way T7.63
  does. **It found 8 of the 15, and called `gazette_celebrants` (97,999 claims) and
  `gazette_insolvency` (490,484) unkeyed when every row of both carries `row_id`**:
  those qualifier dicts are not written as a literal the parse can see. The widened
  arm would have redded two clean families on its first firing. Deriving each
  family's key from the CLAIMS instead is one query, has nothing to rot, and reports
  a half-migrated family as the mixture it is. The earlier rule is right about
  discovering what a writer MEANS to emit; it is wrong as a way to discover what the
  corpus CONTAINS.
  **And the card's prescribed remedy was wrong, which is worth as much.** C063 said
  "quarantine the five". Claims are a REGENERATED layer here: `feed_courts`
  delete-and-replaces by `register` + `row_id`, so quarantining five rows would have
  tombstoned the symptom and left the cause emitting them. The cause was one run
  naming a consolidated appeal's single respondent at three caption positions —
  `[2025] NZCA 278`, NEW ZEALAND POLICE against each of three appellants, three
  register rows collapsing to one entity and three identical claims. Fixed at the
  gate and PROVEN by running the real feed inside a rolled-back transaction: 273
  claims with 5 duplicates became 268 with 0, `parties_collapsed: 5`. When a card
  names a remedy, check which layer the defect lives in before performing it.
  *Paid for by:* 2026-10-07 (C063).


- **A PROBE BUILT TO REPLACE WRITTEN-DOWN KNOWLEDGE HAD WRITTEN-DOWN KNOWLEDGE AT ITS
  CORE — AND A PROBE NOBODY EMITS IS A COMMAND, NOT A DOCUMENT.** `ops/stack_probe.py`
  exists for one stated reason: report "what actually runs, PROBED, not recalled from a
  code default or a variable name (which lie)". Its first table was driven by
  `LLM_PORTS = [8000, 8001, 8020, 8090]`, typed once, and it labelled **8000 as "llm@0
  (fleet model, GPU0)"** — a port that binds nothing and has not since at least
  2026-09-22, when C413/C414 found the gateway naming it while the fleet's live card
  served :8020. The same list omitted :8002 (the embedding server) and :8032 (GLM-OCR,
  THE page recogniser since 2026-09-25) entirely. So the instrument against
  doc-vs-reality drift was itself the drift, in its opening table.
  **And for weeks it emitted nothing.** C067 sat at "exists; emission unverified": the
  docstring said *"paste the output into the pre-pass"*, so the generated doc the card
  asked for had never existed, and the probe's answer lived only in whatever terminal
  last ran it. Discovery from the process table and a `--write` that REFUSES on a
  half-probe are both one-line changes; what they cost was noticing that the gap was
  not in the probe's logic but in its inputs and its outputs.
  **Ask of any instrument: which of its facts are typed in, and where does its answer
  go when nobody is watching?**
  *Paid for by:* 2026-10-07 (C067), carded since the Muster-2 homing.

- **"UNVERIFIED" AND "UNSOUND" ARE DIFFERENT CARDS, AND THE FIRST IS CLOSED BY A
  DEMONSTRATION RATHER THAN A REWRITE.** C083 stood for seven weeks as "delete-replace
  register feeds not verified for reader isolation under concurrent timers", and the
  2026-09-19 triage confirmed it on the shape of the code: "`derive.py` carries no
  transaction-isolation or savepoint structure around the delete-replace". True, and
  irrelevant — **`TRUNCATE` is transactional in PostgreSQL and takes ACCESS EXCLUSIVE**,
  so a reader arriving mid-derive BLOCKS and then sees the new rows. It never sees
  zero, and no savepoint or isolation level would add anything. The absent structure
  was not a missing safeguard; it was a safeguard the engine already provides.
  What the property actually depends on is one line of discipline: **nothing may commit
  between the TRUNCATE and the end of the reload**, because a commit there publishes
  the empty register to every reader at once — and with `autocommit=True` the TRUNCATE
  lands alone, which the test demonstrates by running it and watching a reader be
  served 0. All four reloaders already held one transaction. So the card closed on a
  proof and two gates, not a redesign.
  **Before rewriting for a property, check whether the substrate already guarantees
  it** — and then pin the one assumption that would break it, which is rarely the one
  the card names. The 2026-09-19 triage read the code's SHAPE and concluded from the
  absence of a structure; the engine's semantics were never asked.
  *Paid for by:* 2026-10-07 (C083), carded at the Muster-2 homing.

- **AN XFAIL IS A TEST THAT RAN, ASSERTED NOTHING, AND REPORTS AS A DOT — AND NOTHING IN
  THIS ESTATE COUNTED ONE.** Critic 6's "green may mean did not run" has two spellings.
  The skip half was measured and half-ruled: ruling 165 makes a DB-backed skip a RED
  line, and the non-DB skips were printed per suite. The xfail half had no pattern
  anywhere in `ops/test_all.sh`, so a suite could accumulate them and every line of the
  runner's output would read green. First run that counted them, 2026-10-07: **9
  unasserted of 5,459 collected (0.2%)** — 8 skipped and 1 xfailed, the xfail in `ops`,
  named for the first time. Small, and the point is that it could not have grown
  visibly.
  **An XPASS is the sharper one and belongs in the red, not the count:** a test marked
  expected-to-fail that now passes means the reason it was excused has EXPIRED and
  nobody was told. It is the only pytest outcome that reports good news as silence.
  **And a comment that states a false mechanism is worse than no comment.** The first
  version of this change carried one: that `xfailed` had to be matched before `failed`
  or the patterns would collide. They do not — `[0-9]+ failed` cannot match `1 xfailed`,
  because the space is followed by `x`. Four real summary shapes now pin it in a test,
  because the cost of the false version is a later reader reordering lines to preserve a
  constraint that never existed.
  *Paid for by:* 2026-10-07 (C045), carded at the Muster-2 homing, half-ruled as 165,
  and the other half unmeasured for seven weeks.


- **A DOCUMENT-FRESHNESS GATE MUST BITE WHERE THE DRIFT IS MADE, NOT WHERE IT IS
  VISIBLE.** C410's obvious build was a push gate: fail when a SPEC is older than its
  service's code. Measured before building it — `query`'s SPEC 55 commits stale,
  `ingestion`'s 40, `extractor`'s 12 — that gate would have reddened for nearly every
  service on the day it landed and gone on reddening, because the number RISES WITH
  EVERY COMMIT and no single push can clear it. That is the shape of a permanent red,
  and C529 measured what permanent reds do: 11 of 15 board arms red for 4 to 33
  consecutive boards and a daily instrument reduced to wallpaper. **The drift is made by
  the card that changes the service**, so the gate went there: ruling 326's DOCS answer
  must now NAME the SPEC of the service its LOCATION names. One card, one document, one
  decision, clearable in the moment it is owed. The first thing it caught was a card
  closed an hour earlier whose change had falsified four statements in
  `ingestion/SPEC.md` — including an open risk, F3, standing since 2026-08-04, that the
  card had HALF-DISCHARGED without noticing.
  **And the instrument beside it told its first lie within the minute**: reporting
  `research/SPEC.md` as missing all eight template sections and `registers/SPEC.md` as
  missing seven, when both answer the questions under this estate's own earlier headings
  (`Boundaries` for crossings, `Surfaces` for the contract, `Invariants → tests` for
  invariants). It would have sent somebody to rewrite documents that were already
  complete. Census the vocabulary a document actually uses before reporting on what it
  omits.
  *Paid for by:* 2026-10-08 (C410), where the ratchet that remained — the set of
  services with NO SPEC, by name, may not grow — is the only part of SPEC maintenance a
  push can honestly refuse.

- **A LOOKUP KEY IS A FUNCTION, AND THE WRITER AND THE READER MUST CALL THE SAME ONE.**
  `registers.body_aliases` is keyed on a space-and-punctuation-stripped macron fold, and
  three pieces of code produce that key: the exact-name anchor in
  `person._mp_private_positions` (SQL), the seed that writes the rows
  (`ops/seed_body_aliases.py`), and the lookup that reads them
  (`industry._body_alias_lookup`). The first two strip a declared name's trailing
  parenthetical — *"Stay Hawke's Bay Limited (not trading)"* — and the third folded the
  RAW name. So four alias rows existed that no request could ever hit, and nothing
  failed: the lookup simply returned no row and the declared position abstained, which
  is also what it does when there IS no alias. **A key computed in two places is two
  keys**, and when the failure mode of a mismatch is "the same answer as not knowing",
  nothing will ever tell you. Give the key one callable, import it, and assert the three
  users agree in a test that names all three.
  **The same card's other half:** a curated table holding ONE row had been read for
  weeks as an unstarted job. It was a rule nobody had written — of 4,897 declared org
  names that did not anchor, thirty-eight were the SAME NAME as exactly one register
  entity once the table's own key was applied to both sides (`Rocketlab` /
  `ROCKET LAB`, `T & G Global` / `T&G GLOBAL`, macrons, apostrophes, `(No 4)` /
  `(NO.4)`). Before you extend a curated list by hand, fold both sides with the list's
  own key and count what falls out; what remains after that is the judgment the list is
  actually for.
  *Paid for by:* 2026-10-08 (C189), where the four unreachable rows were found by
  measuring what the table WOULD anchor rather than by any test.



- **A MEASUREMENT AUTHORISES THE THING IT MEASURED, NOT THE FILE THAT HAS REPLACED IT —
  AND FORCING THE RE-RUN IS HOW YOU FIND OUT THE GATE NEVER HELD.** The merge drain ran
  on the newest passing refuter-gate artifact for as long as that artifact existed: 45
  days by 2026-10-06, with three commits to `merge_refuter.py` in between. All three were
  endpoint plumbing, so the judgment the gate measured was in fact unchanged — a fact
  nobody had checked. Fingerprinting the judgment-bearing sources (prompt, verdict
  vocabulary, round budget, the source of the refute path) and refusing a mismatch makes
  the drain fail CLOSED, and the first consequence is that every artifact written before
  the fingerprint existed stops authorising anything, which is the point and the cost.
  **Then the re-authorising run FAILED, and the finding is the gate's arithmetic.** Catch
  0.769 against a 0.80 threshold: 10 of 13 `different` cases refuted where 11 are needed.
  August had scored 0.846 — eleven of thirteen — and therefore passed BY ONE CASE. Six
  verdicts moved between the two runs, three in each direction, on an identical
  fingerprint: model variance, not a regression. **One case is 7.7% of the rate, so a
  13-case denominator cannot support a 0.80 threshold against a non-deterministic
  judge** — the authorisation was never robust and a single re-run was enough to show it.
  Before trusting a pass/fail over a labelled set, divide 1 by the size of the smallest
  arm of it and compare that to the margin.
  **And the lane could not tell "I was careful" from "I was unreachable".** With
  `LLM_API_KEY` unset the research lane raises `LocalProtocolError: Illegal header value
  b'Bearer '`; `refute()` turns that into an ABSTAIN, flags it in
  `meta["abstained_on_error"]`, and the gate dropped the flag while recording `rounds`
  and `urls` from the same dict. Every case "abstained" after four retries at exactly
  75.0 s, and the summary would have read `catch 0.0 < 0.8` — a true statement about a
  lane that never ran.
  *Paid for by:* 2026-10-08 (C513), where the fix cost 50 minutes of model time and what
  it bought was the knowledge that the gate had been passing on one coin-flip.

- **OPT-IN PLUS A FLAG IS DISCLOSURE, NOT A GATE — AND THE GATE WAS ALREADY PAID FOR.**
  The standing ER rule of 2026-07-14 is that a register director NAME resolves to a
  person only through a contextual link — co-directorship, a shareholding, or **the
  company itself** referenced for that person — and that *"no shared-company-context, no
  link, regardless of name similarity"*. The tier-2 lane that serves name-matched
  directorships had no such gate for fourteen months. What it had was `include_candidates`
  off by default, `namesake: true` on every row, and a count. All three are honest and
  none of them is the rule: they tell a reader the set contains strangers without telling
  them WHICH rows are strangers, which is the only question the rule answers.
  **The gate cost nothing because the context was already on the page.** The subject's
  DECLARED interests had been fetched four lines earlier for the same request, and a
  company the member filed themselves is the strongest form of the "company itself"
  reference the rule names. Measured over every MP in the reviewed registers: **151
  name-matched candidate directorships, 15 context-linked, 136 namesake-only** — and
  `Jian Yang`, the most contaminated name in the set, goes from 24 rows to 2. The fifteen
  read as obviously right (Cameron Luxton → LUXTON HOLDINGS, Joseph Mooney → MOONEY
  LAWYERS, Maureen Pugh → PUGH CONTRACTING, Vanessa Weenink → WEENINK MEDICAL).
  **Before building a gate, look for a discriminator the request has already loaded**; and
  when a standing rule has no implementation, check whether what stands in for it is a
  safeguard or merely a warning label.
  *Paid for by:* 2026-10-08 (C192), where the card had asked for the gate to be confirmed
  BEFORE tier-2 landed and tier-2 had been live since 2026-08-25.

- **A LOOKUP THAT ASKS THE WRONG REGISTER IS NOT MERELY USELESS — IT IS A NEAR-MISS
  WAITING FOR A LOOSER MATCH.** `disclosure.py`'s `_nzbn_for` anchored departments by
  asking `entities`, the companies bulk, and so anchored **0 of 904** statement rows for
  three months. The companies bulk holds no government agency at all — every
  `entity_type` is LTD / ASIC / NON_ASIC / UNLTD / COOP — and the 98 department-shaped
  names in it are companies, among them **"DEPARTMENT OF CONVERSATION LIMITED"**, one
  letter from the Department of Conservation. The zero was not the symptom of a spelling
  problem; it was the only thing standing between a department and a joke company, and
  the obvious "fix" of fuzzing the match would have crossed it.
  **The triage restated the card in the dangerous direction**: *"no longer 0/58 — 89
  department-shaped organisations carry an `nzbn` key"*. Those 89 ARE the companies. When
  a count goes from 0 to 89, check WHAT the 89 are before recording that the premise is
  stale.
  **The right register was already in the estate** — `bulk.public_sector_entities_core_
  data`, 2,922 rows, every one with an NZBN, which another service already keyed 940 orgs
  on. Three forms against it, each on a unique answer only: the folded name, a COMPONENT
  of the register's own bilingual string (`Te Puni Kokiri (Ministry of Maori Development)`,
  `Oranga Tamariki — Ministry for Children` — the statements file one of the two names
  and the register files the pair), and a trailing generic the statements leave off
  (`Inland Revenue` → `Inland Revenue Department`). **853 of 904 rows, 32 of 58 names, no
  curated alias anywhere** — the register's own spellings of itself, and ambiguity
  abstains (`Te Puni` matches a school board too, so it anchors nothing).
  *Paid for by:* 2026-10-08 (C197), where "the spellings differ" had been the diagnosis
  since 2026-08-24 and the table being asked was the wrong one all along.

- **A CHRONIC RED IS NOT ONE PROBLEM, AND TRIAGING SIXTEEN OF THEM PRODUCED FOUR NEW
  CARDS, THREE FIXES AND ONE ARM THAT WAS ITSELF THE DEFECT.** The board had 67 arms and
  16 red, the oldest red for 36 consecutive boards, and a reader could not tell debt from
  a condition somebody had already decided to live with. The instinct is to reduce the
  count. **The deliverable is a VERDICT, not fewer reds**: ACTIONABLE (an OPEN card names
  the work), STANDING (the red is the correct state until somebody else acts — a ruling,
  or a runsheet item), WRONG (the arm is the defect). Sixteen reds sorted into 9
  actionable, 3 standing, 1 wrong, and FOUR that went green within the hour once read —
  leaving 13 red of 67, every one of them judged.
  **The registry must not become an exemption list**, which is the one way it rots: a
  verdict labels a red, it never silences one. Nothing in the board's pass/fail path may
  read it, the arm still fails, the unit still exits non-zero — and a test asserts
  exactly that, alongside two refusals that keep the registry honest: an UNTRIAGED red,
  and a verdict naming a card that has CLOSED (which means the red outlived its reason
  and nobody noticed).
  **Three of the sixteen were the board being out of date rather than the estate being
  broken.** `querynz-vision-ocr` reds T7.24 for having no DSN — it runs `llama-server`, a
  binary that cannot read one, and it was added after that arm's exempt list was written.
  T7.54's drift was two units never deployed to node1. And T7.19's remaining red is the
  arm's own narrowness: it clears a red when a source is STOPPED, and `_source_stopped`
  reads one registry, so a party-site host with unreadable robots has no way to record
  the stop the ruling requires. **Read every red before believing any of them**: the
  board is a measuring instrument and a fifth of its reds were about itself.
  **And the streaks are readable from the journal, which nobody had mined.**
  `journalctl --user -u v3-audit` carries `PASS`/`FAIL` per arm per run: 23 runs over 19
  days (the journal's retention, not a gap in the timer) say 35 arms have never been red,
  7 have never been green, and 13 of the 67 do not appear at all because they are younger
  than the window. An arm with no history has no streak to read, which is why a verdict
  is keyed on the arm and not on its age.
  *Paid for by:* 2026-10-08 (C529), where the oldest red had been reported 25 times and
  read none.


- **VERIFY ON THE INSTRUMENT THAT RUNS IT. A BOARD ARM THAT PASSES UNDER PYTEST
  IS NOT A GREEN BOARD.** C535 closed on `pytest tests/test_invariants.py -k
  T7.19`, which passed in 116 s. The BOARD still failed, with the pre-fix
  sentence, and it was caught an hour later only because another card happened
  to re-run it. **The board runs that file AS A SCRIPT**, so `sys.path[0]` is
  `tests/` and the repo root is absent; under pytest the rootdir is on the path.
  `ingestion/fetchgate.py` opens `from ingestion import sourcepolicy`, so in the
  board — and only in the board — the import raised
  `ModuleNotFoundError('ingestion')`. **A fix can be correct and unreachable,
  and only the real runner can tell you which.** The same trap is waiting for
  every arm that imports a capture or data-layer module: pytest's rootdir hides
  it, by design.
  **AND THE SILENCE IS WHAT MADE IT COST TWO BOARDS.** The import raised inside
  `except Exception: pass`, so the arm answered "not stopped" and reported a host
  the gate refuses on every request as one we are still fetching. Fail-CLOSED is
  right — a database outage must leave an arm red rather than produce a clean
  board — but fail-SILENT makes "the gate says we still fetch this" and "the gate
  could not be consulted" the same red, and the difference is the entire finding.
  A check that cannot run is not a check that said no, so it reports itself:
  `STOP_CONSULT_ERRORS`, printed on the arm's own line.
  **The diagnosis went wrong once in the same family**: a probe run WITHOUT the
  DSN exported showed the lookup returning None, and for a minute that read as
  the fix having broken it. Get the instrument right before believing its answer
  — and when a test asserts about how a file is RUN, assert on the source, not by
  importing, because the importer is the thing with the blind spot.
  *Paid for by:* 2026-10-08 (C535 addendum), two boards after a green pytest run.

- **A SCREEN ADDED LATER CAN DISABLE A TEST'S SUBJECT, AND THE TEST THEN FAILS AS
  THOUGH THE SUBJECT WERE BROKEN.** `test_windowed_extraction_long_document` had
  been red, and it reads like the worst kind of red: an entity named in both the
  first and the last window came back with ONE span and a late-window-only
  person was absent entirely, which says the extractor silently truncates every
  long document. The blast radius looked real — 0.017% of a 1% corpus sample
  exceed one 120,000-char window, the longest 672,723 chars, so ~1,200 documents
  across the corpus with most of their text invisible, and long documents are
  exactly the judgments and select-committee reports this project wants most.
  **All of it was wrong, and one more read settled it.** The test builds its long
  document from **1,500 copies of one line**, which is a 0.002 distinct-line
  ratio against C005(b)'s 0.25 floor, so `extract_article` did precisely what it
  says and emitted the note `doc-repetitive … read the first of 2 windows only`.
  The pipeline was correct. The screen was added AFTER the test, and the cheapest
  way to make a document long had become the way to make it unreadable.
  **So: read the arm's own notes before measuring its blast radius.** The
  diagnosis cost two queries against the live corpus and a scaled estimate of a
  defect that does not exist, and the pipeline had been printing the answer in
  its own drop channel the whole time. The near-miss is the card I nearly raised.
  **And a fixture must survive the screens it shares a pipeline with.** The
  filler is varied now, and the test asserts `distinct_line_ratio(body) >=
  _MIN_DISTINCT_LINE_RATIO` read from the pipeline's own constant rather than a
  copy of the number — so the next person who moves the floor breaks the fixture
  loudly instead of silently disabling the one test of cross-window extraction,
  which is what had happened: the coverage had been dead since C005(b) landed.
  *Paid for by:* 2026-10-08 (C536's root-suite run), one near-raised card.


- **A PER-BOX BUILD ARTEFACT HAS NO AGE IN THE REPO, SO ANY CLAIM ABOUT ITS
  STALENESS IS UNFALSIFIABLE — ASK WHO SERVES IT.** "`gui/dist-product`
  (query.app) last built 08-26 — rebuild or retire" was asked three times: the
  2026-08-30 estate audit, queue 14's SPEC pass on 2026-09-19, and C163. Both
  options were wrong and the date was wrong. The directory is **gitignored** and
  `gui/SPEC.md` says every box builds its own, so no comment, card or audit in
  the repo can know when any box last built it — the copy here was rebuilt
  2026-09-28, a month after the date all three quoted. `query/app.py` carried
  the claim in a comment, where no reader could check it.
  **And the age was the wrong question entirely.** `FLEET.md` says public boxes
  run `query.app` *and never install it*, no unit launches it on either box, and
  both boxes are factory boxes serving `v3.api` from `gui/dist`. An unbuilt
  product bundle on a box that never serves the product is the CORRECT state.
  Retiring it would have removed the only non-console serving path the
  product/console split rests on; rebuilding it would have been work for nobody.
  **A question that keeps being deferred to a verdict list is usually a question
  with a third answer.**
  **What could rot was the PAIRING, and that converts cleanly into a gate.** The
  app refuses to start without the bundle (T-D 2026-08-16, after a silent
  fallback shipped console pages to a mis-built public box), so the two are
  inseparable: the day a unit launches the app, that box must build the bundle.
  A test that censuses the launchers fails on that day and names the unit and
  the command, and states the measured zero until then. An audit finding that
  nobody can close becomes a gate that closes itself.
  **Nothing was deleted** — #3d6b74 is exactly this bundle's class: a file git
  could not restore.
  **And a test about a CLAIM must pin the claim, not the characters.** Mine
  first asserted the literal date was absent from the module, which the
  corrected comment then failed — explaining that an old date was wrong requires
  naming it. Narrowed to the phrase, it failed again on my own wording. Both
  failures were the test being right; the fix was to assert that no LIVE
  staleness claim remains, and that the reason the age does not matter is
  written where the next reader of the guard will be standing.
  *Paid for by:* 2026-10-08 (C163), three raisings of one stale sentence.


- **LET THE INDEX SCORE THE GUESSES, AND THE LEXICON DISAPPEARS.** C408 offered
  three fixes for a one-word query finding 1% of its subject — a curated
  compound lexicon, a split-and-OR fallback, or a wider index. Measured first:
  `websearch_to_tsquery('english', 'socialmedia')` makes ONE lexeme and never
  decomposes it, so the compound finds **2 documents where `social media` finds
  2,306** — and the card's own example (`sandmining`, 140x) was the MILD case.
  `nationalparty` 1,091x, `superrugby` 864x, `mentalhealth` 842x,
  `winstonpeters` 339x.
  **The fallback needs no dictionary because a wrong guess costs nothing.** Cut
  the word at every position with both halves ≥ 4 letters and OR the cuts in as
  PHRASE queries: `ment <-> alhealth` matches no document and contributes
  nothing, so precision comes from the corpus instead of from a list somebody
  maintains. The floor is measured, not chosen — at four, `forthe` has no valid
  cut at all (`fort|he`, `forth|e` leave two-letter halves), and measured live
  it stayed at 123 hits before and after, while `kiwifruit` stayed at 191. A
  curated lexicon would have had to carry the 301 candidates the corpus throws
  up, and **reading them is what showed most were worthless**: `forthe`,
  `andthe`, `fromthe`, `thenew` are run-together typos and `newzealand` is
  domain names — a keyword sweep finds the word, not the fact (#7d90b4).
  **PHRASE, not AND, and the difference is 2x.** `national & party` matches
  3,274 documents in 180 days, many of them "National" beside "third party";
  `national <-> party` matches 1,466. A compound means the words are adjacent,
  and the looser operator would have paid for its recall in coincidence.
  **AND A SECOND DEFECT, BIGGER, THAT SPELLING CANNOT EXPLAIN.** The index
  covers the title plus the first **1,500 characters**, and **77.5% of served
  articles are longer than that** (mean 4,147, max 54,584). Documents the search
  cannot reach because the subject is named below the lead: `sand mining`
  90.2%, `lobbying` 60.9%, `consent` 54.8%, `Fonterra` 46.6%, `donation` 45.2%
  — a median near half of every query's own corpus, at every spelling. The card
  led with the compound case; the window was the second finding and the larger
  one.
  **The warning in the docstring WAS the protection, which is to say there was
  none.** `primitives` said index-status "reports the mismatch by name only —
  it cannot see the expression", and `index_status` read `indexname` and
  `pg_relation_size` and never `indexdef`. So editing the window — the whole
  fix — would have left every query using an expression the GIN index does not
  match: planner unable to use it, sequential scans over 7.3 million rows on a
  customer-facing search, and every instrument reporting the index present and
  READY. `ready` now means the index indexes what the queries ask for, compared
  through postgres's own rewriting (`'english'::regconfig`, `''::text`,
  `"left"`), because a byte comparison would disagree always and so be ignored
  always.
  **A new match rule has to go where the match is DEFINED, or the surfaces
  diverge silently.** `keyword`, `drift`, `facets` and `keyness._hits` each
  called `_window(...)` and then bound `params["q"]` themselves. The moment
  `keyword` gained the fallback, salience answered differently about the same
  word — and the only reason it did not ship is that a real-corpus test asserts
  the salience cells sum to `keyword.n`. The term goes through `_window` now,
  and a test refuses any `params["q"] =` outside the one function that builds
  the query.
  *Paid for by:* 2026-10-08 (C408), and the estate has no search query log, so
  "how many one-word queries this hits" could not be answered from real queries
  at all — the population was built from the corpus and that limit is stated.

- **`find_spec` PROVES A MODULE IS LOCATABLE, NOT IMPORTABLE — AND A GATE BUILT
  ON IT CERTIFIES COMMANDS THAT CANNOT START.** `tests/test_unit_modules_import`
  asked, for every unit's `-m` module, whether `importlib.util.find_spec` could
  resolve it, with a comment explaining — correctly — that IMPORTING a job's
  module would run its module-level work under pytest. Both halves of that were
  right and the gate was still blind: `courts.extract` is locatable and dies
  `ModuleNotFoundError: No module named 'extraction.auth_guard'` the moment it
  is imported. **`courts-extract.service` is MANIFEST-declared and sits on
  Arthur's runsheet awaiting his enable**, so the instrument written for exactly
  this class was green over a command that has never been able to start.
  **The fix keeps the right half**: an `ast` probe reads the module's source and
  `find_spec`s its TOP-LEVEL imports — `tree.body` only, because an import
  nested in a `try:` is deliberately optional and a relative import cannot be
  resolved by name — and executes not one line. It caught exactly one unit of
  57 the first time it ran, which is the shape a gate should have.
  **AND THE PACKAGE NEVER EXISTED, which is a different finding from a rename.**
  Zero commits across all branches for `auth_guard`, `pipeline_regulatory`,
  `pipeline_court` and `pipeline_oia`. `auth_guard` was only the FIRST missing
  import of four modules that each need a pipeline too; only
  `news_canonical.processor` needs it alone. Asking git whether the thing ever
  existed is two seconds and it separates "retired badly" from "never built",
  which are opposite repairs — and the three names those modules want
  (`MAX_FAILS`, `AuthExtractionError`, `is_auth_error`) sit in
  `ingestion/hansard/extract.py`, a shared classifier inside one lane's
  extractor, which is #c57b88's shape again.
  **A PERMANENT RED ON A PRE-PUSH GATE GETS THE GATE SWITCHED OFF, so the
  abstention has to be labelled and conditional.** A unit the MANIFEST declares
  disabled on BOTH boxes skips with its unresolved imports IN the skip reason —
  reported every run, never silenced — and flipping one box to `enabled` makes
  it fail, which was proven rather than asserted. The decision reads INTENT from
  the manifest and never systemd, because a box that happens not to have a unit
  installed is not a decision.
  *Paid for by:* 2026-10-08 (C534), and the runsheet still asks Arthur to enable
  the one unit this caught.

- **A CADENCE FLOOR MEASURED OVER ALL DAYS IS A YARDSTICK A WEEKDAY PUBLISHER
  CANNOT REACH — AND THE SOURCES ACTUALLY FAILING WALK PAST IT.** `coverage_scan`
  called a source `daily` at `days_with >= window * 0.6`: 54 of 90. A Mon–Fri
  publisher tops out at **5/7 = 0.714**, so that floor left it **16% of slack
  where a seven-day source had 40%**. `gazette.govt.nz`, published on working
  days BY STATUTE, sat at 0.70 — one bad week from reading as degraded — while
  delivering on **97% of the days it works**. The floor was measuring cadence and
  reporting it as health.
  **AND IT PASSED THE THREE THAT WERE SICK.** Of the 25 sources the floor called
  `daily`, exactly three are under 0.80 on their own working days:
  `newsroom.co.nz` 0.64, `businessdesk.co.nz` 0.65, `www.labour.org.nz` 0.75.
  A single all-days fraction cannot separate "publishes five days and keeps its
  word" from "publishes seven days and misses a third of them", because both land
  near 0.65.
  **SO THE KIND IS THE PATTERN, NOT A FRACTION.** A weekday counts as one the
  source WORKS when it delivered on at least half that weekday's occurrences, and
  the live profiles separate cleanly there rather than clustering at the boundary:
  gazette runs 13/13/13/12/12/0/0 Mon–Sun, hospitalitybusiness 12/13/6/5/2/1/6,
  localmatters 12/11/12/7/11/3/12. Seven worked days is `daily`, five or six
  `weekdays`, two to four `periodic`, one `weekly`. Health is then a separate
  question asked only about the days the source works — which is the question the
  gate was always trying to ask.
  **A FRACTION OF ONE ARTICLE IS NOT A QUANTITY.** The sparse test asks whether a
  day delivered at least 25% of a normal one, which needs a normal day big enough
  for a quarter to exist. Measured: **86 of the 222 (source, working-weekday)
  pairs have a median under 4, and 32 have a median of exactly 1** — so for 39%
  of the pairs the test collapses into "published at all" and `sparse_frac` has
  no effect whatever. That is how a community paper that files ONE article on a
  typical Thursday came to read as a degrading scraper. The condition is
  arithmetic rather than a chosen threshold: below `median * frac >= 1` there is
  no value a day could have delivered that would pass and that being empty did
  not already fail.
  **AND THE PREVIOUS FIX OF THIS SAME ARM LEFT THE ADJACENT HOLE.** 2026-10-05
  made a Sunday comparable only with other Sundays, so a weekday the source has
  NEVER used has no floor. The weekday it uses SOMETIMES was still charged:
  localmatters delivered on 3 of the window's 13 Saturdays, so Saturday had a
  median and the other ten were measured against it — and a HEAVY median makes it
  worse, because the floor then clears one article and every absent Saturday
  becomes a fault. Never-used and rarely-used are the same claim at different
  strengths; fixing one is half the fix.
  **16 SOURCES OVER THE CEILING BECAME 3, WITHOUT TOUCHING THE CEILING.** The
  card's own instruction was "not a threshold nudged until an arm goes green", and
  the three that remain are the two measured at 0.64/0.65 and one whose absent
  days are all on its heavy weekdays — four Tuesdays at 0–2 against a normal 11,
  three Sundays at 0–3 against a normal 15. A gate that stops crying wolf by
  measuring the right thing keeps its teeth; one that stops by moving its line
  loses them.
  *Paid for by:* 2026-10-08 (C541), and C500 before it — raised as a capture
  failure at beehive on the strength of 29 sparse days that were every Saturday
  and Sunday in the window, when the lane had been current the whole time.


- **A RULING EXECUTED ONCE IS NOT A RULING ENFORCED — AND THE SCRIPT'S OWN TESTS
  WILL NOT TELL YOU.** Ruling 203, restated by Arthur on 2026-09-27: *"All papers
  past graph references, entities, claims and mentions were to be deleted
  permanently and irreversibly."* It was done —
  `ops/papers_past_withdraw.py` removed 6,670,282 claims and 20,584,192
  entities, and `papers_past_sightings.py` finished the 50,340,788
  `alias_sighting` rows that carried no foreign key and so never cascaded. Both
  scripts have tests. **Not one of them asserted that the graph was still clean
  afterwards**, so for twelve days the only evidence the ruling still held was
  that nobody had looked.
  **AND WHAT KEPT IT HOLDING WAS A STATUS, NOT A RULE.** The 4,648,837 Papers
  Past articles stay out of the extraction queue because they are marked
  `CONTENT_COMPLETE`. A re-extraction that reconsidered completed articles, or a
  reconcile that reset that status, would return them — and the first symptom
  would be the thing the ruling was made about: an entity carrying claims from
  1858 to 2026 with seventeen records merged into it, two of its oldest an 1858
  assault and an 1882 fine for a stray horse. Different men. **The judge was not
  failing; it was being asked whether two records were the same person while one
  of them was several people.**
  **A LABEL PREDICATE IS HALF A GUARD.** An outlet check only catches rows that
  still carry the label, and C530 measured 8.8% of this corpus carrying a scraper
  module's name where a host belonged — so a re-entry under another label passes
  a label check while looking identical in the output. The other half asks from
  the article side: join `mentions.article_id` against a random sample of real
  Papers Past article ids, which does not care what anything is called. Proven by
  pointing the arm's identifier at `1news.co.nz`: the label half found 32,173
  claims and the id half found **64,100 mentions** — two different numbers from
  two different questions, which is why both are needed.
  **AND GUARD THE OPPOSITE DIRECTION TOO.** The ruling kept the DOCUMENTS
  searchable, so a withdrawal that reached into the corpus would be a fault as
  well — and a silent one, because fewer rows looks like success to a gate
  measuring absence. The arm reds if the corpus drops below 4 M articles. An
  absence gate needs a floor as well as a ceiling.
  **TAKE THE IDENTIFIER FROM THE WRITER.** `papers_past_withdraw.OUTLET` is the
  one home, and its own comment records that `outlet` and
  `source_url ILIKE '%paperspast%'` agreed on all 6,670,282 claims with zero
  rows either side. An arm that re-types the string is a second rule to keep in
  step with the first.
  *Paid for by:* 2026-10-09 (C553), and Arthur having to ask.


- **A DETECTOR WHOSE ANSWER NOTHING ACTS ON IS A COUNTER, NOT A FILTER — AND
  WHERE YOU APPLY IT DECIDES WHETHER IT HELPS OR BREAKS.** `party_lifecycle` had
  `is_furniture()`, a correct test for gazette rows that are notice prose rather
  than party names, and used it in exactly one place: a count in the report. The
  rows it named still entered the party universe, took a window from their own
  `registered` event, and then abstained the entire coverage measurement for
  having no readable end. Five of twenty abstentions were `alogo for New Zealand
  National Front`, `ORNZas the abbreviation of the name of …`, `Internet
  PartyThe Internet`, `NZ Independent CoalitionThe NZ Independent …` and
  `1Law4All 1Law4All's`. The estate knew they were prose and counted them
  anyway.
  **AND MY FIRST PLACEMENT WAS WRONG IN AN INSTRUCTIVE WAY.** Filtering them out
  of `universe()` took the abstentions from 20 to 14 and immediately broke THREE
  filed labels that had resolved through those very rows — because the prose
  carries the alias INSIDE it: `ORNZas the abbreviation of the name of Outdoor
  Recreation NZ` is precisely how `ORNZ` is known to be that party. The right
  split is that a row can be a name to RESOLVE without being a party to MEASURE,
  so the filter belongs in `windows()`: the row keeps contributing names and
  stops claiming to be one. Two different questions were being asked of one
  predicate, and the fix is where it is called, not what it says.
  **FUSED NOTICE TEXT HAS SHAPES, NOT INSTANCES.** The five rows are a repeated
  name (`X X's`), a block fusion at a capital boundary (`…PartyThe Internet`), a
  leading `a logo for` run together, and an `as the abbreviation of the name of`
  clause — which is why the filter is four patterns and not five strings. The
  fusion arm must stay CASE-SENSITIVE: the signal is a lowercase letter running
  straight into a capitalised word, and folding case matches ordinary prose
  inside real names. A furniture filter that eats a party is worse than one that
  misses prose, so the guard is a list of every real party name in the abstained
  set, asserted to survive — `ONE Party`, `New Conservative` and `Internet Party
  and MANA Movement` are the ones that nearly went.
  **AND THE RESIDUAL ABSTENTION WAS NEVER OURS.** After the fix, 14 parties are
  off today's roll with no gazetted cancellation and one registered before the
  feed's reach, so their owed years are unknowable from the Commission's own two
  publications. That is a permanent reason to withhold, not a to-do — and the
  narrower claim IS published beside it: *of the 14 parties on today's register,
  78 of 86 annual returns owed for 2019–2025 are held.* Withholding the number
  you cannot support while saying the one you can is the whole discipline.
  *Paid for by:* 2026-10-09 (C455), and two of its three causes having already
  been fixed on 2026-09-27 without the card being re-measured — "49 of 108
  missing" was 18 before I touched anything.

- **A TEST DOUBLE THAT IS MORE PERMISSIVE THAN THE REAL ENGINE IN THE ONE DIMENSION THE
  CARD IS ABOUT WILL PASS AGAINST THE UNFIXED CODE.** Writing C539's gate meant faking a
  psycopg connection, and the fake was wrong twice in the same five minutes, both times in
  the direction that hid the defect. **First:** `_type_override` builds its cache with
  `{r["norm_form"]: r["type"] for r in conn.execute(...)}` — it ITERATES the cursor and
  never calls `fetchall`. A fake that answered only `fetchone`/`fetchall` raised
  `TypeError` inside that function's own broad `except Exception`, which logs a warning,
  returns `None` and applies **no overrides at all** — so three tests about retyped
  entities ran against an entity nothing had retyped, and passed. The warning was printed
  in the pytest output. **Second:** the fake stored minted rows in a dict keyed by `nzbn`
  and looked them up with `.get(params[0])`. Python's `.get(None)` cheerfully returns the
  row a previous NULL insert left behind; postgres's `WHERE nzbn = NULL` returns nothing,
  ever — **and that difference was the entire mechanism under test**, so the
  duplicate-mint test passed against the unfixed module until the fake was taught NULL
  semantics. **The check that catches both is the same one every time: run the gate
  against the UNFIXED code and count which tests fail.** Seven of ten did, once the fake
  was honest; three did before it was, and the three that moved are exactly the card's
  subject. A gate not run backwards is a gate whose colour means nothing — and reading the
  suite's own warnings is part of running it.
  *Paid for by:* 2026-10-09 (C539). Same family as the C542 finding that a gate
  reimplementing its own predicate passes against the unfixed module, and the `dict_row`
  positional-unpacking guard that reported success while doing nothing.



- **THE PATTERN THAT DECIDES WHETHER A CHECK RUNS IS WORTH MORE THAN THE CHECK —
  AND ITS SILENCE IS INDISTINGUISHABLE FROM APPROVAL.** `ops/four_questions.py`
  enforces rulings 326 and 359, and it judges a card only on an "occasion": a
  `raised <date>` on a live row, a `CLOSED <date>` in a live status, or a row in
  the closed register. Measured 2026-10-09: **110 of 117 live card rows carried no
  occasion at all, so SEVEN of the live register reached the lessons check** — a
  close recorded as `PART <date>`, which ruling 244 makes the normal way to record
  a tranche, matched none of the three. I wrote an invented six-hex rule `#id` into
  a day-log **seven times in one session** and the gate caught none of them: for
  those cards it was not looking, which is not the same as looking and passing
  them.
  **Both blind spots were FORMATTING, and the second was mine, an hour old.**
  `_LIVE_CLOSED` was `^CLOSED` while a status is written `**CLOSED 2026-10-09` as
  often as `CLOSED 2026-10-09` — three live rows invisible, one of them the card
  being closed that minute, which is how the seventh bad id landed. And the fresh
  `_LIVE_PART` missed `PART 02:57 2026-09-08` (C156), a time sitting between the
  verb and the date. **Widening the first immediately red three of that day's own
  closes** — one bad citation and two DOCS answers that never named
  `ingestion/SPEC.md` as ruling 326 requires — so the debt had been there all along
  with nothing able to say so.
  **Audit the vocabulary, do not wait to trip over the next one.** Grouping the
  rows the gate could not see by how their status OPENS took one query and gave the
  whole answer: 69 `open` (correct — no close has happened), and then `STANDS`,
  `RESTATED`, `ADMITTED`, `IN PROGRESS`, `**GO`, `SERVING HALF BUILT`. The forms are
  now pinned by a test, and pinned END TO END: a regex test alone would still pass
  while the loop failed to apply the pattern to the status cell, which is precisely
  the bug `_LIVE_PART` shipped with — added to the loop and not to the line that
  chooses the status cell over the whole row, so the fix was inert and a standalone
  measurement "proved" it by running its own copy of the loop.
  *Paid for by:* 2026-10-09 (C459, C328). Same family as the `any()`-not-`all()`
  defect found in this same gate the same day — it counted a LESSONS line resolved
  if ANY cited id resolved, so one real id covered an invented one beside it — and
  as C544's sum reconciliation: a check that
  cannot see its subject reports the same colour as one that approves it.

- **A GRANT CANNOT ENFORCE AN IMMUTABILITY THAT HAS LEGITIMATE EXCEPTIONS — CENSUS THE
  SITES INSTEAD, AND NAME WHY EACH MAY.** C103 asked for *"triggers/RULE + REVOKE
  DELETE/UPDATE"* on the observation store, and the gap it names is real: no trigger
  and no REVOKE exists anywhere in the estate's SQL. Both remedies would break the
  estate. **REVOKE DELETE breaks REGENERATION** — `TERMINAL_ARCHITECTURE.md` makes the
  extractor "a PURE FUNCTION of (document, era flag)" and says "determinism IS the
  revert path", so `consume` deleting a document's claims and re-emitting them is how
  a document is re-read. **REVOKE UPDATE breaks the JUDGMENT LAYER:** of the six
  columns ever updated on an observation table, four are bindings or a lifecycle flag
  that judgments own — `subject_entity_id` (5 sites), `object_entity_id` (7),
  `claim_entities.entity_id` (2), `suppressed_at` (2). An entity merge repointing a
  claim's subject is the append-only judgment TAKING EFFECT, not the observation
  changing.
  **So immutability here is per-COLUMN, not per-table**, and only two columns are
  observation content: `predicate` and `object_text`. Each is updated in exactly ONE
  place and both are legitimate — `healer/heal.py` writes the `claim_heals` row
  carrying `old_predicate` BEFORE the update, and `claim_graph/split.py` touches
  `object_text` only inside the revert path, restoring an original.
  **What is enforceable is the CENSUS**: fourteen modules mutate an observation table,
  each listed with which of REGENERATION / audited JUDGMENT / REVERT / RULING it is,
  and a new site fails the gate. Plus the two properties the reading established —
  the healer's audit row is written BEFORE its update (an audit row written after
  cannot carry the old value, because the old value is gone), and no `object_text`
  update sits outside the revert path. Both proven by breaking them: an unlisted
  module, and the audit block moved below the update.
  **And the unverified kinds are RECORDED AS UNVERIFIED.** Six of the fourteen were
  listed without reading the site, and they say so rather than carrying a kind guessed
  from the filename — a census whose reasons are invented is the convention it was
  meant to replace.
  **AND A TEST FILE IS PART OF THE CORPUS IT MEASURES.** Adding the two retired
  writers to C116's census the same day, I wrote their paths out —
  `ops/retired/fetch_wikipedia_…py` — and broke `test_estate_clock_column.py`: a
  retired module whose path appears anywhere under `ops/tests/` reads as FIRED BY A
  GATE, which is the mention-as-use error that column exists to correct. The gate
  file's own header says *"THE PATHS IN THIS FILE ARE ASSEMBLED, NOT SPELLED, and
  that is not fussiness… it did, on this file's first run"* — **the warning was eight
  lines above the line I wrote.** Reading the file you are editing is not the same as
  reading the file you are editing AT THE POINT YOU EDIT IT.
  *Paid for by:* 2026-10-09 (C103), where the card's own remedy was the wrong
  instrument and the measurement said which one fits; and C116 the same hour.

- **A VARIANT MAP IS EVIDENCE OF A NAME RELATIONSHIP AND NOT OF AN IDENTITY — RUN THE
  NULL MODEL BEFORE QUOTING THE CANDIDATE COUNT.** C167 wants nickname settlement in
  the graph (`Gerry ↔ Gerard`) via "variant map / merges". The map is the easy half
  and it came out well: rather than buying or inventing a nickname list, derive it
  from names the FILER wrote in the `Formal (Nickname) Surname` shape, so the
  document asserts both forms — **371 distinct pairs** from `charity_officers` and
  `candidates_announced`, screened of 26 organisations (`Ace International Trust (NZ)
  Limited`), 3 titles (`Adrienne (Lady) Stewart`) and 164 non-matching shapes. It
  carries what a bought-in English list never would: **te reo equivalents** —
  `David↔Rawiri`, `Peter↔Pita`, `Ellen↔Erana`, `James↔Hemi`, `Andrew↔Anaru`.
  **Then the map applied to the graph gives a number that means nothing.** Live
  two-token person entities: 1,300,342. Pairs where both the formal and the nickname
  exist with the same surname: **33,989** — which looks like a defect list and is
  not. Shuffling the map so each formal name draws a RANDOM nickname from it yields
  **26,713** on average, so the real map's **lift over chance is 1.27×**. With 1.3M
  entities and common surnames, "Alexander Campbell" and "Alasdair Campbell" sharing
  a surname is arithmetic, not evidence. The sample is dominated by
  `Alexander↔Alasdair`, which is a different NAME rather than a nickname at all.
  **So the card's remedy cannot work on name shape alone**, which is
  #10523e — *a many-to-many alias is evidence a NAME is present, never that an ENTITY
  is the same one* — now with a figure attached. Settling identity needs
  corroboration BEYOND the name: a shared document, organisation, address or register
  id, which is exactly how the graph's own person keys already bind (`a key binds
  ONLY when the DOCUMENT corroborates its org`).
  **The null model cost one query and saved a 33,989-row candidate list** that would
  have been worked as though it were findings.
  *Paid for by:* 2026-10-09 (C167). Map kept at
  `data-layer/registers/data/nickname_pairs_filer_stated.json` with that warning in
  the artifact itself, because a map this reusable will be picked up by someone who
  did not read this rule.

- **A RULE ENFORCED BY ARITHMETIC IS STILL UNGATED, AND THE WEIGHT THAT CLOSES A GAP
  LANDS ON THE THRESHOLD BY ONE ULP.** C430(b) asks that a name-similarity proposal
  with no corroborating leg is never offered. The estate already gets this right and
  nothing asserted it: `name_exact` is worth 0.45 against `ACCEPT_MIN` 0.85, so a
  name leg cannot accept alone; `band_for` abstains on a person at ANY score; and of
  4,421 live corroborated-or-accept rows, **zero rest on name-only legs** — every one
  carries an address, active-years, companies or person-key leg beside it. The rule
  was true by arithmetic, and the way arithmetic breaks is one edited weight with no
  test to notice.
  **Then the gate found something the comment had not.** `unique_legal_name` is
  documented as "worth exactly the gap to ACCEPT_MIN — 0.45 + 0.20 + 0.05 + 0.15 =
  0.85", and in binary floating point that sum is **0.8500000000000001**. It accepts
  because `>=` sees it, so the intent holds by one ULP on the right side — but the
  leg's entire usefulness rests on which side of the threshold a float sum lands,
  and had it rounded down the leg would never fire and **no test would have shown a
  failure**: the register's own identification would simply never be reached. So the
  assertion pins the DIRECTION (`>= ACCEPT_MIN`) as well as the intent (within a
  cent), because an equality is a thing binary cannot deliver and a one-sided
  tolerance is what the behaviour actually depends on.
  **The general shape: when a rule holds because numbers happen to sum correctly,
  the gate asserts the SUM, not the behaviour** — behaviour tests pass for as long
  as the numbers hold and go silent about why they stopped.
  *Paid for by:* 2026-10-09 (C430(b)), with C167's 1.27x measurement as the reason
  the rule matters: name shape at that lift is barely evidence at all.

- **A SELF-DESCRIBING DOCUMENT MUST EXCLUDE ITSELF, OR ITS GATE NEVER SETTLES — AND
  "NOTHING READS THIS" IS THE MOST EXPENSIVE SENTENCE A CENSUS CAN GET WRONG.**
  C293's knob table is generated from the units and `ops/config/*.env`, and the
  first three versions each reported something false about the estate:
  1. Scanning only units' `EnvironmentFile=` lines printed **"nothing — check
     before deleting" against all four config files**, and every one is read — by
     `ops/production/unit-failed.sh`, `ops/offsite_push.py`,
     `extractor/cast.py`, `extract-fleet.sh`, `ops/ruled_env_check.py`. A unit is
     not the only reader of a config file, and a table whose population is wrong
     presents its own blindness as a finding.
  2. Widening the scan to every file made every DAY-LOG that mentions a config file
     a reader of it — six against `alert-channel.env`, none of which reads a key.
     **A citation is not a consumer**, and the question the column answers is
     "would deleting this break something".
  3. Narrowing it to code then listed the table's OWN TEST as a consumer, because
     that test names all four files in order to assert about them — so generating
     the table changed the repo the table describes and `--check` said STALE
     immediately after a `--write`. The exclusion is now by IMPORT: a consumer of
     the table is not a consumer of the knob.
  **AND A SECRET-SHAPED KEY SHOWS NO VALUE, WHATEVER ITS VALUE IS.** The inline
  values are the useful half (`AGENT_MODEL=qwen3.6-35b-a3b-q4km` is what a reader
  came for), but a unit file is somewhere a secret could be put and a generated
  document is the last place it should surface. Masking is on the KEY's shape, not
  on a judgment about the value — today's only hit is `LLM_API_KEY=local`, which is
  not a secret; the mask is for the one somebody adds later.
  *Paid for by:* 2026-10-09 (C293). Proven by adding a knob and watching the gate
  go red, then reverting it.

- **"KEEP THEM IN STEP" IS NOT A MECHANISM — AND THE ARM THE COPY LACKED WAS THE
  LARGEST ROW IN THE CLASS.** C172's screen for a contribution line that is not a
  donor name (`Loan of vehicle for the campaign`, a bare street address) lived as a
  Python pattern in `query.influence.base` and was ALSO restated as a POSIX regex
  inside `query.influence.donations`' blind-spots query, under the comment *"the SQL
  pattern mirrors `_NON_DONOR_LINE` — keep them in step"*. They were not in step:
  the SQL copy lacks the `^p o box` arm the Python one gained, so the counted class
  missed `P O Box 14277` at **$60,000** — more than two thirds of the whole class by
  value. **A comment cannot keep two dialects of one rule aligned**; what can is
  having one of them. The pattern moved UPSTREAM to the loader that writes the
  column (`registers` is imported by `query`, never the reverse), the SQL
  restatement was deleted and the rows are filtered in Python by the one pattern,
  and a test greps the tree for the copy's distinctive arm so a third home fails the
  push.
  **THE CARD ASKED FOR A FIVE-VALUE TAXONOMY AND THE RIGHT ANSWER WAS ONE VALUE IN
  AN EXISTING ONE.** `line_kind` already answers "what does the donor column HOLD",
  so `description` joined `name`/`unreadable`/`furniture`/`example`/`self_funded`
  and every consumer's existing `line_kind = 'name'` filter excluded it with no
  change. **And the taxonomy was already undocumented by one:** the DDL comment
  listed four values while the register held five — `self_funded`, 993 live rows —
  which is how a consumer comes to guess.
  **ORDER IS THE DISTINCTION WHEN TWO ARMS SEE THE SAME STRING.** C427's
  example-address arm and this one both match a street address in the donor column.
  C427's means "the donor column was NOT READ" — the printed example's address
  shifted one column, and Vanushi Walters' 2020 return reconciles exactly on that
  $5,000 — while a filed `42d Lambie Drive, Manukau` means "read, and not a name".
  Same treatment, different statement, so the stronger claim runs first and a test
  pins both.
  *Paid for by:* 2026-10-10 (C172). 8 rows / $86,197.79 in the class; the wide
  alternative measured at 35 rows / $680,894.75 and almost all real unions and
  companies, so it was refused.

- **A GUARD THAT ENUMERATES ITS OWN POPULATION BY HAND WILL BE SHORT BY EXACTLY THE
  ONE THAT BITES — AND TWO SUITES THAT PASS ALONE CAN FAIL TOGETHER.** The root
  `conftest.py` imports the editable packages early so the real module is in
  `sys.modules` before any test prepends `data-layer/` and turns the project
  directory into a namespace package. That remedy and its guard both named FIVE
  packages. **Seventeen of the twenty-one project directories fit the shape** — any
  directory under `data-layer/` whose basename is also an importable package name —
  and `corpus_search` is one of them. So whenever `data-layer/registers/tests` and
  `data-layer/query/tests` ran in ONE pytest process, four `test_search_routes`
  tests failed with `ImportError: cannot import name 'drift' from 'corpus_search'
  (unknown location)`: the exact shadow the conftest's comment block is about, on a
  package neither the conftest nor the guard mentioned. **`ops/test_all.sh` runs the
  suites separately, so the estate never saw it** — the failure needed a
  combination nothing in the harness produces, which is the quietest way for a test
  estate to be wrong.
  **THE FIX IS TO DERIVE BOTH SETS.** The shadowable set is structural (an
  importable basename under `data-layer/`); the set that MATTERS is the one `tests/`
  and `ops/tests/` actually import, read from their own source. The conftest pins
  the ten in that intersection — measured at under 10 ms each, because pinning
  seventeen packages into every suite in the repo would be a cost nobody had counted
  — and a test fails the push when the list falls behind. **A derived list needs its
  own floor:** `test_the_shadowable_set_is_not_empty` exists because a derivation
  that returns nothing makes every case built on it vacuously green.
  *Paid for by:* 2026-10-10 (C556), found while closing C172 — the combined run was
  the only reason the four reds were visible at all.

- **A UNIT TEST THAT REACHES A LIVE DATABASE PASSES OR FAILS ON WHICH VARIABLES THE
  RUNNER EXPORTED — AND THEN ONLY THE RUNNER SEES THE RED.** `ops/test_all.sh`
  reported `SUITES FAILED` on four `ops` tests while a bare `pytest ops/tests` was
  green, for days. The runner sources the factory env; a bare shell does not. Three
  of the four were C547's ordering tests, which hand `weekly_hosts` a FAKE policy
  set of one or two hosts — and C554 had since added a third route whose helper
  **queries the live backlog**, so with `V3_BACKLOG_DSN` exported the function
  correctly reported **188 real landed hosts** as uncovered against a fixture
  expecting one. The function was right; the test had started reaching a database
  it never meant to. The live lookup is now injectable (`weekly_hosts(conn,
  landed=None)`), the default stays the LIVE one — an injectable defaulting to
  empty would quietly stop walking the landed hosts in production — and a test
  asserts that default, because that is the direction this fix could rot in.
  **THE FOURTH WAS A SKIP TEXT, AND IT IS THE SHARPEST OF THE FOUR.** A test of
  mine skipped with `reason="needs V3_REGISTER_DSN"`, and the runner's
  `DB_SKIP_RE` — which exists so a DB-backed skip reads RED rather than green —
  does not match that wording. `ops/tests/test_db_skip_regex.py` catches exactly
  this, and caught it. **A skip is a claim that nothing was checked, and the
  runner's ability to see that claim depends on the WORDS.** Write the skip text
  the runner can read, or the suite reports green for a gate that never ran.
  *Paid for by:* 2026-10-10 (C557), and the four reds were only visible because a
  night of card-closing ended by running the estate's own runner rather than the
  suites I had been touching.

- **"SINCE THE FIX" MEANS SINCE THE CAUSE EXISTED, NOT SINCE A DATE — AND AN ARM
  THAT CANNOT TELL A LEAK FROM A CORRECTION WILL REPORT THE CORRECTION.** T7.70 was
  written on 2026-10-09 to ask the live question C539's code gate cannot: has an
  override minted an entity of its own since the leak was closed. It compared the
  entity's `created_at` against a fixed DATE, and went red the next night on
  `Eana` — minted at 02:47:40 with its override written at **03:12:32, twenty-five
  minutes later**, by the crawler's acronym-type-sanity judge at 0.95. **The leak
  is an override CAUSING a mint, so the override must have existed when the entity
  was minted.** An override that arrives afterwards is `entity_type_overrides`
  doing its job (ruling 303: the dossier's type correction). The clause is
  `e.created_at >= o.created_at`; the date only scopes the window.
  **AND THE RESIDUE FIGURE WAS MIS-SHAPED THE SAME WAY.** Of 17,667 single-token
  overridden person entities, **3,072 were minted BEFORE their override** — the
  leak cannot explain them and they were never residue. The class is 14,595. A
  number quoted in a card, a day-log and an arm's own note was 21% too big because
  the join had no direction.
  **THE TEST FOR THIS SHAPE: ask what the cause's own timestamp is, and whether
  your population could exist without it.** A date is a proxy for "after the
  cause", and it is only a good proxy when the cause is a deploy. Here the cause
  is a ROW, and rows arrive all day.
  *Paid for by:* 2026-10-10 (C539), one day after the arm shipped — and the arm
  found it by going red, which is the arm working. With the order asked: **0**
  minted after their override since the fix.

- **A COUNT THAT THREE READERS DISAGREE ABOUT IS NEVER AN ARITHMETIC DISAGREEMENT —
  IT IS AN UNWRITTEN VOCABULARY.** Muster 4 §B4 was raised because *"three
  reasonable parsers gave three different open counts"* of the card register. Four,
  by 2026-10-10: two readings taken an hour apart while writing the pre-pass gave
  **109 and 114** against the draft's **204**. Nobody had miscounted. Each reader
  had invented, silently, its own answer to *which statuses mean open* — and the
  register held `RESTATED`, `ADMITTED`, `IN PROGRESS`, `STANDS`, `GO`,
  `SERVING HALF BUILT`, `DEAD-CALLABLE HALF DONE`, `hold until a use case` and
  `(a) copying…` as statuses. **Write the vocabulary in one function and make
  everything that wants the number call it.** `open_count` now gives 125 rows = 88
  open + 27 part + 10 closed-awaiting-sweep + **0 unstated**.
  **AND NINE ROWS WERE UNCOUNTABLE FOR A REASON NO VOCABULARY FIXES:** six carried
  **six columns in a seven-column table**, so the status sat where a parser reads
  the size, and a parser reading `cells[6]` got the empty string while one reading
  `cells[-1]` got a plausible-looking answer. A row's SHAPE is part of its contract.
  The remaining three had prose where a word belongs, and prefixing the vocabulary
  word while keeping the prose cost nothing and settled all three.
  **THE ARM BUILT ON IT HAD TO STOP GUESSING FIRST.** Of the live register's four
  reported "broken references", **three were an OPEN row naming the file it exists
  to build** (`C349` → `ops/ux_run_querynz.py`) — so a status-blind checker makes
  every deliverable a defect, which is §B4's own 73%-false-positive class. And the
  fourth was a basename guess: `tools/mtmd/README.md` reported as
  `-> data-layer/extractor/README.md`, a file that is neither retired nor that
  document, inside a module whose docstring already says *"a checker that invents
  moves is worse than no checker"*. **A rule a module states about itself is not a
  rule the module obeys.** With the three classes separated — DELIVERABLE,
  BASENAME-ONLY, MISSING-PATH — the live register reports **0** broken references
  and the arm's red means something.
  *Paid for by:* 2026-10-10 (C558 PF-2, Muster 4 §B2+§B4 built as one arm because
  they are one question). Coverage rides in the note always, because 42 of 125 rows
  name a file, unit or arm at all and "0 broken references" without that number
  tells a reader almost nothing.
  **THERE WAS A FOURTH READER, AND IT SURFACED THE FIRST TIME A CARD WAS
  PARKED** (2026-10-10). `ops/board.py:open_cards` kept its own predicate —
  `head.startswith("open") or head == "stands"`, plus a local `_PART` tuple —
  and it had agreed with the one definition by luck, because no live row had yet
  carried a word only the other knew. The moment C427 was PARKED the render
  refused with *"C427 is triaged but is not an open card row"* while
  `open_count` called it live. Fixed by DELEGATION rather than by adding the
  word: liveness is asked of `muster_audit.row_is_open` and the two now agree at
  114 = 114. The progress LABEL stays local, because a board-column choice is
  not a count. A second dialect that currently agrees is not a second dialect
  that agrees — it is one waiting for the first input that tells them apart.

- **A RULE STATED IN ONE FUNCTION'S DOCSTRING IS A RULE THAT FUNCTION ENFORCES
  — ITS SIBLINGS ARE NOT BOUND BY IT, AND AN UNGUARDED FIX ROTS WHERE NOBODY
  LOOKS.** `query.influence.donations._like_of` has declared the subject
  picker's floor in its own docstring since it was written — *"a string shorter
  than 3 characters matches NOTHING (a '%' or a single letter must never become
  a subject)"* — and enforced it perfectly for every arm that called it. Three
  arms of the same route do not call it, because they are Python substring
  tests rather than SQL patterns: the canonical-party name check
  (`q.lower() in canon.lower()`), the product scope's registered-party set
  (guarded by `ql and …`, which bars only the EMPTY query), and
  `_product_search_extras`'s board scan (`like in nm.lower()`). Measured live:
  **`q=a` answered with nine parties on the default scope and FORTY-SEVEN
  subjects on the product's own search page** — 23 registered parties plus the
  whole board corpus truncated at its cap of 24, which reads to a user as a
  result set; `q=e` returned the same 47. The floor was never breached by a
  metacharacter. It was breached by one keystroke, and the arm below the floor
  was also the most expensive query the product could be asked, because the
  board loop assembles every party's board in order to filter it. Fix: NAME the
  predicate (`too_short`) and have the substring arms ask it, with
  `_like_of` asking the same one — a test asserts no literal `< 3` comes back
  inside it, because a second copy is how the first three arms came to differ
  from the fourth.
  *Paid for by:* 2026-10-10 (C156). **And it had been SAID.** The audit of
  2026-09-03 recorded, the same day the fix shipped, that this item and four
  others had "NO acceptance rec and no UX entry" and put them on a
  shipped-but-unguarded list *"until recs exist"*. Five weeks later the rec
  still did not exist and the floor had been breached in three further arms of
  the route it was installed in. **An unguarded fix is not a fix with a missing
  test; it is a fix with an expiry date nobody can read.** Same shape as the
  third-copy-of-a-predicate rule (#5da4b6) and the fourth reader of the status
  vocabulary above: the copy that drifts is always the one nobody thought was a
  copy.

- **A PROBE WHOSE FIXTURE IS SOMEBODY ELSE'S SELECTION CRITERION WILL NOT BE
  EXERCISED, AND AN ARM RED BECAUSE IT CANNOT REACH ITS SUBJECT ACCUSES RATHER
  THAN FAILS.** PI-77 tests a POPULATION property — the Gazette ministerial
  timeline is read whole and cached (the supersession rule cannot take a person
  predicate), so attribution happens after the cache, and dropping the surname
  test would give every person the entire ministry while each page still looked
  plausible. The test is therefore "the subjects' span sets differ and none
  holds the union", which a dropped predicate destroys instantly. On its first
  run it reported **one** subject carrying a Gazette span, because the acceptance
  runner's person set is chosen by DONATION SIZE and a candidate with large
  receipts is usually not a minister. The probe was correct and useless. Fixed
  by having it SOURCE ITS OWN SUBJECTS from the product — each registered
  party's sitting MPs, walked until two carry spans — rather than by writing a
  list of ministers, which is a curated fixture that goes stale the next time a
  ministry changes.
  *Paid for by:* 2026-10-10 (C156). Cousin of "a stale threshold does not fail,
  it accuses": a permanently red arm teaches a reader to skip it, which costs
  more than the arm was worth.

- **A DUPLICATE-ID RULE MUST COUNT POSSIBLE EXECUTIONS, NOT MENTIONS — AND AN
  ARTIFACT GLOB THAT WAS A NAME BECOMES A PREFIX.** Two findings from giving
  the acceptance runner its first test that looks at `run()` itself (the pure
  helpers each had one; the 1,400-line function that calls them had none).
  (a) Counting `rec("<id>", …)` occurrences in the source flags **47** ids,
  every one of them a `try`/`except` or `if`/`else` pair on purpose — the probe
  and the handler that records its failure, the probe and the branch that
  records "not exercised". Comparing BRANCH PATHS instead (same `If`/`Try`
  node, different branch ⇒ mutually exclusive) left exactly one: a dead
  `try: pass / except: rec("PI-60", False, …)` orphaned by a refactor —
  unreachable, so never a real duplicate, but a second declaration that would
  have recorded a false failure the moment anything was put in that body.
  (b) `var/audits/ux-pi-*.json` no longer names one instrument: the retired
  `ops/retired/ux_pi_gui_checks.py` writes `ux-pi-gui-<stamp>.json` into the
  same directory, and because "g" sorts after a digit **those files sort LAST**
  — so "the newest `ux-pi-*`" was a 2026-09-07 artifact of a different tool,
  two rows wide, with no `gated` key, and the test died on a `KeyError` rather
  than on the thing it was testing. Pick the artifact by what its CONTENT says
  it is (a `run_at`, rows carrying `gated`) and take the newest `run_at`, never
  the last filename.
  *Paid for by:* 2026-10-10 (C156). The two arms the test now holds are the two
  ways an instrument goes quiet: a `probe_*` helper defined and never called
  passes every existing test — it is pure and correct — while guarding nothing
  and being counted in the tally; and an id declared in `run()` and missing
  from the audit means its probe raised before `rec`, after which `summarise`
  reports a smaller denominator as a pass rate, because it cannot miss what it
  never saw.

- **WHEN THE READER TAKES `max(revision)`, THE REVISION MUST BE MONOTONIC IN THE
  CLOCK — A HASH-DERIVED ONE IS WRONG HALF THE TIME AND NEVER RED.**
  `registers.candidates_announced` is served by selecting the newest
  `revision_id` per source page, which makes the revision key load-bearing and
  not bookkeeping. Deriving it from the document's sha256 is the obvious move —
  it is stable, it is the document's identity, and `[[document-identity-is-bytes]]`
  argues for it everywhere else — and it is exactly wrong here: a hash does not
  order, so about half of all future editions would hash BELOW the one already
  loaded, sit in the table unserved, and leave every surface showing the old
  list with nothing red anywhere. The revision is `YYYYMMDDHHMMSS` from the
  capture clock. IDEMPOTENCE still comes from the bytes — the document's sha is
  recorded on every row and an already-loaded document is skipped — so the two
  jobs are done by the two keys that can do them: the clock orders, the hash
  identifies.
  *Paid for by:* 2026-10-10 (C151). Cousin of the dotted version sorted as text
  (2.10 < 2.3): a key that looks like an identifier being asked to behave like
  a sequence.

- **A FLOOR OVER `count(*)` CANNOT SEE A REGISTER WHOSE EVERY ROW IS
  RETRACTED — IT WAS GREEN FOR THIRTY-FOUR DAYS WHILE THE SURFACE SERVED
  ZERO.** `registers.candidates_announced` is catalogued with `floor=550`,
  measured at 660 rows. Ruling 194 stamped `withdrawn_at` on all 660 on
  2026-09-06, the serving query filters `withdrawn_at IS NULL`, and the
  product's announced tier served NOTHING from that day until 2026-10-10. The
  floor never moved, because 660 withdrawn rows are 660 rows. The catalog
  comment even said so out loud — *"the floor counts all rows"* — which is the
  worst version: the blindness was DOCUMENTED beside the number and the number
  was still the one being watched. A register that supports retraction needs
  its floor over what it SERVES, and the fix is one extra: `count(*) WHERE
  withdrawn_at IS NULL`, the figure that would have gone to zero on the day.
  *Paid for by:* 2026-10-10 (C151). The same family as "the green that means we
  did not look", with a twist worth naming on its own: the gate was measuring a
  real quantity, correctly, and that quantity had stopped being the one that
  mattered the moment a ruling introduced a way for a row to exist and not
  count.

- **A JOIN KEY THAT FITS ONE SOURCE'S NAME ORDER BREAKS THE DAY THE OFFICIAL
  SOURCE ARRIVES — AND MAKING THE PARTY A REQUIREMENT TURNS A DEFECTION INTO
  AN ABSENCE.** The PI product tells a reader where each sitting MP is standing
  (`running` on the pickers, `sitting_mp` on the electorate view). Both went to
  ZERO for all 123 sitting MPs the moment the Electoral Commission's own
  candidate list replaced the withdrawn Wikipedia rows, for a reason nothing
  could have flagged: the key was `_cand_name_key`, which keeps a comma, and
  the Commission files `"BISHOP, Christopher"` where the roster carries
  `"Chris Bishop"` — `goldsmith, paul` can never meet `paul goldsmith`. The
  Wikipedia rows were `"Firstname Surname"`, so the join worked perfectly right
  up until the source got BETTER. An estate with `_ec_name_key` beside it, for
  exactly this, and a frozen given-name variant map that already bridges
  chris↔christopher: the fix was one function name, and the defect was choosing
  it when only one source existed.
  **THEN THE SECOND HALF, WHICH IS THE INTERESTING ONE.** The index was
  `(name_key, canonical_party)` and required BOTH, which says "not standing"
  about two classes of person who are: an MP who CHANGED PARTY — Tākuta Ferris
  sat for Te Pāti Māori and is standing in Te Tai Tonga as an Independent,
  Mariameno Kapa-Kingi for the Te Tai Tokerau Party — and an MP whose roster
  row has no party at all, since `(key, None)` is in the index for no row. A
  political-influence product erasing a defection is the whole purpose
  inverted, and it erased it in favour of silence. The party was there as a
  NAMESAKE GUARD, and that is the job it keeps: join by name, take a unique
  hit, use the party only to choose among several, abstain when it cannot
  (ruling 76 — no fame tiebreak, no fuzzy match). Measured: 469 announced rows
  offer ZERO ambiguous name keys, so the requirement bought nothing and cost
  four true matches; `party_change` now states the difference instead.
  *Paid for by:* 2026-10-10 (C319). A predicate added for safety, in a place
  where it could only ever subtract: measure what the guard CATCHES before
  letting it filter.
  **AND THE INDEX HAD TWO READERS.** Changing its shape for the announced tier
  would have made the official-results spine's `sitting_mp` silently
  always-false — the pair form was read as `(key, party) in sitting` at both
  sites, in two differently-spelled copies. Caught only by grepping for the
  other reader before restarting (#5da4b6, again). Both now call one helper,
  and the live counts are 104 and 113 rather than 104 and 0.

- **THE NUMBERS WERE ALL RIGHT AND THE SENTENCE BESIDE THEM WAS A YEAR OUT OF
  DATE.** The first acceptance run after the Commission's candidate list landed
  failed PI-39 with `running=105/123`, 71 electorates and 469 candidacies —
  every figure correct — because the payload's own `note` still read
  *"candidates as collated on Wikipedia from party announcements … Replaced by
  the Electoral Commission's list when published"*, on the day that list was
  published, captured, loaded and being served. A note is a sentence ABOUT the
  rows, written once, and nothing recomputes it; the figures beside it are
  derived every request. So the note is now DERIVED TOO — it reads its own
  rows' `source_page` to name the publisher, counts the list-only and retiring
  rows it set aside, and states the half still unread — and the gate asserts
  what it SAYS, not only what it counts. The arm earned its whole existence in
  one run by failing on the only part of a payload a gate usually ignores.
  *Paid for by:* 2026-10-10 (C319). The prose in a payload is data; if it
  cannot be derived from the rows, it is a comment with a publication date.

- **A REGISTER NOTHING READS PASSES EVERY GATE, BECAUSE EVERY GATE WATCHES THE
  REGISTER.** `registers.mp_expenses` (3,745 rows, 583 members, $51.4 M) and
  `registers.minister_expenses` (1,766 rows, 249 members, $48.9 M) were
  captured, derived and CITED in September, catalogued with floors, watched by
  T7.42 and T7.12, their timers firing weekly and succeeding — and on
  2026-10-10 **nothing in the serving layer imported either name.** A hundred
  million dollars of disclosed public money, in a product called Follow the
  Money, with no surface anywhere, and not one red to say so. The estate's
  no-consumer register even listed the capture scripts as `keep` with
  consumers, because their consumer IS the register; what had no consumer was
  the register itself, and nothing asks that question. A `grep` for the table
  name across the serving package took four seconds and was the whole
  discovery.
  *Paid for by:* 2026-10-10 (C175, whose own card line said "still open: Parl /
  Min Services disclosures" — which turned out to mean not a capture gap but a
  serving gap nobody had named). The general form: **coverage gates measure
  that a thing was collected and a floor measures that it is still there;
  neither can tell you a reader can reach it.** For a register whose purpose is
  to be served, the paired correctness gate belongs on the SURFACE
  (`probe_public_expenses_served`), and it must fail when the panel is absent
  rather than when the table is empty.

- **A COLLISION COUNT CAN BE EVIDENCE *FOR* A KEY, AND ABSTAINING ON IT WOULD
  HAVE DROPPED THE PRIME MINISTER.** A first+last name key over the expense
  registers "collides" on 136 of 355 parliamentary and 56 of 185 ministerial
  keys — 38% and 30%, which reads as a flat refusal to join. Every single one
  is ONE PERSON under several spellings, because the source workbooks put
  footnote markers and honorifics in the NAME cell: `Luxon, Christopher`,
  `Luxon, Christopher (1)` and `Luxon, Christopher (1) (6) (7)` are the same
  Prime Minister; `Alfred Ngaro` and `Hon Alfred Ngaro` the same minister.
  Strip markers and honorifics and **not one key names two different people** —
  the residue is whitespace (`Tuiono,Teanau`, `Tim  Groser`), a mid-name `Dr`,
  a `KC`, a fuller given name. The namesake rule (abstain on a shared key) is
  right everywhere else in this estate and would here have served $0 for the
  members who spend most, reporting nothing wrong. **Classify a collision
  before obeying it:** the question is not "do two rows share a key" but "do
  two PEOPLE", and the second one is answered by normalising and re-counting,
  which takes one query.
  And the fold is safe only while no period arrives under two spellings — also
  measurable, also surprising: exactly ONE (member, quarter) pair in 5,511 rows
  carries two rows, Jami-Lee Ross in 2018 Q4, who left National mid-quarter, so
  the two part-period entries SHOULD sum. The count rides in the payload so the
  day a source restates a period, the number moves beside the total it inflates.
  *Paid for by:* 2026-10-10 (C175).

- **A FRESHNESS CEILING CANNOT TELL "OUR FETCH STOPPED" FROM "THE PUBLISHER
  STOPPED", AND IT WILL BLAME US FOR FORTY-SEVEN BOARDS.** T7.42 asks whether
  the MP expenses register is fresh, and its own docstring named the two causes
  it modelled: *"a newest quarter older than 150 days means the monthly fetch
  stopped or the catalogue moved."* It had been RED since 2026-09-13 on a
  newest quarter ending 2025-12-31, 283 days old. Neither cause was true. The
  catalogue's own `package_show` — which our fetch stores beside the workbooks
  on every run, last read five days earlier — offers nothing newer than that
  same quarter, and the package's `metadata_modified` is 2026-03-09.
  **Parliamentary Service stopped publishing.** What made it look like ours was
  that Ministerial Services, a DIFFERENT publisher in the same register family,
  had gone on to 2026-06-30.
  The fix is not a bigger ceiling — that is how a threshold becomes an
  accusation nobody acts on. It is to ask the question the arm was always
  reaching for: **is OUR copy behind the SOURCE.** Three verdicts replace one
  number: OURS (the catalogue offers a quarter we do not hold), STALE FETCH
  (nothing has asked the catalogue lately — the real "our fetch stopped", which
  the old ceiling was standing in for and could not express), THEIRS (we are
  current, the publisher is late, stated and not blamed on us). And it is
  STRICTER where it counts: under the ceiling, a quarter the catalogue
  published and we failed to fetch stayed GREEN for 150 days after that quarter
  ended; now it reds the same day.
  *Paid for by:* 2026-10-10 (C331's arm, found while closing C175). Two
  further things it cost nothing to get right: the board makes NO request — the
  fetch already does exactly one `package_show` per run and keeps it, so the
  arm reads a file — and a missing stored response falls back to the ceiling
  **and says it has fallen back**, because a lost input that turns a three-way
  test into a pass is the silent-green class this estate keeps paying for.
  Cousin of "a stale threshold does not fail, it accuses", with the mechanism
  named: a one-sided measurement of a two-sided relationship always blames the
  side holding the instrument.

- **FOUR OF THE FIVE ROWS AN ARM WAS RED ON WERE ALREADY GOVERNED, PUBLISHED,
  OR BOTH — AND NARROWING IT TO ONE DOCUMENT IS WHAT MADE IT ACTIONABLE.**
  T7.71 asks that no disclosure line sit below the $20,000 floor the form
  legally exists for, on the stated ground that such a line "is money on a
  customer surface". Read 2026-10-10 it was red on five rows, and the five were
  four different things:
  **(1)** one was the COMMISSION'S OWN published figure (already excused);
  **(2)** two carry `line_kind = 'unreadable'`, which **ruling 191 already
  governs** — the amount stays on the receiver's return, chipped "a line, not a
  donor", and barred from every donor ranking, dropdown, search, index and
  address join. By that ruling they are precisely NOT on a customer surface, so
  the arm was contradicting its own premise;
  **(3)** one was a sub-floor gift on an AGGREGATION disclosure, and the proof
  is the publisher's, not a legal reading of mine: `IEF_Limited_4_September_
  2023.pdf` reads $20,000 on 15 August and $3,000 on 31 August, and the
  Commission's own table lists IEF Limited at **$23,000** — their sum to the
  cent. A document whose name-lines sum to a figure the publisher states is
  corroborated BY the publisher. (Three agreements required — party, folded
  donor, sum — never the sum alone.)
  **(4)** what remained was two rows on ONE document, which is the thing the
  arm was written for.
  *Paid for by:* 2026-10-10 (T7.71, C544's arm). The general shape: **an arm
  that counts a POPULATION will be red on everything that population touches,
  including the parts other rulings have already settled.** Before widening a
  threshold or carding the pile, classify the rows against the rulings that
  already exist — here two of five were settled five weeks earlier by a ruling
  the arm's own file cites elsewhere.

- **AN AMOUNT TEST CANNOT SEE THE WORSE ERROR ON THE SAME DOCUMENT.** The two
  rows T7.71 legitimately reds on are $2,412 and $3,755 from
  `Vision_New_Zealand_25_July_2023.pdf`. The document's THIRD row is
  $27,063.55 — above the floor, so invisible to this arm — and all three carry
  the same donor `Charles Deve`, the same date **15/07/2020** on a 2023
  disclosure, and the party **Freedom Party of New Zealand** from a file the
  Commission filed under Vision New Zealand, whose published table for that
  date lists Cheyne Huka Hakaraia at $23,000 and nothing resembling any of the
  three. `pdftotext` returns NOTHING: it is a two-page scan, so every field is
  OCR output. So the arm reports **$6,167 below a floor** where the defect is
  **$33,230.55 attributed to a possibly wrong party with an impossible date** —
  the amount test found the document, and the amount is the least wrong thing
  on it.
  *Paid for by:* 2026-10-10. This is the seventh document shared between C308
  (no address) and C544 (below the floor), and that overlap had already been
  measured and concluded — *"two symptoms, one cause: the OCR of a photographed
  form"* — so the residue is correctly owned by C171/C417/C418 and waits on the
  re-read. **A gate is allowed to stay red on a known, owned cause**; what it
  must not do is stay red on four things it cannot act on and bury the one it
  can.

- **ADDING A CYCLE TO A DERIVED LIST MOVED THREE THINGS THAT WERE NOT ASKING TO
  MOVE, AND THE TEST THAT CAUGHT IT CARRIED ITS OWN REASON.** Putting the
  live 2026 election into `GENERAL_ELECTIONS` — a factual list; the election is
  running — rippled through `HOME_CYCLES`, which five call sites read, and
  broke three things at once:
  **(1) THE MAP WOULD HAVE DRAWN THE WRONG SHAPES.** `HOME_CYCLES`'s own comment
  says it is *"the electorate map's cycles"*, and the map renders ONE held
  boundary file (Stats NZ 2020). Measured against the Commission's 2026
  candidate list: **ten** 2026 electorates do not exist on those shapes (East
  Cape, Glendene, Henderson, Kapiti, Kenepuru, Mt Maunganui, Waitākere,
  Wellington Bays, Wellington North, Ōtāhuhu) and **eight** 2020 ones are gone.
  A map scoped to 2026 would silently drop ten races and shade eight that no
  longer exist. The failing test's comment had recorded exactly why the list
  stopped at 2023 — *"both fought on the 2019 boundary review, which is the
  review the map's shapes come from"* — so the guard was a sentence someone
  wrote down, not a number someone pinned.
  **(2) EVERY ELECTORATE'S WINNER WENT NULL.** The winner was taken at
  `y == y1`, the newest cycle, which was the latest RESULT until a cycle
  existed that cannot have one. An election not yet held has no `elected`
  candidate, so a field that had a value for all 72 seats blanked. Fixed to the
  latest cycle that actually declares a winner.
  **(3) A FIXTURE THAT ANSWERED THE SAME THING TO EVERY QUESTION TRIPLE-COUNTED.**
  The home test's electorate stub returned one set of rows for every year but
  2020, so a third cycle summed a third copy and spend read $60,201.00 against
  $35,100.50. A stub whose answer does not depend on its argument cannot show a
  per-argument bug, and grows one the moment the caller asks a new question.
  *Paid for by:* 2026-10-11. The shape: **a derived list is a dependency with no
  call site to grep.** `GENERAL_ELECTIONS` looks like data and behaves like a
  function argument to everything downstream of `HOME_CYCLES`. Before adding to
  one, read every reader — and where two readers have different constraints
  (a figure has no geometry; a map does), that is two lists, not one list held
  back to the narrower reader.

- **A SNAPSHOT ON ONE SIDE AND A LIVE READ ON THE OTHER IS A CLOCK SKEW THE ARM
  REPORTS AS A DEFECT.** T7.8 asks whether any graph row points at an article
  the backlog does not have — the NZLII-purge watch, 1,667 articles deleted on
  2026-07-30. It compares the live graph against `audit_articles`, a TEMP mirror
  of the backlog taken when the board STARTS, and it reported **76 orphaned
  mentions and 145 orphaned claims** on the 2026-10-12 01:11 board. Half an hour
  later, same code, **zero**. Nothing was repaired in between. Measured the same
  hour: **1,073 articles fetched in one hour already carried 5,488 mentions and
  2,024 claims** — this estate ingests and extracts CONTINUOUSLY, so an article
  that arrives after the snapshot and is extracted before the arm runs is absent
  from the mirror and present in the graph, which in the mirror alone is
  indistinguishable from a delete.
  The snapshot was introduced to remove a DIFFERENT race (a hand-run of these
  queries once raced the fleet and reported 3,535 phantom ledger violations), and
  it did — then created this one, in the one arm that compares the two sides by
  identity rather than by count. **The fix is a second reader, not a wider
  window:** the candidates come from the snapshot join, and each candidate
  article is CONFIRMED against the live backlog before its rows count. A deleted
  article is still gone when you ask again; a late arrival is not. The late rows
  are reported beside the verdict rather than dropped, because "0 orphans, 221
  rows on articles that arrived mid-board" is the sentence that stops the next
  reader re-deriving this.
  *Paid for by:* 2026-10-12. Tell: **when an arm joins a frozen copy to a live
  table, ask what the frozen side cannot know yet** — and a red that measures
  zero on a re-run without a repair is a clock, not an estate.

- **"DON'T SWEEP IT WHILE IT IS STILL ARRIVING" IS A CONDITION, SO MAKE IT A
  MEASUREMENT THE SWEEP REFUSES ON.** `ops/suppression_shaped.py` argued in
  prose, on 2026-10-08, that T7.10's twelve Roman numerals must NOT be
  quarantined because "quarantining them here would clear the arm until
  tomorrow's extraction and teach the next reader the wrong cause" (#8f68d8: a
  gate must bite where the drift is MADE). Correct that day — and four days
  later the mint WAS closed, the argument still read as a permanent exclusion,
  and the only way to act on it was to edit the prose that had been right.
  A sentence cannot tell you whether its own premise still holds. `FRESH_HOURS`
  can: the sweep measures the newest row of the class it is about to take and
  refuses if anything arrived inside 48 hours — two full days of ticks that fire
  every fifteen minutes, which is a real test of "the mint is closed" and cannot
  be satisfied by waiting a few minutes. The class is still REPORTED while the
  sweep refuses, so the refusal costs no visibility.
  *Paid for by:* 2026-10-12 (T7.10/C539). Tell: a prohibition whose reason is a
  measurable state should be written as the measurement — otherwise it either
  outlives its reason or gets edited away by whoever first finds it
  inconvenient, and both of those are worse than a gate that says `REFUSED:
  this class is still arriving`.

- **A CAPABILITY PROBE THAT NAMES A UNIT IS A JOIN, AND THE JOIN ROTS WHEN THE
  JOB MOVES.** T7.53 asked whether each box can read a scanned return by
  grepping `gazette-derive.service` for `Environment=PAGE_IMAGE_URL=`. True
  when written; then the loader moved — `registers-derive.service` runs
  `registers.party_return_totals --load` and has carried the variable since
  2026-09-24, while `gazette-derive` runs `gazette_register.derive` and has no
  business with it. So the board said **"NEITHER box can"** for eighteen days
  with the recogniser configured, answering on :8032, and read by the unit that
  needs it. **A red that doing the right thing cannot clear is worse than no
  arm**, because the estate learns the arm is noise. Ask the question by its
  SUBJECT, not by a name: every installed unit whose `^ExecStart=` invokes the
  loader must declare the variable, and there must be at least one such unit —
  which also fails if the loader is removed entirely. Match on `ExecStart`, not
  on the name appearing anywhere: three installed units mention
  `party_return_totals` and two only in a comment or a Description.
  *Paid for by:* 2026-10-12 (T7.53). Tell: when a probe hard-codes WHERE
  something should be configured, the next move of that job silently inverts
  its answer — and the arm will be red, not green, which is why nobody suspects
  the instrument.

- **`exit` INSIDE `$( … )` KILLS THE SUBSTITUTION, SO THE PROBE PRINTS AN EMPTY
  ANSWER — AND A COMPARISON OF TWO EMPTY ANSWERS IS "THEY AGREE".** The repair
  for the lesson above put `|| exit 1` inside a probe that T7.53 runs as
  `printf '%s=%s' LABEL $(if PROBE; then echo yes; else echo no; fi)`. The exit
  terminated the command substitution's subshell before either `echo`, the
  label printed with NOTHING after the `=`, and the arm's two tests — "do the
  boxes differ" and "is it missing on both" — both read `""` as benign: the
  boxes agreed, and `""` is not `"no"`. **Green, in the arm whose entire
  subject is a capability nobody checked**, within an hour of fixing the
  opposite failure in the same probe.
  Two guards, both now in the code: no probe may contain `exit`, and any answer
  that is not exactly `yes` or `no` is a BROKEN PROBE that reds and says so
  (the same distinction `_run_arms` already draws between an arm that FAILED
  and an arm that could not start).
  *Paid for by:* 2026-10-12 (T7.53). Family: "checks that silently pass" —
  third instance in this estate of a comparison treating "no answer" as "same
  answer", after `dict_row` positional unpacking and the `_Result` fake that
  swallowed a TypeError into "no overrides applied".

- **A PROBE THAT IS ONE `and` CHAIN REPORTS ONE BIT, AND THE BIT IT REPORTS IS
  NOT THE ONE YOU NEED.** The PI acceptance run stood at **85 pass / 21 fail**
  for days. Every probe was a dozen conditions joined by `and`, recording
  pass/fail plus an evidence string composed by hand — so EC-2 printed *"6/6
  refs resolve to evidence+document; unresolved []"* while FAILING on a half it
  never mentioned, and PI-44 printed *"mps=33/33"*. `and` short-circuits, so
  even tracing it by hand showed only the first failure. Twenty of the
  twenty-one turned out to be the INSTRUMENT.
  `Clauses` — name every condition, evaluate all of them, print the ones that
  failed — took the same report to **105 / 0** in an afternoon, and the one real
  defect it exposed (two surfaces giving one donor two totals) had been invisible
  behind a probe that failed for four other reasons at once.
  **What the twenty were, because the pattern is the lesson:** six were
  thresholds counted from a window that moved (ruling 347 put it at 2019, so
  "≥ 5 elections", "≥ 4 races", "≥ 3 donation years" became unreachable); four
  were a RULING landing (addresses stripped on 10-01, press excluded on 09-28,
  disclosure-only donors joining the list on 10-03) and the probe still asking
  for what the ruling removed; three were a FEATURE landing (2026 became a
  cycle, so `cycles == [2020, 2023]` and a 70–74 electorate band broke); three
  were marker strings for headings that had been reworded, one for a section a
  ruling DELETED; one asked the product for a pre-window year the ruling makes
  it clamp; and **one chose its subjects without the window at all**, so the
  acceptance run was asking about Kim Dotcom (2014) and the Estate of Cyril
  Smith and reading "no rows served" as a defect.
  *Paid for by:* 2026-10-12 (C132). Three tells: **a ruling changes the
  instrument too, and nothing reminds you**; a probe's evidence must state what
  FAILED and not what passed, or the report trains its reader to ignore it; and
  an acceptance run must choose its subjects from the window it is testing —
  otherwise the estate is blamed for obeying a ruling.
