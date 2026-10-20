Filter a row by what it is, never by the route that reached it: a row the links lane confirms arrives as a group member, and a filter on the link route left every per-category expense line in the memo unchanged.
area: subject reports, products/report, the walk, links, groups, expenses
paid-for-by: 2026-10-21, report session 3, step 5.1

The card said expense rows reached the member's report "through links",
so the first fix filtered `link_item`, the route that turns a pub.links
row into an item. The render showed the same fourteen category lines.
The rows were not link items: a confirmed link puts both rows in one
group, and the walk lists a group's rows as members, a route the filter
never touched. The fix that held is one predicate on the row
(`walk.listable`: an expense row is listed only as a total or money
outside the total) applied wherever a row becomes an item, members, links,
the officers' groups and the named route alike. Two things to carry: when
a lane publishes a new link rule, the rows it joins change route (from a
name match to a group member) and every filter keyed on the old route
goes quiet; and a check that reads the memo (the check's route 9b read the
grade and the role of what was printed) catches it, where a test of the
route alone would have passed.
