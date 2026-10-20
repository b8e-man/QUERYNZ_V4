"""The subject-report shape (plan step 5.1): one builder, parameterised by a
template.

It starts from one row, named as the board names a row (`<register>:<key>`,
for example `party_returns:<hash>/A/3` or `companies:companies/9429037782269`),
walks confirmed links outward through `pub.links` and `pub.groups` and lists
near links beside them with their reasons, fills the template's sections from
the published views the template names and nothing else, applies the
template's rules and flags, cites every statement, says "none found" or
"not held" for every blank, and prints as a memo.

Pieces: `catalogue` (how each published view's rows are titled, dated,
cited, which columns are names), `db` (the three connections), `rows` (one
row by its ref; title, dates, citation, statement), `walk` (the group, the
confirmed and near links, the entities and the people on them, the hubs),
`template` (a folder holding `template.toml` and an optional `rules.py`),
`build` (the report), `rules` (the presentation rules, checked on every
report), `memo` (text and HTML), `server` (port 8440, the local network
only), `state` (saved reports, only ever added to), `check` (the outside
check against the real tables).

Presentation rules, from the plan: every connection is dated or marked
undated; hubs are flagged (professional directors, nominees and trustees,
the Crown, an address with a thousand companies); a nominee is never shown
as an owner, a role is shown as the register states it; coincidence is never
joined to cause; absence is not a finding: "none found in the registers
held" is the most a report says. No home address and no suppressed name on
any surface (hard limits 15 and 16)."""
