Before a guard keys on an environment mark, read what each real caller's environment carries: the worker sets QV4_PIECE only on pieced jobs, no installed unit carries a mark, and a session's terminal carries systemd's INVOCATION_ID.
area: support/db, scheduler, installed units, guards, sessions
paid-for-by: 2026-10-22, fix-support-db-1, the card a-lanes-job-path-published-live-from-a-session-before-the-gate

The brief asked `db.connect` to refuse the owner login on `querynz_v4`
unless the caller carried QV4_PIECE ("set by the worker for every job") or
QV4_INTEGRATOR=1. Read against the code and the installed unit files:
`worker._env` sets QV4_PIECE only when the job is cut into pieces, and
every lane's `load --job` and capture is not; the worker daemon itself and
the board, report, scan and offsite units open the owner login on
`querynz_v4` with no mark at all. Built as written, the guard would have
stopped the scheduler at its next restart. The other obvious mark,
systemd's INVOCATION_ID, is useless here because a Claude session's
terminal runs as a systemd service and has it too. What was safe: refuse
only inside a session (CLAUDECODE set), and accept QV4_RUN_ID, which the
worker sets on every job. Check with `env | cut -d= -f1` in the session
and `grep ^Environment ~/.config/systemd/user/qv4-*.service`.
