# insurance: where it stands

**Date:** 2026-10-21. **Step:** 5.2, template 8 (use case 6, insurance
underwriting), `products/templates/06-insurance/`. **Merge request:**
`insurance-1` (raised).

## Done

- `template.toml`: 12 pub views with licence, attribution and refresh;
  depth 2; eight sections in an underwriter's order (namesakes apart;
  standing, age and registered office; the solvency record in the Gazette,
  each notice dated; its people, dated; their other companies and states;
  prohibitions and bankruptcies; the people beside; the safety record, every
  register in it named as not held).
- `rules.py`: 23 flags on the bound contract. `sister-company-failure`: a
  failure dated from its first Gazette appointment beside the person's own
  role on the company, red only on a confirmed role from on or before that
  day and still listed; a hub, a near link, a later role or a holding is
  never red. `officer-churn` never clears. `safety-record` and eight
  not-held checks blocked, never clear. From a company the people checks
  block. `HISTORY = False`.
- Checkpoint on 12 real subjects: all print, none refused, no rule broke,
  0.3 to 5.5 s; two faults found and fixed (an application dated a failure;
  a contested group's start company read near); three facts read against
  the Gazette source file. `limits.md` written.
- Tests: 32 fast (fixtures; a mutant check, sixteen mutants each caught),
  3 slow (real tables). `bin/fast products/templates` green 30.2 s; one-way
  and reading-limit tests green. `python -m products.report check` has one
  problem not of this branch (an MP expense row; carded on
  `session/construction-1`).

## Carded

Lanes: `worksafe-and-regulator-actions-have-no-lane` (the heart of use case
6: 83 prosecutions and 62 undertakings held on the old estate, no lane).
Report lane: `the-not-held-list-has-no-key-for-the-safety-registers`. Leans
on the open `a-company-start-does-not-follow-its-officers`,
`the-catalogue-does-not-know-gazette-possessions` (company_states too) and
`a-contested-groups-near-row-can-make-the-start-rows-own-company-near`.

## Next

1. The integrator merges `insurance-1`; nothing to install (`qv4-report`
   serves every template on disk).
2. When a WorkSafe or regulator lane publishes: name its view, unblock
   `safety-record` / `regulator-actions` (a fix here).
3. When the walk follows a company's officers: unblock the people checks
   from a company start (a fix here).
4. Arthur: the churn settings (two in 365 days, the first 30 days' board
   not counted) are defaults; say if others.
