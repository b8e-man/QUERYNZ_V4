# HEALING_SYSTEM — the rules catalogue

> The single human-readable list of every identity rule the estate runs.
> The rules themselves are CODE (cited per rule); this document is the
> review surface (also a Notes tab). New rules come from Arthur's review loop
> (good / bad / unsure / noise) — "we identify problems and make rules
> to solve them." Last reconciled against code: 2026-08-20 (era-4
> stamp row + doctrine 4 wording; full era-4 rule text lives in
> ERA4_RULES.md — this catalogue points rather than duplicates).

> Every doctrine point below was BOUGHT by a failure. The incidents
> live in [docs/doctrine/LESSONS.md](../../docs/doctrine/LESSONS.md)
> §2 (extraction & rules) — read it before proposing a new rule
> family; it records which rule shapes have already been tried and
> withdrawn at the gates, and why.

## Doctrine (the constraints every rule obeys)

1. **Abstain is the design.** A rule that cannot decide leaves the row
   alone (for the LLM lane or a future rule). No fuzzy scoring, no
   prominence/fame priors — register-asserted signals included.
2. **Reversible, audited, stamped.** Every action lands in a ledger
   (`entity_merges` / `entity_renames` / `entity_quarantine`) with the
   rule's name in the reason. Quarantine, never delete.
