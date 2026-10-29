# links: where it stands

**Date:** 2026-10-30. **Step:** 4.2 and 4.3, `links/`. **Merge requests:**
`links-1`, `review-1`, `links-2`, `fixes-1`, `coupled-1`, `links-3`,
`fix-links-1` to `-5` (merged), `links-4` (raised 30 October; detail in
`docs/merges/` or `merge-requests/`).

## Done

- Rows: 31 published views, a catch log per view; `check.py` fails when a
  lane has loaded rows the links have not read.
- Rules: `full-name@1`, `name-and-address@1`, `seat-and-window@1`,
  `declared-directorship@1`, `official-number@1`, `member-on-the-day@1`
  confirmed; near with a named reason: `company-name@1`,
  `organisation-name@1`, `candidate-name-form@1`, `filed-name@1`,
  `member-and-party-donor@1`, `own-return@1`, `coupled-name@1`. Watch:
  regions apart, very common name, bankrupt-yet-appointing.
- Rulings 106, 107, 109: `candidate-same-party@1`, `successor-name@1`,
  `refiled-name@1` (related); the donor organisation rules, @2 on four
  registers (ruling 114). Ruling 116: the House's member rows. Refs order
  by bytes everywhere (`fix-links-5`).
- `links-4` (ruling 123): `pub.entities`, one row per entity, built by
  `build.build_entities` after the groups (`links.entities`); the display
  name by the ordering in `pane.md`; `check.py` item 11. My SQL run on live
  through the reader (read-only, 43 s): 2,597,213 entities = 724,964
  groups + 1,872,249 lone rows, the brief's figures exactly; 5,025,996
  rows; 2,587,173 person, 9,845 organisation, 195 estate; 43,395
  contested; 798,692 politician; 82,878 on several registers; no blank
  name. 4,333 groups hold no `pub.names` row (a company and its Gazette
  row by NZBN) and are named from `links.bodies`.
- Track C (`review-1`): the agent scored, applies nothing; switch off.

## Carded / queued

- New: `the-display-name-ordering-counts-a-title-and-a-register-s-suffix-as-words`
  ("Brown, Simeon (4)" chosen over "Simeon Brown": ruling 105's ordering,
  built as ruled; the fold is Arthur's), `a-coupled-donor-s-part-rows-are-entities-beside-their-donor-row`.
- Queued: `a-refiled-company-whose-removed-half-has-no-people`.
- Open: `a-coupled-donor-s-part-ref-is-found-through-pub-names`,
  `three-test-pair-kinds-the-registers-cannot-supply`, the mixed views
  card (ruling 114); the review agent's splits and the structure
  questions, held for after the build (rulings 69, 75).

## Next

1. Integrator: merge `links-4`; apply `links.ddl()` then the publish DDL
   (the view needs the table); queue `qv4-links-build`, then
   `python -m links.check` live; catalogue `pub.entities` on the board in
   the merge after (the board's check lists it as uncatalogued until then).
2. The two unruled items of 30 October (organisation rules on every row
   naming a body; bodies under one name across registers) wait on Arthur.
3. Check item 9's second line is red on live, from the data: 35 charities
   carry the NZBN `0000000000000`, and CC58580 and CC61425 share one.
