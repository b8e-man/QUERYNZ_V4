# charities-a: where it stands

**Date:** 2026-10-21. **Step:** 4.1, the Fable build of the charities reading,
`registers/charities_a/`. **Merge request:** `charities-a` (raised).

## Done

- The reading of every page the capture lists (1,158 pages, 1,142,042 rows,
  5.1 GB of JSON): 46,124 charities (29,263 registered), 589,138 officers
  (367,301 with the register's own end; 4,254 flagged disqualified), 430,437
  annual returns (2,247 of groups; tiers, currency, audit, the financial
  fields in columns and `figures`), 357 groups, 29,739 code rows. Load 69 s
  into `scratch_charities_a_full` (sample database), 586 MB; idempotent per
  listing.
- Catch log 123 lines, every page reconciled (rows = typed + set aside):
  61 returns of no organisation and no group; 24 returns and 6 nameless
  officers of the 5 blank organisation rows; 9 numbers held by two rows
  (the later kept, the other's officers and returns attached); 4 officers
  with no publishable name; 19 officers with a name field withheld (15 a
  date, 4 an address), rows kept.
- Outside check green: the register stated 46,132 on the capture day, the
  build holds 46,124 (−8), within the 221 rows that moved during the pass.
- Tests: 21 fast (14 on invented pages, 7 on the filled sample), 2 slow;
  module fast tier green in 30 s; whole-repository fast tier run.
- Two lessons: birth dates typed into name fields; the feed's own shapes
  (group codes index the keyed sets, numbers on two rows, code Ids per set).

## Half-done

- Nothing.

## Next

1. The integrator: run this build against charities_b's tests and the
   reverse; the comparison lesson; keep one and move it to
   `registers/charities` (the `charities` schema, `pub.charities`,
   `pub.charity_officers`, `pub.charity_returns`); append the profile
   `charities-odata-page`; install `qv4-charities-load` after the capture.
2. Open for Arthur: whether a small charity's address for service (it may
   be a trustee's home) stays shown as the organisation's address, as the
   capture's position says and this build does.
