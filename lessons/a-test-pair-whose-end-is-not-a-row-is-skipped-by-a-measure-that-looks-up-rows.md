A test pair whose one end is an entity, not a row (a company ref), is skipped without a word by a measure that looks both ends up in `links.rows`: give such a kind its own judge, and report pairs measured beside pairs drawn.
area: links, links/measure.py, links/pairs.py, test pairs, measurement 3
paid-for-by: 2026-10-28, fix-links-1 session (ruling 107)

`m3_rule_error` reads each test pair's two rows from `links.rows` and
`continue`s when either is missing. A donation row's link to a company
names the company by its entity ref (`companies:companies/<key>`), which
`links.rows` does not hold, so a new kind `donor-and-company-not-live`
(63 pairs) would have measured nothing and printed no line for its kind:
a test that cannot fail. The kind is judged with `rules.sole_company` over
`org_names` and the groups as built; the figures show 63 drawn and 63
measured. When a new kind's ends are not both person rows, read the
measure's lookups before trusting its silence.
