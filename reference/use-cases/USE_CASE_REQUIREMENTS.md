# Use-case requirements — the eight unshipped cases

> Arthur 2026-08-15: "thoroughly research and document the other use
> cases. I want clear resource, performance, completeness, and
> reliability requirements as well as any other minimum requirements."
> Grounded in: full estate inventory + measured capacity snapshot
> (both 2026-08-15). Companion: BACKEND_ARCHITECTURE.md. Status:
> DESIGN — Arthur reviews before build order is set. Statuses
> reconciled in place 2026-08-16: REQ-X1/X4/X5 shipped, REQ-X3 done
> (August import ran), REQ-R1 minimum done, recruitment shipped.

## 0 · Definitions

- **Performance** = p95 latency bounds (the P-set) measured before a
  case ships, plus freshness (P-4).
- **Completeness** = which of the case's claims the estate can
  actually evidence, stated per flag; a case may ship with declared
  gaps (A-10) but never with an unevidenced flag (A-8).
- **Reliability** = degradation behaviour, citation coverage (P-5),
  freshness maintenance, and the ops posture behind them.
- **Resource** = data volume, GPU/LLM budget, storage, and human/legal
  dependencies (subscriptions, permission asks).

Platform baselines (measured 2026-08-15): register p95 18ms · web 23ms
· timeline ≤15ms · person-view ≤300ms · conflicts 33ms. Fleet: 2 boxes
× (16C/62GiB/2×32GB GPU); 4 GPUs >90% busy under drains; 32 LLM slots
(~26–35 t/s each); disk abundant (1.6TB+ free/box); graph ~6.4M
entities / 4.5M claims / 16M mentions per era.

## 1 · Cross-case requirements (apply to all eight)

- **REQ-X1 Flags engine (F-5/A4) — SHIPPED (updated 2026-08-16).**
  data-layer/flags package: pure versioned rules over assembled
  records, statuses fired/clear/blocked enforced structurally (an
  uncited fired flag or unscoped green is a construction error —
  A-8/A-9/A-10). Rulepack person-0.2 (7 rules) serves via
  /api/person-flags; recruitment is the first case through it
  (MC-R1/MC-R2 PASS). Remaining: entity-scope rulepack + signature
  tables for batch rules.
- **REQ-X2 Semantic recall serving (A5)** — 4 MC rows (MC-I3, MC-J4,
  MC-H4, MC-P2) name it; no endpoint exists; embed backlog 64 of
  1.19M articles, bulk job parked behind drains. Requires: finish
  embed (~16h GPU at ~21/s — schedule AFTER drains), hnswlib index
  (~5GB RAM resident, fits), `/api/search/semantic` ≤500ms (P-2), and
  an entity-scoped "adverse coverage" recall variant.
- **REQ-X3 History-preserving bulk imports — DONE 2026-08-16.** The
  aux importer archives vanished rows into `bulk.<table>_history`
  with vanished_at (stage 1.3, 2026-08-01), and the August Companies
  Office package ran today: entities 1,821,452; 9,071 director roles
  ceased (ceased_at set) → 9,071 "was director of" claims fed into
  BOTH graph eras; the 16 bulk history tables now exist and are
  populated (companies_trading_name_history 2,678 vanished rows,
  etc.). Freshness restored to the ≤7d bound; the history clock is
  running. Note for MC-C1: liquidated companies keep their
  trading-name rows until struck off, so a phoenix v0 is derivable
  from the current snapshot + gazette (probe 2026-08-16: the naive
  same-name ≤90d join yields 14.2M pairs — the rule lives or dies on
  name-distinctiveness constraints; construction-tranche design).
- **REQ-X4 Gazette prohibition anchoring — DONE 2026-08-15.** The
  GZ-5 matcher (gazette_register/derive.py) anchored all 286 rows
  (39 name-unique-register with matched_nzbn, 247 name-candidates:N).
  The "no prohibition" green now serves, evidence-gated: the
  person-view assembly carries the coverage stats and the flag rule
  (prohibition 0.2) blocks itself if anchoring ever regresses.
