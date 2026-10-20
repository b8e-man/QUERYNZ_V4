# recruitment: where it stands

**Date:** 2026-10-20. **Step:** 5.2, template 1 (use case 8, recruitment
board screen), `products/templates/08-recruitment/`. **Merge request:**
`recruitment-1` (raised).

## Done

- `template.toml`: 23 pub views with licence, attribution and refresh; seven
  sections in the consultant's order (namesakes apart first, then
  directorships and holdings of record, Gazette insolvency/bankruptcy/
  prohibition, charity and society roles, political money, seats and
  declared interests, what is not held); depth 1 (co-directors are not the
  subject's record); limits.
- `rules.py`: 13 flags for the old seven person rules (liquidation history,
  prohibition, young entity, namesake exposure, charity officer roles,
  charity integrity marks, ComCom) plus identity, subject hub, register
  removals, bankruptcy, public life, replaced return. Red only on confirmed
  rows, amber on a namesake's; a clear only where the walk could have seen
  it (bankruptcy, charity marks and ComCom blocked). Imports nothing of the
  shape (the one-way test).
- Checkpoint on 12 real subjects: 10 print clean, 2 refused by the shape's
  checks (carded); built in 0.2 to 4.6 s; three facts read against their
  Gazette notices. `limits.md` written.
- Tests: 21 fast (fixtures, the shape's CLI), 3 slow (real tables through
  the CLI); `python -m products.report check` green; one-way test green.

## Carded

Report lane: `a-surname-lane-trips-the-home-address-check`,
`a-company-name-with-control-trips-the-cause-check`,
`a-template-cannot-reach-the-flag-contract-or-the-shapes-rules`,
`an-mps-declared-interests-are-not-walked-from-a-person-start`,
`expenses-views-are-not-in-the-report-catalogue`,
`a-gazette-company-notice-date-does-not-say-what-it-dates`,
`the-report-header-repeats-group-rows-a-section-lists`,
`a-donation-row-start-has-no-group`. Links:
`bankruptcies-and-appointments-are-not-in-pub-names`.

## Next

1. The integrator merges `recruitment-1`; nothing to install (the shape's
   `qv4-report` serves every template on disk).
2. When the charities lane publishes, add its views and the integrity-marks
   rule; when links carry bankruptcies, the bankruptcy rule clears.
3. Step 5.2, template 2: use case 4, agriculture.
