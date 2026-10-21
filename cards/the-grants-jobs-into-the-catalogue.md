# The grants lane's schema, positions, profiles and jobs into place
kind: blocker
state: closed
use-case: 9, 14; step 6.3
session: grants-1
opened: 2026-10-21
closed: 2026-10-21

For the integrator at the merge of `grants-1`: add `grants` to `support/db` `LANES` (its `_private` twin holds
nothing); move the two positions from `registers/grants/position/` to `docs/legal/positions/`
(`dia-gambling-and-lottery-grants.md` names `catalogue.data.govt.nz`, which tenders' position names too: one host,
two classes, harmless to the gate); append the two proposed profiles (`registers/grants/profiles-proposed.jsonl`) to
`support/profiles/profiles.jsonl`; set the gate's floor for `www.communitymatters.govt.nz` and `www.dia.govt.nz` to
5 s in `FLOORS` (the catalogue states 10 s itself); put the two proposed jobs in the catalogue as `spec.md` says
(`qv4-grants-capture` nightly 22:45 with a 4 h budget, `qv4-grants-load` nightly 06:35).

Sized from the survey: the national file is one request a month (37.7 MB) and a page; the walk of Community
Matters is of unknown size (its home page links 46 pages of its own), at most about 2,800 pages a night at 5 s,
each page again after 30 days. On 21 October 2026 Community Matters answered 403 to its "ask us" page and the
catalogue served a challenge to a search: the capture asks neither, and a block stops that host for the night.
The check is red until the first walk has read a record of grants and a full file is loaded, as it should be.

Closed by the integrator at the merge of `grants-1` (21 October 2026): `grants` in the lane list with its schema applied on both databases; the two positions in `docs/legal/positions/`; the two profiles versions 1 in the ledger (109 slugs), the proposed file removed; the gate floors `www.communitymatters.govt.nz` and `www.dia.govt.nz` at 5 s; `qv4-grants-capture` (priority 69, 22:45 NZDT) and `qv4-grants-load` (70, 06:35) in the catalogue; the lane's `load.py` carries the staging contract's `load(conn, schema)`. The three board views are catalogued in the merge after this one, once the gate has published them.
