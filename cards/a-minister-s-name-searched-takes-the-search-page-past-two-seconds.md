# A minister's name searched takes the search page past two seconds
kind: finding
state: open
use-case: -
session: fix-products-board-1
opened: 2026-10-28

Measured on live, 28 October, the board's search page for "Simeon Brown"
with the entities state on and nothing chosen: 4.9 to 6.2 s (rows state
5.3 s). The dossier is not the cost: opened on the same page it adds
0.7 s. The cost is the search's scan of 99 views (3.1 s, `search._scan`),
the near names (1.6 s, `near._read`), and the results pane's entity
gather (1.4 s, `people.gather`, of which `members_of` 0.6 s reads every
row of the 30,836-row group ruling 116 joined). The live slow tests ran
beside the measurement, so the figures may be high by some share; the
two-second test (`test_a_search_answers_within_two_seconds`) searches
"Graeme Hart" and does not see it.

Owner: board. Measure first without other load; then read the group's
size and label in SQL in `people.gather` as the dossier now does past
`dossier.MANY_AT`, and look at the scan of the speech and question views.
