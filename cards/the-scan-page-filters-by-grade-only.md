# The scan page filters by grade only
kind: idea
state: open
use-case: 10 tender and award intelligence
session: scan-templates-1
opened: 2026-10-21

Use case 10 reads the award list two ways: for a supplier, every award it
won; for an agency, its awards supplier by supplier. `tender-awards` gives
both in one list of 33,744 lines (one per supplier on a notice), ordered by
the notice; the page pages it 200 at a time and filters by grade only, so
"this agency" or "this supplier" means taking the CSV away. A filter on a
step's title or a carried column (`?award=Kāinga Ora`, `?supplier=…`), and
a sort by it, would let the page answer both. Owner: products/scan.
