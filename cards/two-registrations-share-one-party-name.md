# Two registrations share one party name
kind: finding
state: closed
closed: 2026-10-20
use-case: 1
session: site-2
opened: 2026-10-20

`pub.parties` holds two registration keys named New Zealand Loyal (`ec-party/2023-08-28/1daf08539f3f`, off the register, with a 2023 financial
statement and a return; and a later one). The site gives each its page: the plain path to the key with most to show, the other suffixed and
cross-listed on both pages (`card.other_registrations_of_this_name`); before that rule a set's iteration order chose which page survived and the
donor rows on it moved between builds (1,097 against 1,093). The question for the parties lane: is this one party re-registered, which the lane's
renamed-party join should say, or two?

Which side is right: unknown until the lane says. Owner: parties.

## Closed 2026-10-20 (parties-2): two registrations, kept apart

The Commission's own notices answer it: New Zealand Loyal was registered
on 28 August 2023 (2023-au4027), its registration cancelled at the
party's request on 26 July 2024 (2024-au3676), and registered again on 5
August 2026 (2026-au4360). By the plan's rule a party cancelled and
registered again is a new registration, so these are two and the lane
does not join them. Each now says so: `pub.parties.same_name_as` names
the other and `same_name_note` gives both windows (likewise United Future
New Zealand, 2001–2013 and 2013–2018). A label joins the one live on the
filing's day or year (`pub.party_labels`): `New Zealand Loyal` 2023 (53
rows) and `NZ Loyal` 2023-12-31 (4) the first, `New Zealand Loyal` 2026
(17) the second; a year in which both were live would join neither and
say why (none today). The site's rule (the plain path to the key with
most to show, the other suffixed and cross-listed) agrees and needs no
change.
