> Part of [LESSONS](../LESSONS.md) — living memory, one section per file
> since 2026-10-04 so that "read the relevant section" is a thing a reader
> can do. The rules of the file, and why it exists, are in LESSONS.md.

## 2. Extraction & rules

- **Scarcity is not identity.** A candidate that is the only one left is not
  thereby the right one; require uniqueness on BOTH sides or drop the pairing.
  *Paid for by:* 2026-09-27, the party rename chain. Matching a gazette party
  to a roll party by registration window alone paired `New Conservative` AND
  `New Conservatives New` with `Women's Rights Party` — nine days apart and no
  relation. They were simply the only gazette parties near the only roll party
  with no registration of its own. Requiring one candidate on each side
  dropped all three and kept the three that were real (`Maori Party` → `Te
  Pāti Māori` among them). The discipline belongs in code, not in SQL: it is
  the load-bearing half and a test has to be able to reach it.

- **"New Zealand" is a place; "New" is part of a name.** Strip a country as a
  PHRASE, never as a word. *Paid for by:* 2026-09-27. The loose name-matching
  arm skipped the bare word `new`, which makes `New Zealand Labour Party` and
  the filed label `Labour` one party — correct — and `New Conservative` and
  `Conservative Party NZ` one party, which is two real parties folded into
  one. The same character of error as an over-eager alias rule anywhere else:
  a normalisation that helps on nine names silently merges the tenth.

- **One sentence, syndicated, is one fact.** Count distinct evidence, not
  claims, wherever a number is offered as weight.
  *Paid for by:* 2026-09-27. The first render of the pair-evidence panel spent
  three of a twenty-five-row sample on the same NZTA quote carried by scoop,
  odt and rnz — three claims, one fact, and twenty-two facts pushed off the
  page. Corpus-wide the gap is large: Peter Brown's 699 claims are 461
  distinct sentences, Peter Dunne's 9,032 are 6,041. A panel showing only the
  larger number tells a reviewer there is more evidence than there is, which
  is the exact error an identity queue exists to catch.

- **A record is not a person because it has a name.** Check the span before
  judging the match. *Paid for by:* 2026-09-27, C429. Nine of eighteen pairs
  on the identity queue have an A side carrying claims across more than a
  century — Peter Brown 1858 to 2026 with 17 records already merged in, David
  Wilson 147 years with 19. The oldest are real: an 1858 assault and an 1882
  fine for a stray horse, different men in Papers Past. The judge's `unsure`
  was never a failure of the judge; it was being asked whether B is the same
  person as A while A was several people. **Judging harder cannot clear a
  queue whose question is malformed.**

- **Screens rank; evidence convicts — and the standing four: abstain is the
  design, recover before you exclude, prominence never scores, the register is
  a helper and not an oracle.** A cheap structural query proposes candidates;
  conviction is evidence-gated, reversible and audited. → HEALING_SYSTEM.md
  doctrine 1/5/6; memory: prominence-never-scores.

- **Name shape is not identity: require an ID, ordered-token equality with a
  distinctive-token guard, or independent corroboration.** A ranking finds
  candidates and never decides them. Transitive signals need a
  name-compatibility gate or one hub eats the graph. A verdict must never name
  the keeper — the screen says WHICH PAIR, the actuator takes the survivor from
  evidence (register-anchored side, else mention dominance ≥0.75). And
  provenance can decide structurally where a count is banned: a
  companies-register director node (`nzbn-roster`/`charities`) is BY
  CONSTRUCTION not the parliamentary-corpus person node (`NULL`).
  *Paid for by:* the fuzzy matcher's "Ministry of Defence → MINISTRY OF DENIM
  LIMITED", and its ungated successor mislinking 40–50% of a sample and ~30% of
  its first live hour (Oracle, Forbes, Meta and ACT onto coincidental shelf
  companies) · shared coref-alias plus shared neighbours folding ACC, MBIE and
  DOC into "New Zealand Government", 444 nodes absorbed · 14 crawler merges
  reverted because the queued representative was the correctly-typed side ·
  2026-08-27 (roster G2): filtering to corpus-born candidates collapsed 158
  ambiguous members to 125 single-candidate + 33 genuine fragments with no fame
  prior touched (ops/roster_g2_judge.py) · 2026-08-26 (MP roster):
  string-derivable variants (honorifics, case, confusables/mojibake, decomposed
  macrons) belong in the alias KEY normaliser (`norm_form`) and only there —
  additively, never subset/middle-name folding; non-string coreference (married
  name, diminutive, matai title) is a CITED, reversible MERGE judgment, and a
  roster drives NOMINATIONS for the evidence gate, never a pick by mention
  count · 2026-08-28, JONDAC: a UK Companies House hit (06566292, incorporated
  in the declaration year) was briefly recorded as Jones's — its sole officer
  is Jonathan David Caudwell, "JON-DA-C", no Jones ever. Checking the OFFICERS
  — one WebFetch — is what caught it. A declaration that anchors to nothing in
  NZ registers stays HONESTLY UNRESOLVED (`matched_by='none'`), and the
  research agent's job is VERIFICATION, not discovery: confirm the person is on
  the foreign record, and RECORD the rejection so the lead is not re-chased.

