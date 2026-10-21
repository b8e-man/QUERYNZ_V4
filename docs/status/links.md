# links: where it stands

**Date:** 2026-10-20, 21:30. **Step:** 4.2 and 4.3, `links/`. **Merge requests:** `links-1` (merged), `review-1` (merged), `links-2` (raised).

## Done (links-2, in `scratch_links_2` on the real published tables)

- Rows: every published register read, nineteen views, 2.88 M rows: Gazette
  bankruptcies (64,741; a withheld name is no row) and appointments, MPs' and
  ministers' expense lines, the companies a member's interests declare
  (4,208 entries, 3,593 organisations), the filing candidates and candidate
  donors, the rows loaded since the morning (454 Part A, 560 candidate
  returns; 18 stale donor keys re-read). A catch log per view; `check.py`
  fails when a lane has loaded rows the links have not read.
- The given name is the first given name whichever field a lane filed it in
  (385 filing candidates and 52,939 bankrupts were keyed apart; 26,294
  director rows gained a middle name).
- Rules: `seat-and-window@1` (23,042 confirmed: a return or expense line to
  the seat whose term covers it); `declared-directorship@1` (434, 86 members'
  returns to their directorships); the amended candidate return as the lane's
  own join; near with a named reason: `company-name@1` 88,819,
  `organisation-name@1` 3,228 (declared companies anchored, 64% to one live
  company), `candidate-name-form@1` 402 (37 under two printings),
  `filed-name@1` 172, `member-and-party-donor@1` 106, `own-return@1` 1.
  Watch: bankrupt-yet-appointing (149). Rule 10: `links.rows --register`.
- 2,815,624 links; 681,618 groups over 2,315,026 rows; 172 hold a seat, 40
  reach a company. Measurements re-run (`measurements.md`); error on
  two-people pairs rare 38.5%, middling 22.0%, common 35.5% (a new draw).
  `check.py` 29 of 29 green in scratch; fast tier 35 tests green.

## Since: coupled-1 (2026-10-21, ruling 73)

`coupled-name@1`: a coupled donor row stays one row and is joined, near, to a
part row per person it names; 37 rows, 74 parts, 74 links in scratch. See
`docs/status/coupled-1.md`.

## Carded / queued

- Closed: bankruptcies-and-appointments, member-and-interests-return,
  same-name-donor-rows, same-name-companies, the stale donor key (site-3's).
  Half: expenses-and-member-to-donor (expenses done; the donor half queued).
  Handed on: interests tree (site draws it), candidate name forms (queue).
- New: `the-name-reading-keeps-a-judges-title-…` (keys).
- Queue: `may-a-registers-own-structure-confirm-a-politicians-row` (default
  yes, as built); `may-a-donation-rows-circumstance-confirm-a-link` (default
  no); `may-one-candidate-under-two-printings-be-one-page` (default no).

## Next

1. Integrator: reload `links` from this branch (`build_all`; `tables.sql`
   adds `rows_catch` and an index), run `check.py` live; drop
   `scratch_links_2` and `scratch_links_2_pub`.
2. House rows before ge-2020 and list-vacancy members find no seat: the
   house lane's (card `who-left-the-house-mid-term…`).
3. Score the review agent again on the redrawn pairs (track C's job).
