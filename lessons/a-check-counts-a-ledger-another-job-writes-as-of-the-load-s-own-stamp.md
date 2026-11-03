A lane check that compares its rows with a ledger another job is still writing counts that ledger as of the load's own stamp, never as of the check's moment.
area: loads, checks, scheduler, courts

Why: on 3 November 2026 the courts load (row 1288) went red with "the pull took 15669 records, the lane has 14528 document rows": the 13:00 MCP pull began two minutes after the load and landed 1,141 records between the build and the check. The own capture (ruling 140) runs 22:00 to 06:00 and the courts load runs at 04:40 by its own clock (a job with a clock may not be queued by another's `then`), so the same race was built in from the first night.

How to apply: take one stamp in the load before it reads the ledger (`SELECT now()` in its transaction), read only what landed by the stamp, write the stamp on every row (`loaded_at`), and let the check read the ledger up to `min(loaded_at)` of the rows it checks (registers/courts load.py and check.py). A ledger with no landing time cannot be checked this way: give it one first.
