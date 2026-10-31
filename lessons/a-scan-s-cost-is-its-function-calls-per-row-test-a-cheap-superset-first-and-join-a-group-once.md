A scan's cost is its function calls per row, not its rows, and a group's join is paid once: test a cheap superset of the fold before the fold, and read a group's keys in one statement that every per-view statement then takes.
area: board, search, dossier, PostgreSQL, timing floors, translate, lower, regex, pub.groups, pub.names, statements per request
paid-for-by: 2026-10-31, fix-products-board-7 (the board's two timing tests sat on their floors and refused five merge gates in a day)

The search scanned 103 views with `translate(lower(concat_ws(…))) ~ '\mword'`
over every row. On the 1.9 million companies, reading the heap took 0.04 s,
the two fold calls 0.37 s more and the regex 0.15 s: the fold was two
thirds of every scan, computed for rows that could never match. A
case-insensitive regex over the text as held, with each vowel a class of
its macron forms (`~* '\mgr[aāĀ][eēĒ]m[eēĒ]'`), finds a superset of the
fold's matches at a third of the cost; "and"-ed beside the exact test the
planner runs it first (fewer function calls) and the fold is computed only
for the rows it lets through. The result set is identical by
construction. The search fell from 1.9–2.0 s to 0.65 s on the box as it
stood, with the readers running.

The dossier of a 30,849-row group joined `pub.groups` to `pub.names`
(30,849 index lookups, 0.08 s) once to count, then once more for every
view's page and every gift view's money: ten times. One statement now
reads the counts and the keys per view and name (`array_agg`), and each
per-view statement takes its keys as an array; the page's statement sorts
keys and dates alone and reads the page's rows by key
(`= any(array(select …))`, so a view built as a union reads each part by
its index), where sorting the whole rows had spilled 34 MB to disk. A
relation matched to a column many far rows share (a member's turns) read
every row to keep one; a lateral `limit 1` per value reads one. 0.85–1.0 s
fell to 0.40 s.

How to apply: before touching a floor, log every statement's wall time and
EXPLAIN the slowest; time the statement with its predicates stripped one
by one (heap alone, then each function) so the cost is named. A cheaper
test that holds a superset is always safe to add in front of the exact
one. A statement that joins the same large set as another statement of
the same request is the one to cut. Pin the number of statements a
request runs with a counting connection in the fast tier, so a statement
per row cannot return unseen. See also
[[a-regex-python-and-postgres-both-run-is-written-in-the-dialect-they-share-and-handed-to-both-by-one-function]].
