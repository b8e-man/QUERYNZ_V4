# The procurement lanes' positions, profiles, floors, view and jobs into place
kind: blocker
state: closed
closed: 2026-10-22
use-case: 9, 10; step 6.3
session: procurement-1
opened: 2026-10-22

For the integrator at the merge of `procurement-1` (the merge request lists each step):

1. `contract_disclosures` and `council_procurement` into `support/db` `LANES` (`contract_disclosures` has a
   private twin, made and empty; `council_procurement` none).
2. Three positions to `docs/legal/positions/`: `registers/tenders/position/government-electronic-tenders-listing.md`,
   `registers/contract_disclosures/position/agency-contract-disclosures.md`,
   `registers/council_procurement/position/council-procurement-platforms.md` (each lane's tests look in either place).
3. Two profiles appended (version 1): `acc-health-contract-data-workbook`, `council-procurement-terms-page`.
4. Gate floors: `www.cluthadc.govt.nz` 7 s, `www.tauranga.govt.nz` 5 s, `www.dunedin.govt.nz` 5 s,
   `www.vendorpanel.nz` 5 s. `catalogue.data.govt.nz` keeps its 10 s.
5. Three jobs: `qv4-contract-disclosures-refresh`, `qv4-contract-disclosures-load`, `qv4-council-procurement-watch`
   (each spec's jobs line); before the first refresh, once, `python -m registers.contract_disclosures.capture --copy`.
6. `pub.agency_contract_costs` on the board in the merge after this one (`registers/contract_disclosures/views.md`).

## Closed (integrator, 22 October 2026, the procurement-1 merge)

Every item done at the merge: `contract_disclosures` and `council_procurement`
in `support/db` `LANES` (each with its private twin, as every lane); the three
positions in `docs/legal/positions/`; the two profiles appended (version 1;
the pin is 128); floors for Clutha (7 s), Tauranga, Dunedin and VendorPanel
(5 s); three jobs at priorities 74 to 76, each daily by the clock and gated
by its own 28- or 30-day rule. The copy run and the schema apply follow the
merge; `pub.agency_contract_costs` goes on the board in the merge after.
