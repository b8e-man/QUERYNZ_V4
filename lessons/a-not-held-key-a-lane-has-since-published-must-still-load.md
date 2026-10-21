When a lane publishes a register the templates name as not held, keep the key loadable and drop it from the blank: ten templates cited `charities` in `not_held`, and removing the catalogue entry would have refused every one of them at load.
area: subject reports, products/report catalogue, products/templates, not-held, charities
paid-for-by: 2026-10-21, fix-report-2, step 5.1

The catalogue's NOT_HELD list is the one place the templates' `not_held`
keys resolve, and the loader refuses a key it does not know. So the day
charities-3 published `pub.charities`, "Charities register and officers"
could not simply come out of the list: ten template.toml files under
`products/templates/` name `charities` in a section's `not_held`, and a
fix session scoped to `products/report/` may not edit them. The fix in
the shape: `catalogue.SUPERSEDED_NOT_HELD` maps the old key to the
register that now holds it; a template naming it loads, the key is dropped
from the section's blank and the not-held list, and the memo says under
"what the walk left out" that the template names as not held a register
that is published and which it does not read. The templates then retire
the key each in its own fix, with no gate red in between. The same holds
for any register the plan lists as not held: `courts`, `insolvency`,
`linz` and the rest are cited by name in the templates today, and each
will be published one day. Add the key to SUPERSEDED_NOT_HELD in the
catalogue's commit, not after.
