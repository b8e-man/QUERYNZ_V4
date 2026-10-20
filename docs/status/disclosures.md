# disclosures: where the lane stands

Step 4.1, the large-donation disclosures lane, `registers/disclosures/`.
Session 3, 20 October 2026, node2, Opus, working copy `disclosures-3`.
Merge request `disclosures-3` raised (branch `session/disclosures-3`).

## Done

- 520 declarations, all three regimes, from the Commission's own table;
  catch log reconciles (520 read, 0 set aside from the listing). Nothing
  fetched.
- The 50 with no total read, measured before any change: the page reading
  dropped the "Total amount" box on 49 (31 typed, 18 handwritten, 1 empty
  box); 1 was a bare "$20,000" filtered as boilerplate.
- The total reader now: takes a figure-only line; keeps every figure in
  the box; stops at the next label (an empty box is no total); falls back
  to the scan's typed text layer, never on a page under a full-page
  picture. Form check on all 276 linked: 245 equal, 1 "equal, a second
  figure in the box", 3 differ (each carded), 27 no total read, each set
  aside with hash and pages (stage `form`, ruling 62).
- `check.py`: a difference fails only when no card names it; all four
  (National 2023 and three form differences) are carded. Green on the full
  scratch build.
- The received-date rule is in the spec: a declaration belongs to the year
  of the gift (`given_on`); 8 of 520 were declared in a later year.

## Waiting on others

- The integrator: merge `disclosures-3`.
- The site lane: bucket by `given_on` (`products/published_site/figures.py:84`);
  then 8 comparison differences fall.
- The comparison: correct two cause rules (owner and side), see the cards.
- Arthur: the Commission's word on three declarations ($42,200 box over
  $27,000 of gifts; the May/February link; the 30 June / 30 July date).

## Next

- When a page-reader job is allowed: the 27 set-aside scans (listed in
  `disclosures.set_aside`, stage `form`).
- Take over the old feed only on Arthur's word (step 4.1, step 4.8).
