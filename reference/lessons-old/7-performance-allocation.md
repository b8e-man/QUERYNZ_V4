> Part of [LESSONS](../LESSONS.md) — living memory, one section per file
> since 2026-10-04 so that "read the relevant section" is a thing a reader
> can do. The rules of the file, and why it exists, are in LESSONS.md.

## 7. Performance & allocation

- **A free slot on the wrong model is not a free slot — and a slot too small
  for the ANSWER is not one either.** node2 runs the same Qwen weights on two
  cards at different geometries: 50,176 tokens per request over 2 slots, and
  16,384 over 8. A model name cannot tell them apart, and the balancer prefers
  the 8-slot card whenever the fleet is busy because it has more free slots. A
  job asking for 16,000 output tokens passes a `max_tokens <= n_ctx` test on
  the small card and gets 384 tokens for the page it is reading. **Size a
  request by prompt PLUS answer, against the card's PER-SLOT context**, and
  when the tokeniser is not to hand, estimate high: over-estimating moves work
  to the bigger card, under-estimating truncates an answer silently.
  (2026-09-26, C413.)

- **A filter against a silent fault can cause a loud outage.** The first cut of
  that size test measured the prompt as `len(body)`. A `page_image` call
  carries a base64 page — 1.4 MB of body for a picture worth a few hundred
  tokens — so the vision lane would have asked for half a million tokens of
  room, matched no backend, and stopped. **When you add a filter, ask what the
  WIDEST request in the estate looks like, not the typical one.** (2026-09-26.)

- **The door must say which card answered.** 86% of this estate's model calls
  could not, so establishing that a vision model had answered 27,306 reviewer
  adjudications took a second ledger and a backfill by entity id. Two response
  headers cost nothing and make it a fact the caller holds at the time of the
  call. (2026-09-26.)

Read this before tuning anything, before adding a worker, and before
concluding that something is slow for the reason it looks slow. These
lessons were spread across four sections until 2026-09-24 (C022), which is
why the same convoy was paid for three times. Records written before that
date cite them under §1, §3 and §5 — the records are not rewritten, so a
reference to "LESSONS §3, the convoy family" means this section.

