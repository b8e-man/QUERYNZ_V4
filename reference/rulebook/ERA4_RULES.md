# Era-4 extraction rules — the adopted inventory

Status 2026-08-20: IMPLEMENTED in v3-det-2.0 (V3_EXTRACTOR_ERA4=1;
commits 7adc9cc/a6f396d/81b5134/b86e8d6), VALIDATED, and the
targeted wave is COMPLETE (48,354/48,354, 0 fail; sweep 4 clean —
ERA4_CUTOVER.md is the campaign log). Amendments at
the gates: B2's trailing-repeat arm WITHDRAWN (genuine
reduplication: Te Peeti Te Awe Awe, Ma Htet Htet — crawler-tier
now); A3 object governance NOT implemented (crawler-tier; R5's
Herald species re-mints until it lands); body-of-state blindness
(Cabinet/Caucus/Parliament) added as the R4 twin. Arthur's
per-rule interactive review WAIVED by his ruling ("just do it",
2026-08-20) in favor of the measured gates; validation report:
var/audits/era4-validation-2026-08-20/.

Provenance note: the originally planned rule source — mining the
43k resolver/merge crawl verdicts (Batch B / R2) — was MEASURED
EMPTY at the rule tier (2026-08-19; corpus-zero ≠ world-zero, the
Buffalo Bill lesson). Everything below comes from the productive
label sources that replaced it: use-case triage at the CLAIM tier
(Shane Jones, 2026-08-19/20) and entity-variant triage at the NAME
tier (Jones/Key/Ardern/National, 2026-08-20). Doctrine: each rule
exists TWICE — a mint-guard preventing the error at extraction
time, and a crawler screen finding the retrospective damage. The
screen RANKS candidates; only evidence (or an LLM verdict) ever
convicts; ops stay reversible and audited.

## A. Claim-tier families (from the Shane Jones eval case)

Regression corpus: v3.claim_heals — 584 evidence-gated before/after
pairs. An era-4 extractor re-run over those sentences must emit the
healed form. Sample claim ids per species in issues-ledger.md.

- A1 QUALIFIER PRESERVATION — Associate / deputy / Acting / former /
  then- must survive into the predicate (or a qualifier field).
  "Associate Finance Minister" minted "is minister of Finance" 18×.
- A2 APPOSITIVE-AS-AFFILIATION — "<Party> minister/MP <Name>"
  asserts role + party membership, NEVER office-of-the-party
  ("minister of New Zealand First", 72 claims).
- A3 OBJECT GOVERNANCE — an object binds only if the role phrase
  syntactically governs it; otherwise emit an org-less role mention
  honestly. (Kills "minister of Northland" from a grants story,
  "mp of Herald" from "The Herald reports:", Bathurst from a
  met-with sentence.)
