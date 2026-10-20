# bin/fast runs the system Python in a working copy without a .venv
kind: finding
state: closed
use-case: 0
session: gazette
opened: 2026-10-20
closed: 2026-10-20

In the gazette working copy `bin/fast registers/gazette` stopped at once with
"No module named pytest" and reported RED in 0.0 s: `main()` falls back to
`sys.executable` when the working copy has no `.venv`, while `fill()` falls
back to the main checkout's `.venv`. The same fallback in `main()` fixes it.
Worked round by running the main checkout's venv directly. Outside this
session's folder: the integrator's.

Closed 2026-10-20 by the integrator with its twin from 18 October
(`bin-fast-falls-back-to-the-system-python-in-a-working-copy`): the same
fallback as `fill()` is now in `main()`.
