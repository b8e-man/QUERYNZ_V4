# Overseas investment statements on the view still carry street-shaped text
kind: finding
state: open
use-case: 12
session: fix-registers-overseas-investment-1
opened: 2026-10-23

Hidden until the lane's check could run under the session reader (it was
denied the private twin every morning since the lane merged). Run bare on
`querynz_v4` on 23 October, the check's own street pattern (`check.STREET`)
matches 44 values of `pub.overseas_investment_decisions.investment`: 19
where the reading withheld some addresses and left another street-shaped
span, 25 where it withheld none. Also 2 in `consideration_stated` and 2 in
`overseas_investment_parties.status`. First key 201810074. No value was
read or printed; the counts are by detector only (`read.STREET` and
`read.LEGAL` match none of them, so the reading's withholding and the
check's pattern disagree).

Some may be a company's or a commercial site's address, which may be shown;
some may be a home (hard limit 15). The view listens on the local network
only and nothing feeds the public site, but it is a published table. Next:
a fix session on registers/overseas_investment widens `read.STREET` to the
shapes `check.STREET` catches (or narrows the check where a match is proven
not an address), with the sample's hard cases, and reloads. Owner: the lane.
