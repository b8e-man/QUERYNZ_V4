> Part of [LESSONS](../LESSONS.md) — living memory, one section per file
> since 2026-10-04 so that "read the relevant section" is a thing a reader
> can do. The rules of the file, and why it exists, are in LESSONS.md.

> **SPLIT OUT OF SECTION 3 ON 2026-10-09 (C551).** Section 3 held 182 of the
> corpus's 439 rules and 192 KB against T7.38's 160 KB one-read ceiling — not
> because measurement is 41% of what this estate learns, but because its
> routing pattern (`^tests/|test_|gate|invariants|board|audit`) matches the
> thing EVERY card does. These are the rules about COUNTING — samples, denominators, populations, counters and thresholds. Nothing was edited, summarised or
> dropped: the rules below are byte for byte what section 3 carried, and a
> citation's `#id` is unchanged because it is six hex of the claim.

## 9. Counting, samples & populations

- **A gate proves nothing until you know what it ENUMERATED — make every arm
  report the SIZE of the population it checked.** "0 violations" reads the same
  over 43,493 rows and over none. A gate scoped by a PROXY is quiet until the
  proxy stops meaning what it meant; a fixed list of globs reports zero
  findings about the trees it never named; a capped lane's log line is a
  ceiling, not a measurement, so every capped job reports what it DID and what
  is LEFT.
  *Paid for by:* 2026-09-19, T7.2 decided a backlog row came from the news
  dashboard — and so had to be parked — by testing `upstream_id > 0`, which was
  never a fact about origin but a proxy for "not one of our older negative-id
  scrapers". Lanes then landed through the contract-1 lander, which derives the
  id from a HASH: positive, and enormous. The arm passed for two months, not
  because it was right but because the lanes it mis-scoped happened to land
  parked anyway; the day ruling C394 un-parked three of them it reddened on
  2,211 rows of our own output — and for `parliament.nz`, SCRAPER_OWNED, the
  dashboard copy is DROPPED before it is written, so the arm was asserting
  parking over a population that cannot exist. The fix was a marker named and
  ruled rather than inferred (`PRIORITY_DASHBOARD`) · 2026-09-19, twice in one
  day (the ESTATE register and the doc index): twenty tracked documents were
  not unindexed, they were UNASKED — `test_every_doc_is_indexed` enumerated
  eleven globs and `eval/agentic/results/*` (16), `eval/bakeoff`, the
  `nzbn_canonical` docs and the GUI's attribution file matched none; both gates
  now take their list from one walk (`git ls-files`), in one function ·
  2026-09-19: `healer.crawler` logged `orphans quarantined 500` — exactly
  `FINDER_CAP` — on 34 consecutive runs over a week; nothing was broken, the
  lane was working a 216,880-row backlog at ~2,700 a day, but the number reads
  identically whether 501 rows remain or five million · a blocking cap that
  skipped any normalised form shared by more than 40 entities made common
  person names permanently unresolvable with no signal at all — eight forms
  were already over it when the overflow metric shipped · a gate that only
  PRINTS is invisible: gazette-derive's completeness gate printed to
  scrollback, so drift was visible only to whoever was watching (and a schema
  column with no writer reads as "no data" — `matched_nzbn` had DDL but no
  writer, silently blocking a flag). Persist every check as a row.

- **A "NO-MATCH" RESIDUE IS A STATEMENT ABOUT WHICH REGISTERS YOU ASKED, AND
  THE CARD WILL NAME ONE WHEN FOUR EXIST.** C194, closed 2026-10-10.
  `registers.derive`'s shareholder anchoring matched a holder name against
  `public.entities` and `public.entity_history` — COMPANIES and their former
  names — and reported **26,857 `no-match`** rows, 13% of 204,156. Not one of
  them was an ambiguity or a bad name: a shareholder that is an incorporated
  society, a charitable trust board, a public-sector body or an unincorporated
  entity HAS NO COMPANY ROW, so `no-match` was the only answer the query could
  give (#b86cbf: a lookup that asks the wrong register is a near-miss waiting
  for a looser match).
  **THE CARD NAMED ONE REGISTER AND THE MEASUREMENT FOUND FOUR.** Asking
  `other_incorporated_entities_core_data` alone recovers 2,002 (7.5%); the
  estate also holds charitable trust boards (35,599 rows), public-sector
  entities (2,922) and unincorporated entities (227,984), and asking all four
  recovers **1,583 more**. Final: `no-match` 26,857 → **23,250**,
  `other-register-unique` **3,585**, anchored 86.8% → **88.5%** — and the build
  matched the pre-build measurement to the row, twice.
  **UNIQUENESS ACROSS THE UNION, NEVER WITHIN EACH REGISTER.** A name that is
  one society AND one trust board is two legal persons, which is the same
  unanswerable question as two companies sharing a name, so the
  `count(DISTINCT nzbn)` sits outside the union and 22 names abstain as
  candidates. And the tier fires LAST, only where the company tiers found
  nothing AND the former-name tier found nothing: a name ambiguous among
  companies is never resolved by looking somewhere else.
  **A RESIDUE IS NOT A BACKLOG UNTIL ITS POPULATION IS NAMED.** 13% looked like
  reader failure for as long as nobody wrote down which registers the lookup
  consulted. Before costing a residue, say what was asked — and then say what
  else the estate already holds.

- **A FILE AT EXACTLY THE DOWNLOAD CAP IS A TRUNCATION — AND BEFORE REPORTING
  ONE, CHECK WHETHER THE ESTATE ALREADY CAUGHT IT.** C174, 2026-10-10. Eight of
  eleven unread 2023 candidate returns failed with *"no text (OCR produced
  nothing)"*, and two were **exactly 1,048,576 bytes** with no `%%EOF` and four
  `pdfinfo` syntax errors — a truncation detectable by SIZE ALONE, with no need
  to parse anything. A census of the whole staging tree then found **31 files at
  exactly the cap**, among them the 2021 annual returns of Labour, Green, NZ
  First, the Maori Party and The Opportunities Party, every one failing
  `pdfinfo` and returning `page_total` 0. That reads like a fleet-wide integrity
  failure on the front-page parties and it is not one: **29 of the 31 are named
  `.pdf.truncated-1MiB` with the intact re-fetch sitting beside them** — the
  detector fired, the bad copy was quarantined with the reason IN ITS OWN
  FILENAME, and "quarantine, never delete" left the evidence where a census
  would trip over it. A `rglob("*")` over a tree that quarantines in place
  counts the quarantine as a finding.
  **THE REAL FINDING IS THE TWO THAT ESCAPED**, `Uploads__King-M-Northland` and
  `Uploads__Manning-R-Tukituki`, at the cap and NOT renamed — and even those
  cost nothing, because each is a duplicate of a document already held intact
  under its `candidate-returns__2023__Amended__` name and already read. So the
  measured defect is 2 of 31 in a detector, not lost money. Two rules in one:
  size equality with a power of two is evidence before any parse, and a
  quarantine convention is part of the population definition — a census that
  does not know the convention reports the cure as the disease.