- A4 PARTY-NAME BOUNDARY WHITELIST — party names never truncate at
  interior word boundaries (objects "New Zealand" / "Zealand
  First"). Party list register-driven (EC donations registers).

## B. Name-shape families (from the variant/satellite triage)

Counter-example corpus: the 14,594 distinct-entities-ok verdicts +
the live namesakes (Shane Ardern, Ross Ardern, Raymond John KEY,
Northland Party, National Health Service, Scottish/British National
Party). A merge-shaped rule that touches ANY of them fails,
measured — recover-over-exclude.

- B1 HONORIFIC FOLD — Rt Hon/Hon/Sir/Dame/Matua/Mr/Ms/Dr stripped
  before alias lookup at mint. Screen: honorific-prefixed twins of
  an existing entity. Closed title list; lowest risk.
- B2 DOUBLED-TOKEN GUARD — repeated token sequence in a person name
  is structurally impossible ("Shane Jones Shane Jones", "Jacinda
  Ardern Ardern"). Refuse + re-resolve.
- B3 OUTLET-PREFIX GUARD — leading token matches a known outlet;
  the authoritative outlet list is our own claims.outlet column
  ("RNZ Shane Jones"). Strip + re-resolve.
- B4 CONJOINED-NAMES GUARD — a candidate name containing two
  already-known names is an enumeration failure ("Bradley Ambrose
  John Key", "National and Labour"). Extends comma-split
  (v3-det-1.8) to space/"and" conjunctions. Split-or-refuse;
  retrospective cases queue for SPLIT TOOLING (ledgered gap).
- B5 FUNCTION-WORD GUARD — stopwords/inflections inside a person
  name are span-boundary failures ("no John Key", "John Key-led",
  "John Key later"). Refuse.
- B6 PARTY-SATELLITE GUARD — org name = <registered party> +
  (MP|minister|Cabinet|Caucus|portfolio word) is the appositive
  species, never a real organisation ("Labour MP" 1,768 claims,
  "National Party Finance"). A2's mint-time twin, org side.

## Out of rule reach (LLM-verdict tier only)

- Surname-only entities ("Ardern", org-typed, 683 claims) —
  ambiguous over real namesakes; per-claim evidence direction.
- "National Government"-species concept splits — part real concept,
  part flattened junk; per-claim reads.
- Namesake leakage in cascades (exposure formula blind spot 0) —
  needs the corroboration tier, not a name rule.

## Code audit 2026-08-20 (final pass) — known defects, gate-bound

Adversarial audit after the wave; every finding MEASURED against
live era-4 claims before triage. Fix vehicle: plan item 5b
(era-4.1), through the same corpora gates. None fired in the wave
corpus (A4 slogan-pun class: 0 claims; the one case-mismatch hit
is a source typo and factually correct; B6 real-org specimens: 0).
- A4 party_extension: sentence-wide case-insensitive party search —
  "put New Zealand first" (the party's own slogan pun) can rewrite
  a legitimate place object; needs object-adjacency +
  case-sensitive First.
- A2 "emit both honestly": the follow-on role claim shares the
  dedup key ("ROLE", subj, None, "is", None) with the membership
  claim when the object is text-only (always true post-A4) and is
  silently dropped — recall loss. Tests call structural_patterns()
  directly and never see the dedup.
- B6: two-token collisions with real orgs (National Finance, Mana
  Health, Top Education, Alliance Health) — only 3-token forms are
  trap-covered.
- _HONORIFIC4: matua/whaea not gated to persons (Matua Valley
  Wines org, Matua suburb GPE).
- A1: qualifier "co" fires on "& Co" legal names.
- B4: minted halves bypass stopform/Māori-fragment/bare-role
  guards, share the composite span; no end-to-end test.
- B2 residue: EVEN-length exact reduplication still halves ("Te
  Awe Te Awe" → "Te Awe") — the accepted arm is not zero-risk for
  even-length reduplicated Māori names.
- era4.recover "concept" arm unreachable; NORP-typed satellites
  ("Labour MPs" → people) never offered to B6.
- Adjacent: heal.py R2 convicts on the rhetorical phrase (no
  subject adjacency); era4_validate R2 gate checks
  organisation:new zealand only (place-typed truncations pass
  unseen). Ledgered.

### Era-4.1 disposition (plan B5, 2026-08-22)

Every finding above is amended behind `V3_EXTRACTOR_ERA41` (v3-det-2.1)
with a failing-first specimen test and its flag-off pin in
`extractor/tests/test_era41.py`; the corpus gates run through
`ops/era_validate.py --era 4.1`. Two were found NOT to be what the
audit said once built against the corpus: the A4 adjacency gate must
accept the object ANYWHERE inside the party name (the modifier grab
left-cuts "New" → "Zealand First"; 19 R2 rows), and an "object must
not occur elsewhere" arm regressed R2 and was dropped. "Adjacent"
items (heal.py R2 rhetorical phrase; era4_validate's place-typed
truncations) stay ledgered — not extractor rules.

## Adoption gates (as applied)

1. Measured precision/recall on the named corpora per rule.
2. Zero counter-example violations (distinct-entities-ok set).
3. Arthur reviews every mint-touching rule before era-4 adoption —
   WAIVED by ruling 2026-08-20 ("just do it man"): measured gates
   replaced the interactive review; the validation report is still
   written and any rule stays reversible on his sight of it.
4. Acceptance runs through the harness (benchmark pairs + T7),
   never hand-inspection.
