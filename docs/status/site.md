# site: where it stands

**Date:** 2026-10-20 (site-3). **Step:** 4.4, the published-site shape and
the Follow the Money template, `products/published_site/` and
`products/templates/ftm/`. **Merge requests:** `site-1`, `site-2` (merged),
`site-3` (raised; the detail of each tranche is in `docs/merges/`).

## Done

- Template version 3: the donor page key is the display name's own form
  (`paths.name_key`); no published field repeats a links reading; one
  display name is one donor and one page (`figures.fold_by_display`, a row
  the links have not read takes the reading of its exact filed spelling in
  any register); a declaration's year is the gift's (`given_on`), the
  Commission's date only where no gift date is printed, both shown with
  the year's basis; a statement is one line however many files.
- Nine gates: `name-keys` (every key's words are in the name beside it; no
  name field or path carries a residence word; fails version
  2026-10-20T1513 with 43 faults, names files never text). 61 tests.
- Measured against the frozen 2026-10-20T0620, main's code against this
  branch's on the same tables (never the live comparison): 29,511 → 29,336
  differences; `rebuilt-splits-a-donor-across-two-pages` 198 → 0;
  `declaration-dated-by-the-day-received` 8 → 0; donor pages 990 → 928;
  NZ First and Labour 2023 large-declaration totals equal the frozen.
- Cards: the blocker closed on the site's side; two-donor-pages and
  two-declarations closed; statements-by-period accepted; promoter people,
  expense-return reconciliation, interests counts and the aggregate card
  annotated (the lanes'); new for links:
  `the-links-hold-a-donor-key-read-before-party-returns-5-fixed-the-row`.
  Lesson: a key published beside a name is derived from that name.

## Half-done

- Nothing.

## Next

1. Integrator: merge `site-3` after `disclosures-3` (the two-declarations
   card is appended on both branches); `qv4-site-build` then builds
   version 3 beside the frozen site; `qv4-site-compare` reads it. In
   `checks/comparison.py` the two date causes want right frozen, owner site.
2. Arthur: the section queue item; the window (2017 or 2019); party
   boards in or out; the coupled donor names as a class; the real-property
   text (queue, default no); the frozen site's own copy of the residence
   fragment (hard limit 19, his word).
3. Lanes: links to re-read the donor registers after each load (the new
   card); candidate-returns to publish the Commission's rows where no
   return is read; house to hold the 2020 and 2023 lists; parties on New
   Zealand Loyal.
