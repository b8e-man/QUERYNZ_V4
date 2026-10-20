# report: where it stands

**Date:** 2026-10-20. **Step:** 5.1, the subject-report shape, `products/report/`.
**Merge request:** `report-2` (raised); `report-1` merged.

## Done

- The shape (`report-1`): one builder from one row and one template; the
  walk, sections, citations, blanks, flags, memo, server on 8440, saved memos.
- The second tranche (`report-2`), each closed on run-time rows through
  `python -m products.report check` (green, about 10 s):
  rules 3, 4 and 7 read the report's own words, a register's values masked,
  an address by shape (the Lane and CONTROL refusals); the template
  contract `contract.py`, bound as `contract` in every template's rules
  with no import, the common rules run for every template; an interests
  return's declarations listed as the subject's own; `mp_expenses` and
  `minister_expenses` catalogued and reached by name, near; a Gazette
  notice's date says what it dates with filing and publication beside; the
  header lists no row a section lists; a filed row takes the group of the
  person row a confirmed link names; the stable address
  `/report/<register>:<key>`. Fast tier 26 tests in 25 s with the fill;
  slow 4; one-way, query-crossing and reading-limit tests green.

## Carded

- `a-member-row-and-its-interests-return-join-only-by-name` (links).
- `a-pane-on-the-board-offers-a-report-from-here` stays open for the board
  half (a fix session on `products/board`).
- `expense_release_totals` waits on the lane's `expense-release-totals-has-no-stable-key`.

## Next

1. The integrator merges `report-2`, restarts `qv4-report`. Eight closed
   cards here duplicate files on `session/recruitment` (recruitment-1, raised
   first): take this branch's copies, which carry the closings.
2. The recruitment template drops its own `flag`, `subject_hub` and
   `replaced_rows` copies and its figure-start block (a fix in its folder).
3. Step 5.2 continues: template 2 (agriculture) on the shape.