- **No lane holds a lock, a transaction or a snapshot across slow work — and
  the convoy moves to the next-hottest point when you fix one.** The article
  transaction holds NO advisory lock, ever; serialisation genuinely needed
  (minting) lives in its own milliseconds-long transaction on a side
  connection; conflict-safe writes (ON CONFLICT) need no lock at all. Any
  per-entity write that can land on a hot shared row is COLLECTED during the
  entity loop and FLUSHED sorted at the transaction tail. Re-measure the wait
  profile after every convoy fix. Run hygiene, GC and reconciliation AFTER the
  main tick commits, in their own transaction, and sequence executor-calling
  waves AFTER the drain, never beside it.
  *Paid for by:* THREE bites of one family — alias row locks held to commit
  (2026-08-09); the mint lock on the article connection (2026-08-23, where a
  docset whose documents all mint the same NEW forms convoyed 13–16 of 16
  shards in every sample); and the key-miss lock in `_entity_id` (2026-09-01,
  era-5: per-worker CPU 14.6% of a core ≈ 2.3 effective workers out of 16),
  where a missing key KEEPS missing and the hot pending keys (geonames NZ:
  1.19M proposals; LINZ Wellington/Auckland) sit in nearly every news doc. The
  waits are invisible to every mechanism gate — nothing deadlocks, it is a
  polite convoy — and to docs/hour on small cohorts; only wall-time profiling
  (py-spy --idle) or pg_locks waiter→holder edges show it. Minutes after the
  deletion went live the convoy came back as a ROW lock on
  `entity_key_proposals`' n_seen upsert (26/36 active samples). Pinned:
  test_key_miss_lock_free, test_mint_side_connection · an alias table that
  rewrote every row every tick — 63,346 rows carrying 3,371,681 updates — where
  "serialization conflicts are normal" held until watermarking made it O(delta):
  ~40 minutes to 15 seconds · unindexed anti-joins in a hygiene pass that
  stalled the resolution spine for an hour and threatened already-paid judge
  work · under READ COMMITTED, mentions vanishing between the `INSERT..SELECT`
  and the `DELETE`, plus FK aborts and retype-vs-in-flight-cast races
  (reconciliation/SPEC.md) · 2026-09-02: an orphaned 2.5h analytical SELECT
  (gazette-derive's graph-feed phase, its client gone) held `backend_xmin` 326k
  transactions back, so autovacuum could reclaim nothing —
  `entity_key_proposals` reached 999,729 dead vs 781,747 live, alias_link 4.87M
  dead, every tail-flush upsert walked those dead chains UNDER the row lock,
  Lock:transactionid grew to 13–15% of non-idle backend time, in-span overhead
  went 11ms → ~670ms per doc and the fleet fell ~84k → ~35k docs/hr. DETECT
  with `max(age(backend_xmin))` + the hot tables' `n_dead_tup`; FIX with
  `pg_cancel_backend(<stale pid>)` THEN `VACUUM (ANALYZE)` — order matters, the
  first vacuum run while a SECOND old holder still lived reclaimed zero, and
  the re-run after the census reclaimed 1.19M → 4,126 in 36s. The `statement_timeout` half of the
  prevention was BUILT on 2026-10-10 (C558 PF-3): 27 unit drop-ins and arm
  T7.75, detection included. Still owed: gazette-derive in the era pause list,
  hotter autovacuum. Related trap: the
  fleet's backlog connections sit in ONE open transaction for the worker's
  whole life (22h36m observed) — their snapshots refresh per statement, so any
  long statement on such a connection becomes this bullet.
- **A UNIT'S OWN DEADLINE MANUFACTURES THE ORPHAN IT GETS BLAMED FOR.**
  `TimeoutStartSec` kills the CLIENT; postgres keeps executing the statement,
  because a backend learns its client is gone only when it next writes to the
  socket and a long aggregate writes nothing until it finishes. So the
  2026-09-02 incident above was not bad luck: `gazette-derive` carried
  `TimeoutStartSec=7200` with nothing under it, the SELECT passed two hours,
  systemd killed the client and the backend held its snapshot on. The fix is
  not a longer deadline or a shorter one — it is a `statement_timeout` BELOW
  the deadline, so postgres aborts first, releases the snapshot at a known
  moment and the lane logs an error instead of leaving a ghost. It can shorten
  nothing that would have survived: at the deadline the client was killed
  anyway. Measured 2026-10-10: **43 of 43** database-touching python units
  carried a deadline and not one carried a timeout, five weeks after LESSONS
  recorded the prevention as owed. The requirement lands on deadlines over 30
  minutes, because this primary burns ~3.3M xids/day so the incident's 326k
  xids were ~2.4 HOURS of held snapshot and a unit systemd kills in a minute
  cannot do the harm. `ops/db_deadlines.py` generates the drop-ins; T7.75 reads
  the INSTALLED copies, not the repo's, because a unit is installed by copy.
- **A batch in one transaction loses all of it to a timeout — and its audit
  ledger cannot say when anything happened.** `resolve auto` merged a whole
  wave inside one transaction under `TimeoutStartSec=4h`; the kill rolled every
  merge back, so 609 merges landed one night and zero the next, and the next
  run met the same duplicate forms and lost them again. Nightly, on a schedule.
  The second half is worse and was invisible: `merged_at DEFAULT now()` is the
  TRANSACTION's clock, so all 200 merges of one wave carry one identical
  timestamp — 41,388 recent merges share 122 stamps, the biggest blocks exactly
  2,000 rows wide, which is the old commit checkpoint. "Reversible, audited" is
  a standing rule, and the audit's TIME was a batch marker. Commit per item:
  a kill costs one item and the ledger tells the truth. Make the checkpoint a
  PARAMETER, because the trade it makes (commit rate, paid in WAL on the
  primary, on the standby's replay and in the archive) is a judgment call and
  belongs to whoever is paying for the disk.
  *Paid for by:* 2026-09-20's lost 2h49m wave; fixed and measured 2026-09-21
  (A1, `RECONCILE_COMMIT_EVERY`, `ops/wal_budget.py`, arm T7.51).
- **Measure a database job by what it makes the DATABASE do, not by its own
  log.** The A1 measurement showed the merge path doing three sequential scans
  of an 18 GB table per merge — 43 M tuples a scan, 258 M tuples read in 30
  seconds — because `alias_sighting`'s only index leads with `article_id`. The
  wave's log says "merged N"; `pg_stat_user_tables.seq_scan` and
  `pg_stat_activity` say what it cost. A job that looks slow for one reason is
  usually slow for another.
  *Paid for by:* 2026-09-21, A1's before/after run (the index is A2, Arthur's
  call).
- **No optimisation work closes without an END-TO-END throughput gate that
  would fail on the regression it exists to prevent.** Every mechanism gate can
  be green while the goal is missed.
  *Paid for by:* 2026-08-31, Arthur's ruling on the night the era-5 wave went
  live — the B5 job-allocation work (the lock-contention bench, the heavy-lane
  semaphore, the size-aware AIMD controller, the three-tier wave) was built,
  unit-tested, live-verified and bench-instrumented, and every instrument gated
  a MECHANISM: deadlocks, exhaustions, ceiling convergence, lease safety. The
  first real wave measured ~10.5s of per-document overhead against 11.0s of
  actual extraction work — ~49% wall-clock waste at the mid tier, a projected
  40+ days of pure overhead across the 5.64M-doc light tier.
  Docs-per-hour-per-worker was never behind any gate. RULED the first work item
  of the next muster (ruling 143); RESOLVED IN FLIGHT (ruling 144 → landed
  2026-09-01) once Arthur named the metric — CPU utilisation, size-independent
  — with the overnight recorder plus a 60s wall-time profile finding the root
  cause in hours. The durable gate stands: tests/test_throughput_gate.py, 65%
  of a core median fleet CPU over a recorded drain.
- **Model-lane throughput is duty cycle, prefix stability and per-item
  independence — not raw concurrency.** Raise the batch to amortise the DB
  phase; keep the conversation append-only between compactions; keep N subjects
  in flight and checkpoint each on its OWN completion. Give each worker its own
  DB connection. The model gate tiers by SOURCE HOST, so name the document's
  own host, never a made-up source category.
  *Paid for by:* 2026-08-18, raising the judge batch 1,000→5,000 amortised a
  ~6-min DB phase from ~50% of wall clock to ~15% · prompt-cache prefix
  hysteresis: trimming evidence just under CHAR_BUDGET EVERY round mutates the
  conversation at its earliest message, so the slot's cached KV matches only up
  to there and the rest RE-PREFILLS every round — 84% of prefill tokens, ~20–25%
  of lane-busy time; compact ONCE down to a LOW_WATER (~60%)
  (scope-2026-08-18-agent-runtime-throughput) · 2026-08-28: running the
  role_verify sweep subject-by-subject waited for each subject's slow omission
  task, so one GPU chewed the long pole while the other sat idle (GPU0 96% /
  GPU1 3%); a sliding window refilled both cards (94%/95%) with resume intact —
  there is no least-loaded dispatch across the llama-server slots yet, carded ·
  worker threads sharing one transaction, where a failing worker's rollback
  could erase another's committed-in-spirit verdict · keep thinking for HEAL
  lanes and use per-request no-think for BULK waves, because no-think halves
  truncation-detection at 4× the cost (AUDIT_2026-08-16 §3) · a lane naming a
  made-up source ("party constitutions") is refused as below tier — name
  assets.national.org.nz or cdn.opportunity.org.nz, the hosts that were tiered
  `llm` when the pages were captured; and `NOUS_API_URL` must carry the
  `/v1/chat/completions` path, because the client posts to the URL as given.

### The document states its own answer — check the rows against it before publishing (2026-09-25)

Five EC party returns were published with donor rows that did not add up to
the Part A total printed on their own first schedule page. Every one of the
five was wrong in a different way and every one was visible the same way:

- a schedule continuing onto a page the reader never opened (Green 2023's
  "Page: 6.1", NZ First 2024's sheet inserted between pages 3 and 4);
- a continuation page that is NOT a schedule — NZ First's inserted sheet is a
  date breakdown whose last column repeats the main form's figure, and reading
  it as donations lost $89,921.04;
- an auditor's stamp printed over the amount column ($40,020.00 read as
  $460.00), which lands on the last row of a page;
- a donor's NAME and STREET ADDRESS in two columns under one heading, read one
  column to the right (49 rows of addresses where people should be);
- a handwritten schedule no reader returns anything from.

**None of them needed a person to find. All of them needed a person to fix.**
The check is free and the form provides it: a complete reading of a part sums
to the part's own printed total. A reading that does not is incomplete or
wrong — it is not a party with missing donors, and publishing it as one is how
$588,731.22 sat on a page reading as money nobody gave.

The corollary bites harder: **a plausibility test on the output cannot find
this.** On Labour 2020 a generous "does this look like a name" rule found 23
of 50 bad rows where the truth was 25 of 25, because `Sana`, `level`, `Bente`
and `Tse` all pass. The arithmetic does not care whether the garble is
plausible.

### A rule that fires on half the corpus is noise wearing recognition's clothes (2026-09-25)

`ec-party-return-handwritten` was written with real signals — an image or scan
shape, four or more consecutive unreadable pages — and proposed itself on 29
of 51 live returns, because nothing measurable distinguishes a handwritten
schedule from a photographed typed one before somebody looks. It now
recognises NOTHING by shape, and says so in its own notes. What finds those
documents is a query the estate already computes: a declared part total above
zero with not one row behind it (`unreconciled.classify` → `nothing-read`).

Weak recognition left in place does not degrade gracefully. It teaches the
next reader to ignore proposals, which costs the profiles that ARE precise.

### A field the matcher reads must be a field the surface names (2026-09-25)

`signals` was a profile's recognition key and was not in `PROFILE_FIELDS` — it
survived only through the "carry anything we never heard of" path. A caller
that rebuilt a profile from `PROFILE_FIELDS`, which is the obvious way to edit
one, dropped it silently. The three shape profiles are mutually exclusive BY
their signals, so all three began matching every return at once, and the
symptom (every document matching three profiles) was a long way from the
cause. Same family as the exclusion filter two entries below: a list of the
things we know about today is wrong the moment the file grows.

### Select the kind you want; never exclude the kinds you know (2026-09-25)

`entries_for` filtered `kind != "review-answer"` and was correct for exactly
as long as the ledger held two record kinds. A third (`review-correction`)
arrived and rendered in the question list as a question with no text. The
filter that has to be revisited every time the file grows will be wrong
between the growing and the revisiting.

### A guard written for one lane will fire on another and be right by its own rule (2026-09-25)

`overlapping_documents` refuses a document carrying both a `filed` row and a
reviewed one, because that means two readings of one document and a
double-counted donation. A hand correction to one row of a filed reading
leaves exactly that shape — nineteen filed rows and one corrected row — and
the guard stopped the whole load on the first real run. It was not wrong; it
was being asked a question it does not answer. Nineteen filed rows and one
corrected row is not two readings of a document, it is one reading with a
correction in it. The fix was to run the guard before corrections and give
corrections the check that belongs to them, which turned out to be stronger.

### One render of a filtered list is not the list (2026-09-25)

The 2023 candidate returns came from a bulk pull that fetched every asset
the page linked, and stopped at 237 documents. The Commission's page is a
paginated GET filter form, twenty rows to a page: one render returns six ACT
returns, which is what a complete capture and a first page look like from
the outside. **470 returns are published; the estate held 237, and none of
the 59 amendments.** Nothing measured the hole because the count was never
compared against anything — a capture that reports "downloaded everything it
saw" is telling the truth and answering the wrong question. The index we
compared against later (274 links) was itself a snapshot of the same
mistake. Capture is not complete until it is counted against the source's
own total.

### An amendment is the document that supersedes, and it is named differently (2026-09-25)

The Commission files an ordinary return as
`2023_National-Party_Otaki_COSTLEY_Tim.pdf` and an amended one as
`King-M-Northland-amended-130324.pdf` — no year, no party, a given initial
instead of a name. A lane that takes identity from the filename turns every
amendment into a candidate standing in no electorate, which the surface
above it then drops for having none: read, held, and reaching nobody. The
figures at stake are not marginal. Between two versions of its own 2023
summary the Commission moved MACLEOD from $29,268 to $207,662 and LAWTON
from $425,000 to $4,250. Where the filename cannot name the document, the
document can: the form prints the candidate and the electorate.

### The same fold defect, in the second place nobody looked (2026-09-25)

`[^a-z0-9]` applied to a lowercased string DELETES a macron vowel rather
than folding it, so "Karunā MUTHU" keys as `karun muthu` and "Karuna MUTHU"
as `karuna muthu`. This is written down. It was found in
`query.influence.base._fold_org_key` on 2026-09-16 for "Ngāi Tahu", fixed
there, and left standing in `registers.donations`, where it duplicated four
candidates and double-counted $28,830.21 of declared donations. **A lesson
filed against one module is not a fix applied to the estate.** When a fold
defect is found, grep for the technique, not the symptom.

### A hyphen changes the token count, and first-plus-last keys break (2026-09-25)

`_mp_receipts_key` takes the first and the LAST whitespace token, so
"Willow-Jean PRIME" keys as `willow-jean prime` and "Willow Jean PRIME" as
`willow prime`. Two documents about one person, two keys, no join, no error:
ten candidates' itemised donations reached the surface as nothing —
$70,255.74 in 2020 and $28,320.00 in 2023. **The loss was not uniform.**
Ngarewa-Packer, Peke-Mason, Te Au-Skipworth, Pokere-Phillips, Kapa-Kingi,
Arahanga-Epiha, Prime, Al-Bustanji: hyphenated and Māori names, so the
surface was quietly least complete exactly where this product claims to
look. A key whose failure mode correlates with a class of name is a bias,
not a bug, and it must be measured that way.

### A prose basis is a claim, and it goes stale silently (2026-09-25)

The electorate payload's `basis` told every reader "2023 per-candidate
returns not yet captured — DL-18" while the same payload served $2,278,148.09
of 2023 itemised rows from 241 of those returns; the coverage note said "ALL
of 2023's per-donor rows are unparsed". Both sentences were true when typed.
A basis a reader cannot check against the figures beside it is worse than no
basis: it converts a real caveat into a false one and spends the credibility
of every other caveat on the page. Derive it from what it describes.

### A document read for one figure carries the others (2026-09-25)

The candidate return is titled "RETURN OF ELECTORATE CANDIDATE DONATIONS AND
EXPENSES". The page-read lane extracted step 2 (donations) and stopped, so
every candidate expense figure this estate served came from the Commission's
summary and from nowhere else — on a figure the same Commission publishes
wrongly for two parties on the party table in an identical way. The cost of
reading step 3 was a prompt and a gate; the cost of not reading it was a
whole surface with no second reader. **When a document is opened, ask what
else it states.**

### The orchestrator only orchestrates what calls it (2026-09-25)

Arthur built the GPU gateway on 2026-08-14 — *"build some kind of
orchestration service that passes jobs to the GPUs equally… if we are doing
real work we need 4 gpus running"*. It listens on 127.0.0.1:8090, discovers
which llama-servers are actually up, and forwards each completion to the one
with the most free slots. C413 found it routing onto one card because three
of its four backends were dead, and that was fixed from the GATEWAY's side.

Nothing fixed the other side. **Every chat lane in the estate defaulted to
`http://127.0.0.1:8020/v1/chat/completions`** — one named card — so the
balancing never applied to them at all: `ec_pageread.sh`, `ec_financials.sh`,
`party_rules.sh`, `ec_pageread_disclosures.sh`, and the `querynz-crawler` and
`querynz-sweep` units. A default that names a port is a guess about which GPU
is free, made when the file was written and never revisited; only the gateway
can answer that, and only at the moment of the call. `tests/
test_chat_lanes_use_the_gateway.py` now refuses a default that names anything
but :8090, with the deliberate single-server callers exempted by name and
reason (the bake-offs, which would otherwise measure the router; the page
recogniser, which is one-per-box on loopback by design).

### Four GPUs are only four if the work goes to both boxes (2026-09-25)

The page recogniser is ONE PER BOX on loopback — each box calls its own
(TWIN_FACTORY_ARCH) — which means a single slot per box and no way for a
gateway to spread it. Running a 1,064-document re-read on node2 alone left
node1's two 32 GB cards at 2 GB and 4 GB used, with node1's own GLM-OCR
server sitting enabled and idle the entire time, while node2's single slot
was the bottleneck and its two cards were at 88% and 76% doing other work.
**The lane already had `--shard I/N` for exactly this.** Measured after the
split: node1 alone sustains 13 OCR pages a minute on otherwise idle cards,
against node2's 8 while contending. When a resource is per-box by design, the
only way to use the second one is to take the work to it.

### The orchestrator was right; what it orchestrated changed under it (2026-09-25)

The gateway picks the backend with the best residual capacity:
`(free - inflight) / max(free, 1)`. That is correct, and it was correct for
as long as every backend served the same model. On 2026-09-24 the page
recogniser became a packaged unit, discovery started returning it, and the
arithmetic did what it says: an IDLE 1-slot vision server scores 1.0 against
a saturated 8-slot chat server's 0.0, so it wins every pick exactly when the
fleet is busy. **27,306 reviewer adjudications were answered by GLM-OCR
between 2026-09-23 20:25 and 2026-09-25 08:07.**

The module's own docstring had already seen it coming — *"a free slot on the
wrong model is not a free slot. Today every chat card serves the same model,
so routing does not yet need to filter on it"* — and "today" expired without
anything noticing. A comment that names the condition under which a design
holds is a test that has not been written yet.

### The instrument was on, recording, and unwatched (2026-09-25)

Every one of those 27,306 calls was written to `var/audits/model-calls.jsonl`
with `model_mismatch: true`, by a field added for precisely this. Nothing
read it. Thirty-seven hours of a lane answering with the wrong model, fully
recorded, entirely invisible — and it was found only because Arthur asked
whether I knew about the orchestrator. **A measurement with no arm is a
measurement nobody makes.** T7.56 now reads that field over 24 hours.

### Discovery beat the fixture, and the fixture had no way to say no (2026-09-25)

`tests/test_gpu_gateway_pick.py` pinned the fleet with `GATEWAY_BACKENDS` and
a faked probe. But `backends()` prefers DISCOVERY and reads the env only when
`from fleet import census, probe` FAILS — so the harness held exactly while
`ops` was off `sys.path`. Run in a session where another file puts it on, the
real fleet answered, the fake probe was handed a URL it had never heard of,
and four cases died on a `KeyError` that says nothing about the gateway. The
module already had `GATEWAY_FORCE_BACKENDS=1` for this. A fixture that
controls its subject only by accident is not controlling it.

### I checked four tables and said "zero"; the fifth held 32,279 (2026-09-25)

Asked what the 27,306 misrouted `reviewer` calls had done, I checked
`registers.review_verdicts`, `v3.review_decisions`, the tenant copy and the
reviewer annotations on `v3.er_candidates`, found nothing in the window, and
reported a bounded finding — no rows, but "I cannot say what those calls were
for". The honest hedge was right and the search was wrong. `reviewer` is not
a service here; it is the name `reviewer.model` gives the shared LLM client,
and the callers were `healer.cli crawler` and `healer.cli mint-lane`. Their
verdicts land in **`v3.mint_review`**: 32,279 judged inside the window and
33,213 actioned — 20,185 entities cleared and 1,801 quarantined on the word
of a model nobody chose. **Trace the lane to its CALLER before you name the
table it writes.** A lane name is a label on a client, not an address.

### The verdict knows which model spoke; the schema throws it away (2026-09-25)

`reviewer.model._judge_at` sets `out["model"]` from the RESPONSE body, with a
comment saying why — "so mixed-model verdict corpora stay separable, the
27B→35B-A3B swap is mid-campaign". `mint_review` and `anchor_review` have no
model column. The field is computed, returned, and dropped at the insert, so
the one question worth asking of 32,279 verdicts — which model made this? —
can only be answered by joining on a timestamp against a separate audit file.
**A provenance field that no table stores is a comment.** Intent in the code
that the schema does not keep is intent that was not implemented.

### A fail-closed lane looks exactly like an up-to-date one (2026-09-25)

`source_refusal` fails closed when `v3.source_policy` is unreachable: no
policy, nothing permitted. Right, and it stays. But node2's re-read ran with
no `V3_DSN` in its environment, refused all 532 calls, printed `keep` for
every document, exited 0, and produced the tally of a corpus already current.
Nothing in that output says "I read nothing". Only C186's `keeps_more` stood
between it and 532 good reads overwritten with empty ones. A lane that cannot
REACH its policy has not been refused — it is broken, and the two must be
worded apart and answered ONCE, before the first read, not per call after.
`modelgate.policy_preflight` now does that and `ec_pageread` refuses to start.

### The handler that keeps the batch alive had never once run (2026-09-25)

`_work` caught every read exception so "one bad read must NOT crash the
batch" — and built its gate-fail record with `candidate_meta(path.name)`,
where `candidate_meta` takes a Path and does `path.name` itself. Every use
raised AttributeError inside the except block, `pool.map` propagated it, and
node2's half of a 1,064-document run died on its first WrongModel having read
5 files. The code was written, reviewed and shipped; it had simply never been
executed, because until the fleet grew a second model no read had ever
failed. **An error path that has never run is a comment describing an
intention.** It was a closure inside `main()`, so no test could reach it;
lifting it to `candidate_work(item, args, read=None)` is what made the
promise testable, and the test is the point, not the one-character fix.

### The count agreed with the source's own count, and every row was wrong (2026-09-25)

The promoter register is blocks of labelled fields. The first parser took ONE
line per field, which is right for `Email:` and wrong for `Address:` — so an
address's second and third lines fell through to the branch that starts a new
promoter and overwrote the name. It produced **32 rows against the page's own
count of 32**, every one named `Wellington`, `8011` or `Waimangaroa 7848`.
Counting against the source's own total is the rule that found the 237-of-471
capture hole, and it would have passed this defect green. **A count check
proves the number, and only reading the rows checks the rows.** The test that
catches it asserts the NAMES, against the held documents, not the length.

### The same money, in three columns, is not three times the money (2026-09-25)

The Commission's 2020 promoter expenses table has three columns — general
election, cannabis referendum, End of Life Choice referendum — because each
contest carried its own $338,000 limit. Family First New Zealand declares
**$141,224.34 in all three**, and the page says why: "The full cost of any
joint advertisement must be counted towards each relevant expense limit."
One advertisement, one sum of money, disclosed three times against three
limits. A row summed reports $423,673.02 of spending that never happened.
The figures are therefore returned LABELLED BY COLUMN and never totalled by
the parser — a total it invented would be a figure with no basis (ruling 325).

### "Not applicable" is the Commission writing NONE (2026-09-25)

`Trustees: Not applicable` appears in most promoter entries. Read as a value
it mints a trustee named *Not applicable*, attaches it to every promoter with
no trust, and hands the resolver a name that will happily match itself across
forty organisations. The register's empty is a WORD, not a blank, and every
source in this estate has its own spelling of it.

### The commit was true of the repo and false of the box (2026-09-25)

I committed *"every chat lane repointed to the gateway"* and never ran
`ops/production/install-units.sh`. A systemd unit is installed BY COPY, so on
node2 — the box where the timers actually fire — two of those units were
still pinned to `:8020`, one card of four, exactly as before. The repo said
one thing, the running estate did another, and the commit message asserted
the repo's version. **Editing a unit is half of changing it.** Everything
that reaches a box by copy has this shape: a repo edit is a proposal until
the copier runs.

### The arm built to catch the drift could not start (2026-09-25)

T7.54 — *"the code that is RUNNING is the repo's code, on both boxes"* —
was written on 2026-09-24 and answered `ARM RAISED ModuleNotFoundError: No
module named 'ops'` from the moment it existed. `ops` is a namespace package,
so `ops.box_parity` resolves only with the REPO ROOT on `sys.path`: under
pytest the rootdir is there, under `v3-audit.service` it is not. The arm was
therefore red for its entire life, on the one morning the drift it names was
real on both boxes — and it printed as one FAIL among five.

So the board now says it itself. An arm raising `ImportError`, `NameError`,
`AttributeError`, `SyntaxError` or `TypeError` prints **BROKEN**, not FAIL,
and its detail ends *"this arm measured NOTHING; fix the arm before reading
the estate"*. A `ValueError` off a real query stays a finding. **A broken
instrument and a finding must not read the same** — the first says nothing
about the estate, and a board that conflates them invites the estate to be
blamed for the gauge. Write an arm and then RUN IT THE WAY THE UNIT WILL,
from outside the repo, before believing it.

### The rule that governs opening cards could not count opens (2026-09-25)

`card_balance._OPENED` required the literal `raised <date>` or `ruled
<date>`. Most card rows do not use it — they write the provenance plainly in
the SOURCE cell, `Arthur 2026-09-25 ("ingest everything you can find")` — so
**nine of the twenty cards opened since 2026-09-21 were invisible to ruling
323's arithmetic**, including both raised the day it was found. It reported
11 opens against 84 closes where the truth was 20. Two properties make this
worse than a miscount: the instrument governs the very thing it was
mis-measuring, and its error ran only one way — toward permission to open
more. **An instrument that reads a convention rather than the content will
drift as the convention does, and silently.**

### The fact was never lost — it was put where no query could reach it (2026-09-25)

Asked which model made 510,766 entity judgments, the answer looked like an
inference over a time window: `mint_review` has no model column, so the best
available was "these rows were judged while the gateway was misrouting."
The verdict LEDGER — `var/reviewer_verdicts/mint_lane_verdicts.jsonl`, 271 MB,
append-only, written by the same loop as the UPDATE — carries `model` on
every line. The insert dropped what the file kept. Backfilled by entity id it
gives **exactly 27,306** glm-ocr verdicts, matching the model-call ledger's
count from a completely separate instrument. **Before inferring, look for the
place the fact was already written.** A pipeline that writes the same event
twice usually drops different fields each time.

### NULL where the two ledgers disagree, never a best guess (2026-09-25)

233 of the backfilled rows have a table verdict that differs from the last
verdict their ledger line records: something other than that line wrote them.
They are left NULL. Stamping them with the ledger's model would make the
column *complete* and *wrong* in a way nothing downstream could detect —
worse than the silence it replaced, because silence is honest about itself.
**NULL is not False, and it is not the default either.**

### A skew is evidence of nothing until the sample is controlled (2026-09-25)

The OCR model produced 16.7% of every `real_name` clear in the corpus while
making about 5% of its judgments, and 0.4% of every `mistyped-duplicate`.
That reads as a model that clears too eagerly and merges too rarely. It is
also exactly what you would see if the 37 hours it ran happened to drain a
queue full of plausible names — and the 27,306 are not a random sample, they
are whatever was queued. The difference is settled by re-judging THE SAME
entities with the right model through the production predicate, which is a
measurement, not an assumption. `ops/rejudge_sample.py` writes nothing.

### A shard by list POSITION assumes both workers see the same list (2026-09-25)

The candidate re-read split 452 documents across two boxes with
`i % n == shard`, over a list each box globbed for itself. node1 started
while its archive was still receiving the re-fetched 2023 returns, so its
list was short; every index after the first absence shifted by one, the two
shards **overlapped on 5 documents and left 25 untouched**, and both runs
printed a clean tally over a total neither of them owned. 427 of 452, with
nothing red.

The shard is now a digest of the file NAME. It is the same on both boxes
whatever either can see, so a missing file changes only its own fate and
never anyone else's — and a document keeps its shard as the corpus grows,
which the index scheme never did. **A partition key must be a property of
the thing, not of the moment it was listed.**

### The function had three tests and the caller used something else (2026-09-25)

`shard_of` was written, documented and mutation-proved. Reverting the ONE
line in `main()` that calls it back to `i % n` passed all forty-two tests —
because every test called the function directly and none drove the
selection the run actually performs. The wiring came out as
`files_for_shard()` and got its own test; that test dies on the same
mutation. **Testing the function is not testing the program.** The bug was
never in `shard_of`.

### A name is not free until it is grepped (2026-09-25)

`files_for_shard` was first written as `select_files` — and 190 lines below,
inside the same `main()`, sits `from registers.party_pdfs import
select_files`. A function-level import binds the name for the WHOLE
function, so the call at the top raised `UnboundLocalError: cannot access
local variable 'select_files' where it is not associated with a value` — a
message that points at the call and says nothing about the import that
caused it. The estate already has "a name is not dead until the root tests
are grepped"; this is its twin.

### The third separator: an apostrophe sits INSIDE a word (2026-09-25)

`candidate_key` was fixed on 2026-09-24 to fold macrons, and again to treat a
hyphen as a word break — "PEKE-MASON" meeting "PEKE MASON". Both right. The
same substitution then keyed **"Simon O'CONNOR"** as `simon o connor` while
the candidate return, whose identity comes off the Commission's own FILENAME
which drops the apostrophe, gave **"Simon OCONNOR"** → `simon oconnor`. And a
page-read of the form prints **"O NEILL"**, a third spelling again.

No substitution reconciles all three, because a hyphen SEPARATES two words
and an apostrophe sits INSIDE one. The answer was that the key holds letters
only and spacing is not part of a name's identity — it is a join key, never
displayed, so it owes nothing to readability. Until then the two spellings
each carried a totals row and the electorate view counted their declared
donations twice: **7 candidates over 2020 and 2023, $109,967.75** — O'Connor
×4, O'Rourke, Kanongata'a-Suisuiki. Irish and Pasifika names, exactly as the
macron class was Māori ones.

**And the re-read CREATED it.** Before tonight few enough returns were read
that the two spellings rarely both existed. Filling the corpus in is what
made a latent key defect start double-counting money.

### I hand-rolled the SQL the standing rule forbids, and found a phantom (2026-09-25)

Joining `candidate_donations` to `candidate_donation_totals` with plain
equality, I measured **$671,500.40 of itemised donations attached to no
candidate** and was ready to call it a hole — 34 candidates, overwhelmingly
Māori electorates. Driving `browse.influence_electorate` instead, every one
of them joins: `_fold_electorate` has folded diacritics and hyphens since
2026-09-16. The surface was right and my instrument was wrong. **Measure
through the production predicate, never hand-rolled SQL** — the rule exists
because a hand-rolled join reproduces the defect the production one already
fixed, and reports it as data.

The same query DID surface a real one (the apostrophe duplicates above), so
the lesson is not that ad-hoc measurement is useless. It is that a finding
from outside the production path is a QUESTION, and the answer comes from
inside it.

### Filling the corpus in is what makes a latent dedupe defect start counting twice (2026-09-25)

The candidate loader's twin guard keyed on `(year, candidate, electorate,
AMOUNTS)`. It catches two IDENTICAL readings and misses two that DIFFER — and
two readings differ exactly when one is better, which is the normal case for
a re-read. Two things then landed at once:

- **the same BYTES under two names.** The re-read wrote every 2020 return
  under the new capture generation's filename beside the old generation's:
  1,218 readings for 609 documents, every one held twice.
- **the same RETURN as two different FILES.** The Commission publishes some
  returns twice, hyphen-shape and underscore-shape, different bytes and so
  different sha. Ginny Andersen's two files read 6 donors and 5; both loaded,
  and she itemised $76,681.60 against a declared $40,090.80.

2020's itemised donations came to **$5,190,963.89 against a declared total of
$3,621,072.60** — $1.57M of the same money, twice, on a live surface. Both
guards now exist: sha256 for the bytes, then `(year, candidate, electorate)`
for the return, with the best reading winning (an amendment first, then most
rows, then a passing gate, then newest). A candidate files ONE return.

**A dedupe key that includes the DATA cannot deduplicate two readings of one
thing** — it can only deduplicate two copies of one reading, which is the
easy half and not the half that costs money.

### The itemised total exceeding the declared total is the check (2026-09-25)

None of this was visible in a count of rows or documents. It showed up as a
ratio: itemised donations were **112%** of declared donations for 2020 while
2023 sat at 87%, and a per-donor sum cannot exceed the total the candidate
declared unless something is counted twice or the declaration is missing.
After both guards, 2020 is 110.6% and the residue is explained — $483,323.76
itemised for candidates the Commission's summary gives no total for, plus 16
candidates who genuinely over-itemise by $122,273.77, which is now a real
discrepancy to chase rather than an artefact. **Hold two independent
measures of the same money against each other; the RATIO says things neither
count does.**

### The control reversed the finding: the lane does not agree with ITSELF (2026-09-26)

Having attributed 27,306 entity verdicts to the page recogniser, I re-judged
a stratified sample of them with the correct model through the production
predicate. **Agreement: 10.5%.** `organisation`: 0 of 32. The obvious reading
was that the misrouting had wrecked 27,306 judgments and they all needed
redoing.

Then I ran the control I had nearly skipped — **qwen re-judging QWEN's own
verdicts, same method, same sampler.** Self-agreement **33.3%**:

| verdict | qwen vs qwen | glm-ocr vs qwen | corpus | actioned |
|---|---|---|---|---|
| `debris` | **96.8%** | — | 124,626 | 124,529 |
| `truncated` | 100% | — | — | — |
| `real_name` | 80% | 26% | 53,248 | 53,218 |
| `mistyped-duplicate` | **0 of 26** | 0 of 2 | 105,191 | 22,143 |
| `abstain` | **0 of 15** | 7% | 67,919 | 63,459 |
| `organisation` | **0 of 11** | **0 of 32** | 51,345 | 51,211 |
| `concept` | 0 of 8 | 0 of 1 | 33,962 | 33,821 |
| `distinct-entities-ok` | 0 of 7 | 0 of 15 | 33,176 | 0 |

So the lane is reproducible where the answer is obvious — debris, truncated,
a clear real name — and **not reproducible at all where it is a judgement**.
The misrouted 27,306 are not specially suspect; they have the same property
as the other 483,000, and re-judging them would have produced a third set of
answers, not a correction. The temperature is 0 and the docstring in this
very repo says why that is not determinism: *"temp-0 greedy but NOT
reproducible (no seed; GPU FP + batching vary run-to-run)"*.

**The exposure is not the 27,306, it is `mistyped-duplicate`:** 105,191
verdicts with 0-of-26 self-agreement, 22,143 of them already actioned, and
what they action is a MERGE — a change to who someone IS.

**Run the control before you believe the comparison.** A disagreement rate
without a self-agreement rate beside it measures the task, not the treatment,
and I was one step from recommending a 27,306-row re-judge that would have
changed answers without improving them.

- **A table with no foreign key is not covered by anything you reasoned about
  the ones that have them** (2026-09-28, the Papers Past withdrawal). Eleven
  tables were cleared in the right order because `entities` had NO ACTION or
  CASCADE constraints naming them, and that list was built from
  `pg_constraint`. `alias_sighting` — 126 M rows, written on every extraction —
  has no constraint at all, so it appeared in no list, raised no error, and was
  left with 50.3 M rows naming entities that were gone. **Enumerate the
  referencing tables from the COLUMN NAME as well as from the constraints**, and
  treat the absence of a constraint as the reason to look harder, not as
  permission to skip.
- **"Absent" is not one set: ask WHY each row is absent before deleting on it**
  (2026-09-28). `DELETE ... WHERE the entity is gone` and `DELETE ... WHERE the
  entity is in this run's manifest` differ by 27,045 rows and read as equally
  correct. The difference was 846 entities that had been MERGED away, whose
  evidence survives on the keeper and whose sightings were the only trace of a
  bug fixed eleven days earlier. A deletion predicate that describes a STATE
  will collect everything that ever reached that state; one that names an ACTION
  collects only what that action did.
