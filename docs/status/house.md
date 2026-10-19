# house: where it stands

**Date:** 2026-10-20. **Step:** 4.1, candidates, electorates and who sits
in the House, `registers/house/`. **Merge request:** `house-1` (not yet
raised).

## Plan, in tranches (each measured on the real files)

1. Capture by hash, read-only, from `var/staging/ec-candidate-list`,
   `ec-results`, `ec-byelections`, and the Stats NZ 2020 electorate files
   under `var/staging/boundaries` (names only); profiles proposed with
   their recognition markers; challenged and not-found pages to the catch log.
2. 2026 candidates: electorate workbook and party lists, against the
   Commission's release (530 candidates; 61 list only, 22 electorate only,
   65 independent or unregistered, 382 both; per-party table).
3. 2020 and 2023 results: electorate pages (candidates, votes, the page's
   own total), electorates joined to Stats NZ's names (72 of 72).
4. Members: successful candidates and the held by-election, a window per
   seat; seats per party against the Commission's overall results.
5. Load, publish, sample, tests, check; cards; merge request.

## Done

Nothing yet.
