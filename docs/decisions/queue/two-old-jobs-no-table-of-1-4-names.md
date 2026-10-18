# Two old jobs that no table of 1.4 names: querynz-db-maintenance and querynz-verdict-sync
default: Leave `querynz-db-maintenance` (weekly, ANALYZE and a census of the old database) running with the database it serves. Stop and disable `querynz-verdict-sync` (hourly rsync of reviewer verdicts from node1): with node1 out of the plan (ruling 55) it can never succeed, and it fails hourly. Applied under the default on 18 October, with the unit on the stop list first
blocks: Nothing. The baseline names both as candidates; the plan's three tables name neither
recommendation: The default. Stopping the maintenance job would let the old database's planner statistics age under the carve-out that still reads it; the sync job has nothing to sync from
raised: 2026-10-18 by founding-f05585e (while preparing batch 3; default applied the same day)
