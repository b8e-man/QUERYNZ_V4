# house: where it stands

**Date:** 2026-10-20. **Step:** 4.1 and 4.5, candidates, electorates and who
sits in the House, `registers/house/`. **Merge requests:** `house-1`
(merged), `house-2` (raised).

## Done

- house-1: 167 files copied by hash, 28 elections, 216 electorates, 243
  seats, outside check green (the merge record says the rest).
- house-2, the comparison's six cards: 1,615 candidacies (four more: Mana
  and Rongotai 2020's leading two, read from the status page, with the
  winners joined to their seats); `pub.electorates.candidates_held`; the
  reader stamp is `registers.house 2`. Outside check green, now with the
  status page's margins (2020: 70 of 70; 2023: 71 of 71). Catch log: 13
  lines, reconciling. Fast tier: 26 passed.
- Cards closed: `the-house-lane-has-no-result-...`,
  `a-candidate-s-given-name-differs-...`, `the-rebuilt-pages-carry-vote-counts-...`.
  Left open with what they need: `candidacies-the-frozen-site-shows-...`
  (the two 2020 pages), `an-unregistered-party-label-...` (site, with
  candidate-returns), `the-rebuilt-site-splits-one-candidate-...` (links,
  then site).

## Carded, from house-1, still open

- `stats-nz-2025-electorates-need-arthur-s-key`,
  `three-by-elections-and-two-2020-electorate-pages-are-not-held`,
  `who-left-the-house-mid-term-is-not-in-the-results-files`,
  `the-2020-and-2023-party-lists-are-not-held`.

## The one fetch this lane wants (not made)

Mana and Rongotai 2020 result pages (`electionresults.govt.nz/electionresults_2020/electorate-details-20.html`
and `-43.html`). The old job kept only its browser errors for them. Not
fetched: plan 4.1 keeps the old capture jobs the only fetchers until the
switch. The four questions, for that day:

1. Open without getting past a lock: yes. A public page with no login.
   If it shows a challenge, the read has failed and stops (limit 6).
2. Storing it is lawful copying: yes. It is the Commission's official
   result, published for the public, and kept verbatim as a record.
3. Terms accepted: none. No account is used and no terms are clicked.
4. What privacy law or the statute limits: nothing beyond the result
   itself. It carries candidates' names, parties and votes, which the
   Electoral Act requires to be published. No address.

## Next

1. The integrator merges `house-2` and reloads the lane. Then the
   comparison should see `candidacy-missing-on-the-rebuilt-side` fall from
   139 to 128, `old-person-no-result` from 10 to 9, and four `elected`
   figures go.
2. After the switch, or on Arthur's word: fetch the two pages through the
   fetch gate, once.
3. When Arthur's Stats NZ key is in place: capture the 2025 layers once,
   and join 2026's 71 electorates.
