# The limited partnerships and Board decisions jobs into the catalogue
kind: blocker
state: closed
use-case: 13 (limited partnerships); 6, 7, 12 (Board decisions); step 5.3
session: sanctions-1
opened: 2026-10-21
closed: 2026-10-21

For the integrator at the merge of `sanctions-1`: move the three positions from the lanes' `position/` folders to
`docs/legal/positions/`; append the five proposed profiles (`profile-proposed.jsonl` in each lane) to
`support/profiles/profiles.jsonl`; set the gate's floor for `www.lbp.govt.nz` to 5 s and for `www.police.govt.nz`
and `scsanctions.un.org` to 10 s in `FLOORS`; put the four proposed jobs in the catalogue as each spec.md says
(`qv4-limited-partnerships-capture` nightly 21:00 never Wednesday, `qv4-limited-partnerships-load` 06:50,
`qv4-building-practitioners-capture` Sunday 23:00, `qv4-building-practitioners-load` Monday 06:40). The sanctions
jobs wait on the held lists. Sized from the proofs: the partnerships' frame is 4,114, at 600 calls a night 5 s
apart, so the whole frame is asked in seven nights (about 50 minutes a night); the decisions list is about 80 pages,
7 minutes a week. Both checks are red until then (the frame not yet asked; no finished pass), as they should be.

Closed by the integrator at the merge of `sanctions-1` (21 October 2026): the three positions are in `docs/legal/positions/`; the five profiles are versions 1 in the ledger (86 slugs); `www.lbp.govt.nz` is floored at 5 s, `www.police.govt.nz` and `scsanctions.un.org` at 10 s; the four jobs are in the catalogue at priorities 53 to 56 with `support.scheduler check` green. One departure from the spec: the catalogue has no weekday field, so `qv4-building-practitioners-capture` runs nightly at 23:00 NZDT (about seven minutes against the list) instead of weekly on Sunday, and its load nightly at 06:40; the limited partnerships capture skips Wednesday itself. Each lane's `load.py` gained the staging contract's `load(conn, schema)`.
