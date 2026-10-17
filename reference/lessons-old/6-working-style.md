> Part of [LESSONS](../LESSONS.md) — living memory, one section per file
> since 2026-10-04 so that "read the relevant section" is a thing a reader
> can do. The rules of the file, and why it exists, are in LESSONS.md.

## 6. Working style

- **A worklist and a rate estimator cannot share a list.** The gold tab served
  2,019 open cells: 1,529 a check had objected to, where an answer repairs
  something, and 490 both readers agreed on, where an answer only measures how
  often two readers are wrong together. Arthur's complaint was not that the
  questions were hard — *"i cant tell what you want me to review"*. **Two things
  that buy different outcomes are two queues, and a surface that merges them
  cannot state what it wants from the person reading it.** The estimator also
  must not be ranked by money, or the bound quoted off it becomes a figure about
  big donations rather than about readers. (2026-09-28, C460.)

- **A scope ruling binds what you ASK someone, not only what you serve.** The
  gold queue applied neither ruling 347 (2019 onwards) nor ruling 351 (the eight
  parties), so 42 of its 75 documents were work nobody may act on — a 2015 Mana
  return among them. Both rulings say out-of-scope data is kept and served and
  never WORKED, and a review question is working it. **Asking for a person's
  evening is the most expensive thing a surface does; apply the window there
  first, and print what was excluded rather than dropping it.** (2026-09-28,
  C460.)

- **The unit of a question is the act that answers it.** 1,529 open cells over
  75 documents published as 1,529 questions asks a person to open the same PDF
  twenty times. Folded to one entry per DOCUMENT, with the cells regrouped into
  the LINES the form prints and each failing check stated once above the rows it
  named, a 36-cell document became 12 rows. **Ask in the shape of the work, not
  the shape of the data.** (2026-09-28, C460.)


- **A ruling that is APPLIED everywhere and REGISTERED nowhere is a ruling
  that will be re-litigated.** When Arthur rules, the ruling's home is the
  doc it governs AND a row in `docs/records/DECISIONS.md` — the second is not
  bookkeeping, it is the only index that outlives the workstream doc holding
  the reasoning, which is what that file's own header says it is for.
  *Paid for by:* 2026-09-23. A documentation audit found rulings **323 to 330
  missing from the register** — eight consecutive rulings, made 2026-09-21 and
  2026-09-22, every one of them applied into WORKFLOW.md, TWIN_FACTORY_ARCH.md,
  CLAUDE.md, a dozen SPECs and a dozen gates, and none of them in the ruling
  register. Applying a ruling feels like recording it, and it is not: the
  application scatters the reasoning across the files it changed, which is
  exactly the failure the register exists to prevent. The register is also
  where a SUPERSESSION lands — 331 supersedes 230's window, and without the
  row there is nothing to read that in. No gate caught this, because every
  gate checked whether the ruling was OBEYED.


- **When a surface is not working for him, ask where the work belongs before
  building another control on it.** Three rounds of "add an affordance" is a
  strong signal that the venue is wrong, not the affordance.
  *Paid for by:* 2026-09-21. He said the review cards were "static objects I
  cannot see what they refer to". I added live exhibits. He said he could not
  click them. I made the rows expand and renamed Pass to Approve. He said
  review would happen in the chat and the board should only track cards — all
  three builds discarded, an afternoon gone. The first message already
  contained the question I never asked: *where should reviewing happen?*

- **Build in small verified tranches, each with a verification that can FAIL
  against real data — and interview before building.** Establish the goal,
  agree the scope, reflect back a plan naming the affected services, THEN
  build. Answer the question that was actually asked: a question buried in a
  status wall is a question not answered. A reversal needs no manufactured
  caveat — state the correct position flat. Carding and fixing are different
  acts; diagnose, measure, prototype to CONFIRM if needed, then revert and
  card.
  *Paid for by:* memory: build-in-small-verified-tranches;
  change-request-protocol; be-less-verbose — Arthur, twice in one session, "did
  i ask you a question in there?" and "this makes no sense to me" · having
  wrongly called a bare copyright notice a licence blocker, I added "wholesale
  republication is a different question" to make the correction read balanced,
  guarding against something the product never does — Arthur: "why are you
  talking about republication?" · under the notes-only rule I diagnosed the BO
  depth truncation and started writing the fix — Arthur: "we're still planning
  right?"

- **Doctrine that CAN be enforced structurally is a construction error, not a
  review item — prefer the impossible over the discouraged.** The flags
  contract raises on an uncited fired flag or an unscoped green, so those rules
  cannot be violated by a shipped rule and no reviewer vigilance is required.

- **"Fix the seam" and "repair what the seam already wrote" are TWO steps, and
  the second is the one that gets dropped.** When a landing rule changes, the
  close is the seam, its test, AND a count of the rows the old rule wrote with
  their disposition stated. `ON CONFLICT DO NOTHING` on the write path is a
  reliable sign the second step is missing: re-running the lane cannot repair
  anything.
  *Paid for by:* 2026-09-19, three times in three days — the council minutes'
  capture was corrected to land unparked and 1,024 documents already on disk
  stayed parked, unextracted and unsearchable, for fourteen months; under
  ruling C394 Hansard's lander was corrected and 1,964 ledger rows kept the
  status the old seam had written, which no standing component could heal. Both
  feel like ONE task, because the seam is where the thinking happened and the
  rows already landed are invisible from there.

- **Read LESSONS for the area BEFORE diagnosing, not after.** The cost of
  skipping it is not just the rediscovery; it is the wrong intermediate
  conclusions published on the way.
  *Paid for by:* 2026-09-20, half a session — a three-hour transaction was
  blocking a production index build, and I measured `pg_stat_activity`,
  computed dead-tuple ratios against the wrong denominator, raised a bloat
  alarm, retracted it, and eventually found the cause. All of it was already
  here, written on **2026-09-02**: the held-`backend_xmin` incident, the
  detection recipe, the fix recipe with the ORDER that matters, and the exact
  trap about connections sitting in ONE open transaction for the worker's whole
  life. Had I read it I would also have known at once that 17,398 transactions
  of held xmin is nowhere near the 326k that caused real harm — precisely the
  false alarm I raised.

- **A number reaches the reader only after something produced it — and a
  retraction RATE is a finding about the work, not just the claim.** Once
  several numbers have been withdrawn, the reader has to audit the ones that
  survived, so the CORRECT findings in the same session lose their value too.
  Every timestamp comes from `date`; a record's time is read, never estimated.
  *Paid for by:* 2026-09-20 — six assertions made without measurement and all
  six withdrawn: 175 entities that were 1,186; a 1.31 s figure read from a
  docstring and presented as measured; dead-tuple percentages computed against
  an unseeded counter; "extraction ran for the first time in a week" against
  906 runs · 2026-09-08, twice in one night: the day-log ran ~1–2 h ahead of
  the commit clock and had to be corrected from `git log`, because the agent's
  sense of the clock drifts by hours.

- **A document that claims to be the complete list must be reconciled or it
  will lie, and one word naming two sets hides work.** Self-declared
  completeness is a maintenance promise. Audit the SPECs and READMEs against
  the code after a tranche lands.
  *Paid for by:* 2026-08-20 — HEALING_SYSTEM.md described itself as "the single
  human-readable list of every identity rule the estate runs" while missing an
  entire era's families · "use case" named both the ten industry mockups in
  `gui/src/useCases.ts` and the four built research use cases behind
  `/api/research/use-cases`, only the first documented, so reading the docs
  gave a confident false negative that Arthur had to correct · the 2026-08-05
  fleet-wide audit found three code bugs and every one was a HALF-LANDED
  DOCUMENTED INTENTION — a bug class the tests didn't cover because the doc
  said it was done.

- **Register-honest is not the same as usable.** Every use case needs a written
  UX requirements list that an agent exercises against the LIVE surface, and a
  passing run is what "built" means.
  *Paid for by:* Arthur, after using the Political Influence tool: "it is very
  poor." (memory: ux-requirements-per-use-case.)

