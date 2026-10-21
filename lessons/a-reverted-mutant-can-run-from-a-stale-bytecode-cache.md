A mutant planted and reverted by a same-length edit within a second leaves Python's bytecode cache stale, so the reverted code still runs as the mutant (or the mutant as clean code): run mutant checks with `python -B`, or recompile first.
area: mutant checks, tests, pytest, sed, bytecode, __pycache__, checks that silently pass
paid-for-by: 2026-10-21, scan-templates-1 session, step 6.2

The name step's mutant check swapped `"name"` for `"NAME"` in
`products/scan/lines.py` with sed, ran the test (it failed, as it should),
and swapped it back. The test went on failing on the clean file. Python
keys its cache on the source's modification time to the second and its
size; the revert kept both, so `__pycache__/lines.cpython-314.pyc` still
held the mutant. The same trap runs the other way: plant a same-length
mutant within a second of the last import and the clean bytecode runs, the
mutant "passes", and the check looks like it catches nothing or proves
nothing. `rm -rf __pycache__` is refused by the safety hook; recompiling
the one file (`py_compile.compile` with `cfile=importlib.util.cache_from_source(...)`)
or running with `-B` clears it.