- **REQ-X5 Case-report contract (F-7 generalised) — SHIPPED
  2026-08-15/16.** One case-parameterised builder (query/report.py),
  served as `/api/report/{case}`; same assembly feeds flow and
  report, caps and sources-not-held declared, flag citations carried
  through. Recruitment is the first case in CASES; each new case adds
  a parameterisation, never a bespoke builder.
- **REQ-X6 MC scorecard automation** — A-13 makes MC pass-rate the
  platform measure "re-measured after every era change"; today
  measurement is manual. Requirement: a script that runs every MC row
  and emits the scorecard (extends v3-audit pattern).
- **REQ-X7 Card truthfulness sweep** — stale/optimistic chips found:
  GETS says `planned` (LIVE: 29,874 awards — re-ingested on node2
  2026-08-16 after the drift-repair incident destroyed the 08-14
  node1 ingest; recovered from source CSVs, AUDIT_2026-08-16 §0),
  ComCom says `building` (live — reported tier, scraped releases),
  LINZ/OIO says `building` (OIO absent).
  useCases.ts also has mojibake (double-encoded em dashes) — a real
  GUI bug. Fix with each case conversion.

## 2 · Per-case requirements

Ordering below is by READINESS (found), not the Phase-B order
(healthcare → property → agriculture → recruitment → construction →
government → insurance → journalism), which predates today's findings.

### 2.1 Recruitment — SHIPPED (first case through the flags engine)
Board pre-appointment screen; persona: executive search consultant.
- **Functional minimum**: MC-R1 person name → full public-record
  screen ≤5 min end-to-end including human reading; MC-R2 uncorroborated
  namesakes VISIBLY separate (A-1). Both map onto `/api/person-view`
  (already PASS for banking) + charities + comcom + news.
- **Performance**: person-view ≤5s (measured 300ms); the "5 minutes
  including reading" bound is a PRESENTATION requirement — one screen,
  no tab-hopping: staged flow + report render (REQ-X5).
- **Completeness**: companies/charities/gazette/news/comcom all live.
  Prohibition green now serves, evidence-gated on GZ-5 coverage
  (REQ-X4 done). Gaps to declare: charity-officer→person edges
  58,591 person-NULL (officer roles display by charity, not fused to
  the person — A-1-honest anyway); ComCom is NOT a structured
  register — 1,046 claims from scraped releases, reported-tier, the
  enforcement register declared not-held (the comcom-coverage rule
  says exactly this).
- **Reliability**: register ≤7d (bulk import cadence), gazette ≤1d
  (timers live). Degrade: >50 namesakes → declared partial (exists).
- **Resource**: zero new data; A4 rules + flow UI only. LLM: none.
- **Shipped (2026-08-15/16)**: rulepack person-0.2 (liquidation-
  history, prohibition, young-entity, namesake-exposure, charity-
  officer-roles, charity-integrity-marks, comcom-coverage) +
  /api/person-flags + /api/report/recruitment (REQ-X5) + staged
  Recruitment flow. MC-R1 PASS ≤80ms one-fetch screen; MC-R2 PASS
  (corroborated vs candidates a layout property).

### 2.2 Agriculture — SHIPPED 2026-08-16 (first entity-scope case)
Rural counterparty risk; persona: agribusiness credit manager.
- **Shipped**: rulepack entity-0.1 (group-receivership,
  practitioner-repeat [distinct-entity semantics — the same
  practitioner on one entity's appointment+liquidation pair never
  fires; blocked on partial practitioner coverage, 90,534/322,848
  gazette events named], partnership-dissolved, mpi-coverage
  [media-tier by design]) + /api/entity/{id}/flags assembly
  (NZBN-first across BOTH registers; 103,133/227,984 unincorporated
  rows are name-suppressed so name search reaches only the named
  ~55%; graph trading-name anchors win) + AgricultureFlow staged UI +
  agriculture case in the REQ-X5 builder (entity dispatch,
  ?entity_id=).
- **MC**: MC-A1 PASS (controlling-mind via register slice directors +
  person-view handoff); MC-A2 PASS — measured 2026-08-16 over six
  real subjects: flags+web+timeline summed p50 58ms / max 349ms vs
  the 2s bound.
