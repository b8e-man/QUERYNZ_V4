# Two old jobs that no table of 1.4 names: querynz-db-maintenance and querynz-verdict-sync
default: Leave both as they are. `querynz-db-maintenance` (weekly, ANALYZE and a census of the old database) keeps running with the database it serves; `querynz-verdict-sync` (hourly rsync of reviewer verdicts from node1) stays failed until node1 returns, then stops with node1's half of batch 1, because the verdicts belong to the press graph
blocks: Nothing. The baseline names both as candidates; the plan's three tables name neither
recommendation: The default. Stopping the maintenance job would let the old database's planner statistics age under the carve-out that still reads it; the sync job does nothing while node1 is down and its red on the old board is already expected
raised: 2026-10-18 by founding-f05585e (while preparing batch 3)
