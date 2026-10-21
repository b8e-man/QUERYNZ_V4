# report: where it stands

**Date:** 2026-10-21. **Step:** 5.1, the subject-report shape, `products/report/`.
**Merge request:** `report-3` (raised); `report-1`, `report-2` merged.

## Done

- The shape (`report-1`), the second tranche (`report-2`).
- The third tranche (`report-3`), the templates' open cards against the
  shape, each closed on run-time rows through `python -m products.report
  check` (green, about 40 s) and a fixture test: `gazette_possessions` and
  `company_states` catalogued and reached; expense rows filtered to totals
  by every route; the holding chain (`chain_depth`, by number confirmed, by
  a unique name near, shares as filed); an organisation start's officers
  followed one step (`officers`, near, through the officer's row); the
  companies at a registered office (`office`); a section's `own`,
  `statuses` and `changed` filters; a holder's `holdings` and the holding
  hub; one not-held list with every key the templates asked for; a
  company's own name never read as an address; practitioners via the
  notice; Crown bodies by register name; a filed row's standing; the
  start's own company confirmed in a contested group; a since date
  (`?since=`, `--since`), each row new, not new or cannot say. Fast tier
  34 tests; templates' fast tier green; one-way and reading-limit tests green.

## Carded

- `the-report-keeps-no-watched-list`: carded on to step 5.5 (the trigger is
  the estate's); the shape's since date and saved memos are its half.
- `four-templates-still-say-no-link-reaches-a-bankruptcy`: the four
  templates' change, written into the card.
- Left where they are: `the-companies-lane-publishes-no-list-of-its-monthly-files`
  (companies lane), `worksafe-and-regulator-actions-have-no-lane` (a lane),
  `a-company-holder-carries-no-business-number` (companies lane: the chain
  hops by name until it lands).

## Next

1. The integrator merges `report-3` (card copies: take this branch's on the
   six credit-1 and insurance-1 cards), restarts `qv4-report`.
2. Fixes in the template folders the closed cards name: name `officers`,
   `office`, `chain` in sources and set `chain_depth`; read `company_states`,
   `gazette_possessions`, the new not-held keys, `holdings`, `report["since"]`;
   unblock the checks each card lists.
3. Step 5.2 continues with templates 5, 6, 11 and 12 on this shape.
