Drop many schemas one statement per transaction, never in one DO block: every object stays locked until the block commits, the lock table fills ("out of shared memory") and the whole block rolls back.
area: PostgreSQL, scratch schemas, DROP SCHEMA CASCADE, locks, hand runs for Arthur
paid-for-by: 2026-10-25, integrator (the sample database's 88 scratch schemas)

The first line handed to Arthur dropped 88 scratch schemas in one DO
block. PostgreSQL takes a lock on every object a DROP CASCADE removes and
holds it to the end of the transaction; after about 70 schemas the lock
table (max_locks_per_transaction times the connection count) was full,
the block failed on `scratch_fix_support_scheduler_1` and everything
rolled back, after printing hundreds of NOTICE lines. The second form
worked: one psql selects `format('DROP SCHEMA %I CASCADE;', nspname)` per
schema, piped into a second psql in autocommit, so each drop is its own
transaction. Do this for any hand run that removes many objects.
