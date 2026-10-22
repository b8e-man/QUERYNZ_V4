A lane check the board runs under the session reader cannot count a _private table: the load (owner) writes the count beside its ledger, the reader's run reads that, and the owner's run holds the count to the table.
area: lane checks, the board, private twins, logins

Seen 23 October 2026 on registers/overseas_investment: `check.py` counted
`overseas_investment_private.investments` under `db.READ_KEY`, which has no
grant on a private schema by design, so the board's run died on
InsufficientPrivilege every morning since the lane merged and never
answered. Its tests passed because the fixture connects with the owner
login: verify a board check under the login the board uses. Once it ran,
it found 44 street-shaped values on a view the error had hidden. Test for
it: record the SQL the reader's run sends and assert no `<x>_private.`
reference, and mutate the private branch on to see that test go red. A
table named `…_private` in a readable schema trips the same test: name
the count for what it counts (`read_statements`).
