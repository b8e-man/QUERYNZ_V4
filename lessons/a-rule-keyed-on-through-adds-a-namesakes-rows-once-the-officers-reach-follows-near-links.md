A template rule that groups an officer's rows by `through` counts a namesake's companies as the officer's own once the reach follows near links: split `near_link` rows out first, or a namesake's failure joins the entity's.
area: subject reports, products/templates, officers reach, near links, the holding chain, property, healthcare, ownership
paid-for-by: 2026-10-22, fix-products-templates-1, step 5.2

fix-report-2 made the officers reach list an officer's near links: a row
the link rules join to the officer by name alone, stamped with the same
`through` as the officer's confirmed rows and marked `near_link`. Property's
`_principals` gathered "every director or holder row whose `through` is a
director of the entity", so the day the shape merged, a namesake's
companies became the director's own. On GORING and KERVIL the serial
pattern fired amber by adding the director's namesake PJO CONSTRUCTION
LIMITED (in liquidation) to the entity's own failure; nothing in the
template had changed. The fix keeps those rows as their own principal,
amber at most, counted apart; the serial pattern now blocks on both.

The same field marks the chain: a director or notice read on a company
above carries `through` (the company's ref) and `above`. Healthcare's
officer-company-notices counted "notices with `through`", so a notice up
the chain would have been an officer's company's. Filter on what a row is
(`near_link`, `above`) before what reached it, and when a shape adds a
reach, grep every template's rules for the fields it reuses
(`filter-a-row-by-what-it-is-not-by-the-route-that-reached-it`).
