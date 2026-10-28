# links: where it stands

**Date:** 2026-10-28. **Step:** 4.2 and 4.3, `links/`. **Merge requests:**
`links-1`, `review-1`, `links-2`, `fixes-1`, `coupled-1`, `links-3`,
`fix-links-1` to `-4` (merged), `fix-links-5` (raised; detail in
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
  registers (ruling 114). Ruling 116: the House's member rows.
- `fix-links-5`: refs order by bytes everywhere (COLLATE "C" in the three
  pair-order CHECKs, migrated at the job's start, and in every SQL least,
  greatest, min and ORDER BY of refs), so Python's pair and group id and
  SQL's agree; the build of 28 October died on that. Check item 9 runs in
  5 s on live (was 388 s, past its 300 s).
- Track C (`review-1`): the agent scored, applies nothing; switch off.

## Carded / queued

- Queued: `a-refiled-company-whose-removed-half-has-no-people`.
- Open: `a-coupled-donor-s-part-ref-is-found-through-pub-names`,
  `three-test-pair-kinds-the-registers-cannot-supply`, the mixed views
  card (ruling 114); the review agent's splits and the structure
  questions, held for after the build (rulings 69, 75).

## Next

1. Integrator: merge `fix-links-5`; queue `qv4-links-build`, then
   `python -m links.check` live; read `peak_mb`.
2. Check item 9's second line is red on live, from the data: 35 charities
   carry the NZBN `0000000000000`, and CC58580 and CC61425 share one.
3. House rows before ge-2020 and list-vacancy members find no seat or
   member (the members view's card); 710,322 question rows are older.
