# links: where it stands

**Date:** 2026-10-21. **Step:** 4.2 and 4.3, `links/` (and `keys/` for the
name reading). **Merge requests:** `links-1`, `review-1`, `links-2`, `fixes-1`
(merged), `coupled-1` (raised; the detail of each is in `docs/merges/`).

## Done

- Rows: every published register read, nineteen views, 2.88 M rows, a catch
  log per view; `check.py` fails when a lane has loaded rows the links have
  not read. The given name is the first given name whichever field a lane
  filed it in.
- Rules: `seat-and-window@1`, `declared-directorship@1` confirmed; near with
  a named reason: `company-name@1`, `organisation-name@1`,
  `candidate-name-form@1`, `filed-name@1`, `member-and-party-donor@1`,
  `own-return@1`. Watch: bankrupt-yet-appointing. Rule 10: `links.rows
  --register`. Live reload 21 October 12:17: 2,815,703 links, 2,315,110
  groups, 5,694 decisions, 2,861,589 names; `check.py` green;
  `CURRENT_WEIGHTS` on the old estate's 2.3 (fixes-1).
- `coupled-1` (ruling 73): `keys.names.joint_parts` names the people of a
  coupled filed name ("Greenlees, Craig & Shayne"); `is_joint_name` takes
  the filed forms it missed and asks the director register's given names
  ("Bread and Roses Auction" is no longer a couple). A coupled donation row
  stays one row (filed name, key, kind) and is read as no one person; a part
  row per person (`<donor ref>#<n>`, `rows.part_of`, `pub.names.part_of`);
  `coupled-name@1`, near, donor to each part. In scratch on the real tables:
  37 coupled rows (party returns 14, disclosures 20, candidate returns 3),
  74 parts, 74 links; parts reached by `full-name@1` 27, `name-only@1` 58,
  `member-and-party-donor@1` 1; 2,815,868 links; `check.py` 29 of 29.
- Track C (`review-1`): the agent scored, applies nothing; ruling 69 holds
  its splits for after the build.

## Carded / queued

- Open: `a-coupled-donor-s-part-ref-is-found-through-pub-names` (report,
  board and site resolve a part ref through `pub.names`; a part's key ends
  `#n`); `the-name-reading-keeps-a-judges-title-…` (keys); the review
  agent's splits and the three structure questions, held for after the
  build (rulings 69, 75; cards).
- Unjudged and left as filed: "Drury & Alo, Rod & Rebecca" (pairing not
  stated), initials ("M and J Patterson"), "Mr & Mrs" forms.

## Next

1. Integrator: reload `links` from main after the `coupled-1` merge
   (`tables.sql` adds `rows.part_of`; `publish.sql` adds `pub.names.part_of`),
   run `check.py` live; `scratch_coupled_1` and `scratch_coupled_1_pub` are
   Arthur's to drop.
2. House rows before ge-2020 and list-vacancy members find no seat: the
   house lane's (card `who-left-the-house-mid-term…`).
3. Score the review agent again on the redrawn pairs (track C's job).
