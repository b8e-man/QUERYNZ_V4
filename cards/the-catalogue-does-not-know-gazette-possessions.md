# The report's catalogue does not know pub.gazette_possessions, so no template can show a lender's entry into possession
kind: finding
state: closed
use-case: 2 legal counterparty; 3 banking director history; 4 agriculture counterparty
session: legal-1
opened: 2026-10-21
closed: 2026-10-21

gazette-5 published `pub.gazette_possessions` (3,002 notices: a mortgagee's
entry into possession of land or goods; `mortgagee_register_key` and
`mortgagor_register_key` join a company lender or borrower to the companies
register). `products/report/catalogue.py` has no View for it, and a
template that names a view the catalogue does not know is refused when
loaded. The legal template's `mortgagee-possession` flag is therefore
always blocked. For the report lane: a View with `on="entered_on"`,
`published="published_on"`, and two pointers from a company (as borrower
and as lender) in `POINTING_AT`; the property and every person's name stay
in `gazette_private`, as the lane keeps them. `pub.company_states` (dated
status rows per file) is also published and unknown to the catalogue.

Closed 2026-10-21 by the report session (report-3). `catalogue.py` now
carries `gazette_possessions` (register gazette, an event; dated by
`entered_on` as "entered" with the publication day beside; the mortgagee
and mortgagor name columns, both companies when printed, a person's name
never leaving the lane's private tables; it sits on the mortgagor's
company) and `walk.POINTING_AT["companies"]` points at it twice, by
`mortgagee_register_key` and by `mortgagor_register_key`, so a company's
report lists the possessions it entered and the ones entered against it.
`company_states` is catalogued too (`the-catalogue-does-not-know-company-states`).
The shape's own template reads both, with the licence stated. Measured:
`python -m products.report check` builds a report on the latest borrower
company with a possession, taken from the tables at run time, and fails
unless the possession is listed, confirmed and dated "entered";
`companies:companies/9429051937737` prints "entry into possession, land …
(entered 15 September 2026; published 18 September 2026)". The legal
template names the view in its reads and unblocks `mortgagee-possession`
(a fix in its folder).
