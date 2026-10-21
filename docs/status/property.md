# property: where it stands

**Date:** 2026-10-21. **Step:** 5.2, template 12 (property developer due
diligence), `products/templates/12-property/`. **Merge request:** `property-1` (raised).

## Done

- `template.toml`: 14 published views with licences (companies, company_states,
  directors, shareholders, company_addresses, the Gazette's liquidations,
  liquidators, company notices, possessions, appointments, prohibitions,
  bankruptcies, societies, society officers); 11 sections in a buyer's order;
  the report-3 reaches `officers`, `office`, `chain` (depth 2).
- `rules.py`: 23 flags. Serial pattern (MC-P1), earlier failure, entity
  status, young entity, sole vehicle, professional office, shared office,
  possession, prohibition, bankruptcy, insolvency notices, holding chain,
  history reach, namesakes; nine not-held registers blocked. Window read as
  `report["window_days"]` (ruling 65), no cut until set.
- Tests: 40 fixture tests with 26 mutants, all caught; 3 real-table tests
  (slow), green. Fast tier `products/templates` green (30 s); one-way and
  reading-limit tests green; `python -m products.report check` green.
- Checkpoint: twelve subjects in `checkpoint.list`, none refused, no rule
  broken; four faults fixed on the way (limits.md). Lesson filed.

## Carded

- `the-not-held-list-has-no-key-for-the-property-registers` (report lane:
  keys for OIO, building consents, REA; the charities views).
- `the-officers-reach-does-not-list-an-officers-near-links` (report lane;
  1,956 of 4,602 directors measured).
- `the-chain-reach-reads-nothing-on-the-companies-above` (report lane).
- `the-construction-template-counts-a-lapsed-intention-to-remove-as-a-failure`
  (template 7's folder).

## Next

1. The integrator merges `property-1`.
2. When the report lane lands the keys, the charities views and the window
   parameter: the fixes in this folder each card names.
