# healer — SPEC (created 2026-08-22, plan B0)

**Units:** `querynz-crawler`, `querynz-mint-lane`
**Model:** `qwen3.6-35b-a3b-q4km`

<!-- These two lines are HALF of a cycle (ruling 328, C414). The other
half is data-layer/docs/FLEET_CENSUS.md, generated from the unit files
themselves. `python -m ops.fleet.report --check` asserts the two agree and
rides the pre-push doc gate, so neither can move without the other. Add a
unit, or change the model it uses, and this line must change with it. -->

## Purpose
The graph's REWRITE arm. A heal is an evidence-gated rewrite of a claim —
never a delete — convicted only where the claim's own cited sentence refutes
it, and recorded in `v3.claim_heals` with the full before-state so revert is a
replay of the audit table. Unconvicted suspects stand (they are the LLM
re-read residue).

## Why it exists as a package
`heal.py` lived in `registers`, whose SPEC forbids graph writes; the registers
catalog guard was red for as long as it did. B4 moves mint_lane, crawler and
repair into this same home — one service whose writes are all heals.

## Contract (B4, 2026-08-22 — the executing service)
- Lanes: `mint_lane` (post-mint screens → judge → execute), `crawler`
  (deterministic heals R-G3..R-G13 + the B4 first-queue heals
  [trailing-repeat with the Māori trap, role-string → position, Rt Hon
  titles] + finders [acronym-org, type-multiplicity, conjunction] →
  judge [single-shot `reviewer.model.judge`, or the TIER-3 tool-loop
  `research.crawler_judge.re_read` for conjunctions — loopback model
  only, refused in code otherwise; the capped conjunction queue is
  judged before the backlog] → execute [retype / quarantine /
  SPLIT through claim_graph.split]), `repair` (truncated names),
  `anchor_lane` (register-anchor audit), `heal` (claim-tier rewrites
  R1–R6, Shane Jones scope), `resubject` (claim-tier R7/R8 — role-string
  and surname-only subjects re-pointed to the person the evidence names;
  R8 scoped to the named residue, ruling 58). Rules catalogue:
  data-layer/docs/HEALING_SYSTEM.md. CLI: `python -m healer.cli <lane>`;
  units querynz-crawler / querynz-mint-lane run it.
- Every entity/claim mutation goes through a claim_graph GATE
  (remediate / merge / split) — reversible, ledgered with a rule name.
  Raw SQL touches only the lanes' lifecycle tables (mint_review,
  mint_lane_state, anchor_review + their DDL) and, in heal.py only,
  `v3.claim_heals` (INSERT) / `v3.claims` (UPDATE). Nothing here DELETEs
  an entity or a claim. Enforced by `tests/test_boundaries.py`.
- No network of its own: the LLM client is `reviewer.model` (loopback).
  Crossings into reviewer are exactly {model, settings, fragments,
  corroborate, graph_handle}; into research exactly {crawler_judge}.
- Worker threads use a SIBLING connection of the caller's
  (`crawler._worker_connect`), never the store's own connect —
  `tests/test_crawler_worker_isolation.py`.
