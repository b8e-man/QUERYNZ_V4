A mutation check that edits a module and undoes it within one second, at the same length, leaves Python running the mutant from `__pycache__`: touch the file after undoing it, or mutate by a change of length.
area: tests, mutation, python, checks

Why: on 9 November 2026 the insolvency check's `max(s)` was swapped for `sum(s)` with sed, the test run failed as it should, and a second sed swapped it back. Both edits fell in the same second and kept the file's size, and a `.pyc` is trusted by its source's mtime (to the second) and size. The next run imported the mutant: the live count read 15,218 said for 13,498 seen, while the same SQL through `bin/q` read 13,498. `touch` on the file made it recompile, and the count read right. Tests run with `-p no:cacheprovider` still write bytecode.

How to apply: after undoing a mutation, `touch` the file before anything else imports it, or run the check with `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPYCACHEPREFIX` pointed at scratch. When code and SQL disagree with the same query run by hand, suspect stale bytecode before the data.
