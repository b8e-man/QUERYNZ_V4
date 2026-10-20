# A Crown entity holding shares is not flagged as the Crown
kind: finding
state: closed
use-case: subject report (5.1); 3 banking; 13
session: banking-1
opened: 2026-10-20
closed: 2026-10-21

HEALTH NEW ZEALAND holds 90 shares in ENABLE NEW ZEALAND LIMITED
(checkpoint subject 11, `societies:societies/9429000000000/officer/d323a6097c2c`);
the walk's `CROWN` pattern reads words such as "the Crown" or "Minister
of", so a Crown entity named by its own name is a company holder, not a
hub, and a board shared through it reads as more than it is. For the report
lane: a list of Crown entities (the Public Service Commission publishes
one), or a column the companies lane derives, read instead of a name
pattern.

Closed 2026-10-21 by the report session (report-3). `walk.CROWN_BODIES`
lists the bodies the Crown holds through by their register names, legal
ending off (the Crown entities of the Crown Entities Act 2004 schedules 1
and 2, the Crown research institutes of schedule 4 and the research
organisations they became in 2025, the State enterprises of the
State-Owned Enterprises Act 1986 schedule 2, the three mixed-ownership
energy companies, Air New Zealand and the Reserve Bank; 130 names as read
on 21 October 2026, a list to refresh when the schedules change), and
`walk.crown_body` flags a holder or an entity so named as the Crown beside
the name pattern. The card's HEALTH NEW ZEALAND holding is flagged. A
fixture test holds the names; `python -m products.report check` takes the
first company a listed body holds shares in, from the tables at run time,
and fails unless the holder is flagged crown. A column the companies lane
derives would replace the list; not carded, since the list serves.
