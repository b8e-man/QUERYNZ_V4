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
- The first capture ran BY DAY, on Arthur's word ("run the capture now,
  not at 22:00. Use --anytime"), 19 October 08:36 to 13:06 NZDT, by hand
  from the main checkout (82b169d), `--anytime`, the catalogue's budgets,
  `nice 10`, 5 s floor, one run per lane. Both ended on their budget.
  Tribunal: all 37 months listed, 33,500 orders; 3,608 held (3,152 new),
  every order leaving before 1 March 2027; 1 transport failure.
  Authority: 2010 to 2026 listed but 2016 (1 of 22 pages: a reset), 2,881
  cases; 1,226 held, 1,516 PDFs; 5 set aside (3 resets, a 404, the page).
- A year cut short is listed again (`complete_years`): `windowed-3`.

## Half-done

- The rest of the capture, nightly on the scheduler: Tribunal 29,892
  orders (about nine nights), Authority 1,655 cases and 2016's 21 pages.

## Next

1. `windowed-1` and `-2` merged (82b169d), catalogue lines in; the nightly capture takes the rest (about
   eleven nights for the Tribunal, three or four for the Authority).