- **A cheap probe before the build: blast radius, EXPLAIN, a labelled sample,
  an ambiguity count.** Measure the CLASS before you widen the rule — the rule
  you were asked about may not be the one that matters, and a filed row is a
  hypothesis about where the problem is. Don't redesign a subsystem blind: the
  verdict tables ARE the labelled dataset.
  *Paid for by:* 2026-08-20, two theoretically serious era-4 defects that had
  produced ZERO live claims, turning an alarm into a scheduled card · a
  code-reading review that "found" `::text` casts defeating a join index, where
  both columns were already text, the casts were no-ops and the plan was a
  nested loop over the primary key — plan-shape reasoning from source is
  frequently wrong · a probe over 400 claims finding "the company" sitting
  among 11.2 candidate orgs at article scope (1% singleton), so
  resolution-by-uniqueness was never built — cheap probe, whole feature avoided
  · "a lot of bad merges, the system likely needs an overhaul", answered by
  working the queue to ~100 verdicts and measuring the bad rate per producer
  and reason FIRST · 2026-09-20 (queue 8): a row proposed widening the
  bare-role guard's type scope (175 entities, 11,145 mentions) and measuring
  first found a class beside it of 33 entities and **207,255 mentions** the
  widening would not have touched at all, because those names are not roles but
  function words and company suffixes — the largest was `Ltd` typed CONCEPT
  with 192,009 mentions.

- **A labelled set named in a plan is a claim to be measured, and "by
  construction" is a hypothesis until you read ten rows — then re-read it after
  the first gate run.** Derive the set from the data, print ten rows, read
  them; the gate's misses are where to look next; relabel with the reason
  recorded on the case, never silently. Know what a corpus's verdict actually
  asserts, and never make the diagnostic the fitting target.
  *Paid for by:* 2026-08-22 (B4b) — "the refuter must catch the 14 reverted
  merges" named a set measuring the WRONG property (the 14 were direction
  errors: same referent, wrong keeper), and the first replacement positives
  read on inspection as mostly the SAME entity mistyped by one register lane;
  the honest set was the residue the graph still held, 6 era-separated
  namesakes · seven of thirty "same referent" negatives, built by construction,
  were genuinely different things (a Dunedin street and a saint, a footballer
  and a place) · 2026-08-20: `real_name` means "refers to a real entity", NOT
  "this surface is a valid name" — gating on it would have failed 39 correct
  rewrites, so the gate became `distinct-entities-ok` with real_name
  informational · the truth-set gate was ring-fenced from weight-fitting,
  because fitting to it would have memorised the exam and destroyed the only
  honest measurement we had.

- **Assert AFTER you measure, and run the baseline more than once before
  claiming a delta.** Floors go 5–10% under the observed value and percentages
  only once sweeps show what normal looks like; floors are tripwires for
  collapse and truncation, not growth targets, and a broken catalogue entry
  records `ok=false` rather than blinding the instrument to everything else. A
  parser written from one specimen is measured on the population before its
  residue is believed.
  *Paid for by:* three identical baseline runs of the verdict fleet spreading
  6.5→7.9→8.6 verdicts/min, so a single-run "+45%" for MTP speculation was
  really +23–28% and two other apparent wins fell inside that spread (→ mode 3;
  var/audits/spec-decoding-2026-08-20/) · a synthetic speed win that did not
  transfer: n-gram speculation gave 4× on verbatim quoting and 20% draft
  acceptance on actual verdict prompts, and combining drafters made MTP worse
  (→ mode 7) · 2026-08-23 (B9 T3): `parse_appointment` wanted "appoint X to be
  Y" and derived 239 rows from 1,374 notices, and nothing failed because the
  gate printed and the floor (200) blessed 234 — sample sixty real inputs,
  count zero-row cases, then set the ceiling.

- **A cap is not a population, and an id range is not a sample.** When a count
  pins at a cap the only measurement is a pull; sample by something orthogonal
  to the process you are measuring, or count.
  *Paid for by:* a `totalElements: 10,000` that was an Elasticsearch count
  ceiling, not the archive (~100M articles), and any day over 10k articles
  silently losing its tail without day-bisection · nine decades all reading
  "10,000", reported as ≥94,942, where the first real pull returned 14,949 for
  a single year · 2026-09-19: four contiguous id ranges said 96.6% of orphan
  entities were already quarantined and the full count said 51.1% — ids are
  allocated in mint order and the cleanup lane walks the table in id order
  behind a cap, so an id range encodes BOTH when a row was made and how far the
  cleanup has reached, the two things the sample was being used to measure. The
  error survived being written into a record and a queue row before the full
  count caught it.

- **Two lanes computing the same quantity will diverge — diff them, and
  dedupe on the fact's own key.** A number that only agrees with itself is
  untested. Dedup on the FULL identity of the thing, not on how a path formats
  it; when a change touches counting, add a unit test that asserts the NUMBER,
  because an acceptance gate measures presence and direction, not sums. And
  don't hide a row to make a view "clean" — it breaks the total.
  *Paid for by:* audit 2026-09-03 — the party page's windowed disclosures
  joined `donation_disclosures.party = ANY(filed labels)` because that join is
  correct on `party_donations` (one canonical label per party), while
  disclosure files carry the party in six spellings and two cases, so the
  Greens' $720,436 vanished and National showed a third of its rows while the
  home card, folding via `_fold_org`, showed the full sums an inch away; the
  same audit's "sitting MPs = 137" came from the roster's `parliaments` array,
  which says who EVER sat and has no end date. The acceptance runner pinned
  each lane in isolation and missed both · 2026-08-26: `_merge_disclosures`
  keyed on `(party, donor)` to fold a >$20k disclosure onto its matching party
  return, which also collapsed genuinely-distinct same-donor donations across
  years and amounts — nothing failed, the page rendered, the gate passed, and
  the identity is party+donor+amount+year · 2026-08-28: the name-matched
  gazette block in lobbying_person and _statutory_appointment_spans both read
  gazette.public_appointments, so a roster MP's board seat reached the timeline
  twice (Shane Jones: 'Member' + 'members' @ Industry NZ Board); the durable
  fix collapses on the underlying NOTICE id (+ org + folded office),
  producer-agnostic, pinned by tests/test_gazette_dedup.py · 2026-08-26: the
  donations table defaulted to anchored-only with name-matched rows behind a
  toggle, so the headline exposure disagreed with the visible rows — show every
  row with its name and a label (anchored ⚓ / name-matched), count all, treat a
  return plus a >$20k disclosure of ONE donation as corroboration counted once,
  and FLAG a genuine amount-disagreement rather than suppress it (GOALS §3) ·
  2026-09-07/08: the home card and the party page showed different ">$20k
  disclosed" totals for National because each folded the OCR'd spellings its
  own way and only one applied the window — resolve and date the row ONCE in
  the register (party_resolved / year_received with their basis), read one
  rollup on every surface, hold them equal by a gate (PI-65/66) · serving
  matched a party by SUBSTRING: "act" ⊂ "contact" gave Contact Energy a
  party-board pane, and the party subject matched 21 of National's 849 filed
  rows because the register spelling differs from the filed one (2026-09-03,
  T-A item 4, 809de09) — match on the filed-spelling SET or whole tokens.

