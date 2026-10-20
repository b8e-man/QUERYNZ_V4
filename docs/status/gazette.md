# gazette: where it stands

**Date:** 2026-10-21. **Step:** 4.1 and 5.3, Gazette notices, `registers/gazette/`.
**Merge requests:** `gazette-1` to `-3` (merged), `gazette-4`, `-5` (merged), `gazette-6` (raised).

## Done

- Capture: every notice the old estate holds as text, exported once
  (207,133 notices, sha256 47de7e09…); typed by the Gazette's section code.
- Read, each its own profile, measured on every notice: celebrant lists,
  prohibitions, liquidations (`al`), removals `ds`, winding-up `aw`,
  receiverships `ar`, creditors `md`, administrations `aa`, bankruptcies
  `ba` (addresses in `gazette_private` only), appointments (3,155).
- gazette-4: overseas companies `cb` (95.4% joined), restorations `ot` (93.1%), society and trust board
  dissolutions `is`/`ct` (98.7%). gazette-5: mortgagee possessions `gn` (3,002 notices, 85.5% of company
  lenders joined; property private); `ot` rectifications (99.7%, people by initials), amalgamations (73.1%),
  transfers out (95.8%), deeds (89.7%). Unread 86,173 → 76,803. Details in `docs/merges/gazette-4`, `-5`.
- gazette-6: every published text cut before a street address or property reference (`cut.py`, at the read; the
  uncut in `gazette_private.uncut`): 1,463 titles (`ln` 1,434), 71 companies, 2 plaintiffs; check fails on any left
  (0 on the full load into `scratch_gazette_6_full`, 1,496 notices on gazette-5's uncut load). Card closed.
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

- Left for Arthur's word: `appointment-notices-whose-appointees-run-together-are-unread`,
  `annulled-bankrupts-the-reader-cannot-name-stay-published-on-earlier-rows`.

## Next

1. Disciplinary findings, if Arthur rules yes.
