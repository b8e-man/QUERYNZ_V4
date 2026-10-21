# reconcile-1: ruling 66 in the four political-donation lanes
branch: session/reconcile-1 (pushed; 75fc718)
session: reconcile-1
raised: 2026-10-21
claims: registers/candidate_returns/, registers/party_returns/, registers/disclosures/, registers/party_finance/ (new `reconcile.py` in each; readers, `check.py`, `tables.sql`, `publish.sql`, `load.py`, `sample.list`, `spec.md`, tests; party_finance gains `replay.py`); docs/status/candidate-returns.md, party-returns.md, disclosures.md, party-finance.md; lesson `a-to-the-cent-check-written-in-floats-passes-a-cent`; lessons/INDEX.md regenerated

Ruling 66 (Arthur, 21 October 13:00), for every political-donation
document: where a document's parts do not sum to its printed total, a
difference below $100 is reconciled and the row carries an issue naming
the difference; $100 or more is unreconciled and set aside as before.
**The ruling is not yet in `docs/decisions/rulings.md`: the integrator
records it** (the brief's words above).

Applied per lane through one constant, `reconcile.RECONCILE_TOLERANCE_CENTS
= 10000` (exactly $100 is out), integer cents. The printed total is the one
published; `issue` (e.g. `+0.03: expenses Parts F + G against the printed
total`) is a column on each affected table and the last column of its pub
view. A sum that chooses between readings (the declaration's pairing of
figures and labels, a statement's line) is tried to the cent first and
the tolerance only where nothing holds. No precision rounding admits $100
or more. A part with no row read against a figure that is not nil stays
set aside (nothing read is not a difference).

Replayed on every held document, no fetch, no model:

| Lane | Sum set-asides before | Now reconciled with issue | Stay unreconciled | Largest admitted |
| --- | --- | --- | --- | --- |
| candidate returns (1,105) | 23 (7 declaration, 16 Part A) | 1 (`13e5f25572ae`, expenses +0.03) | 22 (nearest $117.30) | $0.03 |
| party returns (152) | 34 | 1 (National 2023 Part A, +0.01, 182 rows) | 32 by $100+; 1 under $100 kept aside, no lender read | $0.01 |
| disclosures (520 + 1) | 14 itemised `differs` (published flagged, as before) | 1 (`ec-listing/2009-01-07/33dc6812f2c6`, +0.16) | 13 (nearest $500) | $0.16 |
| party finance (108) | 3 by arithmetic | 2 (Leighton Baker 2023 original +0.08; ALC 2024 operating -0.21) | 1 (NZ Loyal 2024, $80,354.02) | $0.21 |

Already-published rows whose difference was passed silently by a float
margin (`<= 0.011`) now carry their issue: 5 candidate returns (1 cent),
NZ First 2023 and Advance NZ 2020 expense returns (1 cent), two
whole-dollar statement position pairs (-$1.00).

Effect on outside checks: candidate returns' spreadsheet check shows 14
differ (was 13): `13e5f25572ae` publishes its printed $337.23, the
Commission has the parts' $337.26. Disclosures' frozen-site comparison
unchanged (amounts unchanged).

Cards the integrator should update (other sessions' cards):
- `national-2023-the-rows-add-to-one-cent-more-than-the-printed-total`: closed by ruling 66 (published, +0.01 issue).
- Decision `may-part-a-pass-a-rounding-cent`: answered by ruling 66.
- `part-a-is-set-aside-on-thirty-three-returns`: 24 set aside; National 2023 off the "add to something else" list.
- `the-scanned-party-statements-figures-are-not-read` (lines 22-23): the arithmetic set-aside is now 1 (NZ Loyal 2024); ALC 2024 reconciled -0.21.
- `five-party-expense-returns-are-unread-against-the-commission` (closed, lines 32, 51): Leighton Baker 2023 original `ef943a1c589a` is now a row (+0.08), not current.
- `the-party-financial-statements-figures-are-not-read` (closed, line 44): the 21-cent surplus publishes with an issue.
- `the-candidate-return-part-a-sets-aside`: unchanged (no Part A within $100).
- Possible board card: `products/board/catalogue.py:161` could show `issue` beside the items check.

Fast tier: each lane green (`bin/fast registers/<lane>`); whole repository
green in 409.5 s (target 300 s missed, recorded). Real tables gain the
`issue` column on the next load (ALTER … ADD COLUMN IF NOT EXISTS).

Lesson: a "to the cent" check written in floats passes a cent silently.

## Result (integrator, 2026-10-21 15:32 NZDT)

Merged into main as f7dfa43 (`merge integrate/reconcile-1: gate green`). Branch `integrate/reconcile-1` from `session/reconcile-1` (75fc718), main merged. Carried with it: five cards for ruling 66 (`national-2023-the-rows-add-to-one-cent-more-than-the-printed-total` closed; the Part A set-asides, the scanned statements, the five expense returns and the financial statements annotated) and coupled-1's merge record. Fast tier green in 485.2 s (target 300 missed under load, recorded). Gate green; staging loaded and published the four lanes with the `issue` column: candidate returns 413 rows, disclosures 521, party finance 116 documents accounted, party returns 140 rows (12 set aside, 1,315 donor rows). Branches and the working copy retired.