- **A wrong merge launders itself into ground truth — so a merge whose only
  evidence is name shape goes to review, and the undo re-points everything
  created in the error window.**
  *Paid for by:* "Will Foley", auto-merged on name shape, whose merge-added
  alias then routed five more days and 33 new claims to the wrong man.

- **A resolver's "no match" is a QUESTION with several answers — inspect the
  residual, never infer a remedy from the count.** Unmatched means "unmatched
  under THESE keys", never "absent"; confirm non-existence with a broad name
  probe before minting an identity, and read a leftover bucket row by row
  because that is where the heterogeneous hard cases concentrate.
  *Paid for by:* 2026-08-27, the roster→graph reconcile left 6 MPs unmatched
  and the arithmetic invited "mint them" — every one ALREADY had a graph
  entity, for three different reasons: initials the roster carries but the
  corpus spells out; a person entity whose alias was never normalised/linked;
  and suffix-polluted duplicates that fold to nothing clean. Minting would have
  deepened the fragmentation the abstain was pointing AT.

- **Person fragmentation has two sources and one rule owns one of them.** Real
  people shatter as (a) caption/role/outlet pollution on a real name ("… MP",
  "RNZ …", "… Photo:", "Doug Woolerton Opinion") and (b) OCR-shatter junk from
  Papers Past ("tlie j Minister"). Measure a cleanup rule against the defect it
  actually owns, or its impact number is mostly someone else's noise; and a
  name-only suffix strip must never touch a token that is also a surname
  (green/act/pool) — that needs the extractor's per-mention context. Until a
  capture-time cleanup exists, roster reconciliation SURFACES the fragments as
  its residue, which is signal, not noise.
  *Paid for by:* 2026-08-27, a measurement of `name_suffix.py` that "recovered"
  ~5k names when ~all the bulk was (b), a quarantine problem.

- **A name-shape rule is proved against the names it would kill before it
  ships, and an OCR garble is never hand-mapped to the name you believe it
  is.** Set the threshold for the CLASS and carry exceptions in a curated
  allowlist — never loosen the threshold to catch them. Reserve the ambiguous
  short tokens before they cost you something. And a register ASSERTS a name
  while a parse GUESSES one: only a guess can be junk, so the predicate judges
  the string and the CALLER judges whether the string was asserted.
  *Paid for by:* 2026-08-20, era-4's B2 trailing-repeat arm would have eaten Te
  Peeti Te Awe Awe and Ma Htet Htet; the counter-example corpus withdrew it at
  the gate (residual: even-length exact reduplication still halves — carded) ·
  dropping the 3-character cast floor to admit "NZ" and "US" would have minted
  `ev`, `gp`, `pe`, `ko` as organisations; same shape for KEEP_FORMS and
  THE_NAMES · 2026-09-20: `AND LIMITED` (NZBN 9429036191666), `WITH LIMITED`,
  `A A LIMITED` and `LIMITED LIMITED` are real Companies Office registrations,
  so a junk-name rule reading only the string would have quarantined twenty
  real companies; and `AT` is Auckland Transport while `IN`, `ON`, `OR`, `BY`
  will one day be an acronym — making them filler-only rather than heads cost
  2 mentions of 207,255 and removed the class · "ee", "G6" and "Wwarwiek ¢
  Avercil" are caught by rule (letters < 3, a junk glyph, digits without a
  word); "Chaistopher Yaakin" $820,500 and "OREGON GRovP" are wordlike and
  pass, so abstain is correct and the re-read of the page crop (C171) is the
  only honest repair — it needs a reader that can SEE (tesseract at 200 dpi
  through a text model is what produced these). *No vision model was packaged
  on either box when this was written; C412 chose one on 2026-09-22 — GLM-OCR
  — so the re-read is now available and the lesson's conclusion stands with
  its blocker removed.* The fold rule (ruling 192) exists precisely so that only
  identical-after-normalisation spellings ever merge.

