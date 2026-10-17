Since the 17 October failover node2's localhost is the PRIMARY, so the old estate's standby-skip guard no longer protects an old test run on node2: a DB-backed old test given a DSN would write a fixture row into a live old database.
area: reference copy, old tests, databases, failover
paid-for-by: 2026-10-18, founding session 2, step 1.2

The old `dbguard.py` turns a write on a read-only standby into a skip; that
is what kept old test runs on node2 harmless. `estate_dsn` carries no default
address, so an old test with no DSN in its environment fails or skips. But
`ops/test_all.sh` sources the credential files from the home folder, and
several old tests carry their own `localhost` defaults.

How to apply: from the reference copy run only tests that touch no database,
and never source the credential files or export a DSN before an old test. A
carried test that writes runs against a scratch schema in `querynz_v4` only
(step 1.2). This stands until node1 is primary again, and then still holds
for a session that sets a DSN by hand.
