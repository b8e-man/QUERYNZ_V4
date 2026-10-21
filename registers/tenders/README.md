# registers/tenders — government procurement award notices

Step 6.2, template 1's register (use cases 9 and 10). The Ministry of
Business, Innovation and Employment's open-data files of award notices
from the Government Electronic Tenders Service (every award since July
2014, keyed on the supplier's business number where one is given),
captured verbatim by hash as the ministry publishes them, read by profile
into one row per award notice and one per supplier, refreshed on a
schedule and checked against the source's own count. The licence
(CC BY 3.0 NZ) and its attribution travel with every row.

Built by `tenders-1`; `spec.md`, `capture.py`, `read.py`, `load.py`,
`publish.sql`, `check.py`, `sample.list`, `tests/` and the position page
are its deliverable.
