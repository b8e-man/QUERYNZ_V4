# house: where it stands

**Date:** 2026-10-20. **Step:** 4.1, candidates, electorates and who sits
in the House, `registers/house/`. **Merge request:** `house-1` (raised).

## Done

- Capture (case 1): 167 files copied by hash from `ec-candidate-list`,
  `ec-results`, `ec-byelections` and Stats NZ's 2020 electorate files
  under `boundaries` (names only). Recognised by shape: 156 to eleven
  profiles (proposed in `profile-proposed.jsonl`), 5 held and not read,
  6 failed reads (2 challenged, 2 Not Found, 2 browser errors).
- Readers: 28 elections with stated polling days; 216 electorates; 1,611
  candidacies (2026: 530; 2023: 495; 2020: 581; Tāmaki Makaurau 2025: 5);
  243 seats with windows. Every read results page meets its own printed
  totals; the 286 status-page abbreviations agree with the party printed
  beside each candidate. Catch log: 13 lines, each a held gap.
- Outside check green: 2026 nominations 42 of 42 Commission figures (530
  candidates); seats per party 2020 18/18 (120), 2023 21/21 (122); Stats
  NZ names 72 of 72 in 2020 and 2023; the PDF 443 of 443 list places.
- Fast tier: `registers/house` 22 passed (13 s); whole repository green
  but `tests/test_generators.py` (the new cards make the board stale).

## Carded

- `stats-nz-2025-electorates-need-arthur-s-key` (2026 join waits on it).
- `three-by-elections-and-two-2020-electorate-pages-are-not-held`.
- `who-left-the-house-mid-term-is-not-in-the-results-files`.
- `the-2020-and-2023-party-lists-are-not-held`.

## Next

1. The integrator merges `house-1`, appends the eleven profiles, loads.
2. When Arthur's Stats NZ key is in place: capture the 2025 layers once,
   join 2026's 71.
3. Mid-term changes from the Gazette lane's published notices.
