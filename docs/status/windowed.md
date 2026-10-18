# windowed: where track E stands

Session 2, 19 October 2026, node2, started in its working copy (fence:
windowed scope).

## Done

- Session 1's tree (18 October) is committed on `session/windowed`: both
  legal positions (`docs/legal/positions/tenancy-tribunal-decisions.md`,
  `real-estate-authority-decisions.md`), both lanes (capture through the
  gate and the landing wrapper, tables, check, spec, pane), their tests,
  the cards, the lesson, two queue questions. Fast tier: both lanes green;
  the one red is the generated card board, rebuilt at the merge.

- Landed 19 October through `support.docstore.landing.land` (fetch times
  of 18 October kept, every hash re-verified): 621 documents. Tribunal: 2
  listings, 1,307 orders listed, 456 held (every order leaving through
  1 November). Authority: 9 listing pages (2023), 84 cases listed, 52
  Committee decisions held (52 abstracts, 102 PDFs). Rows in the lane
  tables in `querynz_v4`, so the nightly run never fetches them again.

- One run of a lane at a time (advisory lock) and an answer from another
  host stops the run: `windowed-2`, pushed (70ff303).

## Half-done

- Tonight's capture, by hand (ruling 56; the catalogue lines wait on the
  merge): at 22:00 NZDT 19 October, from this working copy, both lanes at
  once with the catalogue's commands and budgets under `nice 10`; output
  to `/home/user/querynzv4-work/scratch/windowed/capture-2026-10-19/`.
  [ ] tenancy_tribunal  [ ] real_estate_authority

## Next

1. `windowed-1` raised on `session/windowed`; the integrator merges it and
   adds the two catalogue lines; the nightly capture takes the rest (about
   eleven nights for the Tribunal, three or four for the Authority).
