# The three regulator lanes' schemas, positions, profiles and jobs into place
kind: blocker
state: closed
use-case: 5, 6, 7; step 5.3
session: regulators-1
opened: 2026-10-21
closed: 2026-10-21

For the integrator at the merge of `regulators-1`: add `commerce_commission`, `fma` and `worksafe` to
`support/db` `LANES` (each with its `_private` twin, which holds nothing); move the three positions from the lanes'
`position/` folders to `docs/legal/positions/`; append the eight proposed profiles (`profile-proposed.jsonl` in each
lane) to `support/profiles/profiles.jsonl`; set the gate's floor for `www.comcom.govt.nz`, `www.fma.govt.nz` and
`www.worksafe.govt.nz` to 5 s in `FLOORS`; put the six proposed jobs in the catalogue as each spec.md says
(`qv4-commerce-commission-capture` 22:30, `qv4-fma-capture` 23:00, `qv4-worksafe-capture` 23:30, nightly, each with a
4 h budget; the loads at 06:20, 06:25 and 06:30). Sized from the proofs: the first nights ask about 1,750, 890 and 710
pages, 5 s apart (2.4 h, 1.2 h and 1 h); after the first full pass a night asks the listings once a week and only the
items whose card changed. Every check is red until a full pass is held and read, as it should be.

Closed by the integrator at the merge of `regulators-1` (21 October 2026): `commerce_commission`, `fma` and `worksafe` in the lane list with their schemas applied with grants on both databases; the three positions in `docs/legal/positions/`; the eight profiles versions 1 in the ledger (100 slugs), the proposed files removed; the gate floors `comcom.govt.nz`, `www.fma.govt.nz` and `www.worksafe.govt.nz` at 5 s; six jobs at priorities 61 to 66 (captures 22:30, 23:00 and 23:30 NZDT; loads 06:20, 06:25 and 06:30), `support.scheduler check` green; each lane's `load.py` carries the staging contract's `load(conn, schema)`. The six board views are catalogued in the merge after this one, once the gate has published them.
