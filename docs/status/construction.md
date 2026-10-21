# construction: where it stands

**Date:** 2026-10-21. **Step:** 5.2, template 7 (use case 7, subcontractor
vetting and phoenix detection), `products/templates/07-construction/`.
**Merge requests:** `construction-1` (merged, template 0.1), `construction-2`
(ruling 65, template 0.2; the detail of each is in `docs/merges/`).

## Done

- `template.toml`: 12 pub views with licence, attribution and refresh;
  depth 2; eight sections in a procurement lead's order (namesakes apart;
  officers and holders, dated; the phoenix section; registered offices;
  prohibitions and bankruptcies; the people beside and society roles; the
  Gazette on the entity and the companies above; not held, five named).
- `rules.py`: 26 flags on the bound contract. `phoenix-signature` (ruling
  65): every dated failure on a company sharing a person (from a person) or
  a pre-failure registered office (from a company) beside each going
  company's start, whatever the gap, the gap in days signed, nearest first,
  the pairs within 90 and 365 days counted; it cuts only on
  `report["window_days"]`, the reader's setting (a whole number of days;
  anything else says no cut is applied). Red on a confirmed insolvency not
  through a hub; amber through a hub, a removal or a near link; never a
  name alone. `same-name-failed` and `shared-office` read the same window.
  From a company the people checks block. `HISTORY = False`.
- Checkpoint on 12 real subjects, re-rendered after ruling 65: 11 print, 1
  refused by the shape (a company named like an address, carded); only the
  phoenix flags' text changed, no status or severity; `limits.md` records
  both renders.
- Tests: 35 fast (seventeen mutants, each caught), 4 slow on the real
  tables; `bin/fast products/templates` green 29.2 s.

## Carded

Report lane: `the-report-carries-no-template-parameters` (the key is
`window_days`; until the shape carries it no reader can set a window),
`a-company-named-like-a-street-address-refuses-every-report-that-meets-it`,
`the-walk-counts-the-companies-at-an-office-and-does-not-list-them`,
`a-section-cannot-set-the-starts-own-rows-apart-from-its-peoples`,
`the-not-held-list-lacks-employment-determinations-and-the-change-history`,
`confirmed-expense-links-put-every-category-line-in-a-members-report`.
Companies lane: `a-liquidated-companys-office-before-its-liquidation-is-not-published`.
Templates 2, 3, 4, 13: `four-templates-still-say-no-link-reaches-a-bankruptcy`.
Property-1: `the-construction-template-counts-a-lapsed-intention-to-remove-as-a-failure`.

## Next

1. When the report lane carries template parameters (`fix-report-2`): if it
   puts them under another key than `window_days` in `report`, move
   `WINDOW_KEY`'s read there (a fix here); the lapsed-intention card too.
2. When the walk follows a company's officers: the person half of the
   signature from a company start; when it lists an office's companies or
   past offices are published: the office half.
