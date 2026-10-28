# report: where it stands

**Date:** 2026-10-28. **Step:** 5.1, the subject-report shape, `products/report/`.
**Merge request:** `fix-products-report-3` (raised, branch `fix/products-report-1`);
`report-1` to `report-3`, `fix-report-2`, `fix-products-report-1` and `-2` merged.

## Done

- `fix-products-report-3` (board-10's finding, ruling 106 (2)): `pub.links`'
  third grade, `related`, reads as a relation and never as near.
  `walk.links_of` keeps related links in their own list. `walk.related_item`
  states each one: "EARLIER (registered …) succeeded by LATER (registered …)",
  in the evidence's date order. The people on both are listed by their rows
  on this side, with citations; a suppressed one is counted and never named.
  The other company is never an entity of the walk and is not walked.
  `build.RELATED_SECTION`, "Related companies: one succeeded by another", is
  added to every template's report after its companies section, and counted
  "n related". Presentation rule 10 refuses a related item that is worded
  near, has no relation, or is listed outside that section.
- The memo names every links rule in words (`catalogue.RULE_WORDS`, held
  equal to the board's), including ruling 106's three rules and ruling 107's.
  The walk's own rules (same-name, official-number, chain …) print as before.
- Refused at the gate 28 October 15:10, then fixed: the memo had printed every
  rule as "rule: X", so the walk's own read "rule: through-officer", and two
  templates' real tests (11-healthcare, 12-property) look for "rule
  through-officer". `memo._rule` now gives a links rule in words and the walk's
  own rules as before; the walk was not at fault. Pinned by a 7th test in
  `tests/test_related.py` (red when the colon returns).
- Checks: `tests/test_related.py` (7 tests; both mutations turn it red);
  `QV4_INTEGRATOR=1 bin/fast products/report` green in 43.6 s;
  `python -m products.report check` green in 80 s, with the new
  `routes_related` on a live succession; `test_real.py`, the templates'
  tests and the root tests are green.

## Next

1. The integrator merges `fix/products-report-1` and restarts `qv4-report`.
2. `products/board/links_view.py` still folds an unknown grade into near.
   board-10 owns that.
3. Step 5.2 continues on this shape.
