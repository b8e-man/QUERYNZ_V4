# Extraction defect taxonomy

Every named defect class in the estate, what it looks like, where the rule
lives, and what the rule does about it. Arthur 2026-09-21: *"I need a list of
defects."*

The organising axis is **what happened to the name** — prose joined to it, the
name cut short, two names run together, or a thing that was never a name. That
is the axis the heals actually work on.

Counts are dated because they are measurements, not facts: a card register is
a record of what was found, not of what is true now.

**Disposition** is one of: `fold` (merge into the live twin), `rename`
(audited, old surface kept), `quarantine` (reversible, never deleted),
`retype`, `detach` (the edge goes, claim and evidence stay), `abstain` (leave
the row alone), `queue` (to the LLM judge).

---

## A · Prose glued to a name — run-on blends

| # | class | example | home | disposition |
|---|---|---|---|---|
| A1 | **glued-punctuation** — prose joined across punctuation the tokenizer kept | `expenses).Ōpōtiki`, `claims.16 Te Ururoa` | `lexicons.glued_punctuation`, `crawler.heal_glued_punctuation` | fold / rename; abstain where two names meet |
| A2 | **parenthetical-glue** — the surface begins INSIDE a parenthetical | `Laing Properties)Dokyun` → `Dokyun Kim` | `defects._read_glue` (re-read lane) | rename from the document |
| A3 | **footnote-marker** — a note number flattened out of a PDF text layer | `corruption.16`, `Community Mental Health Survey.353` | `defects._read_footnote` | quarantine (prose) / rename (name) |
| A4 | **caption-credit** — a photo credit is not part of a name | `Bill English Photo: Supplied` | `crawler.heal_caption_credit` (R-G8) | fold / rename |
| A5 | **byline glue** | `Analysis - Nicola Willis`, `Nicola Willis Photo` | `guards.strip_byline` (C8b) | strip at mint |
| A6 | **role-title prefix** — a person wearing their job | `Prime Minister Chris Hipkins` | `crawler.heal_role_title_prefix` (R-G12) | fold into a namesake-unique person only |
| A7 | **article-led** | `a Winston Churchill` | `crawler.heal_article_led` (R-G3) | fold / rename; persons skipped |
| A8 | **definite-article doubles** | `The High Court` vs `High Court` | `crawler.heal_definite_article` (R-G7) | fold |
| A9 | **lead junk** — bullets, attribution dashes, orphan quotes | `• Accenture`, `— Phil Goff` | `crawler.heal_lead_junk` (R-G9) | fold / rename |
| A10 | **comma composites** — an enumeration minted as one entity | every segment already a live entity | `crawler.heal_comma_composites` (R-G13) | quarantine |
| A11 | **url fragments** | a name containing `http://` or `www.` | `crawler.heal_url_fragments` (R-G11) | quarantine; bare domains spared |
| A12 | **email address** minted as an entity | `Suze.RedmayneMP@parliament.govt.nz` → `Suze Redmayne` | `defects._read_email` | rename where the document names the owner, else quarantine |

## B · A name cut short — fragments

| # | class | example | home | disposition |
|---|---|---|---|---|
| B1 | **trailing function word** — cut mid-phrase | `Institute for Governance and` | `crawler.heal_trailing_function_word` (R-G10) | strip to last content word |
| B2 | **truncated name** — a real name cut, completable from its own articles | `Greater Wellington Te`, `Te Rūnanga o` | `healer/repair.py` | complete from ≥2 independent articles, else stay flagged |
| B3 | **name fragment** — the punctuation of a name with the name missing | glue tokens only | `lexicons.is_name_fragment` | refuse at mint |
| B4 | **party-name boundary cut** — NER cuts the party, the claim binds the country | `New Zealand First` → `place:New Zealand` | `era4.party_boundary_at`, `crawler.heal_party_boundary` (C247) | detach the object |

## C · Two things run together

| # | class | example | home | disposition |
|---|---|---|---|---|
| C1 | **conjunction mint** | `A B and C D` as one person | `crawler.find_conjunctions` | queue to the judge; split on a two-people verdict |
| C2 | **trailing repeat** | `Jacinda Ardern Ardern` | `crawler.heal_trailing_repeat` | fold |
| C3 | **party-adjective metonymy** — a union officer read as a party officer | `National secretary` → secretary of the National Party | `era4.national_secretary_metonymy` (C325) | refuse the edge, keep the claim |

## D · Never a name at all