- **Reading a value back is not a verification when something else writes it
  — and a config flag describes what userspace INTENDS, not what is writing the
  hardware.** A fix to state that some other process rewrites on a cycle is
  unproven until it has survived one full cycle.
  *Paid for by:* 2026-09-19, runsheet 69 — both boxes' RTC held local time
  while `/etc/adjtime` and `timedatectl`'s `RTC in local TZ: no` said UTC; a
  root command fixed it, a read-back four minutes later showed UTC on both
  boxes, and I recorded it DONE and pushed. A watch armed almost as an
  afterthought reported node2 reverted after six minutes and node1 after 4.5,
  because chrony's `rtcsync` hands the RTC to the kernel's eleven-minute mode,
  which writes it from a belief set ONCE per boot from `adjtime`. The existing
  record already said "no root command survives eleven minutes" and I overturned
  it on a reading taken inside the window; `adjtime`, `RTC in local TZ` and the
  actual RTC contents disagreed for a day and every one of them was reporting
  honestly · the same shape in the small: treat DB and session timezone as
  load-bearing and test the CALENDAR BOUNDARY rather than the timestamp — a
  documented and fixed UTC→NZ date shift still shipped, because the systemd
  drain took a different code path.

- **A predicate that defines a population is a claim about the world — list
  every table that could hold the thing you say is absent.** And before
  concluding that nothing has done a job, ask what else could have done it: an
  unfired lane and spent clutter can both be wrong about the same script. A
  reconciler that refuses to resolve a contradiction is doing its job — read
  why it declines before widening it.
  *Paid for by:* 2026-09-19 — `era3_orphan_purge.py` defines an orphan by nine
  anti-joins and reported 216,880 entities with "nothing behind them"; Arthur
  asked whether they had an originating document and the answer was yes for
  92.7%, because `alias_sighting` (125.7M rows) carries `entity_id` AND
  `article_id` and is not one of the nine. Worse, most were already quarantined
  under `crawler:zero-reference-orphan` — the healer had found the same
  population by the same rule and withdrawn it reversibly, and *the quarantine
  is what stripped their mentions and claims*, so the predicate was measuring
  the cleanup's own footprint and reading it as debris; the script was nearly
  retired that morning as a spent one-shot and would have deleted what that
  component deliberately preserved · `news/reconcile_ledger.py` only ever moves
  `captured → processed` and never touches `for_review`; when 1,964 rows sat
  extracted-but-ledger-parked the tempting read was a gap in the reconciler,
  and an extracted article whose ledger says parked is a CONTRADICTION that a
  reconciler quietly smoothing it would file away as bookkeeping.

- **Measure which PROPERTY separates the two populations, and instrument what
  the pipeline DROPS.** A wrongly-dropped entity writes no row, so it is
  invisible to every review surface that reads the graph. Rank by SHARE, not
  count.
  *Paid for by:* general-English frequency putting `bookings` below `meridian`,
  and our own corpus frequency interleaving just as badly (a company's name IS
  common in a corpus about that company) — only lowercase-rate separated names
  from common nouns, ≤2% versus ≥19% · over 60 articles, 56 of 110 register
  hits (51%) produced no anchored mention, with nothing distinguishing a
  correct drop ("Olivia" is a boat) from an entity lost entirely · ranking by
  count would have bound `rnz` to RACING NEW ZEALAND and put 26,620 broadcaster
  mentions on a racing body.

- **Measure a probabilistic matcher against labels before granting it any
  authority, and an agentic benchmark measures graph × toolset, not the
  graph.** Hold the toolset fixed when the graph is what's on trial. Label
  signal comes from surfaces being USED, not from mining old verdicts.
  *Paid for by:* Splink restocking 7.0M pairs at a claimed "≥0.95" from a
  2.58M-entity graph, where judging 40 gave 2 same / 33 different / 5 unsure —
  the prior left at its 0.0001 default, EM trained on the POST-merge graph, and
  four correlated name features double-counting; the gates held (auto=0,
  applied=0) and only labels showed it · 2026-08-19: rule induction over 42,824
  resolver labels yielded zero acting rules, and two days of use-case triage
  yielded ten rule families (ARCHITECTURE_LOG 2026-08-19; memory:
  self-evolving-loop) · the gate catches what review would not — era-4's
  interactive per-rule review was waived and the corpora still withdrew a bad
  rule (B2) and documented an exception (B6) (memory: harness-acceptance) ·
  premise verification belongs in PROMOTION as well as generation (batch-plan
  ruling 1, the CIAL false-premise retirement): a false premise must be
  re-checked when a claim is PROMOTED, not only when generated.

- **A stale threshold does not fail. It accuses.** `docread`'s disclosure
  threshold stopped at the 2010 amendment ($15,000 from 2011); the Electoral
  Amendment Act 2022 lowered it to $5,000 for returns from 1 January 2023.
  Held at the old number the rule flagged **1,077 correctly disclosed donors**
  — every donor in the new band — as sitting below the threshold that required
  them, and each became a question waiting for a person: 42% of the review
  queue, from one number. The serving side already had the new figure, so the
  same statute lived in two modules and one was three years out of date. **A
  rule that judges against a statutory constant needs that constant pinned
  across every module that holds it, and the pin belongs in the root suite.**
  The law is also the kind of fact the source WRITES DOWN: the Commission's own
  page, already in our capture, says *"The reporting requirements for parties
  changed on 1 January 2023"*. (2026-09-26.)

- **"Not held" is a claim about the estate, and it needs measuring like any
  other.** The gather inventory listed overseas and anonymous donation returns
  as NOT HELD from the day it was written, and the closeout said foreign
  influence was a question the tool could not answer at all. There is no such
  return: they are Parts C and D of the party annual return, 110 of which were
  held and read. The answer — $64,812.22 of overseas money, 96% of it one
  party's 2022 return — was in a column. Before capturing a new class, check
  whether it is a PART of one already held. (2026-09-26, gate 3.)

- **Fullness is a stock; pressure is the symptom — and sample the cumulative
  counter, never the average.** T7.13 redded on `swap used > 90%`, which a box
  can sit at in perfect health (those pages went out hours ago and nobody has
  asked for them since) while a box at 20% thrashes to a standstill. What hurts
  is the paging, not the occupancy. `/proc/pressure/memory`'s `full` line is
  the kernel's own answer — the share of time EVERY task was stalled — but its
  avg10/60/300 fields describe the last few minutes, so an arm that samples
  them at board time sees nothing of the hour the box spent thrashing
  yesterday. It is `total=`, cumulative microseconds, differenced against the
  previous board's reading, that answers "since the last board" — the same
  question the OOM check already asks. A negative delta is a REBOOT, reported
  and never red. (2026-10-05, C041; both boxes measured at 23%/21% swap and
  `full avg300 = 0.00`, i.e. the old arm passed them for the wrong reason.)

- **A floor computed over all days cannot see a weekday.** The coverage scan
  called a day sparse below a fraction of the median of every day in the
  window — so a corpus that is quiet every Sunday either reds every Sunday or,
  once the fraction is lowered enough to stop that, cannot see a genuinely
  dead Tuesday. The median has to be taken over the SAME weekday. Any
  threshold crossing a cyclical series needs the cycle in the statistic, and
  the symptom of getting it wrong is a gate whose sensitivity was tuned down
  until it stopped complaining. (2026-10-05, C500.)

