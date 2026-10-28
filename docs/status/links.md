# links: where it stands

**Date:** 2026-10-28. **Step:** 4.2 and 4.3, `links/`. **Merge requests:**
`links-1`, `review-1`, `links-2`, `fixes-1`, `coupled-1`, `links-3` (merged),
`fix-links-1` (merged), `fix-links-2` (raised; the detail of each is in `docs/merges/` or `merge-requests/`).

## Done

- Rows: every published register read, nineteen views, a catch log per
  view; `check.py` fails when a lane has loaded rows the links have not read.
- Rules: `full-name@1`, `name-and-address@1`, `seat-and-window@1`,
  `declared-directorship@1`, `official-number@1` confirmed; near with a named
  reason: `company-name@1`, `organisation-name@1`, `candidate-name-form@1`,
  `filed-name@1`, `member-and-party-donor@1`, `own-return@1`,
  `coupled-name@1` (ruling 73). Watch: regions apart, very common name,
  bankrupt-yet-appointing.
- `links-3` (ruling 106): `organisation-sole-company@1` 262 donation rows;
  `successor-name@1`, grade `related` ("succeeded by"), 951 company pairs;
  `candidate-same-party@1` 282 pairs.
- `fix-links-1` (ruling 107): `organisation-one-live-company@1`, 30
  donation rows to 18 companies.
- `fix-links-2` (ruling 109), in `scratch_fix_links_2`: `refiled-name@1`,
  related, "delisted/refiled same year": 12,607 same-name pairs removed and
  registered within twelve months, 2 share a person, **2 related**
  (Chatham Rock Phosphate, Pacific Hygiene). Christopher & Banks is not one:
  its removed company has no people published (queued). `check.py` item 8
  and the widened item 6 proved red on planted faults.
- Track C (`review-1`): the agent scored, applies nothing; ruling 69 holds
  its splits for after the build.

## Carded / queued

- Queued: `a-refiled-company-whose-removed-half-has-no-people`.
- Open: `a-coupled-donor-s-part-ref-is-found-through-pub-names`; the review
  agent's splits and the three structure questions, held for after the
  build (rulings 69, 75).

## Next

1. Integrator: merge `fix-links-2`, then run `qv4-links-build`; `check.py`
   live. `scratch_links_3`, `scratch_fix_links_1`, `scratch_fix_links_2`
   and the `_pub` schemas are Arthur's to drop.
2. Board and report: the relation prints from the column; five notes and
   rule-word tables still say "a year in brackets" (fix-links-2.md).
3. House rows before ge-2020 and list-vacancy members find no seat (house
   lane's card).
