# Use-case realisation programme

> Arthur 2026-08-15: "realise these use cases — first identify shared
> infra and data, build/acquire that first, then work one by one
> through them, establishing minimal functionalities and performance
> requirements to build toward." Assumptions live in
> docs/USE_CASE_ASSUMPTIONS.md (the Assumptions tab).
> Last reconciled against code: 2026-08-16.

## Shared-dependency matrix

What each of the ten cases actually leans on, counted across cases:

| shared capability | cases needing it | status |
|---|---|---|
| Company relationship web (directors, shareholders, shared addresses, trading names as EDGES) | 9 of 10 | **A1 SHIPPED 2026-08-15**: `/api/entity/{id}/register` + dossier Register panel — directors (+name-candidate elsewhere counts), ownership %, trading names, registered office + shared-office expansion, graph cross-links; p95 18ms anchored / 9ms unanchored (P-1 ✓). Anchoring GZ-5-honest (nzbn / name-unique / abstain). 2-hop web UI (F-3 full) still open |
| Person occurrence + corroboration view | 8 | **A2 core SHIPPED 2026-08-15**: `/api/person-view` (occurrences, tier pairs, corroborated-with-seed set, prohibitions, role-linked company health) + Banking flow surface; GraphPage namesakes UX extension still open |
| Dated event timeline (gazette/register/claims merged) | 10 | **A3 SHIPPED 2026-08-15**: `/api/entity/{id}/timeline` — register facts (registration/removal, director changes, office moves, trading names, GST), gazette events cited to the notice, news event claims (STATEMENT class counted-excluded by default, `?statements=true` to include); every row cited (P-5), as-at declared (A-7), caps declared; ≤15ms sampled. Surfaced: dossier Timeline panel + Legal flow step 2b |
| Flags engine (deterministic, cited, versioned rules) | 10 | **SHIPPED 2026-08-15/16**: data-layer/flags package — rulepack person-0.2 (7 rules), fired/clear/blocked contract structurally enforced (uncited fired flag or unscoped green = construction error); `/api/person-flags` + `/api/report/{case}` (REQ-X5 one case-parameterised builder); recruitment staged flow LIVE, MC-R1 PASS ≤80ms, MC-R2 PASS; entity scope SHIPPED 2026-08-16 (rulepack entity-0.1, agriculture) |
| News graph + semantic recall | 8 | keyword live; semantic embed BACKFILL RUNNING (embed-articles unit, relaunched 2026-08-20 after a 17h silent death — watcher card 28w); remaining build = hnswlib index + endpoint + toggle (plan item 25) |
| Gazette events (liquidations, prohibitions) | 7 | LIVE |
| Charities + FINANCIAL | 4 | LIVE — era-3/4 graph serves since the 2026-08-18 cutover (the old era-2 caveat is dead; chips no longer needed) |
| GETS awards | 2 | LIVE — 29,874 awards (re-ingested node2 2026-08-16 after the drift incident; AUDIT_2026-08-16 §0) |
| Courts/tribunals | 5 | building (robots ask carded) |
| PPSR | 3 | planned (access constraints) |
| Insolvency register (ITS) | 3 | carded |
| Political donations returns | 2 | **S2a SHIPPED 2026-08-19** (MC-J1 PASS); S2b completion (LLM+sum-gate over PDFs/scans + scored donor matching) = plan Phase 2 |
| LBP / Immigration employer / WorkSafe | 1–2 each | carded / uncarded |

## Expansion round 1 — the registers NZ doesn't have (Arthur ruled
## 2026-08-19: all three; benchmark questions in the always-asked core)

