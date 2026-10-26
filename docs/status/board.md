# board: where it stands

**Date:** 2026-10-27. **Step:** 4.9 second version, rulings 80 to 93,
96, 100 and 102, `products/board/`. **Session:** fix-products-board-1 (the
Beehive views and the daily PDF), carrying hansard-2. **Merge request:**
`fix-products-board-1i`.

## Done

- Hansard (ruling 96, fix-1h, merged): sitting days, sections with their
  text in their own pane only, speech turns; no pointer to the House.
- Hansard's daily PDF (hansard-2, carried): `hansard_days` titled
  "<day> · daily PDF", pages and words, the PDF as the citation, whether
  the old transcript holds the day, and the sitting's pane by day.
- Beehive (ruling 96, `registers/beehive/pane.md`): the register
  "Beehive: releases, speeches and features" after Hansard, in the
  House's family. A release titled title and type, citing the page; its
  ministers as the site tags them (given-family, the slug, no person
  linked); the provider's topics and quotes under "The source's
  annotation (made by its model, not ours)", never a link or an edge.
- Live, 27 October: check and `tests/test_real.py` green but one line,
  `pub.hansard_days missing` (hansard-2 not yet published); the day's
  view proven in the sample's scratch schema; fast tier green.

## Known limits

- 30 registers share 14 colours, by family (queue item
  `graph-node-colours-by-family`).
- No pointer or edge from a Hansard turn or a Beehive minister tag to the
  House's member row: no shared id is published.
- A release's `published_at` is not shown; the record's own day is.
- Live `pub.beehive_releases` holds only old-estate rows; the MCP's
  62,527 beehive arrivals are not yet loaded (the lane's job).
- Section text is not searched; suppressed names in a section's text
  have no published list to apply.

## Next

The integrator publishes hansard-2's views on live before gating this
branch, then restarts `qv4-board` at the release.
