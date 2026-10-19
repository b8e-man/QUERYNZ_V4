# party-finance: where it stands

**Date:** 2026-10-20. **Step:** 4.1, party finance, `registers/party_finance/`.
**Merge requests:** `party-finance-1` (merged), `party-finance-2` (raised).

## Done

- Capture: 116 documents by hash from `ec-expenses`, `ec-financials`,
  `ec-broadcasting`, `ec-promoters` and the Commission's listing pages.
- Expense returns: 39 of 40 read; 35 of 37 party-elections equal the
  Commission to the cent, 2 explained (Part A alone), 0 differ, 0 unread.
- Promoter returns: each part read from the declaration and the
  schedule; 44 of 49 Commission figures equal, 0 differ, 5 unread.
- Financial statements: headline figures from the text layer, a pair
  only where the statement's own arithmetic holds; 46 of 92 pairs (138
  figures); prior-year columns equal the year before on 53 of 54.
- Party labels: `keys.parties.party_name(label, rows, on=…)` over
  `pub.party_names`; `party` holds the registration's key. Every expense,
  return and statement label resolves; 78 of 89 allocation rows (the
  rest were never registered).
- Broadcasting (89 rows, every round to its printed total), register of
  promoters (69, 303 people; contacts private), statements roster (47).
- Catch log reconciles on all 116 documents.

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
