# Financial statements are not yet on the party page
kind: finding
state: closed
use-case: 1
session: comparison
opened: 2026-10-20
closed: 2026-10-20

The party-finance lane publishes financial statements and the template
reads them, but the rebuilt party page shows `financials` as "not held";
the frozen party page lists each statement with its period, auditor and
opinion. Today: 17 party pages. The site's status names this as next.

Which side is right: the frozen one. Clears when the party page shows the
statements. Owner: site.

Closed (site-2, 2026-10-20). The party page lists every statement the party-finance lane publishes, newest first, the six figures each cited to the
statement document; the statements gate re-counts the lane by SQL and failed once on the way (New Zealand Loyal, a statement and no page, so a party
with a statement now always has a page). Measured by `python -m checks.comparison run` against the frozen 2026-10-20T0620, rebuilt in scratch:
17 differences fell to 0.
