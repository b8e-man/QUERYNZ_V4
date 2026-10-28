Read a starred link between the two rows' groups, never the two rows, and count the stored pairs whose groups share no link: a moved centre left 28 of 80 lines with no link to find.
area: products/scan, check.py, plan.py, links, pub.links, pub.groups, name-only, full-name, stars, query plans
paid-for-by: 2026-10-29, fix-products-scan-1 (links rebuild of 28 October, rulings 114 and 116)

The links lane stores `name-only@1` (and `full-name@1`) as stars, with the
centre in the group whose key sorts first. The rebuild switched refs to byte
order, so the centres moved and the scan's read-back went red. Reading a
`name-only@1` link between the rows' groups (`check.link_between`,
`plan.reached`, `plan.STARS`) brings back only the lines where one group is
still the centre: 1 of 30. The other 29 are two leaves (28) or a confirmed
pair whose full-name star moved (1), and the lane holds no link for those.
The brief assumed every red line was a moved centre. Counting direct,
same-group, between-groups and leaf-to-leaf for every stored line showed it
was not, before any claim went into the request.

Two costs on the way. Group reading applied to every rule turned 80 director
lines into 7,586: every confirmed directorship in a donor's group came along.
Keep it to the rules the contract names. Joining `pub.links` on a group
member made the planner hash all four million links and join them to the
groups twice, which ran past the ten-minute limit. A lateral `offset 0`
lookup by one row's key takes 14 s.
