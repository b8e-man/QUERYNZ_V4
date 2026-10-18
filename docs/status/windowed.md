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

- The first capture runs BY DAY, on Arthur's word (19 October, "run the
  capture now, not at 22:00. Use --anytime"): started 19 October by hand
  from the main checkout (merged code, 82b169d), both lanes at once with
  `--anytime` and the catalogue's budgets under `nice 10`; 5 s floor in the
  lane and the gate, one run per lane (advisory lock: tonight's scheduled
  run skips while it holds). Output:
  `/home/user/querynzv4-work/scratch/windowed/capture-2026-10-19/`.
  [ ] tenancy_tribunal  [ ] real_estate_authority

## Next

1. `windowed-1` and `-2` merged (82b169d), catalogue lines in; the nightly capture takes the rest (about
   eleven nights for the Tribunal, three or four for the Authority).