Each case below follows the strategy doctrine: named incumbent means
to beat, MC rows as the measuring stick, and a core benchmark
question whose 2-day sweep trend IS the use-case scorecard (strata
use-case-lobbying / use-case-beneficial-ownership / use-case-psge,
questions 28-30 seeded 2026-08-19). The BUILT serving surface for these
strata — the /api/research/use-cases tabs, labels, journalism grouping,
component status — is documented in research/SPEC.md §Surfaces
(2026-08-30); "use case" also names the ten gui mockups, a separate set
(the naming collision is plan item 28z's to settle).

**UC-LOB "Who's in the room" (the lobbying register).** Movements
between public office and industry roles, dated and cited. Data:
press-derived appointments (563k relationships), gazette public
appointments, the directorship discrepancy register. Incumbent means:
a journalist's memory + LinkedIn. MC rows: MC-LOB1 revolving-door
query (person with both public-role and industry-role rows, dated,
every edge cited) · MC-LOB2 sector movement map · MC-LOB3
press-vs-register discreprancies surfaced as leads, not asserted.

**UC-BO "Who actually owns X" (the beneficial-ownership register).**
Bidirectional ownership graph with honest anchoring state: the root
company's owners fan right, and (2026-08-26, f40c577) clicking any
company card expands it in place BOTH ways — its holders (owners,
upstream) and the companies it holds shares in (holdings, downstream,
the mirror `WHERE holder_nzbn=`) — splicing into the live graph so
the current trace stays open. Data: shareholdings register + anchoring
pass (86.8% anchored; no-match residue = the offshore signal), press
ownership-control claims; Wave 2b (UK PSC, Open Ownership, GLEIF)
deepens later. Incumbent means: OpenCorporates/Sayari subscriptions,
or hours in the Companies Office UI. MC rows: MC-BO1 chain both ways
(owners upstream, holdings downstream) with per-link basis chips,
expand-in-place per card · MC-BO2 offshore/unresolvable holders
flagged as such · MC-BO3 nominee/trust opacity stated plainly
(abstain surfaced, never papered over). Endpoints:
`/api/use-case/bo/chain` (root trace, upstream), `/api/use-case/bo/expand`
(per-node one-hop both directions).

**UC-PSGE "The PSGE map" (the post-settlement governance register).**
Trusts, holding companies, charities and subsidiaries of
post-settlement entities, with office holders over time. Data: trust
boards + charities (officers, financials) + companies + press
coverage joins. Incumbent means: nothing coherent exists. MC rows:
MC-PSGE1 cross-register entity web rollup for a named PSGE ·
MC-PSGE2 officer overlap across the web · MC-PSGE3 the
register-NZ-doesn't-have story documented per entity served.

## Structural-gap product story (Arthur 2026-08-18)

From the registers survey (registers-survey-2026-08-18.md): New
Zealand has **no lobbying register** (OECD-confirmed, MoJ work
stalled), **no beneficial-ownership register** (policy approved,
no bill located), and **no public register of post-settlement
governance entities**. All three are gaps our DERIVED registers
partially fill — the press-derived appointments/relationship web
approximates lobbying visibility, press ownership-control claims +
international BO sources (UK PSC, Open Ownership, GLEIF) illuminate
beneficial ownership, and deeds + charities + companies joins can
constitute a PSGE register. "The register NZ doesn't have" is a
product story and a use-case seed in its own right — candidate
use cases for the expansion round should be drawn from these three
before anything else, and each derived register that fills a
structural gap should say so in its documentation.



- **F-1 Entity 360**: one call returns registers + graph + news for an
  entity — register facts (roles, addresses, status), claims, mentions,
  FINANCIAL, gazette events. (Exists ~85% since A1 shipped 2026-08-15:
  register role/address/trading-name edges now serve; gazette events in
  the dossier timeline await A3.)
- **F-2 Person view**: for a person name/occurrence — all candidate
  occurrences, corroboration tier per pair, combined view of the
  corroborated set only. (A-1/A-11.)
- **F-3 Web expansion**: from any entity, 1–2 hops over register edges
  (shared director, shared address, shared practitioner) + graph edges.
- **F-4 Timeline**: merged, dated, per-entity event stream, every row
  cited (gazette event, register change, claim with evidence).
- **F-5 Flags engine**: versioned deterministic rules over F-1..F-4
  output (e.g. "≥2 liquidations among corroborated occurrences within
  10y → red"). Rules are code, cited, A-8/A-9 compliant.
- **F-6 Search**: keyword (live) + semantic article recall (embed
  queued behind drains) + honorific-blind (live).
- **F-7 Report render**: case-shaped output (the use-case card layout:
  answer, flags, timeline, web) generated from live data for a REAL
  entity — replacing fictional copy case by case. (First shape SHIPPED
  2026-08-15: the legal counterparty memo — Legal flow step 4 assembles
  register + web + timeline + conflicts into a print-to-PDF document,
  every row cited, caps and sources-not-held declared.)

## Performance requirements (p95, measured before each case ships)

- **P-1** Entity 360 (F-1) ≤ 2s.
- **P-2** Keyword search ≤ 200ms; semantic ≤ 500ms end-to-end.
- **P-3** Person view (F-2) ≤ 5s for names with ≤ 50 register
  namesakes; must degrade honestly (partial + "still checking") above.
- **P-4** Freshness: registers ≤ 7d, news ≤ 24h, gazette ≤ 1d; UI
  shows as-at dates (A-7).
- **P-5** Citation coverage: 100% of flags and timeline rows carry a
  source reference (A-8).
- **P-6** Web expansion (F-3) 2 hops ≤ 5s.

## Phases

**Phase A — shared build (order):**
1. **A1 Register edges in the dossier** (F-1/F-3 core): serve
   director/shareholder/officer/address/trading-name relations from
   canonical registers per entity. Touches: query service, DossierView.
   **SHIPPED 2026-08-15** (see matrix row). Charity-officer edges
   deferred (no confirmed charity↔nzbn mapping); serving indexes in
   ops/register_indexes.sql (re-apply after bulk reloads). First catch:
   the NZTA acronym trading-name mislink (carded in todo.md) — the
   panel makes bad anchors visible on sight.
2. **A2 Person view** (F-2): occurrence aggregation + corroborate tiers
   surfaced. Touches: query service, GraphPage namesakes UX (extends
   the display-only merge).
3. **A3 Timeline** (F-4): merged event stream endpoint. **SHIPPED
   2026-08-15** (see matrix row; built under the legal build-out).
4. **A4 Flags engine v0** (F-5): **SHIPPED 2026-08-15/16** (see matrix
   row — person-0.2: liquidation-history, prohibition [green
   evidence-gated on GZ-5 coverage], young-entity, namesake-exposure,
   charity-officer-roles, charity-integrity-marks, comcom-coverage).
   Phoenix signature awaits its derive (construction tranche).
5. **A5 Semantic endpoint + toggle** (F-6): backfill running
   (2026-08-20); remaining = index + endpoint + toggle (plan 25).
6. **A6 Donations ingest**: S2a SHIPPED 2026-08-19 (MC-J1 PASS);
   S2b completion is plan Phase 2.

**Phase B — case by case** (each: wire F-set to real entities, measure
P-set, rewrite card copy to honest reality, demo):
legal → healthcare → property → agriculture → recruitment →
banking + construction (reframed per A-11) → government →
insurance (media-tier per A-12) → journalism (LIVE 2026-08-16/17 via the research service; MC-J1 donations PASS 2026-08-19).

Sources still missing (courts, PPSR, insolvency, LBP, WorkSafe) attach
to their cases as they land — no case waits on a source it can honestly
ship without.

## Minimal capability checklist (the measuring stick)

Doctrinal (A-13): these are the platform's PERFORMANCE MEASURE. A case
ships when every MC row passes inside its P-bound with 100% citation
coverage; the platform scorecard is the pass-rate over all MC rows,
re-measured after every era change. Each row is a yes/no capability, not
an aspiration.

| case | minimal capabilities (each measured, each cited) |
|---|---|
| legal | **MEASURED 2026-08-15** (endpoints + staged Legal flow live — fictional card copy deleted): MC-L1 web 2 hops `/api/entity/{id}/web` — **PASS, p95 23ms** vs P-6 5s; edges carry basis (corporate-shareholder = NZBN-proved, shared-office, director-name = candidate with register-wide namesake count, director-corroborated = ≥1 non-passing article names the person with both companies, cited + linked) · MC-L2 shared-registered-office — **PASS** (web + A1 panel) · MC-L3 gazette insolvency per web member — **PASS** (claims from the gazette feed, cited via each member's dossier) · MC-L4 conflict overlap `/api/entity/{id}/conflicts` — **PASS, 33ms** for a 4-client list; clients resolve GZ-5-honestly (nzbn / candidates:n) · MC-L5 courts — **PASS**: "source not held" stated in every response (A-10) |
| banking | **MEASURED 2026-08-15** (`/api/person-view` + staged Banking flow live): MC-B1 occurrences + corroborated-with-seed subset (media-shared-article / register-shared-org tiers) — **PASS, max 300ms** vs P-3 5s; >50 namesakes degrades to declared-partial · MC-B2 insolvency events on role-linked companies, corroborated vs candidate sections visibly separate — **PASS** (register-asserted roles only; news ROLE claims deliberately excluded) · MC-B3 prohibitions with GZ-5 basis chips, uncorroborated name-matches labelled — **PASS** · MC-B4 GST age per nzbn-linked company — **PASS** (fills where the company holds an NZBN) |
| insurance | MC-I1 company → dated media claims timeline (reported tier labelled, A-12) · MC-I2 gazette events · MC-I3 semantic incident recall ≤500ms (P-2) |
| journalism | MC-J1 donations by donor/party — **PASS 2026-08-19** (S2a ingest + donations_register research tool + citation kind "donation" party:<id>/candidate:<id>; verification job 39: National's donor history 1996–2006 per-donor with resolving citations + honest coverage statement, 57s; later years join as staged) · MC-J2 public appointments (gazette) · MC-J3 person/org merged timeline, every row citable to a publishable source · MC-J4 semantic thematic recall |
| construction | MC-C1 phoenix signature: trading-name re-registration ≤90d after insolvency event, deterministic · MC-C2 subcontractor officer web · MC-C3 liquidation history among corroborated occurrences |
| recruitment | **MEASURED 2026-08-15** (first case through the flags engine: `/api/person-flags` + `/api/report/recruitment` + staged Recruitment flow live): MC-R1 person name → full public-record screen — **PASS, ≤80ms** for the whole one-fetch screen (rulepack person-0.2: liquidation-history, prohibition [green evidence-gated on GZ-5 coverage], young-entity, namesake-exposure, charity-officer-roles, charity-integrity-marks, comcom-coverage) + print-to-PDF report (REQ-X5 contract, 37ms) — the ≤5 min bound is met by construction: one screen, no tab-hopping · MC-R2 uncorroborated namesakes VISIBLY separate — **PASS**: corroborated-set vs name-candidates is a layout property in flow AND report; every candidate-tier flag says so in its scope |
| government | MC-G1 supplier list → GETS award history · MC-G2 shared identities/addresses AMONG suppliers · MC-G3 staff-conflict vs supplied staff list · MC-G4 donor overlap (S2a data live; full coverage lands with S2b, plan Phase 2) |
| healthcare | MC-H1 operator → full entity web with roll-up · MC-H2 FINANCIAL claims per entity · MC-H3 officer overlap across the web · MC-H4 adverse-coverage recall (semantic) |
| agriculture | **SHIPPED 2026-08-16** — MC-A1 PASS · MC-A2 PASS (p50 58ms / max 349ms vs 2s over six real subjects). First ENTITY-scope case: rulepack entity-0.1, `/api/entity/{id}/flags`, AgricultureFlow, report entity dispatch |
| property | MC-P1 SPV → incorporation web + principals' corroborated occurrence history · MC-P2 prior-project adverse coverage recall |