- **A date in the future is not a scar — a filter over "when was this learned"
  must exclude prose.** `lessons_for --since` ranks rules by the latest date in
  their text, and its first run put a rule dated **2026-11-18** at the top of
  "filed since 2026-10-05": that date is a planned muster milestone inside the
  rule's body, not the day anyone learned anything. A scar is in the past by
  definition. The general shape is worth more than the fix: when a field is
  derived by scraping a pattern out of prose, the pattern will also match the
  prose that is about something else, and the tell is usually an impossible
  value sitting at the top of an ordering. It was caught by reading the tool's
  own first output instead of its exit code. (2026-10-06.)

- **A CUMULATIVE COUNTER READ ONCE IS AN AVERAGE SINCE BOOT, NOT A READING.**
  `/proc/<pid>/stat` holds CPU ticks since the process began, so a single
  sample of a fleet reports its average since the fleet started and cannot show
  a collapse that began ten minutes ago — the exact event ruling 144's floor
  exists to catch. The recorder differences two readings over wall clock, which
  also forces three things that only appear once you are differencing: the
  FIRST sample has no delta and must not be written (it would open the file
  with a 0% that reads as a collapse); a shard that appears mid-interval has no
  previous reading and must be excluded, or its whole lifetime lands in one
  interval as a spike that never happened; and a delta is clamped at zero,
  because a pid can be REUSED between readings and a negative would pull the
  fleet total down. Same family as T7.13's memory-pressure counter.
  (2026-10-06, C002.)

- **THREE COUNTS OF ONE CENSUS, AND ONLY THE LAST WAS TRUE: 34, THEN 17, THEN
  6.** Asking "how many reads of this table forget the filter", a 400-character
  window around the table NAME said 34 — it was counting `from registers import
  donor_anchors` and docstrings. Extracting the enclosing SQL string said 17 —
  it truncated at the quote inside `WHERE band = 'accept'`, so the filter sat
  just past the cut. A plain 500-character window after the match said 6, which
  survived reading every one. Then the test written to hold the result matched
  its own explanatory COMMENT, because the comment contains the words
  `FROM/JOIN registers.donor_anchors`. **Every refinement of a textual census
  is a new way to be wrong, so read the hits at every step and keep reading
  them until the number stops moving** — the first number is never the answer
  and the second is the dangerous one, because it is small enough to be
  believed. (2026-10-06, C113.)

- **A DOTTED VERSION SORTED AS TEXT IS A TIME BOMB WITH A DATE ON IT: 2.10 <
  2.3.** The donor read picked the live judgment with `ORDER BY ...
  weights_version DESC`, and `weights_version` is `donor-anchor-2.3` — a
  string. Proven against the live database: text order ranks **2.9 > 2.3 >
  2.10**, so the day the minor reaches two digits the query serves the OLDEST
  judgment as the newest, and nothing says so — the page simply shows a
  superseded verdict. It had not fired because the version had never passed 9,
  which is the whole hazard: the defect is dormant, dated, and invisible until
  a routine bump sets it off. Compare the parts as numbers
  (`string_to_array(regexp_replace(v,'[^0-9.]','','g'),'.')::int[]`), and
  wherever a version, a build or a chapter number is ORDERED, ask what happens
  at ten. (2026-10-06, C117.)

- **A COUNT THAT NEEDS THE ROWS THE OTHERS EXCLUDE BELONGS IN THE `FILTER`, NOT
  THE `WHERE`.** The panel's held-back counts had `AND superseded_at IS NULL` in
  the WHERE, which is correct for every metric there — and made the superseded
  count impossible to take in the same pass. Moving the liveness test into each
  `FILTER (…)` keeps it one query over one population, so the "what we show" and
  "what we withheld" numbers cannot drift apart. Two queries would have been two
  snapshots of a table a derive rewrites nightly. (2026-10-06, C517.)

- **A KNOWN ERROR ABSORBED BY A GENEROUS THRESHOLD IS STILL AN ERROR, AND IT EATS
  THE THRESHOLD.** T7.58 parsed the published version stamp — written in the
  generator's LOCAL time — as UTC, and carried a comment saying so: *"the stamp is
  written in the generator's local time; compare generously"*. So the arm reported
  the live site's age as **-13 h**, exactly the NZDT offset. Three costs, and the
  third is the one that matters: the age shown to a reader was wrong by the offset;
  the effective ceiling became 49 h rather than the 36 h the docstring promises,
  and 36 was chosen deliberately as one missed daily release plus slack; and
  **a negative age satisfies `age > 36 h` perfectly well**, so a jumped clock or a
  stamp written in another zone reads as fresh for ever. An instrument that can
  report a negative age cannot be trusted about a positive one. Where a threshold
  is "generous" to absorb a known error, the error is the thing to fix — and a
  value that cannot be negative should RED when it is. (2026-10-07, C522.)

