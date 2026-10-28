# links: where it stands

**Date:** 2026-10-28. **Step:** 4.2 and 4.3, `links/`. **Merge requests:**
`links-1`, `review-1`, `links-2`, `fixes-1`, `coupled-1`, `links-3`,
`fix-links-1`, `fix-links-2` (merged), `fix-links-3` (raised; detail in
`docs/merges/` or `merge-requests/`).

## Done

- Rows: 27 published views, a catch log per view; `check.py` fails when a
  lane has loaded rows the links have not read.
- Rules: `full-name@1`, `name-and-address@1`, `seat-and-window@1`,
  `declared-directorship@1`, `official-number@1` confirmed; near with a
  named reason: `company-name@1`, `organisation-name@1`,
  `candidate-name-form@1`, `filed-name@1`, `member-and-party-donor@1`,
  `own-return@1`, `coupled-name@1`. Watch: regions apart, very common
  name, bankrupt-yet-appointing.
- Rulings 106, 107, 109: `candidate-same-party@1`, `successor-name@1` and
  `refiled-name@1` (related); the donor organisation rules, now @2.
- `fix-links-3` (ruling 114), proved read-only on live: eight people views
  read (+757,949 rows, +328,853 name keys; about 373k near and 167k
  full-name links to come); `organisation-sole-company@2` and
  `organisation-one-live-company@2` on the companies, societies, limited
  partnerships and charities registers (`links.bodies`): the same 292
  donation rows confirm, none new (societies and partnerships were already
  `pub.companies` rows; no donor names a charity alone). Check item 9 and
  measurement 10 new. The charities officer id supplies no one-person test
  pair (it keys a row).
- Track C (`review-1`): the agent scored, applies nothing; switch off.

## Carded / queued

- Queued: `a-refiled-company-whose-removed-half-has-no-people`.
- Open: `a-coupled-donor-s-part-ref-is-found-through-pub-names`,
  `three-test-pair-kinds-the-registers-cannot-supply`, the mixed views
  card (ruling 114); the review agent's splits and the structure
  questions, held for after the build (rulings 69, 75).

## Next

1. Integrator: merge `fix-links-3`; `links.ddl()` makes `links.bodies`
   (tables.sql; publish.sql unchanged); queue `qv4-links-build`, then
   `python -m links.check` live and read the run's `peak_mb`.
2. Board and report: the rule words for `organisation-sole-company` say
   "company"; a body may now be a charity or a society.
3. House rows before ge-2020 and list-vacancy members find no seat.
