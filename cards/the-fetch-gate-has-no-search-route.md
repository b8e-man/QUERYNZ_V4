# The fetch gate has no search route
kind: finding
state: open
use-case: -
session: review
opened: 2026-10-20

Track C's review agent may search the web only for evidence that two rows
are different people, with a name and a public role at most (hard limits
12 and 26), through the fetch gate, citing only pages fetched in that run.
`support/fetchgate` gates a URL (`open_url`): a search query has no route.
The old estate's `webtools.py` sent the query to DuckDuckGo's lite page
itself, robots-checked by hand. What `support/` needs, for the integrator or
a support session: a `search(query)` route in the gate that (1) takes one
string and refuses any with a digit (an address or a number is never a
query), (2) sends it to one search host under the gate's own decision,
floor and ledger, with a legal position on file for that host, (3) returns
title, URL and snippet rows, and (4) logs the query text in the gate's
ledger so hard limit 12 can be audited. Until then no reading searches;
`links/review.py` carries `web_query()` and `cite_check()` (tested) and
`search()` raises naming this card. The agent's measured figures are from
the registers alone.