- **Honest gaps (declared in-product)**: NAIT specifics are media-
  tier coverage, never adjudication; the unincorporated register
  carries no officer data (partnership subjects get an empty group,
  said so); officer web is register name-match tier (A-1).

### 2.3 Government — READY MINUS DONOR HALF
Procurement integrity; persona: agency procurement lead.
- **Functional minimum**: MC-G1 supplier list → GETS award history
  (GETS LIVE: 29,874 notices, NZBN-keyed — endpoint needed);
  MC-G2 shared identity/address AMONG suppliers (pairwise web overlap
  — extend /conflicts to all-pairs mode); MC-G3 staff-conflict vs
  supplied staff list (person-view batch); MC-G4 donor overlap —
  BLOCKED until A6 donations.
- **Performance**: batch shapes need bounds: propose ≤10s p95 for a
  20-supplier panel run (parallel per-supplier assembly), declared
  caps beyond.
- **Completeness**: ship MC-G1..G3 with MC-G4 declared "source not
  held: donations returns (ingest carded)" (A-10). GETS quarterly
  refresh card must be standing before ship (P-4).
- **Resource**: A6 unblocks G4 later; GETS award endpoint + all-pairs
  overlap are query-service work only.
- **Minimum to ship**: REQ-X1 + GETS endpoint + all-pairs overlap +
  batch person screen + flow/report + MC measurement (G4 declared).

### 2.4 Construction — REQ-X3 LANDED 2026-08-16; history accruing
Subcontractor vetting / phoenix detection; persona: procurement lead.
- **Functional minimum**: MC-C1 phoenix signature: trading-name
  re-registration ≤90d after insolvency event, DETERMINISTIC;
  MC-C2 subcontractor officer web (exists); MC-C3 liquidation history
  among corroborated occurrences (person-view + gazette, exists).
- **Completeness**: MC-C1 requires deregistered trading-name history
  — the aux importer now ARCHIVES vanished rows
  (bulk.companies_trading_name_history, 2,678 rows from the August
  import; REQ-X3 done 2026-08-16), so the window builds forward from
  today; the current-snapshot + gazette phoenix v0 (probe in REQ-X3)
  covers the past. ERA claims (employee
  proceedings) — blocked source; declare not-held pending MOJ ask.
  Address-reuse ("same yard") — bulk addresses live, needs the rule.
- **Performance**: phoenix rule is a batch/derive computation —
  precompute signature table nightly (gazette event × trading-name
  window join), serve as flag ≤P-1.
- **Resource**: one derived signature table (X3 done); no new
  acquisition; no LLM.
- **Minimum to ship**: phoenix signature derive (measured against
  known cases) → REQ-X1 rules (phoenix, entity-age, group failure
  debt, address reuse) → flow/report → MC measurement.

### 2.5 Healthcare — NEEDS RE-SCOPE (two headline flags unevidenced)
Care-provider governance; persona: aged-care investor/regulator.
- **Functional minimum**: MC-H1 operator web with roll-up (exists);
  MC-H2 FINANCIAL claims (1,450/705 orgs — ERA-3-ONLY: the serving
  era-2 graph holds zero until the cutover; chips must say so);
  MC-H3 officer
  overlap across web; MC-H4 adverse-coverage recall (REQ-X2).
