# board: where it stands

**Date:** 2026-10-26. **Step:** 4.9 second version, ruling 85 (80 to 84
kept), `products/board/`. **Merge request:** `fix-products-board-1d`
(raised).

## Done

- Ruling 85, name order. Each `catalogue.Name` declares an order as data,
  with its reason beside it: `parts` (9), `given-family` (15),
  `family-given` (4) or `ambiguous` (26). Unless the lane's pane.md, its
  spec, its reader or the register's printed form states the order, a
  Name is `ambiguous`.
- The name fields read a one-string name by its view's order. A comma
  reads family then given in every view. A stated order puts each field
  in its place. `ambiguous` lets a first or last name match any word.
  Honorifics come off the front and post-nominals off the end.
- Near matches: the reversed-name class reads only Names with a stated
  order. In an ambiguous view a reversed name is exact. A `family-given`
  name with no comma reads its first word as the family.
- Live, first Phillip, last Mills: party donors exact 8 → 10, Near
  matches 2 → 0 (all registers: exact 48 → 50).
  `python -m products.board check` holds the two MILLS PHILLIP donor rows
  exact and not near, and holds that every Name has an order. It goes red
  on board-3's rule.

## Known limits

- In a `family-given` name with no comma, where the family name ends is
  not marked, so a first name may be any word after the first.
- On a crowded name search ("smith") about a quarter of the graph's
  numbers live only in the list.
- The lanes' pane.md files do not yet state their name order. The merge
  request lists each view's order for them to mirror.
- `pub.mp_expenses.name` holds both orders: 744 rows still read
  surname-first. It is declared `ambiguous`.
- Card `an-address-search-on-the-board-cannot-also-name-the-company` open.

## Next

1. The integrator merges `fix-products-board-1d` and restarts `qv4-board`.
