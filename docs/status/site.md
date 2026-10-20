# site: where it stands

**Date:** 2026-10-20 (site-2). **Step:** 4.4, the published-site shape and
the Follow the Money template, `products/published_site/` and
`products/templates/ftm/`. **Merge request:** `site-2` (after `site-1`,
merged).

## Done

- Template version 2: 26 pub views (candidate return totals and donors,
  the interests register's returns and declarations added); `settled` says
  which side's rule the donor picker, the donor display name, the donor,
  person and party page keys take and why; `page_sections` lists every
  frozen section carried, the person-page ones marked as those the queue
  item `which-frozen-sections-belong-in-the-follow-the-money-template`
  would move; `sections_added` names the keys only the rebuilt side has;
  the known-limits page rewritten.
- Party page: financial statements from the party-finance lane, each
  figure cited; top donors, leaders and rules under `party_window` as the
  frozen keeps them; donations made to candidates (committee, branch and
  club names folded by whole-word sets); sitting members with their
  receipts; coverage; two registrations with one name get two
  deterministic pages.
- Electorate money from `pub.candidate_return_totals` and
  `pub.candidate_return_donors`: 370 of 380 current returns join a
  candidate in the results by year, electorate and surname; the Commission's
  figure is the headline with the return beside it; a candidate with no
  return is "not held", never a nil; returns for contests the results do
  not hold (Tauranga 2022) are listed apart; races, year files, the home
  list, person candidacies, donor pages and pickers carry the money.
- Home page: the frozen's eleven money sections (party transfers, race
  donations and spend, party funding, donor categories, party spend, race
  public money, public money, promoter spend, donors sighted) with bases;
  party spend, public money and promoter totals equal the frozen to the
  cent. Parties page: unaffiliated sitting members, junk labels, unmatched
  declarations.
- Person page: list candidacies (2020/2023 list seats from the results,
  the 2026 list with its place); the member's own returns in the interests
  register under the shared reading (positions, withheld real property
  counted, the other categories, every line cited, repeats folded with
  first and last seen); donations made empty with its basis (no group
  spans house and donor registers); expenses, the interests tree, exposure
  and party boards "not held" with why.
- Two new gates that fail on the real tables: statements (the lane
  re-counted by SQL; caught a party with a statement and no page) and
  candidate money (the Commission's figures re-summed by SQL; caught three
  by-election returns no page showed). Eight gates, 55 tests.
- Comparison, run never edited, frozen 2026-10-20T0620 against the scratch
  rebuild: 43,062 differences fell to 30,447. By cause: sections not in
  the template 10,651 to 266; candidate returns not held 9,618 to 7,077;
  sections only on the new side 1,866 to 209; financial statements 17 to
  0; list-only candidacies 67 to 53. Rising by design: citations 11,869 to
  12,423, aggregates 938 to 1,524, the picker 38 to 125, the 2017/2026
  race 803 to 875, candidacies from the results 170 to 251. 610 uncarded,
  all the comparison's own (two new cards).
- Cards: of the comparison's 18 owned by site, 4 closed, 10 accepted with
  the figures, 4 open with what each still needs; a line on the
  candidate-returns lane's card. New: the comparison's readers predate the
  second tranche; a nil return against a blank; two registrations share one
  name (parties); the links have not read the expenses registers or joined
  a member to a donor. Lesson: a section is matched by its key.

## Half-done

- Nothing.

## Next

1. Integrator: merge `site-2`; the daily `qv4-site-build` then builds
   version 2 beside the frozen site; `qv4-site-compare` reads it.
2. Arthur: the section queue item (which person-page sections stay); the
   window (2017 or 2019); party boards in or out; the coupled donor names as
   a class; the interests register's real-property text (queue, default no).
3. Lanes: candidate-returns to publish the Commission's table rows where no
   return is read, and 2017 if kept; house to hold the 2020 and 2023 lists;
   links to read the expenses registers' names and a rule a member's row
   can meet; parties on New Zealand Loyal; comparison to update its four
   readers and read `sections_added`.