- **A SCALAR IN A MEASUREMENT ARTIFACT IS A DEAD END — RECORD THE ROWS BEHIND
  EVERY COUNT SOMEBODY MIGHT LATER ASK ABOUT.** The 2026-08-23 R3a artifact wrote
  `dissent` row by row and `abstain_one_side` as the number **110**. A card was
  then raised off that number — *how much of the 110 is the 1,024 reasoning
  budget?* — and the artifact it came from could not answer it, because it never
  said which rows abstained. Nor could the draw be re-derived: `sample()` shuffles
  a result set ordered by entity_id with a fixed seed, so it reproduces only while
  that set is still, and of the 54 dissent rows the artifact DOES name, **zero**
  were still in a fresh `sample(n=300, seed=20260822)` six weeks later (the same
  shape as #f00dec, one layer up). A count that cannot be resolved back to rows
  can only be REPEATED, never investigated — which is exactly what the card had to
  do, 44 days later, at the cost of a GPU run with the fleet paused.
  **And a paired measurement needs a SAME-SETTING control.** Judging one pinned
  50-row set at 1,024 and again at 2,048 gave agreement 0.540 → 0.560 and
  `abstain_one_side` 15 → 15 — so the budget buys nothing, which was the question.
  But only 4 of the 8 dissent rows were the same rows: at the row level the model
  is not stable between two runs, and with no 1,024-vs-1,024 repeat there is no way
  to tell that churn from a budget effect. Aggregates answered the card; the
  row-level question needed a control nobody had planned.
  *Paid for by:* 2026-10-07 (C261), the card's number first written 2026-08-23.

- **A CENSUS WINDOW THAT SCANS ONE DIRECTION REPORTS THE MOST CAREFUL CODE AS THE
  WORST.** `test_superseded_is_not_served` walks every read of
  `registers.donation_disclosures` and asks whether it filters superseded rows. Its
  window ran FORWARD from the matched `FROM registers.donation_disclosures` to the end
  of the SQL string, and the file's own comment says the window had already been got
  wrong twice ("the C113 census produced a 34 and a 17 before it settled, both times
  because the window was cleverer than it was correct"). It was wrong a third time in
  the same way: `influence_home` filters `superseded_at IS NULL` on four aggregates AND
  deliberately counts `superseded_at IS NOT NULL` on two more — every bit of it in the
  SELECT list, which is ABOVE the FROM clause. The window saw only
  `WHERE year_received = ANY(%s)` and named the single most careful read in the estate
  as the one that would serve a superseded declaration. **A SQL statement is not
  ordered the way a reader scans it: the clause that qualifies a table usually sits
  before the table is named.** The window is the whole statement, both sides.
  **And it failed for a day without anybody knowing, because the suite that holds it
  is not in the pre-push gate.** The gate runs `tests/` and this lives in
  `data-layer/registers/tests/`. A gate nobody runs is an opinion; found only because
  a card's own close ran the owning suite, which is the whole reason the close runs it.
  *Paid for by:* 2026-10-06 (C517 wrote the careful read) and 2026-10-07 (C107 found
  the census calling it careless).

- **BEFORE BELIEVING A ZERO, NAME THE ROW THAT WOULD HAVE MADE IT NON-ZERO.** C218 was
  argued shut with *"0 redundant and 0 cross-source duplicates"* over `content_index`.
  `content_hash` is that table's PRIMARY KEY, so one hash has exactly one row and
  exactly one source: the query asked whether a primary key has two values, and it
  returns 0 on an empty table, 0 on a perfect corpus and 0 on a corpus riddled with
  duplicates. The same trap sat in `documents`, where `sha256` is unique and "4,973
  with a sha, 4,973 distinct" is a restatement of the constraint. **A zero that agrees
  with you is the one you do not interrogate** — the test is not "is the number right"
  but "what would the database have to contain for this number to be 1", and if you
  cannot write that row down, you have measured a schema and not a corpus.
  **The general form: a de-duplicator's only observable is the REFUSAL, never the
  state of the table it writes.** The table is by construction the set of things it
  accepted; what it rejected, and on whose behalf, is nowhere in it. Count the
  rejection, with both sides named, or the safeguard's value is unmeasurable for as
  long as it runs.
  *Paid for by:* 2026-10-06 (the vacuous close, #968b7d) and 2026-10-08 (C218, which
  found it while trying to turn that zero into a gate).

- **"ABOUT A THIRD DONE" WAS A FRACTION OF THE WRONG DENOMINATOR, AND THE JOB HAD
  FINISHED.** C191 stood for weeks as *"society-officer full 60k sweep (~1/3 done) —
  longer background run if wanted"*, and a triage that re-counted the table (130,475
  rows, 22,766 societies) agreed the card was accurate and left the denominator open.
  The sweep's own SQL names its target: `WHERE entity_status = 'registered'`, which is
  **26,901** societies, not the 59,981 in the feed — the other 28,534 are dissolved,
  deregistered or removed and were never going to be fetched. 22,766 of 26,901 is
  **84.6 %**, and 22,766 / 59,981 is 38 %, which is where "about a third" came from.
  **Read the job's own selection criteria before computing its progress.**
  **The remaining 15 % was not remaining at all.** A society with no officers returns
  nothing, so "has no row" means EITHER unswept OR officer-less, and no completion
  marker distinguished them. Settled by asking the source: 150 of the 4,135 sampled
  through the API, **0 had officers the sweep had missed** (so at 95 % confidence fewer
  than ~83 of the 4,135 do). The sweep was finished. Where a job's output is allowed to
  be EMPTY, absence of output is not evidence of absence of work — and the cheap way out
  is not a completion column, it is one sample against the source.
  *Paid for by:* 2026-10-08 (C191), which asked for "a longer background run if wanted"
  and needed 150 polite requests and two SQL queries instead.

- **`ORDER BY id LIMIT n` IS NOT A SAMPLE, AND IT WAS WRONG BY A FACTOR OF FOUR HUNDRED.**
  C124 asks whether a claim's cited evidence names the claim's subject. The first
  measurement took 200,000 person-subject claims with `ORDER BY c.id LIMIT 200000` and
  reported **0.006 %** — twelve cases, every readable one a middle name ("Simon Bridges"
  against "Simon Joseph Bridges") — and the conclusion written beside it was "the signal
  does not exist in this graph, the card can close". The lowest ids are the OLDEST
  claims, and that slice is dominated by one extractor whose evidence always prints a
  full legal name. `TABLESAMPLE SYSTEM (2)` over the same table says **3.91 %**, about
  455,000 claims, 5,672 of 5,678 from a single DIFFERENT extractor. **A LIMIT without an
  ORDER you chose for representativeness samples whatever the storage order is**, and in
  an append-only table that is always "the past".
  **Then the predicate was wrong too, in the other direction**: asking for the subject's
  FULL name flags 19.5 %, almost all of it ordinary prose — "Trudeau urged Canadians to
  boycott…" names its subject perfectly well. And the containment test was a SUBSTRING
  test, so folded, the surname "Y" is inside "nobody" and "Ng" inside "being": a silent
  false negative that drops real cases out of the queue, found by a two-token fixture in
  the card's own test file. Three readings of one question, three different numbers —
  0.006 %, 19.5 %, 3.91 % — and only the last is about the world.
  *Paid for by:* 2026-10-08 (C124), where the first number would have closed the card.

- **A CAPPED SAMPLE REPORTED AS A COUNT HIDES THE KINDS, NOT JUST THE SIZE.**
  T7.10 printed `20 suppression-shaped ['XI', 'XI', 'XI']` every day for 27
  boards. Both of its queries carried `LIMIT 10`, so twenty was 10 + 10 and the
  population was **51** — the board-arm form of #8c9dd6, filed the day before.
  But the number was the smaller half of the damage. **The twenty were two
  defects with different causes**, and no single count could ever have shown it:
  forty were `Rev C` / `Justice P.` honorific residue, every one minted before
  2026-08-25 and none since, because the cast's `is_anonymised` guard holds and
  only the SWEEP was incomplete; the other eleven were every `XI` in the graph,
  and reading their evidence settled them in one pass — *"first XI cricket"*,
  *"an eclectic starting XI"*, *"the Cromwell first XI hockey goalie"*. A Roman
  numeral is not a suppressed name. One arm, one number, one word
  ("suppression-shaped"), and the word was wrong for 11 of the 20 for 27 days.
  **So a population arm reports the SIZE and the SHAPES, and the shapes are what
  make it readable**: `0 suppression-shaped (population 11, uncapped: {…}), 11
  Roman numerals read as initials — single-token persons, C539, not
  suppression`. The clause that empties prints a measured `0`, because "no rows"
  and "nobody looked" must not read the same.
  **AND THE RIGHT ACTION DIFFERED PER KIND, WHICH IS THE POINT.** The forty were
  quarantined — a cause already closed, so the judgment is just the rest of a
  judgment already made (2026-09-21 took 12 of 52). The eleven were LEFT LIVE
  and the arm left RED, because their cause is open: they are the visible
  eleven of **17,150 live single-token persons** that the mint policy forbids,
  which the override branch of `_entity_id_deterministic` admits by returning
  before the refusal. 731 minted today, so quarantining the eleven would have
  cleared the arm until tomorrow and taught the next reader the wrong cause
  (#8f68d8). **A red whose cause is open is cheaper than a green that lies.**
  *Paid for by:* 2026-10-08 (C536), 27 boards of a three-word finding nobody
  could act on.

- **WHEN MOST OF A POPULATION FAILS ONE THRESHOLD, THE COMMON CAUSE IS YOURS —
  READ THE DATES, NOT THE COUNTS.** T7.43 reported *"17 of 24 daily sources
  sparse for more than 7 days"* every day for 23 boards, and it reads like
  seventeen rotting scrapers. **Seventy-one per cent of a population failing one
  threshold is a statement about the threshold or about a common cause, never
  about seventeen independent things**, and the counts could not show which
  because a count has no dates in it. One query over the sparse DAYS did:
  2026-07-10..14 carried 20, 17, 15, 15 and 14 of 25 daily sources sparse AT
  ONCE, 09-10..11 carried 14 and 13, and 09-27 carried 22 of 25. **Our downtime,
  charged to every source separately** — and eight such days alone exceed a
  ceiling of seven, so every daily source was red BY CONSTRUCTION. Charging each
  to the estate once took 17 → 6, with two sources falling to exactly ZERO. Add
  ruling 290's stops (`blocked:credentials` on businessdesk and newsroom, which
  `_source_stopped` could not see because it read only `blocked:robots` of three
  recorded kinds) and 6 → 4. **The remaining four were two things:** three were
  one crashed unit — `party-sites-recapture` died on a btree index overflow on
  2026-10-04, was fixed by another card on 10-07, and runs WEEKLY so the fix had
  never executed — and one was a community paper's own rhythm. Eleven false
  positives had been sitting on top of a live, fixable, five-day gap in three of
  the seven front-page parties.
  **This is the same mistake one level up from #1484**, "a floor computed over
  all days cannot see a weekday", fixed three days earlier: that was a floor
  computed over all DAYS, this was a floor computed over all SOURCES. When a
  per-item threshold fires on most items, the next question is always what the
  items share.
  **CORROBORATION IS WHAT KEEPS THIS HONEST, and it needs testing from both
  sides.** A rule that can excuse a gap is a rule that can excuse ANY gap, which
  is the opposite of the arm's job and is what C500 cost — a card raised as a
  capture failure when the lane had been current all along. So: a real
  population before any day can be the estate's, a real share of it agreeing, a
  floor of at least two so one source cannot vote itself an outage, and tests
  that fail against a deliberately broken share AND a deliberately broken floor.
  **And the subtraction must stay visible** — the register lists the eight dates
  and a "ours too" column — because an invisible subtraction cannot be audited.
  **Separating blame is not the same as excusing collection.** A day we were down
  is a day whose articles were never collected, so the estate days STAY in
  `sparse_recent` and the backwalk still re-samples them; only the attribution
  moved. A test pins that coupling, because the obvious tidy-up — dropping them
  from the list the arm no longer counts — would silently stop the one process
  that can fill the hole.
  *Paid for by:* 2026-10-08 (C538), 23 boards and a five-day party-site gap
  nobody could see under eleven false positives.

- **A COUNTER INSIDE A CACHED PAYLOAD IS A CACHED COUNTER — AND ONLY CAUSING THE
  THING IT MEASURES WILL SHOW YOU.** The PI product counts what its rate limiter
  refuses and serves it on `/api/health`. I fired 60 requests at `:8300`, 45 came
  back 429, and the payload said **`total: 0`**. The code was correct: the
  middleware recorded every refusal. The body is cached for 5 s (a probe storm
  must be one connect per store, not two bare connects per hit) and the counter
  sat INSIDE the cached body, so it served whatever had been true when the cache
  was filled — before the flood. **A number up to five seconds behind is the
  wrong number precisely during the flood anyone reads it for**, and it is worse
  than that: the health probe has its own budget, so during a real flood the
  probe is refused and the last cached body is all a reader gets. The cache
  exists for the DATABASE round trips; a dict read costs nothing and belongs
  outside it, computed on the way out of every path and stored in none.
  **Reading the diff would never have found this** — every line was right on its
  own. Causing 46 refusals and reading the number back 3 s later, inside the
  TTL, is what proved it: 0 before, 46 after.
  **The same card had two defects of the same family filed as "owed" and one
  nobody had filed.** It counted from PROCESS START, so a board line could never
  say whether anything happened today, on a daemon that may have been up a
  month; and its per-client map was a plain dict keyed on every refusing IP,
  never pruned, in the one process whose job is to face strangers — **the
  payload only ever printed the top 3, which is exactly why nobody would have
  watched it grow.** The token buckets ten lines away had evicted since the
  beginning. When a module bounds one structure and not its neighbour, the
  neighbour is the one to read.
  **A cap that silently drops is a cap that lies about its total**: the overflow
  is counted (`other_clients`), so a reader knows when the top 3 is a sample,
  and a client already in the map keeps counting after the cap fills — otherwise
  the one address that matters goes quiet exactly when it gets busy.
  **And the number goes on the board WITHOUT a threshold.** A refusal is not a
  fault: 120/min sustained with a burst of 40 against a page load of ~5 calls
  means a real browser never meets the limiter and only an unpaced runner does.
  So the arm prints a number it cannot red on. The day a stranger appears in the
  top clients, that is a judgment for a person — and an arm that reds on it has
  to be built by someone who knows what normal looks like. Print normal first.
  *Paid for by:* 2026-10-08 (C126), a counter that was right for a month and
  told nobody, with a stale reading waiting underneath it.

- **A CUMULATIVE COUNTER CANNOT SAY "THAT WAS LAST MONTH" — SO AN AVERAGE SINCE
  RESET CANNOT SHOW THAT THE FIX LANDED.** T7.51 computed the WAL rate from
  `pg_stat_wal.wal_bytes` over the time since `stats_reset` and had been red for
  **22 consecutive boards** at 78.2 GB/day against a 64 GB/day budget. node1's
  WAL archive holds a TRUE daily series — one 16 MB segment per file — and it
  said the rate had already collapsed: **15,596 segments (244 GB) on 09-28, then
  976 (15 GB) on 10-06, 208 (3.3 GB) on 10-07, 215 (3.4 GB) on 10-08.** A ~25x
  fall, three days before the board was read, invisible to the instrument. The
  arm's own docstring defends the long average against a ten-second sample and is
  right to; the opposite error is the one that was live, and it is the harder one
  to notice because the number keeps looking plausible.
  **COUNT THE ARTEFACT WHEN THE ARTEFACT IS FIXED-SIZE.** A WAL segment is 16 MB
  whatever is in it, so counting files per day is EXACT where summing a
  cumulative byte counter is an average — and the archive is also the thing the
  budget is explicitly about, so the instrument and the question finally match.
  **GATE ON THE MEDIAN, REPORT THE WORST.** My first version gated on the worst
  of the last seven days, which keeps the arm red for a week after any single
  heavy night — the chronic red that teaches a reader to skip the board. A
  sustained overrun moves a median; a spike does not. Both numbers print either
  way, so nothing is hidden by the choice.
  **AND THE CLOCK HAS TO BE ONE CLOCK.** The second defect: `ls` dates the
  filenames in the BOX's local time and I compared them against a UTC date.
  NZDT runs 13 hours ahead, so "the last 7 complete days" silently dropped the
  newest complete day — exactly the day a reader is asking about, and exactly the
  day that would have shown the fix. The arm now asks the box for its own date in
  the same command as the listing.
  **A VERDICT THAT NAMES THE WRONG CARD IS WORSE THAN NO VERDICT.** T7.51's read
  *"C321 is the changed-tables nights that shrink it"* — and C321 is offsite
  DUMPS. `pg_dump` reads; WAL comes from writes. The actual source is the graph's
  own merge churn (`claim_entities`: 684 M inserts and 265 M deletes in 21 days),
  where every config lever is already set — `wal_compression=zstd`,
  `checkpoint_timeout` 1 d, full-page images only 6.6% of records. A plausible
  sentence pointed twenty-two boards' worth of attention at a card that could
  not have helped.
  **AND THE WORK IT WAS WAITING FOR WAS ALREADY DONE.** Both of the commands in
  the runsheet's ⌨ AT NODE1 block had been entered: the live server reports
  exactly what `postgresql-wal-tranche2.conf` asks, and the prune's own journal
  says *removed 7,101 older than 14 d; 1.3T on 1.5T free*. Nobody had checked
  from the box. (`ls /etc/sudoers.d/` denied me permission and I read that as the
  file being absent — the journal settled it, which is the absence-of-evidence
  rule turning up in the middle of its own card.)
  *Paid for by:* 2026-10-09 (C552), 22 red boards reporting a number that had
  stopped being true three days earlier, and a runsheet asking Arthur twice for
  commands he had already run.

- **A THRESHOLD THE DENOMINATOR CANNOT EXPRESS IS NOT A THRESHOLD — AND TWO RUNS
  ONE CASE APART ARE THE SAME MEASUREMENT.** The adversarial merge refuter is
  gated at `catch >= 0.80` over the `different` half of a frozen labelled set.
  That half holds **13 cases**, so the only achievable values are 9/13 … 13/13 =
  0.692, 0.769, **0.846**, 0.923, 1.0. **0.80 is not one of them**: the stated
  bar is really "11 of 13", one case moves the rate 7.7 points, and the two runs
  on record differ by exactly one — August 11/13 PASSED, October 10/13 FAILED,
  with six verdicts moving in BOTH directions on an identical judgment
  fingerprint. The 95% Wilson intervals are [0.497, 0.918] and [0.578, 0.957];
  they overlap by 0.34. So `catch 0.769 < 0.8` is not a finding about the
  refuter, it is a statement about the denominator, and a set this size cannot
  tell a refuter that catches half from one that catches nine in ten.
  **MEASURE WHAT THE SET COULD DECIDE BEFORE ARGUING ABOUT WHAT IT SAID.** To
  measure a threshold of this kind to ±0.05 takes about **196** cases. There are
  13. Best-of-N would cut the per-case noise and cannot touch the denominator; a
  confidence interval at n=13 has a lower bound near 0.5, which authorises
  nothing. The acceptance was never the problem.
  **AND "ALL THE MISSES ARE CLASS X" SAYS NOTHING WHEN EVERY CASE IS CLASS X.**
  The card recorded that all three misses were cross-type namesakes and concluded
  the weakness was "one nameable class, not noise". All **thirteen** different-
  cases are cross-type — organisation~person six times, person~people twice,
  place~person twice, and one each of place~organisation and person~facility.
  There is no same-type case in the catch denominator at all, so the observation
  is a property of the SET and localises nothing. A finding about a subgroup needs
  the complement to exist before it can be a finding.
  **RECORD THE RESOLUTION IN THE ARTIFACT, NOT IN A CARD.** The fix was not to
  move the bar — `CATCH_MIN` is ruling-pending and stays 0.80, `passed` is
  untouched, and the drain still fails closed, which is the safe state. What
  changed is that every gate artifact now carries its own achievability, step,
  interval and required n, and the refusal message that the journal quotes ends
  *"the set is the work, not the rate"*. A number that cannot support its own
  threshold should say so where it is read, or the next reader spends a week
  improving a rate.
  *Paid for by:* 2026-10-09 (C532, C540), a merge drain correctly closed for two
  days on a difference of one labelled case, and a card whose headline finding
  did not survive counting the set.

- **A COUNT DRIVEN OFF A STATUS COLUMN IN THE WRONG TABLE IS A PERMANENT NUMBER
  NOBODY CAN ACT ON — AND THE THIRD COPY OF A PREDICATE IS THE ONE THAT CLAIMS
  TO MATCH "EXACTLY".** `news/reconcile_ledger`, which runs every 15 minutes,
  printed *"captured now: 703370 / of those, extracted in v3: 0"* — a figure
  that reads as a 703,370-article extraction backlog and can never go down.
  Measured: **zero** of those rows are eligible. 703,068 are Papers Past marked
  `CONTENT_COMPLETE`, and every one of the 703,371 has text that is NULL or
  under 300 characters, so the drain is right to report `ok=0` and the fleet was
  never stalled. The ledger's `article_ledger.status` and the drain's
  `articles.pipeline_status` are different columns in different tables, and only
  the second decides whether a row can be extracted.
  **`v3/eligibility.py` exists because of exactly this** — *"a rule lands in one
  place or nowhere"* — and it had three readers plus one that kept its own copy:
  `ingestion/backlog.py`'s `captured_count`, whose comment said it mirrored *"the
  v3 drain's selection predicate EXACTLY"* while excluding **one** parked status
  of four. A 300+-character suppressed, held or duplicate row would have counted
  toward the daywalker's target for ever while being unselectable — the same
  phantom that function's own docstring records twice (1,088 rows in 2026-07, a
  7,919-row 200–299-char band in 2026-08). The live cost measured **zero**, so it
  is filed as a latent drift fixed at the cheap moment, not an incident.
  **The tell was two true numbers that disagreed:** 703,370 from the reconcile
  and 0 from `backlog.captured_count`, for the same question, an inch apart.
  **AND THE OBVIOUS FIX WAS FORBIDDEN, which is the half worth keeping.** "One
  home" says make the fourth reader import `v3.eligibility` like the other three.
  It may not: `ingestion/tests/test_boundaries.py` bars this package from
  importing `v3`, `extractor`, `claim_graph`, `reconciliation` or
  `candidate_register` — *"the moment capture imports the graph, the web edge has
  started doing identity work"*. I wrote the import, the boundary test caught it,
  and the estate's own mechanism for parity ACROSS a service boundary is a GATE
  on the restatement, which already existed and already held the 300. **A
  restatement with a gate is honest; a restatement without one is how this
  drifted.** So the check for "should this be one home or two copies" is whether
  an import is ALLOWED, asked before writing it.
  Two further turns of the same screw: the existing gate grepped
  `"length(a.text_content) >= 300"` out of the source and went red the moment
  that 300 became a named constant — **a source-text gate cannot see a computed
  value, so it fails on an improvement and passes a drift expressed as a
  variable**; it now imports both modules and compares the built predicate. And a
  test may cross the boundary the package may not, which is what makes the gate
  possible at all.
  *Paid for by:* 2026-10-09 (C555), found while trying to verify C539 against the
  graph and noticing a 10-shard fleet had written nothing for an hour.