- **RSS is not a budget; the cgroup is** (2026-09-28). Summing the RSS of ten
  forked workers said 30 GB and the cgroup said 8, because a fork shares its
  parent's pages copy-on-write and every child's RSS counts the same 2.41 GB of
  spaCy models. systemd had been recording the true peak for 967 runs. **Read
  the accounting that measures the thing; do not add up a task dump by hand.**
- **A stale reading and a false reading look identical in a status file**
  (2026-09-28). A board arm said `node1 == node2 @ 54eacac3` while neither box
  was at that commit, and I called the guard broken. The guard was correct and
  its reading was 22 hours old — the board runs daily. **Before calling a check
  wrong, find out when it last ran.**
- **Two guards in series are one guard if the first one's failure is swallowed**
  (2026-09-28). `git push mirror main || true`, then node1 fast-forwards from
  that mirror — and because node1's `origin` IS the mirror, a rejected push
  turns the second hop into a NO-OP SUCCESS that prints the old head down the
  success branch. The script's own divergence check could never fire. node1 ran
  17 commits behind as the primary for 22 hours, every tick reporting success.
  **`|| true` on a hop that a later hop depends on converts a loud failure into
  a silent one.**

- **Normalise by work done before you claim a setting improved anything.** The
  WAL tranche looked like a triumph: 281 GB/day before, 3.2 GB/day after.
  Per row-operation it was **1,253 → 1,172 bytes, about 6%** — the other
  140-fold was simply that the box was doing 140× less work than it had been
  during the era. Both numbers are true and only one is about the change. Any
  before/after spanning a change in load is a measurement of the load; divide
  by rows, requests or bytes processed, or say plainly that you cannot
  attribute it. (2026-10-05, `postgresql-wal-tranche2.conf`; T7.51 will take
  days to converge because it averages since the 2026-09-17 stats reset, and
  that wait is the honest answer rather than a reason to quote the 140×.)

