# The two settlements lanes' schemas, positions, profiles, floors and jobs into place
kind: blocker
state: closed
closed: 2026-10-22
use-case: 14; step 6.2 template 3
session: settlements-1
opened: 2026-10-22

For the integrator at the merge of `settlements-1` (the merge request lists
each step): `iwi_directory` and `settlement_commitments` into `support/db`
`LANES`; the two positions from each lane's `position/` to
`docs/legal/positions/`; the six profiles appended; gate floors 5 s for
`www.tkm.govt.nz` and `tehaeata.govt.nz`; three jobs into the catalogue
(`qv4-iwi-directory-capture`, `qv4-iwi-directory-load`,
`qv4-settlement-commitments-watch`); the three `pub.iwi_directory_*` views
catalogued on the board in the merge after this one. Until the first walk
(about 240 pages, 20 minutes, off-peak) the iwi directory's checks are red,
correctly.

## Closed (integrator, 22 October 2026, the settlements-1 merge)

Every item done at the merge: both lanes in `support/db` `LANES`; the two
positions in `docs/legal/positions/`; the six profiles appended (version 1
each; the pin is 126); floors 5 s for `www.tkm.govt.nz` and
`tehaeata.govt.nz`, nothing for `www.whakatau.govt.nz`; three jobs in the
catalogue at priorities 71 to 73. The catalogue has no weekday field, so the
capture is due daily at 22:30 NZDT and relies on its own week guard and
off-peak window (a day that is not due costs no request), the load is daily
at 06:35 NZDT and loads nothing when the walk is the one published, and the
watch is weekly by interval, which lands on Thursday 13:00 NZDT (one
request). The `pub.iwi_directory_*` views go on the board in the merge after.
