Measure a built table against the rule that built it before reporting either: a union-find that never entered its roots left every group's anchor out of links.groups, and only the gap between the rule's count and the built count showed it.
area: links, groups, any table derived by a walk over another
paid-for-by: 2026-10-20, links session, step 4.2 measurement 3

`components()` set `parent[child] = root` and never `parent[root]`, so
`{x: find(x) for x in parent}` had no entry for any root: 670,000 anchor
rows were missing from the groups table while the group counts looked
right. The check that caught it was measurement 3 computed two ways: the
rules applied directly to each test pair said 104 confirmed, the groups
said 9. A single count would have been reported as a 4.5% error rate
instead of 52%. Where a table is derived by a walk, count a sample through
the walk and through the rule, and stop on a difference.
