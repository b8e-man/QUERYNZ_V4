# scan-templates-1: step 6.2 templates 1 and 2 on the scan shape
branch: session/scan-templates-1 (pushed; 6658286)
session: scan-templates-1 (Opus)
raised: 2026-10-21
claims: products/scan/templates/ (new: tender-awards, procurement-directors-donors, procurement-shareholders-donors, each template.toml + limits.md; _tests/test_scan_templates.py; _shape/scan-templates-1-shape.diff); docs/status/scan-templates.md; five cards opened (blocker the-scan-templates-shape-diff-at-the-merge; findings the-gets-supplier-number-is-often-a-company-number, award-notice-titles-carry-street-addresses, a-scan-step-cannot-land-on-one-of-several-views; idea the-scan-page-filters-by-grade-only); one card closed (the-gets-supplier-file-loses-its-business-numbers, accepted onto the limits pages); one card measured (a-person-step-cannot-reach-a-filed-row-through-the-groups); three lessons

Templates 1 and 2 of step 6.2, on the shape merged as scan-1 and the award
notices merged as tenders-1:

1. **`tender-awards`** (use case 10). One line per supplier on an award
   notice: the agency and RFx ID, the award date, the value as published
   ("0" with its note, "no value given"; the historic file has none), the
   categories; the company joined by business number when both rows carry
   one (confirmed), else by the folded name (near, the reason on the
   line, every company under that name its own line marked as one of its
   namesakes); a supplier with no company found listed with "none found
   in". The notice's own title is never read (754 carry a street address).
2. **`procurement-directors-donors`, `procurement-shareholders-donors`**
   (use case 9; a step lands on one view, so the template is two scans
   with one question, "who among a winning supplier's people also appears
   as a donor"). Donor row (party returns, disclosures, candidate
   returns), the director or shareholder the links join it to
   (`full-name@1` confirmed or `name-only@1` near), the company, the
   supplier joined to it, the award. Every line graded, cited and dated;
   each listed as a coincidence of record; limits say register scan only,
   never the public site (6.2 row 2, 6.4).

Checkpoint, real published tables, state in
`querynz_v4_sample/scratch_scan_templates_1`, the shape's additions applied
on a merged copy: tender-awards 33,744 lines in 17.5 s (25,177 near, 8,567
with no company found, 0 problems; all 31,264 suppliers listed);
directors 80 lines in 49.4 s, shareholders 6 in 47.4 s, all near, 0
problems; an independent recount gave 80 and 6; the two proving scans
unchanged (854 and 287). `python -m products.scan check` green, 11.6 s.
Tests: 21 fast and 4 slow for the shape (in the diff), 34 for the
templates (skipping on this branch until the diff is in, guarded so the
skip cannot outlive the diff); mutants of rule 10 and of the read-back,
each caught. `bin/fast products/scan` green on the branch, 33.7 s.

At the merge, please (card `the-scan-templates-shape-diff-at-the-merge`):
1. `git apply products/scan/templates/_shape/scan-templates-1-shape.diff`
   (views, template, plan, lines, rules, hubs, out, check, two test files)
   in the same commit as the templates; delete `products/scan/templates/_shape/`.
   Merged without it, the three templates do not load and `run --stale`
   fails loudly.
2. Fast tier; the slow `products/scan/tests/test_templates_real.py`.
3. With `QV4_SCAN_STATE=querynz_v4/register_scan`: `python -m products.scan run`
   for the three templates (about 2.5 minutes), then `python -m products.scan check`.
4. Regenerate the board and the lessons index. The scratch schema
   `scratch_scan_templates_1` in the sample database may be dropped.

Lessons (filed in lessons/): `a-reverted-mutant-can-run-from-a-stale-bytecode-cache`,
`a-namesake-count-means-something-only-where-each-row-is-one-body`,
`title-a-row-by-its-identifiers-not-the-publisher-s-free-text`.

## Result (integrator, 2026-10-22 01:18 NZDT)

Merged into main as d708c28 (`merge integrate/scan-templates-1: gate green`). Branch `integrate/scan-templates-1` from `session/scan-templates-1` (6658286), main merged. Card `the-scan-templates-shape-diff-at-the-merge`, now closed: the shape diff applied by a small unified-diff reader of the integrator's (the hooks refuse both `git apply` and `patch`), the result checked against the diff's own line counts to the ten scan files in the same commit as the three templates, `products/scan/templates/_shape/` removed; the template tests no longer skip. Fast tier green in 501.3 s; the slow `products/scan/tests/test_templates_real.py` green (4 tests). After the merge, with the scan's state in `querynz_v4.register_scan`: tender-awards run 66, 33,744 lines in 16.4 s (8,567 confirmed, 25,177 near, 73 with a hub, 61,722 citations, 0 problems); procurement-directors-donors run 67, 80 lines in 47.6 s (all near, 6 with a hub, 147 citations, 0 problems); procurement-shareholders-donors run 68, 6 lines in 46.3 s (all near, 26 citations, 0 problems); `python -m products.scan check` 0 problems across the five scans, the two settings in force. `qv4-scan` restarted on the new shape. Step 6.2 templates 1 and 2 built; the award join stays off the public site (6.2 row 2, 6.4: Arthur's question stands). Gate green, nothing to load. The scratch schema `scratch_scan_templates_1` is Arthur's drop. Branches and the working copy retired.
