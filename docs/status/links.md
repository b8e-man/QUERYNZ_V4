# links: where it stands

**Date:** 2026-10-20. **Step:** 4.2 and 4.3, `links/`. **Merge request:** `links-1`.

## Done (in `scratch_links`, measured on the real published tables)

- Rows: 2.75 M person rows from nine registers under the shared reading;
  867 K registered offices; 1.92 M company names (`links.rows`, 3 min).
- Links, stored as a star per component: rule 1 (full name with middle)
  1,257,095; rule 2 (first and last name, one quiet office) 942,014; the
  number 4,384; the house lane's own join 142; organisation names 191
  (near); name-only near 410,160. Groups 669,863 over 2.25 M rows; watch
  flags 149,982 of 2.2 M confirmed links; 51,618 groups contested.
- Old ledgers copied exactly (folds 5,479; anchors 71,319; verdicts 381),
  mapped by content, the last word promoted: 5,355 decisions. Unmapped:
  carded (`old-decisions-that-could-not-be-mapped-to-new-rows`).
- Test pairs (4.3): two directors on one company at once 430 (200/200/30);
  two candidates 1; seat-and-candidacy 142; donor across amended return 0.
  Three kinds the registers cannot supply: carded.
- The six measurements: `links/measurements.md` (full) and
  `links.measurements`. Error rate on "two people" pairs: rare 52%,
  middling 21.5%, common 36.7%, nearly all rule 2 on the two roles'
  shared company (queued); identical full names on one company may be
  the register's own duplicate. Agent reading of 100 confirmed links: 98
  no reason to doubt, 2 contested (the session's judgment, registers
  only, no web search).
- `pub.links`, `pub.groups`, `pub.decisions`, `pub.names`,
  `pub.old_decisions` (`publish.sql`), tested in `scratch_links_pub` in the
  board's shape. `check.py` green (8 of 8). Fast tier: 17 tests green.

## Carded / queued

- `the-links-jobs-into-the-catalogue` (blocker, integrator);
  `three-test-pair-kinds-the-registers-cannot-supply`;
  `old-decisions-that-could-not-be-mapped-to-new-rows`.
- Queue: `may-a-company-name-alone-confirm-a-donor` (default near);
  `does-one-company-s-office-count-as-a-shared-address` (default yes).

## Next

1. Integrator: load into `links` (`rows`, `old`, `build`, `pairs`,
   `measure`, `publish.sql`), catalogue entries, drop `scratch_links` and
   `scratch_links_pub` after the merge.
2. Re-run `links.old --map --promote` and `links.pairs` when party-returns'
   Part A, candidate-returns and charities publish.
3. Register rule 10 (rebuild only what changed); the review job's first
   run on the review profile; the agent scored on the pairs (track C).
