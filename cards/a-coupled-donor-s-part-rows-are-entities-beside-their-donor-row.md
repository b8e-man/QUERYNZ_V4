# A coupled donor's part rows are entities beside their donor row
kind: finding
state: open
use-case: board (4.9), dossier (ruling 110)
session: links-4
opened: 2026-10-30

Ruling 73 keeps a donation filed as two people ("Craig & Shayne
Greenlees") as one row and gives it a part row per person, each joined to
the donor by `coupled-name@1`, which is near. Ruling 123 makes every row of
`pub.names` in no group a single-row entity, so on live the 80 part rows
are 17 grouped (a part confirmed to a director or candidate) and 63 lone,
and each lone part is an entity beside the donor row's own entity. A
reader listing entities sees the coupled donation three times: the filing
and its two halves. The count in the brief (1,872,249 lone rows) includes
them, so the build keeps them; whether a part row in no group should be
folded under its donor's entity (one entity of three rows, `part_of`), or
left as the ruling says, is for the board's reading of ruling 110. Not
worked. Owner: links, with the board.
