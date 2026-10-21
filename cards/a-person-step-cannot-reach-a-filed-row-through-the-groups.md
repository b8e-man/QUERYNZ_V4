# A person step cannot reach a filed row through the groups
kind: finding
state: open
use-case: 9
session: scan-1
opened: 2026-10-21

A scan's person step lands on the rows of the group its row is in
(`pub.groups`, the chains setting "follow"). A filed row (a party-return
donor, a disclosure, a candidate-return donor, an interests entry) is in no
group: the links lane gives it confirmed links to person rows but never
puts it in `pub.groups` (the report's `adopted_group` works around the same
thing). So "which directors are donors" cannot be a person step from a
director row to a donor row; the scan must name a link step by rule
(`by = "link"`, `rule = "full-name@1"`), one rule at a time, and a donor
joined by the address rule is then not on the list.

What the shape needs from the links: either filed rows in `pub.groups`
(gathered by their confirmed links, with the contested flag), or a
published view of (row, group_id) that covers them. Owner: links. The
procurement template (use case 9, donor overlap) is the first that needs it.
