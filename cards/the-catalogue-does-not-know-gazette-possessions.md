# The report's catalogue does not know pub.gazette_possessions, so no template can show a lender's entry into possession
kind: finding
state: open
use-case: 2 legal counterparty; 3 banking director history; 4 agriculture counterparty
session: legal-1
opened: 2026-10-21

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
