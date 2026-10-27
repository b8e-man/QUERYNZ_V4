A lane check the board times never scans every row of a growing table: the load runs the whole scan and stamps it with row count and load time; the check holds the stamp to the rows it sees and re-scans a fixed sample.
area: lane checks, the board, module-checks, published views, address flags, parliament
paid-for-by: 2026-10-28, fix-registers-parliament-1 (1d), the board red every night for "no answer in 120 s"

registers/parliament's check ran a Postgres regular expression over every
text column of its three views: 1 min 55 s to 2 min 18 s on 683,524 written
questions and 8,836 long archived pages, past the 120 s checks/module_checks.py
gives a check. The red said nothing about the data. The whole scan moved into
the load (`load.stamp_scan`, after the views refresh, 99 s) and writes
`street_scan`; the check (36 s) fails when a text column has no stamp line,
when the stamp's rows or `loaded_at` differ from the view's (a stamp from
another load), or when the stamp found anything, and re-scans the first
5,000 rows by md5 of the key. A test records the SQL the check sends and
fails if the pattern runs unbounded. Before choosing "scan only the rows
loaded since", check the load does not rebuild every row each night: this
one does, so every row is new every night.
