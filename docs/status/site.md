# site: where it stands

**Date:** 2026-10-20 (site-2). **Step:** 4.4, the published-site shape and
the Follow the Money template, `products/published_site/` and
`products/templates/ftm/`. **Merge requests:** `site-1`, `site-2` (the
detail of each tranche is in `docs/merges/`).

## Done

- Template version 2: 26 pub views; `settled` says which side's rule the
  donor picker, display names and page keys take and why; `page_sections`
  lists every frozen section carried, the person-page ones marked as those
  the queue item would move; `sections_added` names the rebuilt-only keys;
  the known-limits page rewritten.
- Party page: financial statements (party-finance), top donors, leaders
  and rules under `party_window`, donations made to candidates, sitting
  members, coverage; two registrations with one name get two pages.
- Electorate money from the candidate-returns views: 370 of 380 current
  returns join the results by year, electorate and surname; the
  Commission's figure is the headline; no return is "not held", never nil.
- Home page: the frozen's eleven money sections with bases; party spend,
  public money and promoter totals equal the frozen to the cent. Person
  page: list candidacies; the member's interests register returns (real
  property counted, withheld); expenses, exposure and boards "not held".
- Eight gates (two new, each caught a real fault), 55 tests.
- Comparison (never edited), frozen 2026-10-20T0620 against the scratch
  rebuild: 43,062 differences fell to 30,447 (sections not in the template
  10,651 to 266; candidate returns not held 9,618 to 7,077; rebuilt-only
  sections 1,866 to 209; statements 17 to 0). 610 uncarded are the
  comparison's own readers (carded).
- Cards: of the comparison's 18 owned by site, 4 closed, 10 accepted, 4
  open with what each needs; 4 new. Lesson: a section is matched by its key.

## Half-done

- Nothing.

## Next

1. Integrator: merge `site-2`; `qv4-site-build` then builds version 2
   beside the frozen site; `qv4-site-compare` reads it.
2. Arthur: the section queue item; the window (2017 or 2019); party
   boards in or out; the coupled donor names as a class; the real-property
   text (queue, default no).
3. Lanes: candidate-returns to publish the Commission's rows where no
   return is read; house to hold the 2020 and 2023 lists; links to read the
   expenses registers' names; parties on New Zealand Loyal; comparison to
   update its four readers and read `sections_added`.