- **BEFORE BUILDING A GROUND TRUTH BY HAND, ASK WHAT THE DOCUMENT ALREADY STATES —
  AND STRATIFY ON WHAT PREDICTS FAILURE, NOT ON WHAT THE PAGE LOOKS LIKE.** C411 is
  "the extraction bake-off: ground truth, then a method score", and specifies ~40
  pages with "printed figures keyed by hand", on the premise that *"there is no
  labelled page sample and no per-method score"*. Half of that premise is wrong, and
  the half that is wrong was already on disk: **844 of the 3,632 stored EC reads
  carry the form's own `stated_total`.** The document states its answer, so a
  method's rows either sum to it or they do not — an objective check needing nobody's
  hand, on twenty times the documents the card asked for. **264 of the 844 fail it
  today**, which is a labelled failure set for free, rankable by the size of the gap
  (worst: −$504,032 on a 25-row party return). Hand-keying is still owed, but only
  for what the form does NOT state — which rows, which donors, which amounts — and
  that is what a sample of forty is actually for.
  **AND THE CARD'S FOUR SHAPES ARE THE WRONG AXIS.** "Text table, photographed
  schedule, mixed, the 2008 form" all describe how a page LOOKS. Measured,
  appearance barely moves the outcome — **71% reconcile with a text layer against
  68% photographed**, at the same median table size — while table SIZE moves it a
  lot:

      rows  1-5   n=626   78%        rows 21-50  n= 29   55%
      rows 6-20   n=155   48%        rows   50+  n=  7   43%
      rows    0   n= 27    0%   <- a read that found nothing against a stated total

  A sample drawn on appearance would have been stratified on the axis that does not
  separate, and would have missed the 27 zero-row reads entirely — the sharpest
  failure class in the corpus, and the easiest to overlook because a read that
  returns nothing looks like a document with nothing in it.
  **AND THE SIGN OF THE GAP IS A REAL SIGNAL; THE SIZE OF IT IS NOT.** Of the 264
  failures, **170 over-count and 94 under-count** — and over-counting is the shape a
  duplicated row makes, which is worth knowing because C463 has an open
  duplicate-emission defect. So I tested the obvious fingerprint: does the gap equal
  exactly one printed row? 117 of 170 said yes, and **the figure is worthless.** The
  worst case opened to two DIFFERENT donors who gave the same amount —
  `Jonathan Hutton` and `NZ National Party, Selwyn Electorate`, $17,500 each — so the
  gap matched a row by coincidence. That is #235179, *round numbers from committed
  donors REPEAT, so amount-matching is a coincidence generator and not a
  fingerprint*, which I had filed that same morning for C544 and then reached for
  anyway. The document does not even resolve by arithmetic: four of its five rows sum
  to the stated total, and WHICH four is a judgment. **The direction of a discrepancy
  can be counted; its cause has to be read.**
  *Paid for by:* 2026-10-09 (C411), where the instrument "every later reader decision
  is judged by" turned out to be mostly present and unused.

