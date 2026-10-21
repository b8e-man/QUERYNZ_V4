# scan templates: where they stand

**Date:** 2026-10-21. **Step:** 6.2, templates 1 and 2, `products/scan/templates/`.
**Merge request:** `scan-templates-1` (raised). Templates 3 and 4 are later sessions.

## Done

- `tender-awards` (use case 10): every supplier on every GETS award
  notice, the company joined by business number (confirmed) or else by
  name alone (near, namesakes marked), "none found" kept. 33,744 lines in
  17.5 s; every one of 31,264 suppliers listed.
- `procurement-directors-donors` and `procurement-shareholders-donors`
  (use case 9, one question in two scans): donor, director or shareholder
  by the links, company, supplier, award. 80 and 6 lines, all near, about
  50 s each. For the register scan only, never the public site.
- Each folder has `limits.md` with its checkpoint (real tables, state in
  `querynz_v4_sample/scratch_scan_templates_1`) and lines read by eye. An
  independent recount matched each count. `python -m products.scan check`
  green on the merged copy (11.6 s).
- The shape's additions (award views, name step, optional step, several
  link rules, rule 10, the read-back) as
  `products/scan/templates/_shape/scan-templates-1-shape.diff`; fast tests
  21 + 34, slow 4, mutants for rule 10 and the read-back.

## Carded

- Blocker: `the-scan-templates-shape-diff-at-the-merge` (integrator).
- Findings: `the-gets-supplier-number-is-often-a-company-number` (links or
  tenders), `award-notice-titles-carry-street-addresses` (tenders),
  `a-scan-step-cannot-land-on-one-of-several-views` (scan).
- Idea: `the-scan-page-filters-by-grade-only`.
- Closed: `the-gets-supplier-file-loses-its-business-numbers` (accepted
  onto the limits pages). Measured onto
  `a-person-step-cannot-reach-a-filed-row-through-the-groups`.

## Waiting on Arthur

- Step 6.4: whether the award join, pre-2019 awards or a councils tier
  ever appear on the public site. Default: no.
- The two trust settings stay "default in force".

## Next

1. The integrator merges with the diff and runs the three scans.
2. Template 3 (use case 14), then 4 (use case 15), in the plan's order.
