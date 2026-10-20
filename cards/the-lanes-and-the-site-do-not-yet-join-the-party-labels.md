# The lanes and the site do not yet join the party labels
kind: finding
state: open
use-case: 1
session: parties-2
opened: 2026-10-20

`pub.party_labels` (parties-2) resolves every party label the other lanes
publish to the registration live on the filing's day or year, by any name
it carried. On the real published tables of 20 October it joins rows the
lanes leave unjoined, and disagrees with none: 2 party returns (Te Pāti
Māori 2021), 53 declarations, 249 candidacies, 12,271 MP expense lines,
7,513 minister expense lines, 1,344 interest returns and 14,449 interest
lines. The disclosures, house, expenses and interests lanes resolve their
labels against the 18 October snapshot of today's 17 parties, so a
renamed or cancelled party's filings join nothing there, and the
comparison sees none of the view's joins until a lane or the site joins on
(`label`, `on`): `on` is the filing's day as YYYY-MM-DD, or its year as
YYYY where the lane keeps only the year.

Owners: party-returns, disclosures, house, expenses, interests (a fix
each: join the view, or call `keys.parties.party_name` with
`pub.party_names` and the day), then site.
