# Confirmed expense links put every per-category line in a member's report, and the report check fails
kind: finding
state: open
use-case: subject report (5.1); 8 recruitment; every template naming the expense views
session: construction-1
opened: 2026-10-21

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