- **"UNDER HALF THE PARTY-YEARS" WAS TRUE OF THE BARS AND WRONG ABOUT THE
  READING — THE DENOMINATOR HELD 35 YEARS IN WHICH NO RETURN COULD EXIST.**
  `data-layer/pi/SPEC.md` said the register holds a parsed return total "for
  under half the party-years since" 2019, and Arthur asked whether that was
  true. Measured: **59 of 136 served party-year bars are `declared` — 43%, so
  the sentence is arithmetically right.** But 35 of those bars are years BEFORE
  the party was registered (Alliance Party registered 5 August 2026; its
  2019–2025 bars cannot have a return) and 2 are 2026, whose returns are filed
  in 2027. **On the 99 party-years a return could exist for, 59 are declared —
  60%.** The claim read as "our reading fails more often than it works" and the
  truth is the opposite.
  What IS a gap is the **33 eligible party-years with no return held**, and it
  is not spread evenly: NZ Outdoors & Freedom alone is 7 of them, registered
  2017 with nothing held for 2019–2025. A number that conflates "the party did
  not exist" with "we could not read it" hides the only part anyone can act on.
  *Paid for by:* 2026-10-11. The shape, which this estate keeps paying for in
  new forms: **a coverage fraction is a claim about a POPULATION, and the
  population is the argument.** Before publishing one, subtract the rows that
  could not have been there — and where the remainder is concentrated, name
  where, because "43% of party-years" and "seven years of one small party" ask
  for completely different work.