- **Completeness — REQUIRED RE-SCOPE**: (a) statutory-supervisor
  churn: NO supervisor field exists in bulk.retirement_villages (512
  rows, operator names only) — either source supervisor data
  (registers.retirement-villages full file — recon task) or the flag
  goes; (b) HPDT: blocked (robots + JS), permission ask carded, HDC
  is the green-lane alternative (no robots.txt, decisions + case
  notes, providers sometimes named) — recommend HDC ingest instead;
  (c) charity-officer↔supplier loop needs officer edges: charities
  officer facts exist (58,591) but person-matching unfilled — the
  loop can be shown ORG-side (charity ↔ supplier org overlap via
  officers' shared names, declared candidate-tier).
- **Resource**: HDC ingest (small, docpipe archetype once unfrozen);
  supervisor-data recon; REQ-X2 for MC-H4.
- **Minimum to ship**: re-scoped card (A-8: no unevidenced flags) +
  REQ-X1 rules + officer-overlap surface + MC-H1..H3 (H4 after X2).

### 2.6 Property — MEDIUM (two dead pipelines feed it)
Developer due diligence / SPV history; persona: apartment buyer.
- **Functional minimum**: MC-P1 SPV incorporation web + principals'
  corroborated occurrence history (exists via web + person-view);
  MC-P2 prior-project adverse coverage recall (REQ-X2).
- **Completeness**: SPV-liquidation pattern is companies+gazette,
  live — the SPV-serial rule (same principals, sequential SPVs,
  post-settlement liquidation) is an A4 rule over existing data.
  Council minutes (consent amendments): captured but extraction DEAD
  (imports retired V2 pipeline) — either revive as deterministic
  agenda-item derive (95k-char docs, own card) or declare not-held.
  Courts (stranded remediation claims): T3 litigation edges will
  partially serve; OIO absent (chip wrong).
- **Resource**: council-minutes derive is the big-ticket item (defer;
  declare); REQ-X2 for MC-P2; rest is rules + flow.
- **Minimum to ship**: REQ-X1 rules (SPV-serial, guarantee-scope
  note) + honest card re-scope (council minutes declared) + MC-P1
  measured; MC-P2 after X2.

### 2.7 Insurance — WORST-SERVED (A-12 already concedes media-tier)
Underwriting beyond the proposal; persona: commercial underwriter.
- **Functional minimum**: MC-I1 company → dated media claims timeline
  reported-tier labelled (timeline exists; labelling exists);
  MC-I2 gazette events (live); MC-I3 semantic incident recall ≤500ms
  (REQ-X2).
- **Completeness — REQUIRED RE-SCOPE**: WorkSafe prosecutions:
  record-level data (defendants, fines) PROVABLY absent from the
  official API (aggregates only). The sanctioned path (doctrine 6,
  recover-over-exclude): a gazette-style deterministic derive over
  the WorkSafe release texts we already scrape → prosecution facts
  at "reported/derived" tier with per-release citation, upgraded to
  adjudicated only if courts T3+ lands the underlying prosecutions.
  BIC-change flag: REQ-X3 done 2026-08-16 — the BIC history window
  accrues from that date. Sister-company receivership:
  live (gazette + shared-director web).
- **Resource**: WorkSafe release derive (new parse module, archetype
  C, ~small corpus); REQ-X2 (X3 done).
- **Minimum to ship**: MC-I1+I2 now with A-12 framing; WorkSafe
  derive as the case's build core; MC-I3 after X2.

### 2.8 Journalism — LIVE since 2026-08-16/17 (research service:
cite-or-mark jobs + adversary baseline + gap-miner; it was the
era-3 acceptance instrument). ONLY MC-J1 (donations) remains
blocked on A6. Original heading kept for the record:
### 2.8 Journalism — HARD-BLOCKED AT THE SPINE (until A6)
Follow the money; persona: investigative reporter.
- **Functional minimum**: MC-J1 donations by donor/party (BLOCKED —
  no ingest); MC-J2 public appointments (gazette phase-3 LIVE);
  MC-J3 merged timeline, publishable citations (exists); MC-J4
  semantic thematic recall (REQ-X2).
- **Completeness — the A6 plan (corrected 2026-08-16)**: the
  elections_donations DocSource IS wired (in GROUPS,
  elections-finance, since 2026-07-26) — the blocker is CAPTURE, not
  wiring: 0 donation PDFs held; elections.nz sits behind Incapsula
  (browserfetch clears it) and returns are PDFs → pdfpipe (re-enabled 2026-08-18; was frozen
  until the drain constraint lifts). A6 therefore = browserfetch
  capture + pdfpipe window + a donations derive (amounts, donors,
  parties, years; aggregation by NZBN family) + donations-1.0 gates.
  Ranked #1 source opportunity.
  Hansard/council extraction dead (V2 imports) — declare; gazette
  appointments carry MC-J2 alone.
