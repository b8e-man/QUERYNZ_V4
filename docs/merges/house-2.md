# house-2: the comparison's six house cards
branch: session/house-2 (pushed; 9c064dd)
session: house-2 (Opus)
raised: 2026-10-20
claims: registers/house/ (read.py, results.py, check.py, tables.sql, publish.sql, load.py, spec.md, pane.md, tests); six cards owned by house (three closed, three left open with what they need); lesson `a-missing-row-is-often-the-same-row-under-another-name-form`; docs/status/house.md

Step 4.1 and 4.5. Nothing fetched; the same 167 held files.

What changed in the lane:
- Mana and Rongotai 2020 (pages 20 and 43) are held only as the old job's
  browser errors. The reader (stamp `registers.house 2`) now reads their
  leading and second candidates from the held 2020 status page: EDMONDS,
  Barbara and HAYES, Jo; EAGLE, Paul and CROSSEN, Teall. Votes are null,
  and each party comes from the year's abbreviation pairing. Each seat's
  `candidate` is joined to its winner. Candidacies 1,611 → 1,615.
- `pub.electorates.candidates_held` (new column) says what a race holds:
  every candidate from the result page; the leading two only, from the
  status page; the nominations; or a by-election's page.
- The outside check adds the status page's printed margins, counted again
  from the result pages' votes: 2020 70 of 70, 2023 71 of 71 (Port
  Waikato's poll was cancelled). A test shows it fails on one wrong vote.
  Every held page's two leaders equal the status page's (no catch-log line).
- `party_basis` on the 135 candidacies with an empty party cell says the
  label as filed is on the candidate's return.

Measured: on scratch, the outside check is green, and the catch log has 13
lines and reconciles. `bin/fast registers/house`: 26 passed. The whole
repository is green except `tests/test_generators.py`, where the card board
is stale from the three closed cards; the integrator regenerates it. A site
was built on scratch from listing 2026-10-20T0620, with only the house
tables swapped, and compared against a baseline built the same way.
House-owned differences: `candidacy-missing-on-the-rebuilt-side` falls from
139 to 128, `old-person-no-result` from 10 to 9, and four `elected` figures
go. The day's total rises by 33: two more person pages (Jo Hayes, Teall
Crossen) now match frozen ones, which surfaces their candidate-return and
template gaps under those lanes' cards.

For the comparison (checks/, not this branch): the rules
`house-lane-lacks-a-result` and `old-person-no-result` point at a card now
closed, and should point at
`candidacies-the-frozen-site-shows-and-the-house-lane-lacks`. That card's
rule also catches 104 figures and 16 pages that are name forms, other given
names or frozen duplicates (counts in the card).

Integrator: merge; reload the lane (the new column needs `tables.sql` as it
is); regenerate the board.

## Result (integrator, 2026-10-20 15:39 NZDT)

Merged into main as aa249fa (merged main first). Done at the merge: the
lesson's rule cut from 248 to 228 characters; records regenerated; the
recruitment-1 record rode along; status and briefs. Fast tier and gate
green; the gate's load and publish: 167 files, 28 elections, 216
electorates, 1,615 candidates, 243 members, 225 figures, 13 set aside. The
comparison's two rules that point at the closed card are the comparison
session's (`comparison-2`, launched 15:45). Arthur's: the two 2020 pages
(Mana, Rongotai) stay unfetched until the switch, as the plan says, with
the four questions answered in the lane's status file; the Stats NZ key.
The session ran headless from the integrator as Opus, about 50 minutes.