- **Build a capability in the corpus service and let the use case CALL it.**
  The test for a new capability: which LAYER is it, which service owns that
  layer for the whole corpus, and does a second use case get it for free?
  *Paid for by:* 2026-09-07 services audit — the roster folds, the
  person-corroboration legs, the address key and the review thread were each
  built where the PI work stood (donor_anchors, query, a var/ file) and so
  reached donors only (F1–F5).

- **Moving code keeps the tests green and breaks the paths.** The gate for a
  move is a before/after diff of the SERVED payloads. Grep `__file__` and `from
  \.` in every moved file before the first restart; rewrite cross-module
  references as ALIASED module attributes (a bare module name is shadowed by
  any local of that name, and attribute access at call time makes import cycles
  harmless); tuple-unpacked constants are invisible to a naive top-level scan;
  and tests that patch `routes.X` stop patching once X lives elsewhere, because
  the re-export keeps `routes.X` resolving for CALLERS while the module's own
  code looks up its own global.
  *Paid for by:* 2026-09-07 (ruling 239) — lifting 5,400 lines of routes.py
  into `query/influence/` and the product pages into `data-layer/pi/` passed
  275 unit tests while three `__file__`-relative repo paths and one in-function
  relative import had silently taken their "not held" branches: coverage gaps
  became "no return read yet", source URLs became None, the MP interests tree
  vanished. The unit tests mock the register, so they never see a path; 17
  routes captured from the still-running old code and compared caught all four
  in one run.

- **Plan Arthur's lines as Arthur's: the classifier will not let the agent
  widen its own allowlist, install a unit, or run a repo-rewriting script
  direct — and that is MO §8 working as designed.** A plan that says "Claude
  installs" plans a refusal.
  *Paid for by:* 2026-09-08, three refusals in one night, all correct.

- **A non-blocking question is built with the conservative default and
  CARDED, never waited on.** Take the recover-over-exclude / abstain default,
  record the question by SUBJECT with the card it produced, and walk the file
  with Arthur at the close; the ruling is the truth, the file is only the
  index. Interrupting per question is the waste MO §7 names; guessing a ruling
  is the breach. (MUSTER_1_QUESTIONS pattern, 2026-08-28.)

- **Before a class goes to Arthur: sample three bodies and quote one — and
  state what CONSUMES the thing being decided.** Describe a notice class from
  its TEXT, never its title family. A field with no live consumer is deferred,
  not tiered; asking for a ruling can be the wrong question asked precisely.
  *Paid for by:* 2026-08-23 — the gazette survey called 6,232 "confiscation
  orders" Criminal Proceeds Act asset forfeitures ("tie respondents to
  companies and property — HIGH value") and three sampled bodies showed
  Sentencing Act motor-vehicle confiscations against sentenced individuals;
  Arthur ruled on the wrong description (GAZETTE_SURVEY corrected; ruling 98) ·
  2026-09-19: I put the council `llm_tier` to Arthur as a one-word permission
  choice, argued by analogy to gazette.govt.nz and Hansard. The analogy was
  sound and the question was still wrong, because it assumed a model was
  reading these documents and the summarising feature is parked — a ruled `llm`
  would have opened 17,929 claims to a lane nobody runs.

- **A proposal that runs is not a proposal.** A proposed judgment row is
  created DISABLED and ruled before it runs; the machinery is exercised by a
  test fixture that cleans up, never by live proposals.
  *Paid for by:* 2026-09-13 — the three feed filters seeded as
  `owner=claude-proposed` were created `enabled=true` so the new unit and board
  arm had rows to exercise, and by morning they had run 30 times and written
  10,866 hit rows before Arthur had seen them (ruling 255b: stopped). Same
  class as the 2026-08 "notes only until the workstream closes".

- **A muster's ordering: fixed external dates first, then corpus INPUT before
  an era and graph REGENERATION after it — and plan the last batch with a gate
  or do not plan it.** A re-extraction erases and replaces every feed-minted or
  healed entity on its docset. Sweep every card home before a planning session.
  *Paid for by:* Muster 1 D5/C2 (ruling 123), generalised at the close, with
  era 5 proving the erase half at scale — every claim-keyed ledger orphaned
  (AUDIT 2026-09-04 A11) · the 2026-11-18 commencement (seal + redact), the
  IPP-3A backstop and an election's nomination close are clocks the estate does
  not control, so they go at the TOP of a muster plan · 2026-09-08 (ruling
  245): B7+ was "everything else", a placeholder from the pre-pass on, so when
  B0–B6 were done the muster had no gate left to close on, only a backlog ·
  2026-08-20: items Arthur had asked to be recorded were spread across todo.md,
  the ideation docs and the issues ledger, so the agenda looked thinner than it
  was and he had to correct it.

- **A close is not recorded until the row the PLAN is read from says DONE with
  the time.** The brief is the worker's checklist; the queue table is the
  plan's truth. A finding recorded in a session brief is not filed — briefs are
  working notes and they end, so a "found elsewhere" item is filed when it is a
  ROW. The checkpoint is per CLOSE, never per session, because the agent cannot
  see its own context fill and a session-end checkpoint is written after the
  compaction that erased what it would have said.
  *Paid for by:* 2026-09-15 — queue 3 closed on 09-14 with its brief ticked,
  its day-log written and its commit pushed, and nine rows in
  MUSTER_3_QUEUES.md still read open a day later; Arthur's "how far through are
  we?" found it · 2026-09-19: the session-scope hook's bare-filename false
  positive was found at 11:00, written into a brief's "found, not touched", and
  hit twice more the same day · 2026-09-07 overnight compacted twice and picked
  up clean only because each card was recorded at its close (ruling 244).

- **The daily instruments are the board and the acceptance runner; the unit
  suites run only when someone runs them.** A close that does not run the suite
  is not a close. And the slow part of "what happened" is not reading the reds,
  it is deciding which are known — which is why the board says "NEW" / "since
  <date>" itself rather than growing a status script (C372, no-reader form).
  *Paid for by:* 2026-09-08 — between the B6 close (09-05) and the Muster 2
  close (09-08) nobody ran `ops/test_all.sh`, and four reds accumulated unseen:
  two the overnight's own test doubles, one a SyntaxError in a retired module's
  test since 09-06 · twenty minutes of one morning went to establishing that
  three of four board reds were baseline.

  **AND THE ACCEPTANCE RUNNER IS THE HALF THAT WENT UNRUN** (C132, 2026-10-10).
  `ops/ux_run_political_influence.py` says it in its own first lines — *"the
  report is the artifact and a passing run is what 'built' means"* — and the
  last report before today was dated **2026-09-28, twelve days earlier**. Run
  fresh against the live product: of 98 gated requirements, **97 pass / 1 fail
  became 78 / 21. Twenty regressed and NOTHING was fixed.** They are the home
  page, the party, MP and electorate pages and the party-asserted pane —
  `PI-5, PI-7, EC-2, PI-35, PI-37, PI-41b, PI-42b, PI-43, PI-44, PI-45, PI-47,
  PI-48, PI-56, PI-57, PI-64` and five `PAGE-*-drawn`. PI-5 is visible in one
  call: searching **"NZ First"** returns only `NZ First BOP Electorate`, a
  $1,498 donor, while "New Zealand First" returns the party at $2,984,508.52.
  A board arm would not have caught it, because the board watches the factory
  and this is the product.
  **THE RUN IS ALSO HOW YOU LEARN WHAT IS IN THE DEPLOYED BINARY.**
  `querynz-pi-web` has been up since **2026-10-08 13:49**, so nothing committed
  after that is serving, and the regression window (09-28 → 10-10) contains a
  deploy. With today's code `label_keys` DOES carry the `nz first` key PI-5
  fails on — so a restart may fix it and a restart is a decision, never a side
  effect of tidying. Twelve days of not running the instrument is twelve days
  of not knowing which.

- **Gate on the instrument's own exit status, never on a filter's.** `pytest …
  | tail -1 && git commit` commits on red, because the pipe's status is
  `tail`'s.
  *Paid for by:* 2026-08-22 (B2b, B3b), twice in one day — the B2b commit
  landed with a red registers test and the gateway was restarted with one of
  four herd tests failing. `pytest -q; rc=$?` or `set -o pipefail`.

