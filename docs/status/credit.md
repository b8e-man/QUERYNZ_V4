# credit: where it stands

**Date:** 2026-10-21. **Step:** 5.2, template 7 (use case 5, business credit
and monitoring), `products/templates/05-credit/`. **Merge request:**
`credit-1` (raised).

## Done

- `template.toml`: 12 pub views with licence, attribution and refresh;
  depth 2; seven sections in a credit analyst's order (namesakes apart;
  standing today; what changed, by monthly file; the Gazette on the entity;
  its people; prohibitions and bankruptcies; not held, eleven named).
- `rules.py`: 25 flags. `monthly-changes` (arrivals, departures, a changed
  holding, an office move, the entity first shown or gone, newest first,
  dated by file, "a month and not a day"); `recent-adverse-change` (90 days
  for a Gazette notice, the latest file for a change); `officer-churn`; the
  Gazette, standing, people and young-entity checks; ten blocked checks for
  what cannot be seen. `STATES = False`, `HISTORY = False`.
- Checkpoint on 12 real subjects: 12 print, none refused, 0.2 to 4.9 s; six
  faults found and fixed; two Gazette notices read against the source file
  (six fields, no text printed). `limits.md` written.
- Tests: 32 fast (fixtures; a mutant check, twelve mutants each caught,
  two of them only after the properties were tightened), 3 slow.

## Carded

Report lane: `the-catalogue-does-not-know-company-states` (the largest gap),
`a-report-takes-no-since-date`, `the-report-keeps-no-watched-list`,
`a-section-cannot-select-the-rows-that-changed-between-files`,
`the-not-held-list-lacks-credit-bureau-and-the-business-number-interface`.
Companies lane: `the-companies-lane-publishes-no-list-of-its-monthly-files`.
Leans on the open `a-company-start-does-not-follow-its-officers`,
`the-catalogue-does-not-know-gazette-possessions`, step 5.5.

## Next

1. The integrator merges `credit-1`; nothing to install (`qv4-report`
   serves every template on disk).
2. When the catalogue knows `pub.company_states`: `STATES = True` and the
   status and name changes in `monthly-changes` (a fix here).
3. Arthur: the windows (90 days recent, 365 days churn, 5 years for a
   bankruptcy to turn amber) are defaults; say if others.
