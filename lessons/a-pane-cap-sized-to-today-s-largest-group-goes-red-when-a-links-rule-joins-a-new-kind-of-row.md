A pane that gathers a group's rows under a cap sized to today's largest group goes red the night a links rule joins a new kind of row: count by view in SQL past a line, read a page of each view, and let the check hold each count apart.
area: board, dossier, links, measuring, outside checks
paid-for-by: 2026-10-28, fix-products-board-1, ruling 116

The dossier read every row of a group under `people.PANE_ROWS = 1500`,
sized to the largest live group (1,220 rows). Ruling 116's
member-on-the-day@1 joined written questions and speech turns to the
sitting member, and one minister's group became 30,836 rows. Gathering
them whole took 4.4 s and a 58.7 MB page; the cap made the check red.
Past `dossier.MANY_AT` the dossier now counts views and names in SQL,
reads 50 rows a view, and the check compares each view's count on the
page with its own count of the group's rows. The fixture mutation that
drops a view stayed green until the check held each view to its own
suppressed count rather than the group's total.

Two smaller things: a computed view (mp_expenses) is planned badly
through a join to pub.groups (0.20 s for 147 rows); read its keys first
(0.02 s). The same key-first read is slower for 29,365 rows, so choose
by the count.