- **Reliability**: publishability = P-5 strictly + notice ids/return
  years on every edge (the card already promises exactly this).
- **Resource**: A6 ingest (small data, real plumbing); REQ-X2.
- **Minimum to ship**: A6 → donations gates → REQ-X1 donor-overlap
  rules → flow/report; MC-J2/J3 measurable earlier.

## 3 · Readiness ladder (proposed build order, replaces Phase-B order)

1. **Recruitment** — SHIPPED 2026-08-15/16 (validated the flags
   engine end-to-end; MC-R1/R2 PASS)
2. **Agriculture** (nothing new; adds MPI surfacing + partnership slice)
3. **Government** (GETS endpoint + batch shapes; G4 declared)
4. **Construction** (X3 landed 2026-08-16; phoenix derive is high-value IP)
5. **Property** (rules now, council minutes declared, X2 later)
6. **Healthcare** (re-scoped card; HDC swap for HPDT)
7. **Insurance** (WorkSafe derive core; X2)
8. **Journalism** (A6 spine; X2)

REQ-X1 (flags engine) fronted the ladder and is SHIPPED with
recruitment. REQ-X2 (semantic) waits on drain completion by physics
(GPU); the embed job is queued and self-starts when the fleet frees.

## 4 · Reliability requirements (platform, from the capacity snapshot)

- **REQ-R1 Standing register sync / replication — minimum DONE
  2026-08-16.** nzbn_canonical/sync.py: register-wide node2→node1
  sync (public/bulk/charities; table discovery from source, FK topo
  order, column-parity preflight, reference tier syncs on count
  change only, one count-verified target transaction) on the nightly
  gazette-derive chain. Same-day fold (audit T-C): it owns gazette.*
  and courts.* too — gazette_register/sync.py deleted; one sync
  owner, tables discovered. Target stays: single-writer + real
  replica per the twin doctrine.
- **REQ-R2 Off-site factory backup.** None documented; the shopfront
  is a projection, not a backup. Minimum: nightly dump of
  extractions.v3 + nzbn_canonical + incoming_news to an off-box
  target with retention; restore drill documented.
- **REQ-R3 Query-service test depth.** 25 endpoints / 5 tests, and it
  is the entire product read layer. Minimum: response-shape tests per
  MC-serving endpoint + the boundary tests; target: MC scorecard
  (REQ-X6) doubles as its integration suite.
- **REQ-R4 Node1 post-drain hygiene**: claim_entities bloat (9GB over
  twin at fewer rows) → VACUUM after drains; entity_prominence MV
  refresh after heal waves (standing lesson); investigate failed
  units (querynz-crawler, querynz-sync) — timer truthfulness
  (always-red newsscrapers unit) stays a carded fix.
- **REQ-R5 Freshness instrumentation (P-4).** as-at dates now serve
  per-surface; requirement: a freshness row in /api/stats per source
  family (register/news/gazette/courts) with its P-4 bound, red when
  breached — the StatusBar already has the surface for it.

## 5 · Resource requirements (platform)

- **GPU/LLM budget**: drains own the fleet now (~31/32 slots). After:
  embed backlog ~16 GPU-hours; courts T4 outcome extraction (119 docs)
  trivial; OpenLaw 47k-case wave ≈ 100M+ output tokens ≈ multi-day
  fleet occupancy — schedule as campaign units like drains, after
  era-3 cutover. Flags engine, phoenix derive, all register work: CPU
  only, negligible.
- **Storage**: all identified ingests (donations, WorkSafe derive,
  HDC, OpenLaw text) sum well under 20GB; disk holds >1.6TB free per
  box. No constraint.
- **RAM**: hnswlib index ~5GB resident in the query service — fits,
  but note node2 swap pressure (4GB in swap under drains); load the
  index AFTER drains or on node1.
- **Human/legal dependencies (Arthur)**: MOJ ask (sent?), OpenLaw key
  (DONE), PPSR + NZBN API subscription on portal.api.business.govt.nz
  (carded — biggest structural register win: debtor→secured-party
  edges), NZLII research programme, HPDT ask (or HDC swap), NZX ask
  (only if ever needed).
