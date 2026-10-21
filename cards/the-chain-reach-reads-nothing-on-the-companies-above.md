# The chain reach lists the companies above and their holders, and reads neither their directors nor the Gazette on them
kind: finding
state: open
use-case: 12 property developer due diligence; 13 ownership
session: property-1
opened: 2026-10-21

The brief for template 12 asks for the Gazette on the entity and the
companies above it. `walk.chain` returns each company above with its
holders of record, and runs no `pointing_at` and no `roles_on` on it, so a
liquidation, a removal or a mortgagee possession on a parent company, and
its directors, are not in the report. The template's Gazette section says
"the Gazette on the companies above in the holding chain is not read" and
`holding-chain` tells the reader to start a report from each.

For the report lane: on each chain company, the notices pointing at it
(gazette_liquidations, gazette_company_notices, gazette_possessions) and
its current directors, with the chain item's grade, under the chain's
company limit.