- **A fleet that refuses on RAM alone will spend the serving tier's
  connections.** `extract-fleet.sh` checked free memory and nothing else, so
  widening a fleet was free to exhaust `max_connections` — and the thing that
  falls over when it does is the serving API, the one part of this estate a
  person is actually looking at. Measured on the primary: 100 max, 3 superuser
  reserved, 30 reserved for `querynz_serving` (ruling C007), 14 otherwise in
  use → **53 free, which is 17 shards at three connections each**, against a
  default of 16 and a number somebody might reasonably type of 24. **A reserve
  is counted as SPENT whether or not its owner is using it** — a fleet that
  fits only because the product happens to be quiet does not fit. (2026-10-05,
  C008.)

- **A set-based migration is usually three wrong answers deep; rehearse each
  one against the real table.** The alias re-fold took three attempts and none
  of the failures would have shown on a small fixture. (1) **The wrong
  question:** "does a row already hold the trimmed key?" — which quietly
  skipped **415 groups of two or more dirty rows with no clean row among
  them**, the exact population the migration existed for. (2) **The wrong
  index:** `WHERE alias_id = %s` against `v3.alias_sighting`, whose PK is
  `(article_id, alias_id, entity_id)` — the filter is not the leading column,
  so each merge scanned all **78M rows**, putting the run at **19 hours**.
  (3) **The wrong primitive:** `ON CONFLICT` cannot resolve a conflict the
  statement CREATES WITH ITSELF, so two dirty rows folding onto one key raise
  `CardinalityViolation`; `GROUP BY` the target key before the write. A
  `--rehearse N` arm that rolls back caught all three before anything was
  committed, and is cheaper than any of them. (2026-10-05, C457,
  `ops/alias_refold.py`.)
