# registers/courts — court judgments, by caption

Step 5.4, items 2 and 3. The judgments the estate holds (courtsofnz, the
district courts, the Waitangi Tribunal's PDFs), read deterministically by
a profile per court format into one row per judgment and one row per
party and role, with the suppression lever that withholds a name on every
surface and is never undone by a command. The research note on how legal
documents are structured is `docs/research/legal-documents.md`.

Built by `courts-1`; `spec.md`, `read.py`, `load.py`, `publish.sql`,
`suppress.py`, `check.py`, `sample.list`, `tests/` and the position page
are its deliverable.