- **A guard runs against the value it guards, AFTER everything that can change
  it — and a bug that comes from ORDER is fixed with a fixpoint, not another
  pattern.** When a guard is conditioned on a field, ask what else writes that
  field and whether it runs first. Corollary for the LLM half: a verdict is
  only safe to act on within the question it was asked.
  *Paid for by:* 2026-09-19 — the caster refuses a bare role arriving as
  `person` or `concept`, and its drop record proves it working 46 times on one
  form; it still reached the graph because NER read the surface as an
  ORGANISATION, which the guard allows, and an `entity_type_overrides` row
  applied LATER in `consume` retyped it to `concept` on the way in. Nothing was
  wrong with the predicate or the scope — only the ORDER; and the judge had
  answered "is this really an organisation?" correctly with "no, a concept", a
  true answer to a question that was never about whether the thing should EXIST
  · "The Rt Hon John Key" still minting at v3-det-1.9 because the honorific
  strip is `^`-anchored and runs BEFORE the article strip, so a leading "The"
  shielded the honorific the article strip then exposed — B1 became "repeat the
  cycle until the surface stops changing" · fixing one normaliser can remove an
  accidental shield: the macron fold exposed, twice in two days, that
  variant-merging stripped a leading "te " (Te Mātā → Mata, Te Brake → Brake;
  2,051 merges reverted), because macronised names had been safe only in that
  they could never match. Re-run the neighbouring rules after ANY normalisation
  change.

- **An absent configuration must not silently select the OLDEST behaviour, and
  a default on a scope/type/era parameter breaks idempotent re-extraction as
  well as mislabelling.** A default that is merely OLD looks like a default;
  the tell is that nothing had to ask for it. Put the refusal on the WRITE
  path, never in settings — importing a settings module with a bare environment
  has to keep working.
  *Paid for by:* 2026-09-19 — `extractor.settings` reads four era flags and,
  with none set, falls through to `v3-det-0.7`, a 2026-07 extractor with every
  era rule inert, stamping claims with that version. On 2026-09-18 a hand-run
  from an unsourced shell extracted 52 articles that way while the standing
  tick stamped 1,924 rows of the same backlog at the current era; no unit was
  misconfigured, and the hole was that an unconfigured process could write at
  all. The drain now refuses unless the flags were configured or the caller
  says it wants the flagless default, and a flag set to `0` COUNTS as
  configured so the golden-corpus proof is untouched · Hansard's documents were
  right while its 769 claims defaulted to "news", and re-extraction under the
  correct label could never clear them, because the cleanup DELETE is scoped by
  that same key.

- **A rule expressed once is half a rule: every error family needs a
  mint-guard AND a crawler screen — and a rule fix binds only FUTURE
  extraction.** Nothing in the graph heals itself, so a rule change is not done
  until its re-extraction is scheduled; sweeping is a cost per rule-change ERA,
  not a one-off. → HEALING_SYSTEM.md doctrine 3.
  *Paid for by:* the re-extraction table going from three rows to nineteen in a
  single day, each addition a reason the sweep would have had to run again had
  it gone first.

- **Determinism is the revert path — which is why flag-off byte-identity is
  the whole guarantee, and why re-extraction destroys anything keyed to a claim
  id.** The extractor is a pure function of (document, era flag); reverting an
  era is re-running it. Consume is delete-and-replace per article, NOT
  quarantine. Every wave must be followed by deterministic resolve waves.
  *Paid for by:* `entity_merges.payload` pointing at claim ids a wave deleted —
  all 129,269 pre-sweep merges are in this state, which is the concrete
  argument for entity-as-derived-view (→ terminal Layer 1; plan Phase 7).

- **Deterministic derive beats LLM extraction wherever grammar reaches, and
  coverage runs with the burden flipped.** Emit a relation only if the text
  states it and leave the entity uncovered otherwise; every input either yields
  typed facts or matches an explicit fact-free whitelist, and unexplained
  residue FAILS the run. Coverage that isn't accounted for is not coverage.
  Classify templated documents by the source's own structural code, not by
  title regex, and keep the title as a cross-check only.
  *Paid for by:* the courts caption parse scoring 119/119 with no LLM at all
  (→ FLEET.md composition rule) · one recall-chasing rule that manufactured
  weak relations and then poisoned three separate measurements — the anchor
  gap, the descriptor saga, and corroboration inflation · title patterns
  dumping 49.6% of gazette notices into "other" where the notice-id prefix
  mapped cleanly and is zero-maintenance.

- **Measure what the pipeline does AFTER a proposed rule fires — the fallback
  path is often worse than the defect.**
  *Paid for by:* demoting single-token register matches labelled PERSON, which
  would have taken Fonterra from organisation-with-NZBN to person to entirely
  OUT of the graph, because consume never mints a single-token person.

- **A new provenance or label column is only as good as the LAST path that
  carries it — enumerate every writer, fold, migration and revert before
  shipping, and constrain it with a CHECK.** A value that isn't carried
  everywhere is worse than no value, because it reads as trustworthy. Related:
  SQL exclusions are NULL-blind, so `coalesce(..., false)` everywhere with a
  gate test that fails on the pre-fix code.
  *Paid for by:* 2026-08-26 (audit F1) — adding `alias_link.basis` was easy;
  the fold migrations (`ops/fold_aliases.py`, `ops/clean_folded_aliases.py`)
  repointed links WITHOUT the column, so the survivor of a fold that included a
  register-authority alias silently became 'frequency', defeating the column's
  purpose for exactly the rows the fold touched; two more writers
  (enterprises.py, the shortform feed) set the wrong or no basis · a bare `col
  = ANY(...)` filter that silently dropped every row where the column was NULL,
  removing every article-person from auto, crosstype and hygiene folding.

