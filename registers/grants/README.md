# registers/grants — grants from gaming-machine societies and the Lottery Grants Board

Step 6.3, a source step 6 adds (for use cases 9 and 14). The grants each
gaming-machine society publishes under the Gambling Act 2003 (recipient,
amount, purpose, date) and the Lottery Grants Board's published decisions,
captured verbatim by hash through the fetch gate under the four questions,
read by profile into one row per grant and one per recipient as published,
checked against each publisher's own listing count. Recipients are
organisations; a grant to a named individual is kept as the publisher
prints it and never joined to a person's row by this lane.

Built by `grants-1`; `spec.md`, `capture.py`, `read.py`, `load.py`,
`publish.sql`, `check.py`, `sample.list`, `tests/` and the position pages
are its deliverable.
