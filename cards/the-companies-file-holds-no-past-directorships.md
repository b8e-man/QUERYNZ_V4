# The companies file holds no past directorships, so no director history can clear
kind: finding
state: open
use-case: 3 banking director history; also 5, 7, 12, 13
session: banking-1
opened: 2026-10-20

The published companies view is a snapshot of current roles. Measured on
querynz_v4, 2026-10-20: none of 1,185,805 rows in `pub.directors` carries an
`ended_on`; 9,056 have left the latest file since July 2026 and carry no
end; the 1,066,680 removed companies keep 4,888 director rows and 6,300
holder rows between them (`first_file` runs only from `companies-2026-07`).
So "every company the person has touched, and how each ended" (use case 3)
sees only the companies the person sits on now: a company they left, or
that was struck off with them on it, is invisible, and so is every
liquidation that followed. The banking template fires on what it sees and
blocks every clear over the person's companies (`HISTORY = False` in
`products/templates/03-banking/rules.py`, flag `past-roles`). For the
companies lane: the change history (16 tables, kept since 16 August 2026,
step 5.3) and the business-number interface (step 5.5) are the two routes
plan names; the old estate's bulk history tables and its "was director of"
claims may hold more, to be measured before relying on them. When a view
publishes past roles with their end dates, set `HISTORY = True` there (a
fix in the template's folder) and its tests already cover the clears.