3. **Same rule at both ends.** A rule is enforced at mint time (extractor,
   version-stamped) AND applied in arrears to strata minted before it
   existed (deterministic heal, or LLM lane where structure can't decide).
4. **The LLM executes; Arthur reviews.** Verdicts auto-execute inside
   calibration bands (2026-08-14 ruling); every verdict is recorded;
   Arthur samples the verdict mirror / findings in chat (the Resolve
   surface was deleted 2026-08-14 — review is conversational) and
   mints rules, never touches the graph.
5. **The register is a helper** — correctness over coverage; corroborator
   tiers, never an oracle.
6. **Recover over exclude** (Arthur, 2026-08-15: "all of our rules are
   eliminating poor extraction output but they are also thinning our
   signal down"). A rule that can re-attribute signal instead of dropping
   it must (R-G13's split arm is the pattern); a rule that must drop
   leaves a reviewable drop note, never silence; and the running cost is
   measured — 83,774 of 16.2M era-3 mentions (0.52%) sit on quarantined
   entities, re-measured at each census. Mention re-attribution from
   already-quarantined composites is carded.

## The graph-dig rules (R-G series, all Arthur 2026-08-14)

| rule | statement | mint-time | in-arrears |
|---|---|---|---|
| **R-G1** | "Aotearoa New Zealand X" IS "New Zealand X" — fold, retain the Aotearoa surface as alias | `cast.py` (v3-det-1.2), alias retention beside the aotearoa fold in `build_cast` | folded during era-3 drain |
| **R-G2** | Place-blind executive titles: an executive/team title never binds a place entity (A8 extension, "Lloyd Budd" class) | `relations.py:188,209,483` (v3-det-1.2) | n/a (relation-time rule) |
| **R-G3** | A lowercase indefinite article is never part of a name — "a Winston Churchill" → "Winston Churchill" | `lexicons.strip_leading_article(indefinite=ERA3)` (v3-det-1.2) | `crawler.heal_article_led`: strip; fold if exactly ONE live same-type base node (`crawler:article-led-fold (R-G3 heal)`, 4,110), rename if none (`…-rename`, 3,547), abstain if ≥2 (61 left). Persons skipped — register rule owns person identity (1,113 in LLM lane) |
| **R-G4** | The negation of an entity is not an entity — "non-X" never mints | `cast.py` drop in `build_cast`, reason `negation-prefix` (v3-det-1.2) | `crawler.heal_negation_prefix`: quarantine (`crawler:negation-prefix (R-G4 heal)`, 1,194; residue 0) |
| **R-G5** | Post-nominal honorifics are not part of the name ("Anne Norman CNZM" class) | `cast._POST_NOMINAL` strip (v3-det-1.4) | `crawler.heal_post_nominals`: fold suffixed→bare when namesake-unique (`crawler:post-nominal-fold (R-G5)`, 1,068 + 110 media-corroborated) |
| **R-G6** | An institution wearing a person's name is not the person — a trailing institutional noun forbids person and names the type ("Edmund Hillary Collegiate" → organisation, "… Library" → facility, "… Avenue" → place, "… Trophy" → work) | `cast._corp_override` via `EPONYM_SUFFIX_TYPES` (reconciliation.lexicons, corpus-seeded 47 nouns; ambiguous surnames Park/Hill/King/Ward/Lane refused) (v3-det-1.5) | `crawler.heal_eponym_retype`: reversible retype through `entity_type_changes` (`crawler:eponym-retype (R-G6 heal)`; era-3 8,053 + era-2 8,165). Punctuation-guarded; retype only — same-name twin folds stay with the type-multiplicity lane |
| **R-G7** | "The High Court" and "High Court" are ONE node — the definite article folds unless The IS the name. **Both ends of the allowlist** (Arthur's Warehouse find, 2026-08-15): NER often leaves the determiner outside the span, so a protected name grows a bare twin ("Warehouse", 1,363 era-3 mentions beside a 14-mention "The Warehouse") — bare X re-attaches its The when "the x" ∈ THE_NAMES | C5 article strip (2026-07-31) + `THE_NAMES` allowlist (101 measured names, in `claim_graph.contract`); bare-form re-attach in `strip_leading_article` (v3-det-1.9) | `crawler.heal_definite_article` (fold/rename/abstain, ~3,500/era) + `crawler.heal_the_names_bare_twins`: same-type unique twin folds INTO the The-form, no twin + organisation renames, 2+ abstain (`crawler:the-names-bare-fold/-rename (R-G7 heal)`; era-2 44, era-3 104) |
| **R-G8** | A caption credit is not part of a name ("Bill English Photo: Supplied") — the colon form is structural; bare-word form restricted to photo/photograph/supplied (Blockbuster Video is a real name) | `cast._CREDIT_SURFACE_RE` trailing extension (v3-det-1.6) | `crawler.heal_caption_credit`: strip tail → fold on unique twin / rename / quarantine when the base is too short to be a name (`crawler:caption-credit-* (R-G8 heal)`; ~144/era) |
| **R-G9** | List bullets, attribution dashes and orphan quotes are markup, not name ("• Accenture", "— Phil Goff") | `cast` leading-junk strip (v3-det-1.7) | `crawler.heal_lead_junk` via the shared disposition (~21k era-2 class) |
| **R-G10** | A name ending in a function word was cut mid-phrase ("North End Health Centre and") — the English trailing-particle | `cast` trailing function-word strip (v3-det-1.7) | `crawler.heal_trailing_function_word`, iterative strip then shared disposition (~19k era-2 class) |
| **R-G11** | No real entity name contains a URL protocol or www. — capture artifacts quarantine; bare-domain outlets ("interest.co.nz") are spared | — (arrears-only) | `crawler.heal_url_fragments` |
| **R-G12** | Leading role titles are not part of a person's name ("Prime Minister Chris Hipkins") — bare military ranks deliberately absent (Major is a name) | — (arrears-only; mint honorific strip covers Mr/Dr class) | `crawler.heal_role_title_prefix`: R-G5's guarded shape — namesake-unique fold, register-ambiguous needs a corroborator, else rename/abstain |
| **R-G13** | A two-plus-comma surface whose segments are each name-shaped is an ENUMERATION, not a name ("Okato, Opunake, Stratford") — the first rule mined from the judge-verdict corpus (2,317 debris / 851 real_name on the 2-comma stratum, the real half dominated by lists the judge mislabelled real). One-comma names NEVER enter (58% real: "ReachLocal, Inc.", MBIE); Oxford-comma and lowercase/digit-led-segment names fail the shape test and pass. Shape test shared in `claim_graph.contract.comma_name_segments` | `cast.py` (v3-det-1.8): every segment register-known → **split, segments mint individually** (signal recovered — the first recovery-arm rule, Arthur's 2026-08-15 ruling below); else refuse with drop note `comma-composite` (reviewable). The pre-precedence gazetteer snapshot matters: longer-NER precedence is exactly how known-segment composites minted | `crawler.heal_comma_composites`: quarantine only when EVERY segment exists live (`crawler:comma-composite (R-G13 heal)`); not-all-known enumerations stay with the comma-list LLM screen — 50/50 judged, no deterministic call is safe there |

Ampersand twins (`crawler.heal_ampersand_twins`): "X & Y" / "X and Y"
same-type pairs fold — register side keeps, else the older node; the
merge keeps the other spelling as alias.

Standing orthography folds (`crawler.heal_orthography_twins`, run FIRST
so R-G7/9/10 folds get unambiguous bases): macron twin → macronned node
(register orthography canonical); case twin (JOHN SMITH) → mixed-case
node; exact 1-1 same-type pairs only. Shared disposition counts ACTIONS
only — abstains must never read as progress (drain-loop lesson,
2026-08-14).

Extractor stamps carry the rule era on every claim: v3-det-1.0 (base) ·
1.1 · 1.2 (R-G1–R-G4) · 1.3 (FINANCIAL) · 1.4 (R-G5) · 1.5 (R-G6) ·
1.6 (R-G8) · 1.7 (R-G9/10) · 1.8 (R-G13 comma split/refuse) ·
1.9 (R-G7 bare-twin re-attach) · **2.0 (ERA-4, V3_EXTRACTOR_ERA4:
A1 qualifier preservation, A2 appositive-affiliation, A4
party-boundary, R4-twin body-of-state; B1 normalization fixpoint,
B2 doubled-token halving, B3 outlet-prefix, B4 conjoined-names,
B5 function-word, B6 party-satellite — full statements, gates and
amendments in ERA4_RULES.md)**. `extractor/settings.py`.

## Māori-name rules

- **Mint-guard** (era-3, 8b8acbe): structure protects capitalised te reo
  surfaces; the traps list in `extractor/lexicons.py` is load-bearing —
  particles that signal a mid-phrase cut never end a minted name.
- **Screen patterns** (`mint_lane.PATTERNS`) for strata the guard predates:
  `trailing-particle` (name ends in te/ngā/o/mō/…), `lowercase-led`
  (lowercase-led te reo prose). Structure alone can't condemn a
  capitalised surface — these go to the LLM lane, never auto-quarantine.
- **Rule-gap detectors**: `negation-prefix` and `article-led` screens
  should stay at ZERO under v3-det-1.2+ — nonzero means a mint regression.
- **Leads-batch screens** (Arthur 2026-08-14, "you can handle these
  yourself"): mixed classes the LLM owns — `comma-list` (a list is not
  an entity; "Smith, Jones & Partners" is), `headline-prose` (person
  names >40 chars are usually headlines; long legal names exist),
  `possessive-stub` (single-token "Auckland's" lost its noun;
  McDonald's didn't), `quoted-name` ('John "Hondo" Smith' vs 'Caitlyn
  "Jesus'), `at-handle` (@handles may shadow real entities),
  `and-couple` ("Kate and Bob" is two people; "Marks and Spencer"
  isn't), `role-led-person` ("Former Prime Minister X"), `word-stutter`
  ("Picton Picton" is a capture stutter; "Aka Aka" and "Duran Duran" are
  names), `verb-phrase` (headlines hide real people — Will Hughes,
  Hamed Said). Backfilled both eras 2026-08-14/15 (~25k rows/era total).
  Verdict corpora from these screens are RULE-SEED material — mine them
  for deterministic rules once judged (carded).
- **R-G4 extension — embedded negation** (Arthur 2026-08-14, "we still
  have some non-maori entities"): "non-" MID-name is a mixed class
  (cohort labels and headline debris beside real things — "Nuclear Arms
  Non-Proliferation Treaty"; the register holds "Non Fungible Labs
  Limited"), so structure never condemns it; the `embedded-negation`
  screen sends it to the LLM lane. Prefix negation stays deterministic
  (R-G4 proper). Era-2 catch-up heals also run whenever the serving
  graph lags the era-3 ledger — R-G3/R-G4 applied 2026-08-14 (8,493
  folds/renames + 1,447 quarantines).

## The first queue (B4, ruling 9 — 2026-08-22)

Rules added to the crawler (`healer/crawler.py`) and the claim tier
(`healer/resubject.py`) for the era-4 wave residues named in ruling 9.
Every op goes through a claim_graph gate, is ledgered with the rule
name (T7.17 asserts it), and abstains where the evidence does not
decide. Gate tests: `healer/tests/test_gate_first_queue.py`.

- **trailing-repeat** (`heal_trailing_repeat`): a person name of 3+
  tokens whose last token repeats the previous one ("Jacinda Ardern
  Ardern"). Disposition = the shared R-G8/9/10 shape (fold into the
  unique live twin / rename / abstain on 2+). REFUSES when the repeated
  token is spellable in the Māori alphabet — reduplication is a feature
  of te reo (Te Heu Heu, Paki Paki, Kiri Kiri were the top matches of
  the naive rule); refusals are counted per run, never silent. Measured
  2026-08-22 before the rule: 1,150 persons / 1,489 mentions matched the
  shape, Māori reduplications inside.
- **Rt Hon / Hon** joined `_ROLE_TITLES`, so R-G12 strips them ("Rt Hon
  Winston Peters" folds into Winston Peters under the namesake-unique +
  register-corroboration rule). 107 such entities on 2026-08-22.
- **conjunction persons** (`find_conjunctions` → pattern
  `crawler-conjunction`): person mints shaped "A B and C D" (both halves
  2–3 tokens; "Simon and Garfunkel" is skipped). Judged by the TIER-3
  RE-READ — `research.crawler_judge.re_read`, a tool loop over the
  graph's own evidence with labels two-people / one-person /
  not-a-person (+ abstain). `execute()`: two-people ≥ `CONJUNCTION_SPLIT_BAND`
  (0.95 — a split MINTS entities; the first live hand-read found ~8/13 of
  the 0.90 verdicts wrong and all 14 at that band were reverted) → the
  SPLIT gate (`claim_graph.split.split_entity`, ruling 10): both halves
  become new persons carrying every mention article and every claim (a
  conjunction sentence is about both), the source is quarantined; the
  judged row is frozen into `var/audits/b4-conjunction-set.json` before
  the split — the acceptance set the plan cited but never enumerated.
  one-person / abstain clear; not-a-person ≥ AUTO_BAND QUARANTINES
  through the gate (reason `crawler:conjunction-not-a-person`, frozen
  into the set as `quarantined`) — the first live verdicts were 24/31
  furniture, advert phrases and implements, and parking them threw a
  paid verdict away; the rest park. The queue is capped at
  `CONJUNCTION_CAP` (40) per cycle and `judge()` picks it BEFORE the
  oldest-first backlog, else it never reaches the re-read (found live
  2026-08-22 behind 4,793 older rows). 5,481 candidates measured
  2026-08-22.
- **R7 role-string-subject** (claim tier): subject is a minted role
  string ('National MP', 'Labour MP', …) and the claim's own evidence
  reads "National MP Greg Fleming …" → re-subjected to the ONE live
  person of that name; none or two → abstain. 1,060 / 1,692 mentions
  behind those two entities on 2026-08-22.
- **R8 surname-co-mention** (claim tier): subject is a single-token
  surname ('Ardern') and the SAME DOCUMENT mentions exactly one live
  person whose name ends in it → re-subjected. The document's own
  co-mention is the evidence; no co-mention, or two, → stays.
  Prominence never decides which Ardern. Ledger: `claim_heals` with
  old/new subject columns (homed in claim_graph/schema.sql).
- Not yet owned by a rule: "National Government" (1 entity, 5,313
  mentions, typed organisation — a concept read), surname-only mentions
  (R8 moves claims, not mention rows). Both counted, carried in the
  ledger.

## Judge lanes (verdict vocabulary → disposition)

**Mint lane** (`mint_lane.py`, prompt fragment-tier1-v1, AUTO_BAND=0.9):
verdicts `debris | truncated | real_name | abstain`.
debris ≥0.9 → quarantine (`mint-lane:<pattern>`) · truncated ≥0.9 →
flagged-truncated (repair lane fixes, never deletes) · real_name/abstain →
cleared · below band → parked for the crawler · entity healed away
while queued → `gone` (verdict moot, not an error — race found live).

**Anchor lane** (`anchor_lane.py`, prompt anchor-v1, AUTO_BAND=0.9;
Arthur 2026-08-15: "hand the task to one of the LLM instances" — the
register panel's absurd-anchor spotting, mechanised after the NZTA
find): SCREEN is deterministic — an nzbn-anchored live entity whose
name shares zero content tokens with the register name AND every
trading name under that NZBN. JUDGE sees both sides (news surfaces +
evidence vs register row + directors + trading names): verdicts
`same | different | abstain`. different ≥0.9 →
`remediate.unanchor_entity` (nzbn NULL + gazetteer blocklist so the
next build cannot re-anchor; mentions/claims untouched, fully
reversible) · same/abstain → cleared · below band → parked. Verdicts
mirror to `anchor_lane_verdicts.jsonl`. First run: era-2 8/8
different at 0.95–1.00 (Waka Kotahi, Oturei Marae, Waitaha Primary
Health Trust…), era-3 zero suspects — the v0.6.1 gazetteer gates held.
Rides the crawler cadence.

**Crawler lane** (`healer/crawler.py`, moved from reviewer in B4 2026-08-22): `crawler-acronym-org` (verdicts
organisation/person/place/concept/work/debris/real_name; retype only at
≥0.9, else cleared) · `crawler-type-multiplicity` (mistyped-duplicate /
distinct-entities-ok / conflated). Since stream S5 (2026-08-19)
mistyped-duplicate verdicts ≥0.9 DRAIN via `crawler.merge_duplicates`
(in the timer run() behind B4b's adversarial refuter — measured-gated,
capped; it rode run() 2026-08-19 → 2026-08-22, was removed by ruling 31,
and B4b restarted it once the refuter gated it — `crawler-merge` is the
CLI form. audit #44, 2026-08-30): verdict
selects, EVIDENCE
directs — the verdict names no keeper (first-tranche lesson: 14
merges reverted after the queued representative proved to be the
correctly-typed side). Pair-case only; keeper = the register-anchored
side, else mention dominance ≥0.75; n-node names / both-anchored /
no-dominant park with reasons in the mirror. Merges go through
`claim_graph.merge_entities` (full payload, revertible in-era —
revert path exercised live on the 14). Arthur sampled the mirror and
passed it (2026-08-19) — the actuator rides the daily crawler timer
(`MERGE_CAP = 40` per run in `healer/crawler.py` since B4b's refuter gate;
the CLI's `--cap 500` default is the hand-tranche ceiling — corrected
2026-09-04, audit A58). Conflated (a split, not a merge) and
distinct-entities-ok stay observation-tier.

**Repair lane** (`repair.py`, cap 300/run): truncated names —
register-unique or media-corroborated merge (`repair:truncated-merge`),
else rename (`repair:truncated-rename`), else abstain; no evidence →
`repair-no-evidence` (re-queue policy carded).

## The adversarial merge refuter (B4b, 2026-08-22)

Every verdict-backed merge (`merge_duplicates`) now passes, after
target resolution, through `research.merge_refuter` — an agent whose
ONLY job is to find evidence the two entities are DIFFERENT (graph
reads on both sides, then robots-absolutist web lookup). Dispositions:
`refuted` → the pair parks as `refuted`, no merge; `not-refuted` → the
merge proceeds with `refuter:not-refuted <conf>` in its reason (a
failed refutation, not a confirmation); `abstain` → parks. Junk names
(`_JUNK_NAME`: '4fd', '7/u', '2.20pm', '18S4') park as `junk` without a
refuter call. Ledger: `merge_refutations` (verdict, reasoning, evidence,
fetched URLs, merge_id). Cap 40 pairs per crawler run. Believed only as
far as its last measured gate run (`ops/b4b_refuter_gate.py`,
`tests/test_refuter_gate.py`: catch ≥0.80 on labelled-different,
false-refute ≤0.10 on labelled-same).

## Corroboration tiers (`corroborate.py`)

Order tried: `media-shared-article` → `register-shared-org` →
`register-shared-office` (PAF preferred); first hit is recorded in the
merge reason; none → abstain. Register namesakes ≥2 REQUIRES a tier;
register unreachable counts as 2 (strictest). "No register occurrences
get combined on name alone."

## The review loop (conversational, 2026-08-14)

The Resolve surface was DELETED 2026-08-14 (Arthur: "I'm going to talk
to you about these things from now on and traverse the graph myself…
and find things wrong"). No review queues, no tag buttons, no human
graph writes of any kind. Arthur reports problems in conversation;
Claude turns them into rules here; the doctrine is unchanged — good /
bad / unsure / noise as the vocabulary, no revert. The auto-rule the
surface carried (register signal tagged bad → `gazetteer_blocklist`
insert, `rule:signal-tagged-bad`) retires with it; blocklist entries now
land the same way rules do, from the conversation. The decision corpus
(`review_decisions`) and the blocklist keep their history.

## Register-mint hygiene

- **Whitespace collapse** (2026-08-14): roster fields arrive padded
  ("Tracy  COGHLAN") — `ops/mint_register_entities._clean` collapses at
  insert; 811,207 existing names bulk-normalised through the
  entity_renames ledger (`mint-hygiene:whitespace-collapse`), both eras.

## Gazette-derive rules (GZ series, 2026-08-15 — deterministic parser rules; each names the CAUSE it cures)

- **GZ-1** clock tokens gated the date-trim → a clock opens a date run.
- **GZ-2** dropped-newline glue fuses digits to names ("2003.Broadband")
  → digit-punct-letter tokens split before any trim.
- **GZ-3** wrapped lines hyphen-fuse connectors ("And-D.K.") → strip.
- **GZ-4** cue-word variants outside the kind map leave "called" in
  aliases → aliases cue-stripped at every emission point.
- **GZ-5** matched_nzbn/match_basis had NO writer (schema without code
  reads as "no matches") → matcher built with A-1 semantics: unique
  register name fills matched_nzbn; else `name-candidates:n`; flags
  amber until corroborated.
- Cause classes recorded as future-rule food: unrecognised tokens stop
  guards; lost line boundaries manufacture fused tokens; enum-mapped
  extraction degrades silently on unlisted variants; schema-first
  columns without writers lie.
- OPERATIONAL (corrected 2026-09-04, A58): since the 2026-08-18 cutover
  nzbn_canonical is CANONICAL ON NODE1 and every writer (gazette-derive
  included) is repointed at `db-primary`; the "derive writes node2, fleet
  reads node1" twin drift is closed. The nightly node1→node1 self-copy
  the derive still carried was retired in Muster 2 (K1); the standby
  rebuild is Arthur's (K11 → D11).

**GZ-6 — trailing punctuation and qualification initialisms**
(feed find, 2026-08-15: prohibited director minted as "Barry Ross
Higgison."): sentence punctuation is never part of a name —
`parse._clean_person` trims trailing `.,;:` from person names,
`_trim_company` from company tails, alias cues keep dotted cores
("Oval.Co.NZ." → "Oval.Co.NZ"); and a "name" that is ONLY
qualification initialisms (C.A., M.B.A. — 170 practitioner rows the
signature regex caught instead of the person) NULLS rather than trims.
In arrears: 125 gazette-sourced graph entities renamed per era
(`gazette-feed:GZ-6-trim`). Rebuild lesson recorded the same hour:
gazette table rebuilds change serial row ids, so `feed --rebuild`
purges by FAMILY through the gate; and person reuse now rides
entity_keys (claims-based rosters forget everyone the moment a purge
runs — 70,632 duplicate nodes per era minted once, quarantined as
`gazette-feed:rebuild-orphan`, 126,896 keys backfilled). Residue: 25
insolvency company names carrying embedded legal phrases — a future
GZ rule, different cause.

### The gazette → graph feed (A0.4 as amended, Arthur 2026-08-15)

Ruling: "I want the aliases to be fed into the graph and I also want to
extract edges and context." A0.4's core stands — the Gazette is NEVER
LLM-extracted (zero extracted claims) — and deterministic, cited claims
DERIVED from the typed gazette.* tables are now the sanctioned path:
`gazette_register/feed.py` → `claim_graph.register_claims` gazette gates
(the F7 pattern: extraction_method='register', stamp gazette-1.0,
qualifiers.row_id idempotency, delete-and-replace per row). Per era:
414,797 claims (insolvency events + practitioner roles, prohibitions
with GZ-5 match qualifiers, public appointments), 4,302 alias links
(seen_count=0 — register-asserted findability, article sightings
ratchet later), 56,632 gazette-keyed orgs (pre-NZBN companies), 70,917
register-sourced person occurrence nodes (roster-scoped reuse;
prohibited directors key per (notice, name); corroborate tiers own the
folds, as ever). The three retired reconcilers are DELETED; the
gazette_register boundary test pins all of it (no raw graph writes, no
legacy imports, no network). Runs nightly after derive against the
serving era (era 5 since 2026-09-03; "both eras" was the era-3/4 twin
period — corrected 2026-09-04, A58).

## Search rules (lookup-side, graph untouched)

- **Honorific-blind search** (Arthur 2026-08-14, the Sir Edmund Hillary
  find): the extractor strips pre-nominal honours at mint and keeps no
  "Sir X" alias, so an honorific in the query matched only register
  names that happen to carry it. `/api/search` strips Sir/Dame/Lord/
  Hon/Rev/Dr/Prof from the QUERY and matches both forms. Canonical-name
  policy unchanged.

## Standing hygiene rules

- `crawler.quarantine_orphans`: article-minted, zero references anywhere →
  quarantine (`crawler:zero-reference-orphan`, 2,001 to date).
- `acceptance:macron-twin-fold`: register orthography (macronned) is
  canonical when a macron/plain twin pair is same-type (13 to date).
- Eager register mint: persons are OCCURRENCE nodes
  (`nzbn|lower(name)` keys); name alone never combines; companies dedupe
  on NZBN, charities on registration_no, govt on org_id.

## Audit surfaces

Ledgers (`entity_merges`, `entity_renames`, `entity_quarantine`) — reason
= rule name. `mint_review` — verdict/confidence/reasoning per judged row.
`var/reviewer_verdicts/*.jsonl` — every verdict + model stamp + prompt
version (Arthur's sampling surface; standing cross-box sync is carded).
`review_decisions` — Arthur's tags. `guard_drops` — mint-time refusals.

**Gate tests** pin each rule: `healer/tests/test_gate_crawler.py`,
`console/tests/test_boundaries.py` (audit #46, 2026-08-30: the former
`console/tests/test_gate_decisions.py` reference was dropped — no such file).