- **"Keep the longest variant seen" systematically selects for extraction
  artifacts, and longest CONTAINING match wins while an NER type label never
  vetoes a verbatim gazetteer hit.** Normalise before storing anything that
  will be displayed.
  *Paid for by:* cast keyed on the whitespace-collapsed form but storing the
  raw span for display, so `Google\n\n\nAnalysis` always beat the clean form —
  39,575 dirty display names, clustering perfectly correct, every name a human
  read wrong · without containment, bare "Fonterra" swallowed "Fonterra
  Co-operative Group Limited" and left "Group Limited" as its own organisation;
  and because spaCy called "Fonterra Limited" a PERSON, writing a company's
  full registered name was the one phrasing guaranteed NOT to anchor · a
  surface form shared by more than K entities is a coref word, not a name —
  "the man" absorbed 76 mentions and "Ministry of Health" fused foreign
  ministries, so the `_STOP_FORMS` guard extends to the alias WRITE, not just
  linking (er_redesign_notes S2).

- **A place or institution NICKNAME can collide with a real company name, and
  the extractor will link every mention to the company.** The label is RIGHT
  for the company; the LINK is wrong — fix it upstream, and note that the tell
  was the aggregate being EXPANDABLE, because the artifact hid inside the total
  until you could see its contributors.
  *Paid for by:* 2026-08-27 — "The Beehive" is Parliament's Executive Wing and
  "THE BEEHIVE LIMITED" is a registered restaurant (BIC H451130), so 27 senior
  politicians were press-linked to a café and its genuine Accommodation-and-Food
  BIC flowed as spurious industry exposure; serving blocks the nzbn as a
  stopgap (_METONYM_BLOCK_NZBNS).

- **A form is not the filer, a form's own furniture is not data, and a
  register's CATEGORY is not the role TITLE.** What the FORM prints is an
  observation of the form: learn its examples, headers, aggregate rows and NIL
  markings before trusting a row in the data area, and read the member's own
  words where the filing bucket disagrees with them. A parser that reads a form
  must not ingest the form's instructions. What a column HOLDS is a judgment
  made at derive time, so every consumer inherits it — fixed upstream, never
  patched in the view. And a gate that fails is EVIDENCE about the parse, not
  only about the file: a pattern of residuals is a rule waiting to be written.
  *Paid for by:* 2026-09-05 (rulings 190/191) — the EC candidate return prints
  a greyed worked example, "EXAMPLE: John Smith, Smiths Publishing, $5,000", in
  the Part A data area; the page-read kept it on 68 returns, the loader summed
  it, "John Smith" became a $218,756 donor with a dossier, and 52 returns
  failed the sum gate BECAUSE of it. The reader's own `note` said "illustrative,
  not a donation" and nobody read the note — a loader that keeps a row the
  reader flagged is not recovering signal, it is laundering an artefact
  (`line_kind`) · 2026-08-28: the mp_interests PDF parser exploded the Standing
  Orders preamble into hundreds of fake declared "orgs" ("(a) the Crown:",
  "voting right means…"), Jonathan Young alone carrying ~60, because each
  fragment looks like a row — a real declared org is a proper noun, boilerplate
  starts "(" or lowercase, dangles on "and/or/:", or cites an Act/clause
  (routes._mpint_is_garbage, 666/2788 dropped; root fix is the parser +
  re-sync) · 2026-08-28: mp_interests mapped category→label, so 22
  "discretionary beneficiary only" declarations were served as "Trustee", and
  "chair of board"→Employee, "celebrity dancer"→Employee
  (routes._refine_mp_role).

