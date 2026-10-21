# The not-held list has no key for the registers a property developer check names, and the catalogue cannot reach the charities views
kind: finding
state: closed
use-case: 12 property developer due diligence
session: property-1
opened: 2026-10-21
closed: 2026-10-21

The property template (`products/templates/12-property/`) must say it
cannot see the Overseas Investment Office's decisions, building consents
and council minutes, and the Real Estate Authority's decisions.
`catalogue.NOT_HELD` has no key for any of them, and a section that names
an unknown key is refused when loaded, so today they are named only in the
not-held section's text and in three blocked flags (`overseas-investment`,
`building-consents`, `real-estate-authority`), and the memo's "not held"
list and a blank cannot carry them. Land titles (`linz`), courts,
securities and insolvency have keys and are used.

For the report lane: add `oio` ("Overseas Investment Office decisions"),
`building_consents` ("Building consents, code compliance certificates and
council minutes") and `rea` ("Real Estate Authority decisions") to
NOT_HELD. The Real Estate Authority capture lane exists and publishes no
view; the key says not held until it does.

Second ask, the same as healthcare-1's
`the-report-cannot-reach-the-charities-register`: a developer often sits
behind a trust, and where that trust is a registered charity the template
would read `pub.charities` and `pub.charity_officers` (charities-3, not
merged). The catalogue knows neither, so the template names the Charities
Register as not held. When both land, the fix in the template folder: the
three keys in the not-held section's `not_held`, the two views in `reads`
and the principals section, and the three blocked flags' text pointing at
the keys.

Closed (fix-report-2, 2026-10-21). `oio`, `building_consents` and `rea`
are in `catalogue.NOT_HELD` with the wording above; the Real Estate
Authority key says not held until its lane publishes a view. The second
ask is closed with `the-report-cannot-reach-the-charities-register`: the
catalogue knows `pub.charities`, `pub.charity_officers` and
`pub.charity_returns`, a company's charity is reached by business number
and a person's namesake officer rows by name; a template that still names
`charities` as not held loads, and its memo says the register is published.
The property template's fix (the three keys in `not_held`, the two views in
`reads` and the principals section, the flags' text) is carded in
`the-property-template-can-now-read-the-charities-register-and-the-reaches`.