- **A config value is not a boundary: where a package's doctrine is "local
  model only", make the CODE refuse.** Do not rely on the file that happens to
  be mounted, and drive both arms with a test.
  *Paid for by:* 2026-08-22 (B4) — the tier-3 re-read inherits its LLM URL from
  whatever environment the unit loads, and the fleet env file carried a
  non-loopback endpoint left over from before the local lane, so under the
  crawler's unit the first live run would have sent graph evidence off-box
  (`_re_read` rejects unset or non-loopback; the unit pin is belt-and-braces).

- **When a lane adds a label set, write the execute branch for EVERY label the
  judge can return; when it adds a capped finder, state where its rows sit in
  the pick order.** A capped queue behind an oldest-first picker is never
  served, and a verdict label without an execute arm is a paid verdict thrown
  away.
  *Paid for by:* 2026-08-22 (B4), both found on the first live cycle and
  neither in the gate tests — the 38 conjunctions (capped 40/cycle, screened
  last) sat behind 4,793 older rows under `ORDER BY screened_at LIMIT 1000`,
  and 24 of the first 31 verdicts were not-a-person at 0.95+ which `execute()`
  parked.

- **A LANE'S "COULD NOT DECIDE" IS DATED, NOT FINAL — AND THE RE-ASK TAKES SPARE
  CAPACITY ONLY.** A status the select never asks for again is a terminal state
  however it was named: the row goes invisible for ever, while the corpus that
  could have answered it grows every night. So a "no evidence" status carries the
  clock it was written at and something re-asks it after a window. But the re-ask
  must TOP UP a batch the new work has not filled, never share its `ORDER BY` —
  an aged backlog is always larger than the live one, so a shared pick order
  makes the lane spend every night re-asking answered questions while fresh rows
  wait. And a re-ask that still finds nothing refreshes the clock, or the same
  rows return nightly for ever.
  *Paid for by:* 2026-10-07 (C246) — `repair-no-evidence` held **7,001 rows,
  5,220 of them judged more than 30 days ago**, against 2,298 live
  `flagged-truncated` and a cap of 300 a run. The status was first written in
  August and nothing had read it since; 5,220 rows into one pick order would have
  starved new truncations for weeks, which is why the top-up is spare capacity.

- **A hook is live the moment its file is saved, and a tripwire's honesty is
  its list.** The command that edits a PreToolUse hook is judged by the hook it
  just wrote, so text that names what a hook blocks goes through Edit/Write
  (judged by path), never through a Bash heredoc — and a hook's tests run
  BEFORE the next Bash call, not after. Both hooks carry three lists in the
  docstring: caught, refused-as-unresolvable, known limits, with a test per
  caught shape. CURRENT holds the brief's REPO-RELATIVE path — a bare filename
  deadlocked every tool, because the hook blocks on a brief it cannot resolve,
  including the write that fixes it.
  *Paid for by:* 2026-09-15 (queue 4), where a heredoc naming the credential
  dir in a regex was refused by the relative-spelling rule added one call
  earlier · 2026-09-14 21:10, where Arthur had to run the echo himself (the
  hook now resolves a bare name and keeps the CURRENT-only write open).

- **Never `--amend` a commit that has been pushed anywhere.** The two-remote
  push is not atomic; a gate failure after a push attempt gets a NEW commit on
  top.
  *Paid for by:* 2026-09-15 — the mirror accepted one amend of the queue 3
  close while origin refused it at the gate, node1 pulled the mirror's copy,
  the next amend diverged from it, and force-push is rightly refused; the
  divergence was healed with `merge -s ours` (850e25a), never a rewrite.

- **Test the seam, not the halves.** A watcher's proof is the arm end to end on
  the row shape the database actually returns.
  *Paid for by:* 2026-09-14 §6 — T7.39 was green in its verdict tests and dead
  on the live board, because the adapter between the cursor (tuples) and the
  verdict (dicts) was never exercised.

