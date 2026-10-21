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

Measured by scan-templates-1 (21 October 2026), which met it as foretold:
the procurement scans (`procurement-directors-donors`,
`procurement-shareholders-donors`) go from a donor row to a director or
shareholder row by a link step of two rules (`full-name@1`,
`name-only@1`; the shape now takes several rules in one step). The links of
those two rules join 718 donor-to-director pairs (88 full-name, 630
name-only); the groups of the director rows they land on hold about 6,000
director rows, so a donor reaches roughly one directorship in eight of the
person it is joined to. The chains setting cannot widen it until filed rows
are in `pub.groups`. On both templates' known-limits pages.
