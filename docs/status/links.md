# links: where it stands

**Date:** 2026-10-30. **Step:** 4.2 and 4.3, `links/`. **Merge requests:**
`links-1`, `review-1`, `links-2`, `fixes-1`, `coupled-1`, `links-3`,
`fix-links-1` to `-5`, `links-4` (merged), `links-5` (raised 30 October;
detail in `docs/merges/` or `merge-requests/`).

## Done

- Rows: 31 published views, a catch log per view; `check.py` fails when a
  lane has loaded rows the links have not read. Rules: six confirming
  (`full-name@1`, `name-and-address@1`, `seat-and-window@1`,
  `declared-directorship@1`, `official-number@1`, `member-on-the-day@1`),
  seven near with a named reason, two related (rulings 106, 109); the
  watch; `pub.entities` (ruling 123, check item 11).
- `links-5` (ruling 125): `organisation-sole-company@3` and
  `organisation-one-live-company@3` (`rules.body_on_date`,
  `build.body_links`) on every organisation-named row of every people
  view, "live" judged on the row's own date, never today; a row with no
  date stays near, "undated". @2 retired; the declared interests' near step
  on the companies register alone is gone; check item 9 and measurement 12
  follow. Measured read-only on live (measurements.md §12), confirmed rows
  by view: MPs' interests 2,039 sole + 259 one-live-of-several (of 3,593;
  87 removed before and 64 registered after the return stay near); party
  donors 181, disclosures 95, candidate donors 16 (as @2, same pairs);
  society officers 25; charity officers 15; directors 2; shareholders 0 of
  1,170 (all undated, 484 near). 2,632 confirmed where @2 had 292. 33 rows
  (Christopher & Banks, Ivory, Oriwa, AMP, …) name a company whose one
  live namesake today is the wrong one: the rule confirms the one alive
  on the date.
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

1. Integrator: merge `links-5` (no DDL: no table or view changes); queue
   `qv4-links-build`, then `python -m links.check` live. The board's and
   report's rule words for `organisation-sole-company` and
   `organisation-one-live-company` (`products/*/catalogue.py`, keyed without
   the version) still say "a donation's organisation name": reword for
   every organisation-named row, on the row's date, in the merge after.
2. Check item 9's second line is red on live, from the data: 35 charities
   carry the NZBN `0000000000000`, and CC58580 and CC61425 share one.
