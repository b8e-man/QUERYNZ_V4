# Two declarations sit in 2023 on the frozen site and 2024 on the rebuilt one
kind: finding
state: closed
use-case: 1
session: comparison
opened: 2026-10-20
closed: 2026-10-20

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

Closed (site-3, 2026-10-20), on disclosures-3's measurement that the frozen
side is right and the owner is site. The site now buckets a declaration by
`given_on` (the gift's year), by `received_on` only where no gift date is
printed (the 2008–2022 declarations itemising several gifts), and every
row shows both dates with the year's basis (`figures.disclosure_year`, the
window filter in `read.py`, the commission gate's SQL). Measured on the
home page's party-years from 2023 against the frozen 2026-10-20T0620: New
Zealand First 2023 $888,141.69 and Labour 2023 $744,672.35 now equal; the
2024 rows ($57,000 and $20,368) are gone; National 2023 stays $23,000
apart under its own card. Before 2023 three party-years moved to their
gift years (Te Pāti Māori 2020/2021, the Greens 2019/2020), where the
frozen shows nothing. The comparison's `declaration-dated-by-the-day-received`
8 → 0. Its cause rule in `checks/comparison.py` still says right new,
owner disclosures; it wants right frozen, owner site: the integrator's edit.
