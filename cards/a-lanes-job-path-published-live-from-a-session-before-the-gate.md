# A lane's job path published live from a session before the gate
kind: finding
state: open
use-case: all (the merge gate, step 2.14)
session: founding-f05585e (integrator)
opened: 2026-10-21

Twice on 21 October the merge gate's first run was refused by the board's
live check: views were published and uncatalogued before the gate's
staging step. At sanctions-1 four step 5.3 views stood empty
(`pub.limited_partnerships`, `pub.limited_partnership_partners`,
`pub.building_practitioner_decisions`, `pub.building_practitioners`); at
tenders-1 `pub.award_notices` and `pub.award_suppliers` stood with 29,874
notices and 31,264 supplier rows, the session's own read of the old
estate's files. The lanes' tests publish only into the sample schema, so
the sessions ran the lanes' job path (`load --job`, or `publish` on the
owner connection), which writes `pub.*` on the live database. Nothing
forbids it: the job path has no check that the scheduler is its caller.

Cost: a refused gate run each time (eight minutes), and a catalogue entry
that has to go on the lane's own branch instead of the merge after it (the
lesson `a-lane-s-new-view-is-catalogued-on-the-board-in-the-merge-after-the-lane-s`
assumed the gate publishes first).

Fix (a fix session on `support/jobrun` or each lane's `load.py`): the job
path refuses to run unless the scheduler's worker is its caller (an
environment mark the worker sets), and says so; a session proves a load in
a scratch schema only. Until then: the integrator checks `pub.*` for the
lane's views before the gate and catalogues them on the branch when live.
