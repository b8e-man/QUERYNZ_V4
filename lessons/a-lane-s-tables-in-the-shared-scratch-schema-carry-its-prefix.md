A lane's tables in a session's scratch schema carry the lane's prefix (load.table with shared=True), even for a one-off full build: an unprefixed set_aside or files collides with another module's table and breaks the whole sample fill.
area: sample, scratch schema, load, measuring
paid-for-by: 2026-10-20, societies session, step 4.1

The session's scratch schema (`scratch_<session>`) is shared by every
module's sample fill. Some lanes (party returns) create unprefixed tables
there with `CREATE TABLE IF NOT EXISTS`, so a table of the same name left by
another lane, with other columns, makes their inserts fail. The safety hook
refuses a DROP from a session, so the mess cannot simply be cleared.

How to apply: build real rows for measuring with `shared=True` into the
scratch schema (or read in memory, which took 3 s for 210,000 rows here),
never with the lane's bare table names.
