# bin/fast runs the tests with the system Python in a working copy that has no .venv
kind: finding
state: open
use-case: -
session: scheduler
opened: 2026-10-18

A working copy made by `bin/start-session` has no `.venv`; `bin/fast` fills
the sample through the main checkout's environment but runs pytest with
`sys.executable` (the system Python, no pytest), so `bin/fast support/scheduler`
is RED in 0.0 s. The scope hook refuses a `.venv` link in the working copy.
Fix in `bin/fast` (a main-session edit): fall back to the main checkout's
`.venv/bin/python` for the test run as `fill()` already does. Until then a
session runs `/home/user/querynzv4/.venv/bin/python -m pytest <module> -m "not slow"`.
