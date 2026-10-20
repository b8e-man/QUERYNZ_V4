# Confirmed expense links put every per-category line in a member's report, and the report check fails
kind: finding
state: closed
use-case: subject report (5.1); 8 recruitment; every template naming the expense views
session: construction-1
opened: 2026-10-21
closed: 2026-10-21

`python -m products.report check` reports one problem on 21 October
(seen by construction-1, which changes nothing in `products/report/`):
"house:be-2025-tamaki-makaurau/seat/tamaki-makaurau: an expense row
reached by name is not near with its reason". The member's report now lists
the expense release rows as **confirmed**, through links, and every
per-category line (accommodation, travel, VIP transport) beside the grand
total, where the shape's route 9b lists only totals and money outside the
total, near, by name. The links were reloaded at 09:25 (2.82 M); a links
rule now joins `mp_expenses` rows to a member. For the report lane: take
expense rows from a confirmed link through the same filter as the named
route (totals and outside only), or have the links lane join only the total
rows; then the check is green again.

Closed 2026-10-21 by the report session (report-3). The links lane's
`seat-and-window@1` joins expense rows to a seat as confirmed (22,357
links, measured 21 October), so the rows reach the report as rows of the
seat's own group, not by name. The walk now lists an expense row by the
named route's filter however it is reached (`walk.listable`: a group
member, a link, a name match): the period totals and the money the release
prints outside its total, never a per-category line. The lane's grade is
kept: a row the lane confirmed is confirmed; a row matched by name only
stays near with its reason. Measured: the card's seat
`house:be-2025-tamaki-makaurau/seat/tamaki-makaurau` lists 4 expense rows
(two periods' totals and outside-total money) where it listed 14; route 9b
of `python -m products.report check` fails on a category line by any route
and on a confirmed row that names no rule and is not of the seat's group;
the check is green. A fixture test holds the filter.
