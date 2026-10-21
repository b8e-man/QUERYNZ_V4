# The chain reach lists the companies above and their holders, and reads neither their directors nor the Gazette on them
kind: finding
state: closed
use-case: 12 property developer due diligence; 13 ownership
session: property-1
opened: 2026-10-21
closed: 2026-10-21

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

Closed (fix-report-2, 2026-10-21). On each company the chain lists
(`walk.chain`, under `chain_companies`), `walk.above_company` reads the
notices pointing at it (`gazette_liquidations`, `gazette_company_notices`,
`gazette_possessions` as lender and as borrower) and its current directors
(`in_latest`, no end filed, under `officer_rows`, the rest counted), each
via the company with the company's grade and reason (near where the hop
was by name), marked `above` at the company's depth; the memo prints "on a
company N up the chain" and counts what was read on the companies above.
They are in the `chain` bucket, so a section naming `chain` and the views
lists them. Fixture test `tests/test_reaches_2.py`; `python -m
products.report check` takes a company holder of record resolved by a
unique name whose own row has a current director (and a liquidation where
one exists among the first forty) and fails if the director, or the
notice, is not listed above at depth 1 with the chain's reason. The
property template's Gazette section and `holding-chain` flag can now read
them (its chain section names `companies` and `shareholders` only, so it
adds the Gazette views and `directors` to a section naming `chain`):
carded in `the-property-template-can-now-read-the-charities-register-and-the-reaches`;
ownership's in `the-ownership-template-can-now-read-the-charities-register-and-the-reaches`.
