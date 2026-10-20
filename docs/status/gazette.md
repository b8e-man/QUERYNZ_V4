# gazette: where it stands

**Date:** 2026-10-20. **Step:** 4.1 and 5.3, Gazette notices, `registers/gazette/`.
**Merge requests:** `gazette-1` to `-3` (merged), `gazette-4` (raised), `gazette-5` (raised; carries gazette-4).

## Done

- Capture: every notice the old estate holds as text, exported once
  (207,133 notices, sha256 47de7e09…); typed by the Gazette's section code.
- Read, each its own profile, measured on every notice: celebrant lists,
  prohibitions, liquidations (`al`), removals `ds`, winding-up `aw`,
  receiverships `ar`, creditors `md`, administrations `aa`, bankruptcies
  `ba` (addresses in `gazette_private` only), appointments (3,155).
- gazette-4, three new kinds in `company_notices`, profiles proposed in
  `profile-proposed.jsonl`: overseas companies leaving NZ `cb` (2,601 of
  2,607 notices, 95.4% joined); restorations `ot` (868 of 888, 31,515 rows,
  93.1%; the applicant and address never read); society and trust board
  dissolutions `is`/`ct` (1,697 of 1,813, 33,749 rows, 98.7% by the
  register's own number, 90.2% agreeing by name). Check floors 92/90/95%,
  name agreement 85%. Full load 92 s into `scratch_gazette_4_full`
  (sample database); the check exits 0. Unread fell 86,173 → 80,865.
- gazette-5 tranche 1, mortgagee entries into possession (`gn`): `possessions.py`, proposed profile
  `gazette-mortgagee-possession`, `pub.gazette_possessions`, private `possession_details`. 3,002 notices,
  2,899 lender named, 2,951 day, 2,449 of 2,864 company lenders joined (85.5%); floors 95/95/82%. Full load
  101 s into `scratch_gazette_5_full`; the check exits 0. Unread 80,865 → 77,863.
- gazette-5 tranche 2, `ot` (`companyacts.py`, four proposed profiles): rectifications 486 of 503
  notices, 2,877 rows, 99.7% joined, 85.1% by name, people by initials only; amalgamations 369, 1,000
  rows, 73.1%; transfers out 167, 95.8%; deeds 21, 89.7%. Unread → 76,803. Both cards closed.
- `pane.md` covers all ten views.
- The parties lane reads this lane's `au` notices (parties-2: 137).

## Unread, by use case (recruitment 08, agriculture 04, banking 03, legal 02)

Wanted and not yet read: none of the carded sections. Waiting on Arthur (queue): vehicle confiscation orders (`go`, 6,213)
and disciplinary findings (`gn`, 96). Not wanted: `ln` 25,679
and `lt` 2,637 land (use case 12); the rest of `go` (education licences,
medicines, school agreements, JPs), `au` 7,165 (the parties lane reads 137),
`gs`, `sl`, `cu`, `rs`, `dl`, `vw`, `pb`; `pn` 555 firm partners; `vr`/`ps`
ministers and vacancies (the house lane); `fs` 109 friendly societies.

## Carded

- `published-gazette-titles-can-carry-a-street-address` (gazette-5: `ln` 1,642, 57 elsewhere).
- Left for Arthur's word: `appointment-notices-whose-appointees-run-together-are-unread`,
  `annulled-bankrupts-the-reader-cannot-name-stay-published-on-earlier-rows`.

## Next

1. Cut every published title before a street address (card above).
2. Disciplinary findings, if Arthur rules yes.
