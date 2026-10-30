# links: where it stands

**Date:** 2026-10-30. **Step:** 4.2 and 4.3, `links/`. **Merge requests:**
`links-1`, `review-1`, `links-2`, `fixes-1`, `coupled-1`, `links-3`,
`fix-links-1` to `-5`, `links-4`, `links-5` (merged), `fix-links-6` (raised
30 October; detail in `docs/merges/` or `merge-requests/`).

## Done

- Rows: 31 published views, a catch log per view; `check.py` fails when a
  lane has loaded rows the links have not read. Rules: six confirming
  (`full-name@1`, `name-and-address@1`, `seat-and-window@1`,
  `declared-directorship@1`, `official-number@1`, `member-on-the-day@1`),
  seven near with a named reason, two related (rulings 106, 109); the
  watch; `pub.entities` (ruling 123, check item 11).
- `links-5` (ruling 125): `organisation-sole-company@3` and
  `organisation-one-live-company@3` on every organisation-named row of
  every people view, "live" judged on the row's own date; an undated row
  stays near. Measured on live (measurements.md §12): 2,632 confirmed
  where @2 had 292; shareholders all undated (no filing date published).
- `fix-links-6`: an all-zero NZBN is none in `links.bodies` (35 charities
  rows); the charities of one NZBN are one body, the earliest row where no
  Companies Office or society row is (CC58580 and CC61425); a body's
  charities rows are its registrations in turn, removed only where the last
  registered is (`rules.body_dates`, `body_dates_sql` for the check and
  measurement 12). Measured on live (measurements.md §13): check item 9's
  second line goes 2 → 0; 2,023,825 bodies rows before and after, one body
  moved, no link touches it.
- Track C (`review-1`): the agent scored, applies nothing; switch off.

## Carded / queued

- New: `pub-shareholders-publishes-no-filing-date-so-every-organisation-named-holding-stays-undated`
  (for the companies lane; about 400 confirmations wait on the date).
- Open: `the-display-name-ordering-counts-a-title-and-a-register-s-suffix-as-words`,
  `a-coupled-donor-s-part-rows-are-entities-beside-their-donor-row`,
  `a-coupled-donor-s-part-ref-is-found-through-pub-names`,
  `three-test-pair-kinds-the-registers-cannot-supply`, the mixed views
  card; queued `a-refiled-company-whose-removed-half-has-no-people`; the
  review agent's splits and the structure questions (rulings 69, 75).

## Next

1. Integrator: merge `fix-links-6` (no DDL); queue `qv4-links-build`, then
   `python -m links.check` live: `nzbns_on_two_bodies` 0, every item green.
