# The report walk reads a namesake star one hop, so a spoke sees only the centre
kind: blocker
state: closed
use-case: every template's namesakes section and every Gazette source joined by name (02, 03, 04, 05, 06, 07, 08, 11, 12, 13)
session: fix-products-templates-1
opened: 2026-10-28

`name-only@1` draws one star per first-and-last name: from one anchor row
of each confirmed component to the anchor of the component that sorts
first (`links/build.py` `near_links`). Two spoke components carry no link
between them. `products/report/walk.py` `links_of` reads the links touching
the subject's group rows and stops, so a subject whose group is a spoke
sees one namesake, the centre, and none of the others.

Since the 28 October build the centre is often a row of a view the lane
read for the first time (charity officers, celebrants, building
practitioner decisions), because `building_practitioners:` and
`charities:` sort before `companies:`. The most shared director name: its
centre is a building practitioner decision with 157 spokes (89 director,
40 charity officer, 14 shareholder, 9 celebrant, 3 bankruptcy and 2
society officer components); the subject's group of 360 rows holds one
near link, to that row, which recruitment does not read, so its memo lists
0 namesakes. Of 160 Gazette prohibition rows with a namesake, about 90 are
spokes of a wider star: a memo from another spoke clears `prohibition`
saying "every link from the subject's rows was read", and the notice was
not reachable. None was a prohibition on the name above; the clear is
right by luck there, not by reading.

Also: the anchor of a component is its first row of that name, not its
group id; on a 200,000-link sample 770 `row_a` and 413 `row_b` are not
their group's id. A reader that looks only at the group id misses them.

Wanted, in `products/report/walk.py` (outside the templates' fence): for
each `name-only@1` near link the walk reads, read that other end's group's
`name-only@1` links of the same name key as well (one hop through the
centre), and always pass the group id with the group's rows (the members
limit orders by `row_key` in the database's collation, which need not put
the group id first). Then the namesakes do not depend on which row carries
the centre, as `links/spec.md`'s contract asks.

Closes when: the strict xfail
`test_the_most_shared_name_lists_its_namesakes_whichever_row_carries_the_star`
in `products/templates/08-recruitment/tests/test_recruitment_real.py`
passes (it then fails as XPASS and is unmarked).

Closed 29 October 2026 by fix-products-report-4: the walk follows a name-only star through its centre; all 160 prohibition rows with a namesake are reached from every namesake (70 before); the recruitment xfail lifted at the merge.
