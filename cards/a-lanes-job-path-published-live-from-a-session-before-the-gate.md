# A lane's job path published live from a session before the gate
kind: finding
state: closed
use-case: all (the merge gate, step 2.14)
session: founding-f05585e (integrator)
opened: 2026-10-21
closed: 2026-10-22

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

Closed (fix-support-db-1, 2026-10-22): the fence is in `support/db`, not in
the job path, so every caller is covered at once, lanes, links and tools
alike. `db.connect` refuses the owner login on the live database
`querynz_v4` to a session (`CLAUDECODE` in its environment) without a mark,
before psycopg is touched, with one sentence: a session proves a load in
its scratch schema in `querynz_v4_sample` only; the live tables are written
by the scheduler and the merge gate. The sample database and the reader
logins are never refused. Where the marks come from: `QV4_PIECE` and
`QV4_RUN_ID` are set by the scheduler's worker (`support/scheduler/worker.py`,
`_env`; `QV4_RUN_ID` on every job, `QV4_PIECE` only on pieced ones, so the
unpieced `load --job` jobs pass on `QV4_RUN_ID`); `QV4_INTEGRATOR=1` is
exported by the integrator in the shell that runs the merge gate, the
installer, the catalogue commands and its hand runs, and the gate's tests
and staging subprocess inherit it. The installed units are not sessions
and pass without a mark (decision queue:
`whether-every-live-writer-carries-a-mark-or-only-a-session-needs-one`).
Proved on the real credentials from the fix session: owner on `querynz_v4`
refused, owner on the sample and reader on `querynz_v4` connected.