- **A CUT THAT BINDS AND A PAGE THAT IS LOST ARE TWO CLAIMS, AND ONLY ONE OF
  THEM WAS TRUE.** Asked whether "the donor list is cut at 1,500, so a donor
  can lose its page". The cut is real and binding — 1,877 donors in the window
  before any fold, 1,500 taken by `ORDER BY total DESC LIMIT`, so **377 never
  reach the dropdown** and 1,350 survive the identity folds. The second half is
  false: the subject route takes a NAME and `influence_search` is a different
  query with no such cap, so a dropped donor keeps its page and stays findable
  — checked end to end on two of them (Simon Anderson $3,550, Remarkable
  Advisors Limited $3,500: absent from the dropdown, one search hit each, each
  page serving its money).
  **AND I NEARLY REPORTED THE OPPOSITE.** Both pages showed
  `donations_made_total: 0`, which I read as an empty page before checking the
  rest of the payload — the money was in `donations_made_to_candidates_total`,
  a separate pane kept deliberately apart (PI-42b), because a gift to a
  candidate is not a gift to a party. **One field is not a page**; a surface
  that splits a quantity on purpose will look empty to a reader who only knows
  one of its names.
  *Paid for by:* 2026-10-11. The cut is now declared in the payload
  (`donors_listed`, `donor_population`, `donors_not_shown`, `donors_cut_at`)
  under the standing rule that what the panel cannot show, it counts — and the
  basis says what is NOT lost, because that is the half a reader gets wrong.

- **TWO ROWS UNDER ONE NAME ARE A FOLD DEFECT WHEREVER THE FOLD RAN, AND A
  LIST KEYED BY THAT NAME TURNS IT INTO A LAYOUT BUG.** National's donor roster
  held "Craig & Shayne Greenlees" twice — $82,995 of return rows and a $50,000
  disclosure-only row — because `attach_disclosed_to_donors` folds on the FILED
  spellings, the two documents filed the name differently, and
  `apply_display_names` then gave both rows one name AFTER the fold had run.
  Nothing on the page said so; `pi_open_year`'s arithmetic held (the money was
  all there, once each). It surfaced as something else entirely: React keyed the
  rows by name, the duplicate key left a stale DOM node when the race selector
  swapped the list, and every race's roster opened with a donor that was not in
  it. Two rules: (1) any step that RENAMES rows after a fold must be followed by
  a fold on the new names, or the fold has not run on what the reader sees; (2)
  a client list keyed by a field the server does not guarantee unique is a bug
  waiting for the first duplicate — key by the row's own citation.
  *Paid for by:* 2026-10-16, found by `ops/pi_party_race.py` comparing the drawn
  first row with the payload's; fixed by `donations.fold_disclosed_into_namesakes`
  (the disclosure becomes the return row's `also_disclosed`, ruling 277) and a
  name + tier + ref key.
