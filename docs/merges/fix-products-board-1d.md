# fix-products-board-1d: name order per view, ruling 85
branch: fix/products-board-1 (pushed, 629b3ac; one commit on a592258)
session: fix-products-board-1 (Opus, fix, scope products/board/; fourth use of the name)
raised: 2026-10-26 (written to the session's scratch folder: the fence refused the inbox link)
claims: products/board/ (catalogue.py, search.py, near.py, check.py, spec.md; tests test_fields.py, test_near.py,
test_real.py); lessons/read-a-name-column-s-printed-form-before-declaring-its-order.md; docs/status/board.md.
No card opened or closed.

## What it does

1. **An order on every Name, as data.** `catalogue.Name.order` is one of `parts`, `given-family`, `family-given` or
   `ambiguous` (`catalogue.ORDERS`). The reason sits beside each in a comment. The sources were the lane's pane.md and
   spec, its reader (`house/read.py`, `mp_interests/read.py`, `expenses/read.py`), and the register's printed form.
   The printed form was measured per column by aggregate counts (rows with a comma, where the capitals sit), then a
   handful of public rows. Where none of them states the order, the Name is `ambiguous`.
2. **The name fields read by that order** (`search.name_patterns(field, value, order)`):
   - A comma reads family then given in every view.
   - With a stated order, each field matches its own place. The last name is the family place. The first name is
     the first given place. A middle name is any other given place.
   - `ambiguous` with no comma: a first or last name matches any word. A middle name matches any word but the first,
     in a name of three or more words.
   - `parts` views are matched column by column, as before.
   - Honorifics come off the front. Post-nominals come off the end (keys.names' `_POST`, through `fold.py`).
3. **Near matches** (ruling 83). The reversed-name class reads only Names in `catalogue.STATED`. An ambiguous view is
   never read for it. A `family-given` name with no comma reads its first word as the family (`near.as_read`).
4. **The live check, case 9.** Every Name declares an order. The donor rows filed MILLS PHILLIP are among the exact
   results for first Phillip, last Mills, are not under Near matches, and are shown above the Near matches section.
   It replaces board-3's "MILLS PHILLIP under Near matches and not exact".

## Live figures, first Phillip, last Mills

| | before | after |
| --- | --- | --- |
| party_return_donors, exact | 8 | 10 |
| Near matches, names (all registers) | 2 (both party_return_donors) | 0 |
| all registers, exact | 48 | 50 |

## Checked

- `QV4_INTEGRATOR=1 bin/fast products/board`: green (41.8 s).
- `python -m products.board check`: green against the live pub (24 s).
- Slow tests (`-m slow`): 8 passed. `test_near_matches_render…` now uses first James, last Taylor. That query has 84
  reversed rows in directors and shareholders, so the near section still shows a reversed class. It also holds that
  Mills is exact and has no reversed row.
- Each new test was shown failing against mutants applied in memory (scratch `mutant_plugin.py`):
  - With board-3's rule put back: the ambiguous test fails ("Mills Phillip" and "Phillip Mills" both exact), and so
    do the given-family "first is the first word" and "last is the end" tests and the family-given test.
  - With the reversed class reading every Name: the ambiguous-near-empty test fails.
  - With the comma ignored: the comma test fails.
  - With a stated order read as ambiguous: the given-family "Phillip Mills not matched by last Phillip" test fails.
  - With a family-given name read given-first: the family-given near test fails.
  - The live check goes red on board-3's rule (2 of 2 rows not exact; under Near matches; not shown exact). It also
    goes red with the donor's order removed.
  - Board-3 already read a comma as family-first and kept a given-first surname off the first word. So the comma test
    and the given-family last-name test pass against board-3 itself, and fail only against their mutants.

## For the integrator

1. Copy this file into `inbox/merge-requests/` (the session's fence refused the link).
2. Merge, then **restart `qv4-board`** at the release (expected: catalogue.py, search.py, near.py and check.py
   changed). No table, unit or other module changes. No `state` run.
3. **Rebuild `lessons/INDEX.md`** at the merge (`bin/lessons-index`): one new lesson. No card, so `docs/board.md`
   is unchanged.
4. **For the lanes to mirror in their pane.md** (each view's name order, as the board now reads it):
   - parts: directors, company_lookup_roles, society_officers, charity_officers, candidate_return_totals,
     candidate_return_donors (given_names + surname), gazette_celebrants, gazette_bankruptcies (given_names +
     surname), limited_partnership_partners
   - given-family: shareholders.name (the Companies Office's full_name); minister_expenses.name and .member;
     gazette_prohibitions.name, gazette_liquidators.name, gazette_practitioners.name, gazette_appointments.name;
     candidates.display_name, members.display_name; mp_interest_returns.name and .member, mp_interests.name and
     .member; party_board_roles.name and .name_as_declared
   - family-given: candidates.name, members.name (the Commission's "SURNAME, Given"); mp_expenses.member (the
     workbook prints the surname first, with or without a comma); gazette_bankruptcies.also_known_as
   - ambiguous: company_lookup_holdings.name; promoter_expense_returns.promoter, promoters.promoter,
     promoter_people.name, promoter_expenses.promoter; candidate_return_donors.donor; disclosures.donor_name,
     disclosure_items.contributor; mp_expenses.name; gazette_prohibitions.also_known_as, gazette_possessions
     .mortgagee and .mortgagor; parties.secretary; party_return_donors.donor, party_return_loans.lender;
     court_judgment_parties.name; building_practitioner_decisions.name, building_practitioners.name;
     sanctions_listings.name; commerce_commission_parties.name, fma_parties.name, worksafe_parties.name,
     overseas_investment_parties.name; grants.recipient_as_published; councillor_interests.member;
     local_election_returns.candidate_as_listed
5. **A note for the expenses lane** (not carded): `pub.mp_expenses.name` is said to be given-first, but 744 rows from
   the workbook print "Surname Given" with no comma, and `person()` leaves them as they are. The board declares the
   column `ambiguous` until the lane turns those rows round. Then it can be `given-family`.

Lesson filed (above).

## Result (integrator, 26 October 06:30 NZDT)

Merged as a5ecac8: fast tier green (622 s), gate green, nothing to load.
Moved from the session's scratch folder into the inbox by the integrator;
the lesson's first line cut to one sentence under 240 characters at the
merge (the index refused 267). Working copy and branches retired; release
copy moved; `qv4-board` restarted; first name Phillip, last name Mills on
the live board shows the reversed donor among the exact rows and Near
matches 0. `board-4` (rulings 86 and 87) launched from this main.
