# party-finance: where it stands

**Date:** 2026-10-21. **Step:** 4.1, party finance, `registers/party_finance/`.
**Merge requests:** `party-finance-1` (merged), `party-finance-2` (raised);
ruling 66 applied in `reconcile-1`.

## Done

- Capture: 116 documents by hash from `ec-expenses`, `ec-financials`,
  `ec-broadcasting`, `ec-promoters` and the Commission's listing pages.
- Expense returns: 40 of 40 read; 35 of 37 party-elections equal the
  Commission to the cent, 2 explained (Part A alone), 0 differ, 0 unread.
- Promoter returns: each part read from the declaration and the
  schedule; 44 of 49 Commission figures equal, 0 differ, 5 unread.
- Financial statements: headline figures from the text layer, a pair
  only where the statement's own arithmetic holds; 47 of 92 pairs;
  prior-year columns equal the year before on 53 of 54.
- Broadcasting (89 rows, every round to its printed total), register of
  promoters (69, 303 people; contacts private), statements roster (47).
- Catch log reconciles on all 116 documents.
- **Ruling 66** (`reconcile.py`, `RECONCILE_TOLERANCE_CENTS = 10000`):
  parts below $100 off a printed total are reconciled, the printed figure
  published, the row's `issue` naming the signed difference and the
  parts; $100 or more set aside. A sum that guides a choice is tried to
  the cent on every pass first. Replayed on all 108 held returns, pages
  and statements (`python -m registers.party_finance.replay run|compare`):
  2 set-asides now reconciled with an issue (Leighton Baker 2023 original
  +$0.08, A + B + C; Aotearoa Legalise Cannabis 2024 operating pair
  -$0.21), 45 stay set aside (1 by arithmetic: NZ Loyal 2024, $80,354.02
  off; 44 lines not read), largest newly admitted $0.21. Published rows
  that already passed and now carry an issue: NZ First 2023 and Advance
  NZ 2020 (-$0.01, a cent the old 0.011 tolerance hid), ACT 2024 and one
  more whole-dollar statement position pair (-$1.00, within the printed
  precision; no precision admits $100 or more). 12 figures carry an issue; promoter parts and
  broadcasting rounds none. `check.py` counts the issue rows.

## Carded

`four-promoter-return-parts-are-unread`,
`the-scanned-party-statements-figures-are-not-read`,
`the-board-joins-party-finance-on-the-party-s-name` (blocker, the
integrator's one edit at the merge), `party-rules-are-not-in-this-lane-s-folders`,
`keys-dates-does-not-read-a-day-month-word-two-digit-year`.

## Next

1. Scanned statements' figures from the page reader's stored readings
   (card), the same two checks.
2. Party rules, once the lane's folders take them (card).
