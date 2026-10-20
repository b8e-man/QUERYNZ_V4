# gazette: where it stands

**Date:** 2026-10-20. **Step:** 4.1 and 5.3, Gazette notices, `registers/gazette/`.
**Merge requests:** `gazette-1` to `-3` (merged), `gazette-4` (raised).

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
- `pane.md` covers all nine published views (card closed).
- The parties lane reads this lane's `au` notices (parties-2, merged 20
  October: 137 notices from `pub.gazette_notices`), so the old next item 1
  is done.

## Unread, by use case (recruitment 08, agriculture 04, banking 03, legal 02)

Wanted, carded for the next session: mortgagee entries into possession
(`gn`, 2,953; 03, 04); amalgamations and rectifications (`ot`, ~740; 02,
03). Waiting on Arthur (queue): vehicle confiscation orders (`go`, 6,213)
and disciplinary findings (`gn`, 96). Not wanted by the four: `ln` 25,679
and `lt` 2,637 land (use case 12); the rest of `go` (education licences,
medicines, school agreements, JPs), `au` 7,165 (the parties lane reads 137),
`gs`, `sl`, `cu`, `rs`, `dl`, `vw`, `pb`; `pn` 555 firm partners; `vr`/`ps`
ministers and vacancies (the house lane); `fs` 109 friendly societies.

## Carded

- `mortgagee-entries-into-possession-in-the-gazette-are-unread`,
  `amalgamations-and-the-registrar-s-rectifications-under-ot-are-unread`.
- Left for Arthur's word: `appointment-notices-whose-appointees-run-together-are-unread`,
  `annulled-bankrupts-the-reader-cannot-name-stay-published-on-earlier-rows`.

## Next

1. Mortgagee entries into possession, addresses private (card above).
2. Amalgamations and rectifications under `ot` (card above).
3. Disciplinary findings, if Arthur rules yes.
