# The limited partnerships and Board decisions jobs into the catalogue
kind: blocker
state: open
use-case: 13 (limited partnerships); 6, 7, 12 (Board decisions); step 5.3
session: sanctions-1
opened: 2026-10-21

For the integrator at the merge of `sanctions-1`: move the three positions from the lanes' `position/` folders to
`docs/legal/positions/`; append the five proposed profiles (`profile-proposed.jsonl` in each lane) to
`support/profiles/profiles.jsonl`; set the gate's floor for `www.lbp.govt.nz` to 5 s and for `www.police.govt.nz`
and `scsanctions.un.org` to 10 s in `FLOORS`; put the four proposed jobs in the catalogue as each spec.md says
(`qv4-limited-partnerships-capture` nightly 21:00 never Wednesday, `qv4-limited-partnerships-load` 06:50,
`qv4-building-practitioners-capture` Sunday 23:00, `qv4-building-practitioners-load` Monday 06:40). The sanctions
jobs wait on the held lists. Sized from the proofs: the partnerships' frame is 4,114, at 600 calls a night 5 s
apart, so the whole frame is asked in seven nights (about 50 minutes a night); the decisions list is about 80 pages,
7 minutes a week. Both checks are red until then (the frame not yet asked; no finished pass), as they should be.
