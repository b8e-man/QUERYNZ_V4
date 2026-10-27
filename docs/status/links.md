# links: where it stands

**Date:** 2026-10-28. **Step:** 4.2 and 4.3, `links/`. **Merge requests:**
`links-1`, `review-1`, `links-2`, `fixes-1`, `coupled-1` (merged), `links-3`
(raised; the detail of each is in `docs/merges/` or `merge-requests/`).

## Done

- Rows: every published register read, nineteen views, a catch log per
  view; `check.py` fails when a lane has loaded rows the links have not read.
- Rules: `full-name@1`, `name-and-address@1`, `seat-and-window@1`,
  `declared-directorship@1`, `official-number@1` confirmed; near with a named
  reason: `company-name@1`, `organisation-name@1`, `candidate-name-form@1`,
  `filed-name@1`, `member-and-party-donor@1`, `own-return@1`,
  `coupled-name@1` (ruling 73). Watch: regions apart, very common name,
  bankrupt-yet-appointing.
- `links-3` (ruling 106), in `scratch_links_3` on the real tables:
  `organisation-sole-company@1` confirms 262 donation rows to the one
  company of their name live in the year; `successor-name@1`, a third grade
  `related` ("succeeded by", `pub.links.relation`), 951 company pairs with a
  person confirmed on both, never followed by the groups;
  `candidate-same-party@1` confirms 282 candidate pairs (206 names, one
  party, two elections). Groups 681,628 → 681,815, contested unchanged.
  `check.py` 33 of 33, four new checks, three proved to fail on planted
  faults.
- Track C (`review-1`): the agent scored, applies nothing; ruling 69 holds
  its splits for after the build.

## Carded / queued

- Open: `a-coupled-donor-s-part-ref-is-found-through-pub-names`; the review
  agent's splits and the three structure questions, held for after the
  build (rulings 69, 75).
- Queue: `one-company-of-several-live-in-the-donation-s-year` (30 donation
  rows, each with exactly one live company of several).

## Next

1. Integrator: merge `links-3`, then run `qv4-links-build` (tables.sql adds
   `links.relation` and widens the grade check in place; publish.sql
   appends `pub.links.relation`); `check.py` live. `scratch_links_3` and
   `scratch_links_3_pub` are Arthur's to drop.
2. Board (a later session): draw `related` links as a frame around the two
   companies in date order, the shared people once.
3. House rows before ge-2020 and list-vacancy members find no seat (house
   lane's card).
