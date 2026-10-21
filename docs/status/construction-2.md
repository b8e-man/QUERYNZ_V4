# construction-2: where it stands

**Date:** 2026-10-21. **Card:** ruling 65, the phoenix window is the
reader's setting. `products/templates/07-construction/`, template 0.2.
**Merge request:** `construction-2` (raised).

## Done

- `rules.py`: `WINDOW_DAYS` gone. `phoenix-signature` sets every dated
  failure on a company sharing a person (from a person) or a pre-failure
  registered office (from a company) beside each going company's start,
  whatever the gap, gap in days signed, ordered nearest first; counts the
  pairs within 90 and 365 days; cuts only on `report["window_days"]` (a
  whole number of days; anything else says no cut is applied). Severity
  rules unchanged (red on a confirmed insolvency, not through a hub; amber
  through a hub, a removal or a near link). `same-name-failed` and
  `shared-office` read the same window.
- Tests: 35 fast (seventeen mutants, three new: no default window, nearest
  first, the 90/365 counts; the window mutant rewritten); seven fail on the
  old rules. 4 slow green on the real tables. `bin/fast products/templates`
  green 29.2 s.
- Checkpoint re-rendered (12 subjects, old and new): only phoenix flags
  changed, no status or severity; recorded in `limits.md`.

## Carded

Report lane: `the-report-carries-no-template-parameters` (the key is
`window_days`).

## Next

1. The integrator merges `construction-2`; nothing to install.
2. When the report lane carries template parameters: if it puts them under
   `report["parameters"]`, move `WINDOW_KEY`'s read there (a fix here).