- **A document's own release valve rusts shut if nobody turns it.** This
  file's rule 4 (GRADUATION) and rule 6 (DELETE the impossible) are the
  mechanisms that were supposed to bound its size; at 341 separately-filed
  lessons and 181 KB, past a 160 KB one-read ceiling, perhaps a dozen entries
  were pointers. Nothing was wrong with the rules — no step in the loop ever
  called them, because appending is what you do the day you learn something and
  graduating is what nobody is doing that day. **A rule that only runs when
  someone remembers it is not a mechanism: give it a trigger (here, the ceiling
  arm and rule 3's "append to the rule, not a new one") or expect it to be
  dead.** (2026-09-20.)

- **When the deliverable is something a PERSON will read, render one and show
  it before you build anything around it.** The form of the thing is the
  deliverable; the pipeline that produces it is not. Reviewing one rendered
  instance costs a paste and a sentence, and it is the only step that can tell
  you the form is wrong before the form has been applied 63 times and
  published into an append-only ledger.
  *Paid for by:* 2026-09-28, C418 — the gold-tier review questions went through
  FOUR formats. Format 1 was a wall of text (*"this is a mess the first doc has
  a really long question. it must be short and specific"*), format 2 still
  1,040 chars of heading-plus-rows (*"these questions are still rambling and
  incomprehensible"*), and 33 entries in the unreadable shape were already
  published in a ledger that had no withdraw verb — so `docreview.store` grew
  `withdraw()` + `fold(include_withdrawn=)` + a `FORMAT` version to get them
  back. Formats 3 and 4 — one entry per FINDING, one sentence and one question,
  no rows — landed at a median of 126 chars. Three rounds of Arthur's time
  bought what one paste would have. Its corollary: **the unit of a question is
  the act that answers it**, not the cell, not the document.

- **A fold fixed on one surface is not fixed; find every surface that builds
  its own.** `_reg_fold` was written on 2026-09-25 after five of the eight
  front-page parties' returns — $144,479.42 — folded to no party and were
  dropped in silence. The party page was moved onto it that day. The home grid
  was not: `influence_parties` kept a narrow map built inline, and went on
  dropping **$96,046.69** (Te Pāti Māori $58,775.42, Vision NZ $37,271.27) into
  the same silence, through the front-page chart and the party headline it
  feeds. The returns it could not place were the ones with NO ITEMISED ROWS,
  where the label falls back to what page 1 says. **When a shared predicate is
  written to fix a defect, grep for every place that was doing it by hand and
  move them all in that commit** — and pin it with a test that fails on the
  SHAPE (a second inline fold), because no fixture can hold the money.
  (2026-09-29.)

- **Draw the data and the gap acquires a shape.** The $96,046.69 above had
  survived two surfaces and a dedicated ruling. It was found the hour a
  histogram was put on the party page: a missing row in a table reads as a
  party that filed nothing, and five grey bars in a row do not. The same week,
  format 4 of the gold questions was only recognisable as right once one was
  rendered. **A visualisation is an instrument, not decoration — build it early
  on data you already believe.** (2026-09-29.)

- **A zero someone filed and a zero you have nothing for are different facts,
  and only one of them is a number.** Vision NZ filed $0.00 for 2019 and 2021;
  it also has years the register would have held nothing for. Drawn as a flat
  bar both read "received nothing", which is a claim the product cannot make
  about the second. The chart draws a filed NIL in the party's colour and an
  absence in grey, and the hover names which it is. Same rule as ruling 325 and
  as `mp-gap`'s *"a gap, not zero"* — it just has to be re-made in every new
  visual idiom, because a chart has no null. (2026-09-29.)

- **A tooltip the platform draws is a fallback, not a readout — and a position
  that depends on two measurements in different units should be pinned, not
  computed.** Told the figure could live on the hover instead of in a caption
  under the chart, I deleted the caption and left the native SVG `<title>`,
  which waits about a second, renders outside the page's design, and is found
  only by someone who already knows to wait: *"the hover number has
  dissappeared."* Then, floating the replacement card above the hovered bar,
  its position depended on the BAR's height in viewBox units and on the CARD's
  height in CSS pixels, which changes with how its own text wraps — a threshold
  tuned against one card was 30 px wrong for a narrower one that wrapped to
  four lines, and it escaped the chart. Pinned to the plot's top corner,
  opposite the hovered year, it cannot overflow by construction and the eye
  learns one place to look. (2026-09-29.)

- **A band drawn at an edge the law moved cannot carry a trend — pick the one
  cut that holds across the whole window.** The donations-by-size map used the
  statutory categories, and every edge in them changed in 2023 (itemisation
  $15,000 → $5,000, the within-10-days cut $30,000 → $20,000). Measured, its
  $5,000–$15,000 band went from $163,950 over 16 rows in 2022 to $3,240,906
  over 365 in 2023: **donors did not change, the threshold did**, and the box
  published that as a shape. More than $15,000 is named in every year, so it is
  the only line that means the same thing throughout. Two corollaries. The
  statute says "more than", and `>=` would have pulled in 8 pre-2023 rows the
  law never required, into a band advertised as complete. And where a band
  mixes kinds of money — named rows plus one undifferentiated filed total —
  **say what the band is made of inside it, rather than adding a band**: the
  third band here would have been 0.5% of the money and invisible at every
  party's scale. (2026-09-29, PI-61.)

- **One fill per category, and never a second fill to carry a nuance.** The
  size map drew its lower band part solid and part hatched to show how much of
  it was a single filed figure — three visual states for two bands, which is
  what a reader has to decode before they can read anything: *"a solid brown, a
  striped brown and a dark green. this is confusing."* The nuance belonged in
  the block's own label, where it reads in one pass. **A fill answers "which
  category"; it cannot also answer "how much of this one is like that".**
  (2026-09-29.)

- **An answer, left on the page, becomes a standing explanation of an absence.**
  A fold on the party page explained why >$20k disclosures are not added to the
  totals. It was written the day Arthur asked why, and it was right; five days
  later it was clutter, because nobody arriving at the page is asking that
  question, and text nobody is asking for is the text a returning reader learns
  to skip. **When a surface answers a question that was asked once, put the
  answer where someone who asks it again will look** — the SPEC, the basis
  string, the doc — not permanently under the figures. Removing it cost nothing
  measurable: the figures stay served and the gate that holds two surfaces equal
  reads the payload, never the rendered section. (2026-09-29.)

- **A filename is what the publisher called the upload; the heading is what the
  filer said the document IS.** A hand-curated alias mapped the Commission's
  file stem `NNP` to the National Party, guessed from the initials. The
  document's own first page says **New Nation Party**, and the Commission's real
  stem for National is NZNP. Another party's financial statements sat on a
  front-page party's page for three weeks, under a basis reading `exact`.
  **When a document states its own identity, that outranks anything in its
  name** — the same lesson as `document-identity-is-bytes`, one level up.

  And the part worth more than the fix: **three general gates were tried for
  "catch the next wrong alias" and every one fired on the legitimate aliases**
  — 8, 4 and 11 false positives against 1 true. The good aliases (`greens`,
  `top`, `alcp`, `tpm`) are as loose as the bad one, so no string rule
  separates them. **When every candidate rule is noise, the honest output is a
  regression test on the case, a narrow test for the class you CAN decide, and
  the reasoning written where the next person will edit** — not a gate that
  reds the board for a reason that is not about the product. (2026-09-29.)

- **A layout that happens to be right because of how the data sorts is not
  right.** `SizeMap` packed bands squarified, and for as long as it had three
  bands it drew a clean stacked bar — because sorting by size produced one row
  per band by coincidence. The moment the order was fixed by MEANING (big
  donations on top, whatever their total), the packer put the two big bands
  side by side, since two bands summing to 99% of the area fit in one row.
  **When an arrangement only holds while an incidental property of the data
  holds, it is a bug that has not fired yet** — and a request to reorder is
  exactly what fires it.

  Its sibling, from the same change: **a heading should name what the reader is
  looking at, not the machinery that made it.** "Industry exposure, cascaded up
  from the donors" described ruling 226's mechanism; "from named donations"
  describes the picture AND states its scope, which the old one hid — only
  itemised rows carry a donor, so 71% of the money is not in that chart at all.
  (2026-09-29.)

- **Ranking and composition are different pictures; know which one the measure
  is.** A donut, a row-per-item bar chart and a single segmented bar are not
  three styles of the same thing. Industry exposure is a WHOLE BEING DIVIDED,
  so the donut had the right property and the wrong geometry (arcs around a
  corner, plus a key); one row per division fixed the geometry and lost the
  property — it ranks, and a reader cannot see a share. The single segmented
  bar keeps both. **Ask what the measure IS before choosing the marks.**
  (2026-09-29.)

- **A build that transforms six modules where it usually transforms hundreds
  has already failed — read the count, not the tick.** Splicing CSS rules out
  by string index cut inside a media query and left its closing `}`. Vite
  printed *"✓ 6 modules transformed"* and then died on
  `ENOENT ... rename 'pi.html' -> 'index.html'` — a filesystem error naming
  neither the stylesheet nor the rule, three steps downstream of the cause.
  **When a tool's error names something that could not possibly be wrong, look
  at the last number it printed before it.** (2026-09-29.)

- **If a chart needs a key that repeats every label and every figure, the key
  is the chart you wanted.** The industry-exposure donut carried a nine-row
  legend naming each division and its number, because a ring cannot be read
  without one — it answers "what share of the whole is this slice", by asking
  the reader to compare arcs around a corner, when the question was "which
  industries, in what order, and how far ahead is the first". One row per
  division — label, bar, figure — is that legend, with the comparison drawn
  into it. **A legend is a symptom: it means the marks could not carry their
  own names.** (2026-09-29.)

- **The "we don't know" row is the one a top-N cut will silently eat.** The
  exposure chart showed nine rows and the untagged remainder was appended
  ninth, so any subject with nine tagged divisions lost it: on National that
  was 1.11 of 3.78 — 29% of the exposure, bigger than every division but the
  first — absent from the chart. Pin the unknown OUTSIDE the ranking: last by
  position, never by size, never truncated. This is the same rule as the size
  map's grey band, and it had to be learned twice in one hour because it lives
  in the layout, not in the data. (2026-09-29.)

- **Label a category with what it IS, not with what you lack about it.** A
  band of anonymous, overseas and protected money was labelled "size unknown" —
  accurate, and it spent the one line the block had on an absence. When the
  sentence underneath that said what the money actually was got cut as
  redundant, nothing on the page could answer it any more. The band now prints
  the categories it actually holds, and a category with no money in it is never
  named. **Before deleting a line as redundant, check what it was the only
  carrier of.** (2026-09-29.)

- **A band too thin to see is a band that is not there — give it a floor, not
  an exile.** Drawn strictly to area, a 1.4% band came out ONE PIXEL tall:
  present in the legend, absent from the chart. I had argued against adding
  that band on exactly this ground, then shipped the problem by adding it
  without touching the layout. Every non-empty block now takes a minimum height
  from the tallest and carries its own figure and percentage, so the geometry
  is a few pixels generous and the number is not. The same rule killed the
  seven-band map this replaced, where three of five non-zero bands drew
  nothing. (2026-09-29.)

- **A decomposition that does not add up to the thing it decomposes is worse
  than no chart, because it is drawn.** The size map's blocks summed to
  $31,705,632 under a headline of $31,713,984, and its own payload carried both
  figures and showed neither. The $8,351 was Part A money the returns declare
  that our reading of their rows does not reach — two returns already flagged
  as not reconciling. Money with no size at all (anonymous, overseas,
  protected) has no honest place in an area chart either: it goes in a note and
  out of the denominator. **Serve the shortfall next to the area, every time.**
  (2026-09-29.)

- **A suite that stays green through a rewrite was not testing the thing.**
  `size_bands` — seven bands, the statutory edges keyed by year, the per-year
  reconciliation — had NO test of any kind, and the whole scheme could be
  replaced with 348 tests still passing. It was the UX marker that caught the
  shape, and only because it asserted a band count. **When you are about to
  rewrite something, run its tests FIRST and read what they actually pin; if
  they pass on the new code too, the gap is the finding.** (2026-09-29.)

- **THE SENTENCE AFTER AN INSTRUCTION IS USUALLY ITS REASON, NOT A SECOND
  INSTRUCTION.** Arthur asked for three formatting changes and wrote *"let's get
  rid of the notes for the 'current board'. We should only be using the party
  websites for the board."* I read the second sentence as a sourcing ruling and
  rewrote the board from three tiers to one — dragging three test files, four UX
  markers and a second page with it, and emptying two of the eight front-page
  boards. He meant it as why the notes were redundant. **The tell was available
  before any of it was written: the diff was an order of magnitude larger than
  the ask.** When a small request implies a large change, that gap is the thing
  to raise, in one line, before building. (2026-09-29)

- **SIZED BY ACCIDENT IS NOT SIZED.** Three separate instances on one page, all
  the same bug: the donor card matched the MP card because a layout effect
  MEASURED it and copied its pixels, so the page's proportions were a function
  of how many MPs a party happened to have; the Party Rules topics stretched to
  the tallest in their grid row (552px beside 2,894px on National); and the two
  column heads sat level only because both happened to wrap their basis line, so
  deleting one basis line put the cards 18px out of step on every party. If you
  cannot state the rule that makes a layout true, it is not true yet — and the
  rule needs a gate that RENDERS, because nothing else sees 18px. (2026-09-29)

- **A FLOOR NEEDS SOMETHING STANDING ON IT.** Giving the cards a `min-height` so
  every party's page has one shape turned an empty MP list into 512px of blank
  white, which reads as a load that failed, not as a party with no seats. The
  sentence explaining it already existed — under the card, where nobody looked.
  Whenever a container gets a size independent of its contents, ask what the
  empty case says, and say it inside the box. (2026-09-29)

- **"A NORMAL BROWSER WINDOW" IS A MEASUREMENT, SO MEASURE IT.** *"2 should fit
  vertically in a normal browser window"* cannot be met by a height in rem — it
  would pass on a tall monitor and fail on the laptop the request was written
  on. The height is viewport-relative and the gate renders at 1440×790, a
  1440×900 screen less its chrome. Turn a requirement phrased in the user's
  furniture into a number the harness can hold, and write down which furniture
  you assumed. (2026-09-29)

- **A STRING DESCRIBING A SORT IS NOT THE SORT.** The MP list carried "leader
  first (Christopher Luxon — the party's own roster), then A–Z by surname". The
  sentence could be right while the order was wrong. Deleting it cost nothing:
  the leading row already wears a 'leader' chip, which is the same fact where
  the eye is. Gate the behaviour, never the prose that claims it. (2026-09-29)

- **A MERGE THE MACHINE REFUSES IS A JUDGMENT, NOT A MISSING FEATURE.** The
  donor-spelling fold is mechanical by ruling — *"never fuzzily"* — so it will
  not join "John Tamihere" to "John Taminere", one letter apart in the SAME
  document. That refusal is correct: a one-letter difference is as often two
  people as one. The answer is not to loosen the rule, it is to record the
  decision — a curated table beside the mechanical fold, keyed on the fold's
  own output, carrying the party, the documents and what made it a misreading.
  And the table needs a test proving it folds NOTHING it was not given, because
  a curated table that catches a neighbour is a fuzzy fold in disguise.
  (2026-09-29)

- **THE SURFACE THAT DOESN'T CHANGE IS THE ONE THAT ISN'T WIRED.** The curated
  merge went into the one chokepoint every money surface folds through, and the
  party page — the page that prompted it — showed exactly the same eleven
  donors. That was the finding: the party page grouped donors with a SQL
  `GROUP BY donor_name` and had never folded spellings at all, while the
  identity page's basis line claimed in as many words that a fold group "is
  what the product already treats as one donor on every money surface". **When
  a change lands everywhere and one place is unmoved, the unmoved place is the
  bug** — 58 donor groups across eight parties had been showing double.
  (2026-09-29)

- **TWO TRUE NUMBERS THE READER CANNOT RECONCILE ARE WORSE THAN ONE WRONG ONE.**
  The size map said 35 donations; the donor list beside it had 11 rows. Both
  correct — one counts gifts, one counts givers — and nothing on the page said
  which was which, so the only available reading was that something was broken.
  Pick the unit the reader is asking in and use it everywhere, and keep the
  other in the payload as the figure's basis rather than on the page competing
  with it. (2026-09-29)

- **A COUNT TAKEN BEFORE THE FILTERS IS A COUNT OF SOMETHING ELSE.** The party
  page's "N named donors" came from the SQL's own `count(*)`, computed before
  the non-donor filter and before all three folds ran — so National counted
  "Loan of premises" as a donor, and the number above the list disagreed with
  the length of the list. Derive such a number FROM the thing it describes
  (`len(rows)`) rather than alongside it, and it cannot drift. (2026-09-29)

- **A BARE `except` TURNS A BROKEN QUERY INTO A DELIBERATE-LOOKING ANSWER.** A
  new cross-party count joined on a column named `party` when it is
  `party_resolved`; the except swallowed it, the result was an empty dict, and
  the topic order fell back to its editorial list — which looks exactly like
  the feature working. Caught only because the counts were printed while
  checking. Every fallback except LOGS, and the fallback itself gets a test.
  (2026-09-29)

- **A DUPLICATE IS ONLY A DUPLICATE WHERE THE OTHER COPY EXISTS.** Ruling 277
  kept every >$20,000 disclosure out of every donor total, because a s 210C
  disclosure is the same gift the annual return carries months later. Correct —
  and it silently hid $6.35m, because a year whose return is NOT YET FILED has
  no second copy: the declaration is the only public record. The rule was right
  and its SCOPE was wrong. When a rule exists to stop double-counting, ask which
  years actually have two records, and read that from the corpus rather than
  writing the year down — the panel now empties itself when the returns land.
  (2026-09-29)

- **A LANE THAT CANNOT CALL THE MODEL MUST NOT REPORT AN EMPTY DOCUMENT.** A
  constitution read ran twelve slices and returned "0 clause rows on 0 topics",
  which is exactly what a document with nothing in it looks like. Nothing was
  wrong with the document: `V3_DSN` was missing, the model gate failed closed on
  every call, and the log said *"every named source is below tier"* — a sentence
  about the SOURCES, when the cause was an unset variable. The estate had
  already built the answer (`policy_preflight`, 2026-09-25: "a broken lane is
  not a refused one") and this lane was not calling it. **Fail closed, stop, and say
  which of the two it is.** (2026-09-29)

- **A DOCUMENT WITH NO RECORDED SOURCE IS THE DEFECT — NOT THE GUESS THAT
  COVERS FOR IT.** Two constitutions arrived by hand with no URL. The extractor
  falls back to naming `elections.nz` as the outlet when a document has none,
  and I called that a misattribution and tore it out. **Arthur corrected me and
  he was right:** the Electoral Commission publishes every registered party's
  rules, because a party must lodge them to register — so for this class of
  document the default was a good guess, not a borrowed name. And a file locker
  is not a wrong source either: Labour's constitution is served through Google
  Drive from its own site, and Drive is the transport while the party is the
  publisher. **Where a document came FROM is the question; which CDN handed over
  the bytes is not.** The fix was never a cleverer default — it was asking where
  the file came from and writing it down. (2026-09-29)

- **"BESIDE" MEANS THE SAME TOP AND THE SAME BOTTOM — ASK, DON'T INFER.** Told a
  panel must sit beside the chart and the map and *"not extend beyond the map"*,
  I read it as "not beyond the SCREEN" and built sticky plus a viewport cap. That
  is defensible and it was not what was wanted: **Arthur, same day — *"align the
  list box with the height of the chart and the bottom of the map."*** Two ends
  named, so the height is the left column's and nothing about the viewport comes
  into it. A layout instruction with two nouns in it usually names two edges;
  when it is ambiguous the cost of asking is one line. Only the LIST scrolls
  either way: a panel scrolled to row 200 still has to say what it is and what it
  adds up to. (2026-09-29)

- **A SCROLL CONTAINER STILL OFFERS ITS WHOLE CONTENT TO GRID SIZING.** "Make
  this box exactly as tall as the other column" is `align-items: stretch` — and
  it silently does the opposite, because the panel's 236 rows count toward the
  row's max-content height even with `overflow-y: auto` and `min-height: 0`, so
  the row grows to the panel instead of the panel being fitted to the row. The
  box must be out of flow (`position: absolute; inset: 0` in a relative column)
  for its own content to stop voting on its height. Neither version looks wrong
  in the browser at one list length, which is why this one has a gate that
  renders and measures both ends. (2026-09-29)

- **AN ORDER OVER A MANGLED FIELD NEEDS A BOUND, NOT A REFUSAL.** I ordered the
  declarations by amount and wrote that ordering by date would be "an order built
  on OCR". Asked for recency, the field turned out to read in four shapes and 230
  of 236 parsed; the six that did not are answered by the Commission's file name.
  But two rows read three weeks INTO THE FUTURE, and unbounded they led the list:
  the two worst reads on the page at the top of an order that exists to put the
  newest first. Money cannot be received in the future — the same judgment
  `year_from` already made about an OCR "2035". **The argument for not sorting was
  really an argument for reading the field properly and saying what could not be
  read.** (2026-09-29)

- **READ THE REGISTER'S OWN INDEX BEFORE OCR-ING ITS SCANS.** The feed had been
  capturing the Electoral Commission's table of >$20k declarations for six weeks
  and using it ONLY to find the PDFs — while the register was built out of OCR of
  those photographed forms. The table carries every field in clean text. What the
  scans cost, measured over the open year: the table says 127 declarations and
  $6,964,741.50, the OCR said 243 rows over 114 files and $6,351,420.88; one
  declaration of $22,040 became 20 rows, and over 154 single-row declarations the
  amount disagreed 37 times — $7 for $24,500, $820,500 for $20,500. **A page you
  already fetch is a document: read all of it, not just its links.** (2026-09-29)

- **A DECLARATION IS ITS PARTY, ITS YEAR AND ITS TOTAL — NOT ITS FILE NAME.** The
  Commission renames its own assets between weeks: `G_Garing_24_July_2026-final.pdf`
  is the table's `J_Garing_24_July_2026-amended.pdf`, and the scan had split that
  one $23,000 declaration into its three component gifts — so neither the file
  name nor a row-by-row amount match could tell they were the same money, and it
  was counted twice. The total saw it. The total ALONE is not enough either: IEF
  Limited's $23,000 is also the Maritime Union's, so the match needs one shared
  identifying word (four letters or more, and not "limited", "group" or a month).
  (2026-09-29)

- **WHAT THE PANEL CANNOT SHOW, IT COUNTS.** 7 of 243 declarations could not be
  read and 10 name no registered party. Dropping them would have made a clean
  list that was quietly $466,000 short of the register. The filter that excludes
  them is the SAME one the donor totals use, so the panel and the totals are one
  set — two surfaces disagreeing about which rows exist is worse than either
  being incomplete. (2026-09-29)

- **A card is not closed while any document about it is still stale by one
  line.** Two found in a sweep of my own closes: T7.59 was added to the board
  with no row in `FLEET.md` (the watcher table ruling 28w exists to make a
  unit's absence visible — an arm nobody has a row for is an arm nobody will
  maintain), and `RETURNS_FLAWS.md` still said 25 unreadable lines when the
  load now produced 26 and $5,000 more — **exactly the row the card had just
  added**, so the one document a reader would check to see the effect of the
  change denied it had happened. The DOCS question of ruling 326 is asked
  before the close for this reason; answering it honestly means opening the
  file, not recalling it. (2026-10-05, C427/T7.59.)

- **A gate that matches on a format will say "nothing owed" when the format is
  wrong.** Four-questions blocks written as `- **LOCATION.** text` — the
  period INSIDE the bold — matched **zero of four** labels, and
  `ops/four_questions.py --check` passed, because a block it cannot parse is
  indistinguishable from a card that owes nothing. The labels are exactly
  `- **LOCATION** — text` under a heading of exactly
  `**Four questions — C<nnn>.**`. A parser whose failure mode is silence needs
  a could-have-seen-it assertion: `owed()` now also matches the live
  register's STATUS cell, and the test fails if no block carries any
  recognised label at all. (2026-10-05, C509.)

- **A lesson you cannot grep is a lesson you do not have — and a discipline
  whose correct execution costs 99 KB is an intention.** MO.md has said *"read
  the lessons for this area FIRST"* since it was written, and CLAUDE.md asks
  for the relevant section before touching that area. Both were true and
  neither was happening, and the reason was not laziness: the honest reading
  was 99 KB and 122 rules for anything touching a gate, and the fast path —
  grep — silently missed **177 of 318 claims**, because a claim is a bold
  sentence at the head of a WRAPPED paragraph and grep is line-based. A miss
  reads exactly like *"there is no rule about this"*, the most expensive wrong
  answer a corpus whose whole value is recall can give. The cure was mechanical
  (`ops/lessons_index.py`, one line per rule with a content-stable `#id`;
  `ops/lessons_for.py`, retrieval keyed on a card, its paths or your words),
  not a firmer resolution. **When a practice everyone agrees with is not
  happening, price its correct execution before blaming anyone for skipping
  it.** (2026-10-06, ruling 359.)

- **Measure a retrieval tool against real pairs, publish the misses, and never
  report one blended number.** `lessons_for --selftest` runs eight pairs — a
  card closed here, and the claim of the rule that would have warned it — and
  scores **5 of 8, 2 of the 5 a rule ALREADY covered.** That is the ceiling of
  lexical retrieval and it is printed on every run, because the alternative is
  a tool that says "here are your lessons" while the one that mattered is
  absent: mode 11, inside the machinery built to stop mode 11. The miss is
  structural, not a bug — C037's card said *"embed-backfill runs at 2/s, tune
  the rate"* and its lesson says *"a lane that cannot call the model must not
  report an empty document"*, with not one shared word, because the card
  described a performance question and the defect was a reporting one. Adding
  the files' own vocabulary to the query was tried and MEASURED: some ranks
  improve, others worsen, none of the three misses is fixed. So the ranked list
  is the specificity layer and the always-printed layers (the twelve failure
  modes; every claim in the affine sections) carry recall. (2026-10-06.)

- **A "what's new" filter over a long window returns the corpus — rank it,
  don't list it.** `lessons_for --since` was built for ruling 359's second
  check and listed every rule filed since the date, newest first. Run on C216,
  raised 2026-09-19, that is **210 of 321 rules** — no more useful than reading
  the index, and worse, because a wall of output reads as though the tool had
  answered. The question is never "what is new" but "what is new AND about my
  card", so the fresh set is scored by the same relevance as everything else
  and the remainder is COUNTED (35 of 210 for C216). Any time a filter's
  selectivity depends on how old its input is, check it on the oldest input you
  have. (2026-10-06.)

- **A STUB THAT ANSWERS ONLY THE CALLS IT WAS BUILT FOR MAKES THE NEXT REAL READ
  LOOK LIKE A BUG.** `_Conn.execute` in the page-read loader's tests returned a
  value for `INSERT` and `None` for everything else, which was true of the loader
  until C515 added a read-back pass — and then five tests died on `'NoneType'
  object has no attribute 'fetchall'`, pointing at production code that was
  correct. The fix belongs in the stub (one place, now answering any read with an
  empty result), not in hardening the real function against a fake connection:
  tolerating `None` from `execute` would defend against something psycopg never
  does and would mask a genuine breakage. **When a test double fails on new
  production code, ask first whether the double is the thing that is wrong.**
  (2026-10-06, C515.)

- **WHEN EVERY ENTRY IN A CURATED LIST NEEDS THE SAME EDIT, IT WAS NEVER DATA — IT
  WAS A RULE BEING COPIED.** The known-alias tier gives each group a `types` list
  saying which minted types its forms may match, and C406 was raised because nothing
  measured whether those lists covered the types the corpus actually produced:
  measured on the live graph, **118 entities and 7,454 claims across 33 of the 36
  groups** sat outside their own fold — not backlog, INVISIBLE, because the wave's
  `WHERE e.type = ANY(types)` never selected them. `Te Pāti Māori` person 1,044
  claims, `Te Puni Kōkiri` person 779, `Air New Zealand` people 265.
  The obvious fix is to measure the gap and extend the lists. I started doing exactly
  that and stopped at the count: **24 of the 30 organisation groups needed the same
  two values**, `person` and `people`, and the file's own docstring already said why
  ("NER habitually mistypes Māori org names as persons — the group fixes that too").
  A value needed by every member of a set is not a per-member fact. Putting it in
  thirty literals fixes today and leaves the thirty-first group to be added without
  it, which is the same hand-maintenance that failed; one `match_types()` covers the
  group somebody adds tomorrow. **Count how many entries need the edit before writing
  it: all of them means you are about to copy a rule instead of stating it.**
  **The widening STOPS where a real alternative begins, and the biggest row is the
  trap.** `Tāmaki Makaurau` typed person carries 1,605 claims and is the ELECTORATE,
  not Auckland, so a place group matching person would fold an electorate into a city
  — the single largest stranded row in the corpus is the one that must not move. The
  remaining 4,064 claims are reported as needing curation and nothing folds them.
  *Paid for by:* 2026-10-07 (C406), raised 2026-09-21.

- **A `sed` RANGE WHOSE CLOSING PATTERN NEVER MATCHES DELETES TO END OF FILE, AND IT
  EXITS 0.** Removing one five-line entry from `data-layer/docs/board/triage.py` with
  `sed '/^"C107": /,/^    "non-emitting lanes are uncounted.*$/d'` deleted **441
  lines** — C107 to EOF, the `CLUSTERS` block with it — because the closing pattern
  was my PARAPHRASE of the card text and the entry actually says "non-emitting PATHS
  are uncounted". One word. sed does not fail on a range that never closes; it finishes
  quietly with everything after the opener gone, and the next command in the same
  chain printed its own success.
  **The habit that caused it is quoting from memory to build a matcher.** Four cards
  this session were closed by deleting a triage entry, and each `sed` range was typed
  from what I remembered the row saying. The replacement is to extract the exact text
  first and assert on BOTH ends — the repair did
  `assert block[0].startswith('"C107": (')` and `assert block[-1].endswith('contested
  facts.")),')` before writing — or to edit structurally rather than by line range.
  **It was cheap for one reason only: the file is Python that `ops/board.py` imports,
  so the pre-push board gate hit a `SyntaxError` and refused.** The same `sed` against
  a Markdown register would have pushed, and the loss would have been found by somebody
  wondering where a card went. A destructive edit is only as safe as the gate standing
  behind the file it edits.
  *Paid for by:* 2026-10-07 (C107's close).

- **A CARD THAT NAMES THE INSTANCES IT FOUND IS A SAMPLE, NOT A COUNT — WRITE THE CENSUS
  AND READ THE NUMBER.** C116 named two `registers.*` tables written from `ops/` outside
  the package that owns them, and the 2026-09-19 triage confirmed both by reading the
  live columns. One regex over the tree found **nine**: `party_board_asserted`,
  `candidates_announced`, `party_officials`, `mp_aliases`, `mp_tenure_events`,
  `mp_org_resolutions`, `body_aliases`, `party_site_documents` and `suppressed_names`.
  Two have only a RETIRED writer, and `suppressed_names` is written by
  `query/influence/suppression.py` — **the serving layer producing a register it also
  reads**, which is the sharpest of the nine and was in nobody's card.
  This is the third time in one day that the census found several times what the card
  named: C435 said one unbounded job and there were four, T7.25 watched 2 of 15 register
  families, and here two of nine. The pattern is the same every time — a card records
  what somebody HIT, and nothing had asked how many there were. **The first deliverable
  of a "there are N of these" card is the query that counts them**, and it costs minutes.
  *Paid for by:* 2026-10-07 (C116), carded from the day-logs and verified STANDS in
  September — on both instances, neither of which was the interesting one.

- **DEAD MODULES KEEP EACH OTHER ALIVE, AND THE PACKAGE DOCSTRING IS WHAT SELLS IT.**
  The news dashboard-API lane was retired with #129 on 2026-08-28 and `newsscrapers.run`
  replaced it. Five modules then sat in `ingestion/news/` for six weeks importing one
  another — `backfill_era` → `daywalker` → `ingest` → `client` — so every one of them had
  an importer and none of them had a consumer. `first-run.sh` went on calling
  `news.ingest` behind `|| true` until 2026-09-19: a fresh box ran a retired lane, failed,
  and said nothing. **"Is anything importing this" is the wrong question in a cluster;
  ask what runs it** — a unit, a timer, a script, a live caller — and treat a cycle of
  mutual importers as one candidate, not five.
  The package's `__init__.py` described `client.py` and `ingest.py` and nothing else: the
  two deadest files in the directory, named as the package's purpose. A docstring listing
  what USED to be there is how a retired lane reads as live to everyone who opens it, and
  it costs nothing to correct on the way past.
  **And the card had named four of the five.** `news/ingest.py` was dead too — the census
  of `from news.*` imports outside the package found exactly three live modules
  (`review_sources`, `extract`, `reconcile_ledger`), so the card's deferred second half,
  "split the live DB helpers out", turned out to be empty: there were none to split. The
  reason it had been deferred did not exist.
  **Retiring a test that pins a rule costs the rule unless you say where it went.**
  `test_backfill_era_dsn.py` pinned `V3_BACKLOG_DSN` beating `INCOMING_NEWS_URL` — paid
  for on 2026-08-22, when a unit moved to an EnvironmentFile connected to node2's
  read-only STANDBY and died on its first INSERT. The rule survives in `estate_dsn`
  ("the first name the environment sets", no default); what no longer has a test is the
  ORDER callers pass the names in, and three live register derives pass the indicted one
  first. Written into the retired directory's README beside the module, and carded.
  *Paid for by:* 2026-10-08 (C206), six weeks after the lane stopped running.

- **A BUCKET IS NOT A SUBJECT: WHEN ONE SECTION HOLDS 41% OF A CORPUS, READ ITS
  ROUTING RULE BEFORE SPLITTING IT BY SIZE — AND THE SECOND CAUSE IS THAT THE
  CLAIMS GOT LONGER.** `3-measurement-gates.md` reached **182 of the corpus's 439
  rules and 192 KB** against T7.38's 160 KB one-read ceiling, and it was the only
  section over. That is not because measurement is 41% of what this estate learns.
  Its routing pattern in `ops/lessons_for.py` is
  `^tests/|test_|gate|invariants|board|audit` — **it matches the thing every card
  does**, because every card here closes with a gate, so it had become the default
  bucket for anything that was not obviously a unit, a source or a card process.
  Two real subjects came out of it byte for byte (reading documents; counting and
  populations), 30 claims each, and the remainder sat at 129 KB with headroom.
  **THE HONEST SECOND CAUSE WAS MINE.** The median claim ran 1,253 B across claims
  1–40, fell to **449 B** across 81–120, and reached **2,740 B across the newest
  twelve — eight of them filed in the five days to 2026-10-09**, by me, in this run
  of card work. The newest twelve alone were 32.6 KB, more than the entire
  document-reading subject (19 KB across 30 claims). A section splits once; a habit
  of writing 2.7 KB where the corpus median is 780 B refills it, and the next split
  is then arbitrary because no subject seam is left. **Measure the length
  distribution before concluding a corpus has outgrown its container.**
  And the card's own stated blockers were both false, which is worth the check every
  time: *"`ops/lessons_index.py` carries a HARDCODED `SECTIONS` map (no glob)"* — it
  does not; `SECTIONS` is the DIRECTORY and both generators `glob("*.md")`. What is
  hardcoded is two naming maps, `HEADINGS` for display and `AFFINITY` for routing,
  one line each. **The gate for the split was retrieval, not size:**
  `lessons_for.py --selftest` scored 5 of 8 real pairs before and 5 of 8 after.
  *Paid for by:* 2026-10-09 (C551), which also found the index's own table rotted —
  it said section 3 was 99 KB when the file was 192 KB and the corpus 294,000 B when
  it was 486,204. A generated artifact nothing checks is a hand-maintained one with
  extra steps, so `--write` now emits that table and `--check` fails on it.

- **BEFORE PUTTING A SCOPE QUESTION ON THE BOARD, GREP THE CLOSED CARDS FOR IT — AND
  AN ARM THAT JUDGES ROWS A RULING REMOVED FROM SERVICE WILL JUDGE THEM
  ARBITRARILY.** T7.7 reported `merch.opportunity.org.nz` as a new wholly-undated
  source for weeks, and I wrote the verdict text as an open question: *"whether a
  merch subdomain is a source at all"*. Arthur: *"It is not. I ruled this a while
  ago."* **C311, 2026-09-22** — *"we dont need merch store data"* then
  *"quarantine"* — closed the same day, with commerce subdomains refused at capture
  and `party_shop_quarantine.py` applied to 436 documents, 811 claims, 6,569
  mentions and 281 entities. The ruling was three weeks old, the sweep had run, and
  `grep -rn merch` over the closed register would have found it in one command. A
  question already answered costs more than an unanswered one: it asks for the same
  judgment twice and implies the first was not recorded.
  **The defect underneath was real and better.** All 406 commerce rows sit at
  `pipeline_status='held'`, and the arm counted them, so its verdict was decided by
  a technicality: `merch.opportunity.org.nz` was flagged with 56 of 56 held, while
  `shop.greens.org.nz` escaped with **308 undated rows of 311** because three happen
  to carry a date and the discriminator is "wholly undated". Same ruling, same
  quarantine, opposite verdicts. **A held row cannot be served, so a missing field
  on one is not a live fault — the hold is the whole remedy** (the shape of ruling
  290). The arm now excludes `held` and reports their count instead of hiding it,
  and the one finding that survived is genuine: `greens.org.nz`, the 52-row minority
  label of the pair C530 measured, wholly undated because its pages are menus and
  candidate profiles.
  **SECOND INSTANCE THE SAME DAY, in a gate rather than an arm (C116).** Its census
  of "registers written from outside the package" counted NINE, and the card's
  residue read *"fold in nine lanes"* — but two cannot be folded because nothing
  live writes them: the only writer of each sits under `ops/retired/` (ruling 157
  disables and KEEPS) and ruling 194 withdrew the Wikipedia source behind both.
  Measured: no unit, no bootstrap entry, no non-test caller. An inert INSERT counted
  beside a live one makes one number mean two things, and the figure that matters —
  outside writes by code that can RUN — is **seven**. The split carries an assertion
  the single number could not: a writer that LEAVES `ops/retired/` is live debt
  again, proven by reviving one and watching the gate name it.
  *Paid for by:* 2026-10-09 (C554), where the permission half of the card was sound
  work and the scope half should never have been asked; and C116 the same day.

- **A CITATION IS NOT A HARVEST, AND THE INDEX CITES EVERYTHING BY DESIGN.** C024
  asks every file in `docs/records/` to carry a `HARVESTED:` line naming where its
  durable content went, with 71 left owing one and the card's own constraint that
  *a fabricated harvest claim is worse than a counted gap*. The sweepable subset is
  the one with a DOCUMENTED harvest, so the question is which records a durable home
  cites — and the first answer was **69 of 71, which means nothing**: almost every
  hit was `docs/INDEX.md`, the estate map, which lists every record **by design**.
  Being in the catalogue is evidence a record EXISTS, not that its content moved.
  **Excluding the catalogue the shape is completely different:** 24 cited by
  doctrine, a card register, a SPEC or CLAUDE.md — and **47 cited by nothing durable
  at all**, which is not a reading job but a backlog of findings that were never
  carried anywhere.
  **And the 24 do not all mean the same thing.** Of the 13 cited by doctrine, ten
  CARRY the record's claim — the lesson states the rule and cites the record as its
  scar, `truncation-detection at 4× the cost (AUDIT_2026-08-16 §3)` — and those are
  harvested. Three only POINT at it: MO.md says *"Why: DIAGNOSIS_2026-09-20.md"*,
  which keeps the record as the HOME of the detail, and
  `PLAN_2026-08-20_MASTER.md` is itself a durable reference record. **So the
  direction of the citation decides, and it has to be READ.** A sweep that counted
  citations would have written ten true lines and three false ones, and a false
  harvest claim is the thing the card exists to prevent.
  *Paid for by:* 2026-10-09 (C024), 71 → 61 on a documented basis, with the arm's
  ceiling ratcheted so the ten cannot come back.

- **A POINTER FILE GETS READ AND THE FILE IT POINTS AT DOES NOT — SO A PLAN CAN BE
  DEAD FOR TWENTY DAYS WHILE EVERY SESSION IS TOLD IT IS LIVE.** `CLAUDE.md` is
  loaded into every session and said *"The live plan is
  **data-layer/docs/MUSTER_3_QUEUES.md**"*. That document's own first paragraph has
  said since 2026-09-20: *"CLOSED — RULING 318 … This document is no longer the
  live plan and no session opens against it."* Both sentences were true at once for
  three weeks, and `docs/INDEX.md` carried the same error (*"THE LIVE COLLECT"*).
  **Nobody followed the pointer to the file**, which is exactly what a pointer file
  is for and exactly why its claims rot unchecked: the orientation is read a
  hundred times and the target once.
  **THE TELL IS A DOCUMENT THAT DESCRIBES ITS OWN STATUS, AND NOTHING CHECKS THE
  TWO AGAINST EACH OTHER.** `test_doc_drift.py` checks that every document is
  INDEXED and that generated tables are current; no gate asks whether a document
  called live by its referrer agrees that it is live. The banner and the pointer are
  two statements about one fact, which is #8a634c's shape in prose.
  **AND THE SUCCESSOR'S PREMISE EXPIRED WHILE NOBODY WAS WORKING IT.**
  `MUSTER_4_PLAN.md` was built on *"the find rate has caught the close rate —
  2026-09-20: 7 closed, 7 opened"*, which was true that day and shaped the whole
  draft (instruments before card work). Measured 2026-10-10: **239 closed for 31
  opened.** A plan's founding measurement has a shelf life, and a draft left
  unopened for three weeks is a draft whose premise nobody re-took. **Re-measure the
  founding fact before inheriting the shape it justified.**
  *Paid for by:* 2026-10-10 (C558). Found by reading the file the pointer pointed
  at, which took one command.

- **TWO SEARCHES OVER ONE SITE, AND THE ONE THE PUBLIC USES IS THE OTHER ONE.**
  "NZ First" was fixed in the live API (`influence/browse.py`), verified against
  `:8300`, released — and `followthemoney.nz` still answered *"Nothing filed
  under that name"*. The published site is a STATIC snapshot whose search runs
  in the BROWSER over `data/search-index.json`, which is a different matcher
  over a different list: it held each party's registered name and nothing else.
  Fixing the server's search does not fix the site's search, and the only reason
  this was caught is that the fix was re-verified ON THE PUBLIC URL rather than
  on the box ([[the-site-is-followthemoney-nz]], the same failure shape as
  2026-10-11's "i dont see it on my computer").
  **Then the release gate caught the fix's own gap**, which is the part worth
  keeping: the first cut built the snapshot's aliases from the payload's
  `abbreviation` + `variants`, and `pi_search_gate` refused the deploy with
  *"'top': the published search missed 1 of 9 server hits it holds pages for,
  e.g. ['Opportunity Party']"* — because the Opportunity Party's EC abbreviation
  is "Opportunity", and "TOP" lives only in the register's fold. Nothing
  deployed, nothing flipped. The alias set is now served once
  (`base.party_search_aliases`, the register's fold minus our own filing noise)
  and both searches read it.
  *Paid for by:* 2026-10-12. Two tells: **when a product has a static mirror,
  every behaviour has two implementations and a fix is not done until both are
  measured**; and a gate that refuses a deploy over one missing search hit is
  worth more than a gate that passes a site nobody searched — it found in
  thirteen minutes what the live API had hidden from me.
