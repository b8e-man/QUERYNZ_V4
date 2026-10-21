# healthcare: where it stands

**Date:** 2026-10-21. **Step:** 5.2, template 11 (healthcare operator
governance), ninth in the plan's order, `products/templates/11-healthcare/`.
**Merge request:** `healthcare-1` (raised). **Merge after `report-3`:** the
template names the third tranche's reaches, filters, `company_states` and
not-held keys, and the report-2 loader on main refuses it (and with it every
template's load test).

## Done

- `template.toml`: 13 pub views with licence, attribution and refresh
  (companies, company_states, directors, shareholders, company_addresses,
  societies, society_officers, the Gazette's liquidations, liquidators,
  company notices, appointments, prohibitions, bankruptcies); depth 2,
  chain two up; seven sections in an investor's order (namesakes apart,
  `own = false`; standing and age; governance with the chain; the charity's
  returns; officer overlap through the `officers` reach; the Gazette; what
  is not held).
- `rules.py`: 21 flags, `flag`, `items`, `section`, `all_items` from the
  bound contract, no import of the shape. Officer overlap dated side by
  side, care-named organisations apart, the entity's own name word apart,
  hubs never amber; prohibitions and bankruptcies on officers' records;
  insolvency on the entity and on officers' other companies; young entity;
  four charity flags written against the charity views by name, blocked
  until the template reads them; six not-held flags and past roles blocked.
- Tests: 31 fast (fixtures; a mutant check of eighteen breaks, each caught)
  and 3 slow (real tables, subjects at run time), green on the report-3
  shape; `products/templates` and `products/report` fast tiers green there
  (249); one-way, reading-limit and generator tests green on this branch.
- Checkpoint: twelve subjects (`checkpoint.list`), all printed, none
  refused, no rule broke; three faults found and fixed (`limits.md`).

## Carded

- `the-report-cannot-reach-the-charities-register` (report lane and links
  lane, after `charities-3` merges).
- `the-not-held-list-has-no-key-for-the-health-registers` (report lane).
- `the-officers-reach-counts-past-officers-against-its-limit` (report lane).
- `the-retirement-villages-file-holds-no-operator-or-supervisor` (a lane,
  plan 5.3).

## Next

1. The integrator merges `report-3`, then `healthcare-1`.
2. When `charities-3` merges and the report lane catalogues its views: a
   fix in this folder adds the three reads and their sections (the card
   says how).
3. The Health and Disability Commissioner's decisions are to acquire (plan
   5.3); the "articles mentioning" section comes with step 7.6.
