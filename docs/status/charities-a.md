# charities-a: where it stands

**Date:** 2026-10-21. **Step:** 4.1, the Fable build of the charities reading,
`registers/charities_a/`. **Merge request:** not yet raised.

## Done

- Read: the plan index, step 4, the four contracts, the capture lane
  (`registers/charities/`: 46,138 Organisations, 589,148 Officers, 430,522
  AnnualReturn rows in one finished full pass each; code lists; Groups 357).
- Lessons searched (OData count cap; shared scratch tables carry the lane's
  prefix; a loader reconciles to the capture's own counts; a name field that
  reads as an address is set aside).
- Surveyed the pages for shapes (counts only; no name or contact field printed).

## Half-done

- Writing the reading (`read.py`), tables, loader, check, sample, tests.

## Next

1. Full build into `scratch_charities_a` (sample database); figures.
2. Fast tier green; slow tier timed; push; merge request `charities-a`.