| # | class | example | home | disposition |
|---|---|---|---|---|
| D1 | **OCR-impossible glyph** | a name carrying `\|^~_<>\` | `lexicons.is_ocr_debris`, `crawler.heal_ocr_debris` (C235) | strip and fold, else quarantine |
| D2 | **OCR garble** — no token a printer could have set | `loag)Jfo`, `ASfJf)6iATiON` | `defects._read_garble` | quarantine, once the document is re-read |
| D3 | **anonymised honorific + initial** — a suppression placeholder | `Miss M.`, `Hon J.` | `lexicons.is_null_like`, `crawler.heal_anonymised_honorifics` (C252) | quarantine |
| D4 | **bare role** — an office with no holder | every significant token is role vocabulary | `lexicons.is_bare_role` | refuse at mint |
| D5 | **role-string entity** | `National MP`, `Labour MP` | `crawler.heal_role_string_entities` | retype to `position` |
| D6 | **negation prefix** | `non-X` | `crawler.heal_negation_prefix` (R-G4) | quarantine |
| D7 | **`<Party> Government`** — a party's government is not the party | `National Government` | era-4 mint screen (C251) | refuse at mint |
| D8 | **exec-role-place** — an executive title bound to a place | "chief executive of Auckland" | `crawler.heal_exec_role_places` | detach the object |
| D9 | **orphan entity** — article-minted, zero references anywhere | — | `crawler.quarantine_orphans` | quarantine |

## E · One thing, two nodes

| # | class | example | home | disposition |
|---|---|---|---|---|
| E1 | **orthography twins** | macron vs non-macron | `crawler.heal_orthography_twins` | fold into the macronned node |
| E2 | **ampersand twins** | `Johnson & Johnson` / `Johnson and Johnson` | `crawler.heal_ampersand_twins` | fold |
| E3 | **post-nominals** | `Anne Norman CNZM` → `Anne Norman` | `crawler.heal_post_nominals` (R-G5) | merge |
| E4 | **the-names bare twins** | `The Warehouse` / `Warehouse` | `crawler.heal_the_names_bare_twins` | fold |
| E5 | **eponym mistype** — an institution wearing a person's name | `Edmund Hillary College` typed person | `crawler.heal_eponym_retype` (R-G6) | retype from the trailing noun |
| E6 | **type multiplicity** | one name carried by entities of 2+ types | `crawler.find_type_multiplicity` | queue (observation tier) |
| E7 | **acronym org** — short all-caps, no register anchor | `OCR` the Official Cash Rate | `crawler.find_acronym_orgs` | queue for type sanity |

---

## What is measured

| class | measured | live at that date |
|---|---|---|
| D1 OCR-impossible glyph | 2026-09-20 | 1,024,328 entities, 250,606 typed person |
| D7 `<Party> Government` | 2026-09-20 | 5,313 mentions |
| A1 glued-punctuation | 2026-09-20 | 3,882 seams; 1,243 recover, 2,639 abstained |
| B4 party-name boundary cut | 2026-09-20 | 190 ROLE claims, 164 leader-class |
| D5 role-string entity | 2026-08-22 | 1,060 / 1,693 mentions |
| D3 anonymised honorific | 2026-09-20 | 102 entities, 8,381 subject claims, 97,103 mentions |
| A2/A3/A12/D2 (re-read) | 2026-09-21 | 24.3% of 2,359 abstained rows acted on |

## The two axes, and the gap between them

Every class above is a **surface** defect: it is visible in the string or in
the claim shape, and every finder reads the GRAPH.

The second taxonomy in the estate is `SOURCE_TIERS`
(`claim_graph/contract.py`, 2026-08-14) — how a fact is known, not what its
name looks like. It has no finders at all, because no document or claim
carries a tier. That is C401.

A defect of PROVENANCE — advertorial minting a ROLE claim — is invisible to
every rule in this file, and would remain invisible however many classes were
added to it.

---

## Re-extraction, not just healing (C402)

Every disposition in this file repairs the NODE and leaves the original
extraction untouched, so the same document re-extracts the same defect on the
next era. The re-read lane (C241b) proved the other direction: go back to the
source, read the seam in its context, and recover the name the string never
contained — `Laing Properties)Dokyun` is `Dokyun Kim`, which is on neither side
of the seam.

**C402** makes that a process: select documents BY defect class, re-extract
only those, measure the class before and after. Arthur 2026-09-21: *"we need a
re-extraction solution and process for targeting and re-extracting these
defects."*