- **Exact-name anchoring to a BULK snapshot misses; the register API is the
  escalation, and a hand-curated alias is not.** Name-search the declaration,
  then PERSON-MATCH the declaring member against the candidate's
  directors/officers/shareholders and anchor only on a UNIQUE confirmation —
  uniqueness-or-nothing, no fuzzy or fame tiebreak
  ([[prominence-never-scores]]). The person-match is safe here only because the
  member DECLARED the interest, so it confirms WHICH company, not the identity.
  Cache negatives. Curated aliases stay for true statutory shorthand ("Te Ohu
  Kai Moana").
  *Paid for by:* 2026-08-28 — "Castlerigg Limited" vs the register's CASTLERIGG
  HOLDINGS LIMITED, with 1,744 unanchored MP-org pairs making a per-miss alias
  unscalable and burying a register fact in a hand list (ops/settle_mp_orgs.py
  → registers.mp_org_resolutions, consulted by routes._mp_interest_roles;
  Arthur: "isn't that what the v5 API is for?").

- **A press-derived register must exclude register-asserted claims, or it
  launders official facts into "press says"** and the discrepancy register ends
  up comparing the register against itself. The same boundary in ruled form is
  the DUAL-EMISSION rule (Arthur, 2026-08-19 ruling 2): NO claims emission
  where A1 already serves the edges live; FULL dual emission only for genuinely
  NEW sources (C5 donations was the first). → registers/SPEC.md.

- **Māori-debris: block single-token structurally, lexicon the rest.**
  Measured on the 17,484-verdict truth set: R1 (single lowercase macron word)
  fires 496 @ 98% precise and is hard-blockable, while R2 (lowercase-led +
  macron token) kills 121 real names and R3 (lowercase-led + signal particle)
  kills 66. For multi-token, use a per-form lexicon blocklist seeded from LLM
  ≥0.9 debris verdicts — zero structural false-kill risk.
  (ERA_RULES_EVIDENCE §2.)

- **When the string cannot decide, the DOCUMENT usually can — go back to it.**
  C241 abstained on 2,639 glued names because `Laing Properties)Dokyun` gives
  no evidence for which side is the entity. The document gives the answer, and
  it is neither side: *"1st place: Dokyun Kim (Laing Properties)Dokyun
  delivered..."*. Re-reading 2,359 of those abstains against their own sources
  acted on 24.3% and recovered names the string never contained. The general
  lesson is that an abstention on a STRING is not an abstention on the
  EVIDENCE: before recording one, ask whether the source is still reachable.
  (`healer/reread.py`, `reconciliation/defects.py`, 2026-09-21.)

- **Most of a defect class is usually a different defect class.** The same
  re-read found that 62.6% of C241's "glued names" were never glued names:
  they were footnote markers flattened out of a PDF text layer and OCR garble
  from Papers Past. A taxonomy written from the string shape alone put four
  different problems in one bucket, and only reading the sources separated
  them. (2026-09-21.)

- **A lane that does not record its abstentions never finishes.** 73% of the
  re-read candidates abstain. Without `v3.reread_log` excluding what has been
  read, each cycle re-selects the same rows and the lane never reaches the
  rest of the backlog — the same shape as the 2026-08-14 drain loop that read
  its own recurrence as progress. (2026-09-21.)

- **`<> 'one value'` is not `= 'the other value'` — enumerate the column
  before you filter on its complement.** Diverting unreadable donor lines out
  of the electorate ranking, I scoped it `line_kind <> 'name'` and the query
  returned **424 races and $1,034,587** of perfectly readable donors (Mahuta,
  Seymour) because a fourth value exists: `self_funded`, **993 rows, $2.2m** of
  candidates' own money, which ruling 193 lists APART and which that filter
  swept into "unreadable". Scoped `= 'unreadable'` it is 25 rows and
  $143,316.91. Had it shipped, every electorate page would have lost $2.2m and
  nothing would have looked broken. `SELECT line_kind, count(*), sum(amount)
  GROUP BY 1` is one query and it is the whole defence. (2026-10-05, C507;
  the values are `name` 2,428, `self_funded` 993, `unreadable` 33, with
  `example` dropped at load per ruling 190.)

- **The EC form's own sample address is the tell for an example line left in a
  return.** `MAIN STREET, SUBURB` appearing inside the donor NAME field is the
  blank form's specimen, not a donor — one more `unreadable` line (+$5,000)
  that had been ranked as a person. Ruling 190 drops a line reading `EXAMPLE`
  at load; this is the same artefact wearing the address instead of the word,
  and it needed its own recogniser (`_EXAMPLE_ADDR_IN_NAME`) because the name
  field is the last place anyone looks for an address. A bare `EXAMPLE` beside
  a REAL amount stays `unreadable` rather than `example`, because that amount
  sums into Helen White's declared total — the line is counted, never ranked
  (ruling 191). (2026-10-05, C427.)

- **A column whose value is the same in every row is not information — it is
  something the reader has to rule out.** The donor-history table carried a
  `band` column reading `no match` in every row Arthur looked at, and a
  `line_kind` chip beside it; both were internal state wearing the costume of
  a finding, and the first question he asked about the page was what they
  meant. Ship a column when its variation means something to a reader, or
  keep it in the payload and off the page. (2026-10-05, C508/C510.)

- **A BETTER KEYWORD LIST IS STILL A KEYWORD LIST — when a word cannot decide,
  the SHAPE around it has to.** `donor_kind` called a name corporate on any
  suffix word anywhere, so `Richard Chambers` read as a company. The obvious
  escape was to grade the WORDS: split the triggers into STRONG (never a
  person's surname) and WEAK, and let a weak one alone mean "person". The split
  is real and was measured non-circularly — 1,185,771 register-asserted
  Companies Office director surnames, deliberately NOT the graph's own
  `type='person'` set, because an organisation mistyped as a person is the
  defect under repair and that population would teach the measurement its own
  error. It still failed, **twice, and the second failure is the instructive
  one**: the plain split flipped 116 of 1,043 corporate donors to person; adding
  a given-name test cut that to 3, and all three were still wrong —
  `Te Ehutu Trust`, `Tim Scott Trust`, `Augustine Trust` — because
  `<Given> <Surname> Trust` is the ordinary NZ family-trust name and its shape
  IS a person's. **The rule that fell out: a word earns a place in the "also a
  surname" set only if `<given name> <word>` is more often a PERSON than an
  organisation — which is a different question from whether the word is ever a
  surname, and it is the question that matters.** `trust` is a surname 11 times
  in 1.19 M and an organisation head-noun nearly every time it appears in a
  donor row. Final: 0 flips on the live register, 164 of 1,097 graph persons
  repaired. (2026-10-06, C118 / ruling 360.)

- **A VOCABULARY THRESHOLD IS A DECISION ABOUT WHOSE NAMES COUNT.** The
  given-name vocabulary for `donor_kind` is "appears at least N times among
  1.19 M Companies Office directors". At **N = 25** it holds 3,142 names and
  **excludes `hine` (18) and `whetu` (20)** — two of the fifteen Māori given
  names probed, so roughly one in seven. The classifier would then have gone on
  calling `Hine Chambers` a company, which is the original defect surviving
  precisely where this estate has paid most to get names right. At **N = 10** it
  holds 6,826, both are in, `ruahine` (1 occurrence) is still out, and no
  trigger word is a common first name — so the looser threshold costs nothing
  it was protecting against. **Probe a frequency cut against the names most
  likely to be rare before choosing it**, because the cut always looks fine
  against the names you already thought of. (2026-10-06, C118.)

- **A GATE KEYED ON THE SOURCE TAG EXEMPTS EVERY OTHER SOURCE WITH THE SAME
  PROPERTY.** The era-5 acronym context gate (rulings 139/140) is right and does
  what it says: an acronym→org pairing is a candidate, so the letters anchor only
  where the document corroborates the reading. It fires on gazetteer entries whose
  register tag ends `_acronym` — and those come solely from the curated
  `gazetteer_acronyms` lexicon. A registered **trading name** arrives tagged
  `companies_trading`, so a bare acronym filed as a trading style walked straight
  past the gate built for bare acronyms. **"NZTA" is a registered trading name of
  NZ TALENT ALLIANCE LIMITED**, and 488 of the 18,486 single-token trading-name
  forms in the automaton are the initials of their own registered owner — among
  them `N.Z.S.A.` of NEW ZEALAND SPACE AGENCY LIMITED and `SINZ` of SPORTS
  INTEGRITY NEW ZEALAND LIMITED. Ask of every gate: is it keyed on where the row
  CAME FROM, or on the property it is actually about? The first is a whitelist
  wearing a gate's name.
  **And the cheap proxy for the property is usually the wrong one, which only a
  measurement shows:** "single-token and all-caps" refuses 1,500 trading names of
  which TESLA, JUCY, OMNIA, BLOOMZ, REEFS and EBUILD are ordinary brands. What
  makes a form dangerous is that it is DERIVED by initials — the same construction
  by which NZTA abbreviates the NZ Transport Agency — so the letters are ambiguous
  between abbreviation targets. A brand is derived from nothing and is not
  ambiguous. (2026-10-07, C242.)

- **A LENGTH CAP IS NOT A COST CAP: WHAT COSTS IS WORK PER CHARACTER, AND REPETITION IS
  WHERE IT HIDES.** C005 was raised on one document that took **40 minutes at 190k
  chars**, and `_MAX_DOC_CHARS = 1_500_000` was already in place with a `doc-truncated`
  drop-note. The cap could never have fired: 190k is an eighth of it. Repetitive text
  makes the gazetteer automaton and the NER repeat the same work thousands of times, so
  the expensive document is not the long one — it is the one that says the same thing
  over and over, and it can be short.
  **Measure the ratio before choosing it.** Distinct non-blank lines over total, across
  4,000 live documents above 40k chars: p50 0.926, p25 0.822, p5 0.513, p1 0.275, floor
  **0.021** — a 357,898-char scanned PDF whose commonest lines are `'VICT'` x8,117,
  `'FALSE'` x7,616, `'KELB'` x5,908. OCR debris. A floor of 0.25 catches 29 of 3,420 and
  sits below the first percentile of real documents, which is the test a cut has to pass
  (#5c860e's shape, one layer out: prove the threshold against what it would kill).
  **Two causes need two guards, and the cheap one goes first.** Repetition is detectable
  in one pass; everything else slow is caught by a clock checked BETWEEN windows — never
  mid-window, because a half-read window puts claims at offsets nothing else agrees
  with, and never before the first, because a document that emits nothing is worse than
  the 40 minutes it replaces. Both drop-note and keep what was read: the note is what
  makes the loss countable, and the alternative — discarding the document — turns a
  measurable cut into a silence.
  *Paid for by:* 2026-10-07 (C005), carded at the Muster-2 homing and confirmed STANDS
  by the 2026-09-19 triage.

- **READ THE DECLARED TEXT ONLY WHERE A COMPANY COULD NOT BE THE THING IT NAMES.** C266
  asked for the obvious fix — derive an MP's role title from the interest text instead of
  from the register's coarse category, since *"Media Works Limited – celebrity dancer"*
  was being served as "Employee". Measured first: of 99 employment declarations, **80
  describe the ORGANISATION'S BUSINESS and not the member's job** — "Agincourt Farms
  Limited – dairy farm business", "Dean and Associates – solicitors", "Auckland Council –
  local government". Reading those as titles invents a job called *local government*. The
  usable rule is narrower and it is a semantic test, not a grammatical one: a company can
  be a broadcaster, a consultancy, a law firm or a management company, so none of those
  words qualifies however much each looks like an occupation (`'Radio Tonga of Aotearoa
  1593 AM – radio broadcaster'` is the station describing itself). A company cannot be a
  dancer, a fellow, a professor, a barrister or a trust officer. Ten declarations moved;
  82 correctly did not.
  **And the scope came from the measurement too:** of the sixteen matches in the whole
  18,340-row register, FOUR were shareholdings in an entity called *"Richard Worth
  Barrister"*. The CATEGORY is the relationship and an occupation inside a company's NAME
  is incidental, so the rule applies to `employment` alone. No test would have found
  that; running the rule over the register did, in one query.
  *Paid for by:* 2026-10-08 (C266), where the card's own proposed fix was the wrong one
  and the measurement said so before anything was built.

- **A FIX THAT SATISFIES A SHAPE TEST BY MOVING AN `if`'s CONDITION CAN LEAVE A WORSE
  DEFECT THAN THE ONE IT CLOSED — AND AN IDENTITY BRANCH KEYED ON A NULLABLE COLUMN IS
  "ALWAYS MINT" IN DISGUISE.** The rule above says an ORDER bug is fixed with a fixpoint,
  not another pattern. This is what the other repair looks like. On 2026-09-19 the guard
  `_junk_for_type` had to be re-asked after `entity_type_overrides` retyped an entity, and
  the test written to hold it in place asserted the guard appeared in `fn.body[:2]` — *"the
  guard must be re-asked in the SAME block that changes the type"*. **ADJACENCY WAS NEVER
  THE INVARIANT; ORDER WAS.** The cheapest way to satisfy an adjacency test is to move the
  guard into the neighbouring block, and the edit that did it changed that block's
  CONDITION rather than adding a statement: `if ent.nzbn:` became `if ov:`. So every
  overridden entity inherited an NZBN-only find-or-mint:

      SELECT id FROM entities WHERE nzbn = %s      -- nzbn IS NULL: matches nothing
      INSERT ... ON CONFLICT (nzbn) DO UPDATE      -- NULL never conflicts

  `col = NULL` matches no row and a unique index does not constrain NULLs, so **both
  halves of a find-or-mint degenerate to "mint" together** and the failure is silent: no
  error, no duplicate-key, just a new row. 46 of the 62,433 override rows match a live
  entity that carries an NZBN, so for the rest the alias lookup twenty lines below was never reached and a
  BRAND-NEW entity was minted per document. Measured 2026-10-09: 15,686 surplus live
  entities over 27,524 (name, type) groups, 192,207 mentions stranded on them, 3,822 of
  them in one week — `Winston Peters` nine times and `New Zealand` fifty-seven. The same
  edit also made the NZBN branch unreachable for a register entity nobody had retyped;
  that half cost one row, which is the warning about blast radius being luck.
  **The query that found it, after two that did not:** mentions-per-row ACTIVELY MISLED
  (80–203 each, so the rows looked well-used) because `claim_entities` tags one entity to
  every claim near it. Rows versus DISTINCT DOCUMENTS settled it in one statement —
  1,404 of 1,502 live `Kiwi` rows carry exactly one document each. **When you suspect
  duplicate minting, count the documents per row, never the mentions.**
  *Paid for by:* 2026-10-09 (C539), and the 2026-09-19 fix it inverted. The gate now
  drives the real function and asks the two questions that survive a refactor: does the
  guard run after the override, and does it run before ANY row is written.

- **A PERSON-NAME TEST APPLIED TO A COMPANY FINDS THE LEGAL FORM WHERE IT EXPECTS A
  GIVEN NAME — AND A NORMALISER THAT REWRITES A CLASS WORD INSTEAD OF REMOVING IT
  HANDS IT OVER AS A DISTINGUISHING TOKEN.** C430(d). `initial_compatible()` turns an
  alias approval into a merge PROPOSAL by reading two names as a surname plus given
  names, matching first initials, and accounting only for the SHORTER side's words.
  `Tower Limited` beside `Tower Corp Holdings Ltd` came back **initial-compatible**:
  `fold_core` normalises `Limited` → `ltd` rather than deleting it, so the legal form
  was the short side's ONLY "given name", it matched the other side's `Ltd`, and
  `Corp Holdings` was never looked at. Two registrations folded into one donor on the
  word that says what KIND of registration each is.
  **MEASURED AGAINST THE REGISTER AND NOT AGAINST MY READING OF THE NAMES.**
  `nzbn_canonical` says the same rule folded `CONTACT ENERGY LIMITED` into
  `CONTACT ENERGY SOLAR LIMITED`, `CONRAD PROPERTIES LIMITED` into
  `CONRAD PROPERTIES HOLDINGS LIMITED` and `SKYCITY AUCKLAND HOLDINGS LIMITED` into
  `SKYCITY AUCKLAND LIMITED` — six separate, currently registered companies, and
  `TOWER %` alone has over a hundred siblings for a bare `Tower` to land on. An
  organisation's identity is a REGISTRATION; a parent and its subsidiary are an
  ENTERPRISE, not an alias (ruling 253). This is #c34847 — *name shape is not
  identity: require an ID, ordered-token equality with a distinctive-token guard* —
  with the guard named: the legal form (`ltd`, `inc`, `corp`, `company`) is the class,
  and `holdings`, `group`, `properties` and `energy` are the register's own
  distinguishing words. Put ANY of the latter in the class pattern and the fold
  returns, silently.
  **ELEVEN OF THE TWELVE WERE ALREADY REFUSED — BY THE WRONG TEST, IN A PERSON'S
  VOCABULARY** (`Sky City Entertainment Group` vs `Sky City Auckland Holdings`:
  "given names disagree"). A refusal that comes from a test asking a different
  question survives only as long as the name shapes do, which is the same hazard as
  #837fff: right answer, no gate. So the arm that decides an organisation pair now
  runs FIRST and says why in the register's terms.
  *Paid for by:* 2026-10-09 (C430d). One live proposal withdrawn of 24; it had not
  reached the graph, because the pair's entities are not named there — so there was
  nothing to reverse, and that is luck, not design.

- **A NAME-KEYED JUDGMENT MUST NOT RETYPE A REGISTER-ASSERTED IDENTITY — AND
  THE MINT PATH THAT TRUSTS THE REGISTER SITS ABOVE THE POLICY THAT WOULD HAVE
  REFUSED IT.** `entity_type_overrides` is keyed on a NORM FORM: it is a
  statement about an ambiguous string. An NZBN is a statement about an
  IDENTITY. `_entity_id_deterministic` applied the override first and then took
  the NZBN find-or-mint, which is deliberately ABOVE "a single-token person
  never mints" ("the NZBN is the identity: proof enough") — so the string's
  judgment walked an identity straight past the policy. Measured and reproduced
  on the live graph 2026-10-12, rolled back: the surface **"Mura"** in a 2014
  wine article is anchored by the gazetteer to NZBN 9429051168872
  (`companies_trading`); `entity_type_overrides` says `mura` → person
  (`crawler:acronym-type-sanity 1.00`); the mint wrote a single-token **person**
  carrying a company's number.
  **Then the next lane erased the evidence of how it happened.** The anchor lane
  strips a wrong register anchor (`remediate.unanchor_entity`: `nzbn=NULL,
  register_source=NULL` plus a `gazetteer_blocklist` row), so within the day the
  row is a bare one-word person with nothing on it to say where it came from —
  which is exactly how T7.70 reported it, and why five days of 1–2 rows a day
  (Eana, Erica, Jiani, Loder, Mura) read as "the policy refusal is being
  bypassed" with no visible route. **Zero of the 1.8 M nzbn-carrying live rows
  are persons**, because that lane always wins the race; the only trace left was
  the blocklist row, written 2026-08-24, naming this very pair a mislink and
  INERT ever since because the gazetteer has not been rebuilt (T7.64, §AO).
  The fix is one definition, not three: `_effective_type` returns the type an
  entity will actually carry, a register assertion outranks the override, and
  `_lock_key`, `_entity_id` and `_entity_id_deterministic` all read it — because
  a disagreement between them inverts the advisory-lock order, which is the
  deadlock class the cast sort exists to prevent (933 deadlocks, 2026-07-26).
  *Paid for by:* 2026-10-12 (C539 part 2, T7.70). Three tells: **ask what is
  KEYED ON WHAT before letting one table correct another**; a guard placed
  above a refusal for a good reason is a hole for every input that can reach it
  by a bad one; and **when a defect's provenance is missing, look for the lane
  that cleans up after it** — the correction is the thing hiding the cause.
