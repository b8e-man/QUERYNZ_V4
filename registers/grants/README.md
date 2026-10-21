# registers/grants — grants from gaming-machine societies and the Lottery Grants Board

Step 6.3, a source step 6 adds (for use cases 9 and 14). The Department of Internal Affairs publishes every class 4
society's grants, approved and declined, in one national file ("Grants from Gaming Machine Profits", CC BY 4.0), and
the Lottery committees' records of grants as pages on Community Matters. Both are captured verbatim by hash through
the fetch gate under the four questions, read by profile into one row per grant and one per recipient as published,
and checked against the documents' own counts and the Department's own list of societies. A recipient is kept as
printed and never looked up; no address is read.

The 31 societies' own lists (Gambling Act 2003 s 110(4)) are surveyed in `survey.md` and carded by class
(`cards/the-societies-own-grants-lists-by-class.md`): they add 2017 to 2020 and the purpose as printed.

Built by `grants-1`: `spec.md`, `capture.py`, `read.py`, `load.py`, `tables.sql`, `publish.sql`, `check.py`,
`sample.list`, `sample.py`, `pane.md`, `tests/`, the two positions in `position/` and the two profiles in
`profiles-proposed.jsonl` (to move at the merge: `cards/the-grants-jobs-into-the-catalogue.md`).
