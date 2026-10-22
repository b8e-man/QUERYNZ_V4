# scan templates: where they stand

**Date:** 2026-10-23. **Step:** 6.2, templates 1 to 3, `products/scan/templates/`.
**Merge request:** `scan-templates-2` (raised). Templates 1 and 2 merged 22 October.

## Done

- Template 3 (use case 14, the post-settlement governance map): one
  question in six scans, `settlement-map-iwi`, `-settlements`,
  `-charities`, `-companies`, `-societies`, `-shareholdings`, over the
  directory's 185 organisations and governance entities. Charity, company,
  society and holding by number where both carry one (none printed today),
  else by folded name (near, namesakes marked); "none found in" kept. Register
  scan only, never the public site.
- Checkpoint on the real tables, state in
  `querynz_v4_sample/scratch_scan_templates_2`: 231, 193, 2,163, 198, 329
  and 331 lines, 0 problems; an independent recount equal for all six;
  ten bodies read against their stored pages (`settlement-map-iwi/limits.md`).
  `python -m products.scan check` green over all eleven scans (23.3 s).
- Shape additions as `products/scan/templates/_shape/scan-templates-2-shape.diff`
  (the directory's three views; a citation numbered per row; the check
  reads the cited document back; `chain_readback`). Tests: 1 fast and 7
  slow in the diff, the template tests in `_tests/test_settlement_map.py`;
  10 mutants, each caught. `bin/fast products/scan` green on the branch, 41.6 s.

## Carded

- Blocker: `the-scan-templates-2-shape-diff-at-the-merge` (integrator).
- Findings for `registers/iwi_directory`: `a-settlement-key-names-several-rows`,
  `the-iwi-directory-key-folds-two-bodies-into-one`.
- Closed: `the-settlement-commitments-are-not-held` (accepted onto the limits).
- From scan-templates-1, still open: `the-gets-supplier-number-is-often-a-company-number`,
  `award-notice-titles-carry-street-addresses`, `a-scan-step-cannot-land-on-one-of-several-views`.

## Waiting on Arthur

- Step 6.4 (award join, pre-2019, councils on the public site). Default: no.
- The 200 Tribunal reports (queue `a-named-use-for-the-200`, updated):
  recommendation history search, not this template. Default: held, unread.
- Te Haeata (queue `whether-to-ask-for-the-settlement-commitments`).

## Next

1. The integrator applies the diff and runs the six scans.
2. Template 4 (use case 15), in the plan's order (ruling 79 holds it).
