# registers/openlaw — parsed case law from OpenLaw NZ

Step 5.4, item 1. The OpenLaw NZ interface (about 47,000 parsed cases,
mostly High Court, under its arrangement with the Ministry of Justice),
captured record by record through the fetch gate with our own key, landed
by hash, read into one row per case, one row per party and role, the
citation graph and the statute links. A court's suppression order binds
every surface: a suppressed party keeps its row and loses its name.

Built by `openlaw-1`; `spec.md`, `capture.py`, `read.py`, `load.py`,
`publish.sql`, `check.py`, `sample.list`, `tests/` and the position page
are its deliverable.
