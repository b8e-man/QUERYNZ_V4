# Two declarations sit in 2023 on the frozen site and 2024 on the rebuilt one
kind: finding
state: open
use-case: 1
session: comparison
opened: 2026-10-20

New Zealand First: the frozen home page shows $888,141.69 of large
donations in 2023 and nothing in 2024; the rebuilt one $831,141.69 and
$57,000. Labour: $744,672.35 against $724,304.35 and $20,368. In each
case one declaration is bucketed by the day the Commission received it on
the frozen side and by the day the party received the gift on the rebuilt
one, which is the disclosures lane's rule (the lane's own check found 15
of 16 party-years equal before its reload took the received date from the
scans).

Which side is right: the rebuilt one, if the received date it read is
right; the lane should confirm both scans. Owner: disclosures.

## Measured 2026-10-20 (disclosures-3): the frozen side is right; owner site

The direction above is the wrong way round. The Commission's table carries
two dates: it leads with the day the Commission received the declaration
(`received_on`) and prints the day the party received the gift after the
amount (`given_on`). The lane buckets by `given_on`, and its own check
equals the frozen site on 15 of 16 party-years that way, so the frozen site
buckets by the gift too. The rebuilt site buckets by `received_on` first:
`products/published_site/figures.py:84`, `year_of(d.get("received_on") or
d.get("given_on"))`; the same order is in `gates.py:187` and the window
filter in `read.py:95`.

The scans confirm the gift dates: Labour's $20,368 (Hon Pete Hodgson) reads
18-9-23; New Zealand First's $57,000 is two declarations the Commission
received on 23 May 2024, P D Harrison $25,000 (scan 25/08/2023) and
J Marcroft $32,000 (scan grid: $27,000 on 9/8/23 and $5,000 on 30/8/23).

On all 520 declarations held, 8 have a gift year other than the
Commission's year: 5 of the 276 from 2023 on (the three above; NewZeal
$27,000, gift 4 September 2023, Commission 17 July 2024; Freedoms New
Zealand $21,959.25, gift 30 July 2023, Commission 22 April 2024) and 3 of
the 220 from 2011 to 2022. The rule is now in `registers/disclosures/spec.md`.

What it still needs: the site lane to bucket a declaration by `given_on`
(the gift's year), keeping `received_on` beside it; then the comparison's
8 differences under this card fall. The comparison's cause rule should say
`right="frozen"`, `owner="site"`. Nothing changes in the disclosures lane.