- The merge drain (`crawler.merge_duplicates`) is back in `run()` since
  B4b (2026-08-22) BEHIND the adversarial refuter: verdict → target
  resolution → junk screen → `research.merge_refuter.refute` → the
  merge gate only on `not-refuted`; refuted parks with status `refuted`,
  abstain parks; every refuter verdict (reasoning, evidence, fetched
  URLs) lands in the lifecycle ledger `merge_refutations`, linked to
  the merge id when one follows. Cap `MERGE_CAP` = 40/run (≈480/day at
  the 2-hour cadence). `tests/test_crawler_no_merge_in_run.py` asserts
  the GATED FORM (drain present, refuter before the gate, cap ≤ 40);
  `tests/test_gate_merge_refuter.py` drives it on the testkit graph. The
  refuter is the second sanctioned research crossing — it is where the
  web tools live; healer still never imports `research.webtools`.
  **The drain runs only while a FULL gate artifact says `passed`**
  (`refuter_measured()`, plan B4b), and it is OFF since 2026-10-07:
  catch 10/13 against the ruling-pending `CATCH_MIN = 0.80`. **That
  threshold is not measurable on this set** (C532, 2026-10-09): the
  catch denominator is 13 `different` cases, so the achievable values
  are 0.692 / 0.769 / **0.846** / 0.923 / 1.0 and 0.80 is not among
  them — the real bar is 11 of 13, one case is 7.7 points, and the 95%
  Wilson intervals at 10/13 [0.497, 0.918] and 11/13 [0.578, 0.957]
  overlap by 0.34, so August's PASS and October's FAIL are the same
  measurement. Six verdicts moved between those runs in BOTH directions
  on an identical judgment fingerprint. ~196 different-cases would be
  needed for ±0.05. Every artifact now records that resolution and the
  refusal string states it, so the work is the labelled set and not the
  rate; `CATCH_MIN` is unchanged and the drain still fails closed.
- R3a (`dense_validation.py`): re-judges a seeded, pattern-stratified
  sample of `mint_review` verdicts with a SECOND model at an explicit
  endpoint (`reviewer.model.judge_at`), using the fleet's own
  `crawler.build_prompt`, and writes `var/audits/r3a-<stamp>.json`
  (agreement, dissent rows with both reasonings). Annotate-only — it
  writes nothing to the graph. Live run is Arthur-fired (the dense 27B
  needs GPU0). CLI `healer dense-validation --url --model --n`.

## Judgment tables are append-only (ruling 157; Muster 2 B2, 2026-09-04)
A judgment is withdrawn, never deleted. `registers/judgments.py` names the
JUDGMENT_TABLES (donor_anchors, mp_org_resolutions, party_board_asserted,
candidates_announced; shareholder_anchors is a regenerated set-based view
and stays out) and a FAIL-FIRST guard reds (a) any DELETE against them in
the code base and (b) any serving read without the `withdrawn_at IS NULL`
filter — both fired on real sites when written (settle_mp_orgs, the
Wikipedia re-parse, six routes) and were fixed. Every DDL home appends the
withdraw ALTERs (`withdrawn_at`, `withdrawn_reason`). The healer's own
ledgers (`claim_heals`, merges, quarantine, splits, renames, type changes,
detachments) were already append-only with a rule name (T7.17); this
extends the same rule to the register judgments the serving layer reads.
The same batch made the register derives CONTENT-KEYED (worksafe,
disclosure: upsert by natural key, ids stable across nights, `retired_at`
instead of delete-and-reinsert) so the nightly gazette feed sees deltas,
not a full replacement — see reconciliation/SPEC.md for the waves' own
direct DELETEs, which are still owed the same treatment.

## Open
Route heal.py's claim rewrites through the remediation gate rather than
writing claims directly (then `v3.claims` leaves the raw-write allowance).
The donor-anchor pass re-points kept judgments at re-derived row ids every
run (`_rebind_ids`, 2026-09-05) — a judgment keyed by content still SERVES
by id; LESSONS §3 rule 4.

## Audit trail

2026-09-17 (queue 8, brief `2026-09-17-judgment-arms.md`; audit 2026-09-14
MED): `heal_role_title_prefix` opened a register connection every cycle and
never closed it, and the post-nominal fold and the anchor lane closed theirs
only on the happy path — one register connection leaked per crawler cycle.
`crawler._close_quietly` on every exit path (`try/finally`), pinned by
`tests/test_register_conn_closed.py` (normal and raising paths). Found on the
way: `test_gate_crawler::test_post_nominal_fold_merges_into_base` reads RED
when `V3_REGISTER_DSN` is absent from the shell (the register tiers abstain
by design, so the fold abstains) — the gate depends on the register being
reachable; run the healer suite with the unit's environment.
