# site: where it stands

**Date:** 2026-10-30 (site-4). **Step:** 4.4/4.5, the published-site shape
and the Follow the Money template, `products/published_site/`.
**Merge requests:** `site-1`, `site-2`, `site-3` (merged), `site-4`
(raised; detail in its request).

## Done

- Template version 3 and the nine gates (site-1 to site-3).
- Site-4, the two causes of 4.5 that were the template's:
  (1) a Commission row (`read_from` 'commission') cites the spreadsheet
  under its own label with the Commission's figures, or "prints no
  figures"; 675 citations relabelled, none from the empty return columns.
  (2) where the result prints no party, the candidacy shows the label as
  filed on its joined return or the Commission's row (`party_filed_from`,
  `party_filed_basis`), blank with neither; `party_funding` carries such a
  label with its candidates' money only (`registered` false).
- Measured against the frozen 2026-10-30T0617, main's code and this
  branch's built in scratch from its listing: total 28,619 → 28,497,
  uncarded 0, new-side-wrong 5,280 → 5,153.
  `unregistered-label-not-on-candidacy` 106 → 20 (person pages);
  `candidate-returns-not-held` home 311 → 270, donor 1,412, pickers 542,
  subject 919, electorate 3, electorates 2 unchanged;
  `candidacies-from-the-results` +18 (the party figure on candidacies the
  frozen site lacks; ruled neither). 65 tests.

## Half-done

- Nothing.

## Next

1. Integrator: merge `site-4`; `qv4-site-build` builds it beside the
   frozen site. In `checks/comparison.py` the unregistered-label cause's
   owner wants `candidate-returns` (outside this scope).
2. Candidate-returns: 13 Commission rows with a blank party cell where the
   frozen site wrote "Independent"; the template does not infer a label.
3. Arthur: the section queue item; the window (2017 or 2019); party
   boards; the coupled donor names; the real-property text.
4. Lanes: Part A from the scans' readings (ruling 79) for the donor pages,
   pickers and person pages' donations received.
