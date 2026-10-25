# board: where it stands

**Date:** 2026-10-25. **Step:** 4.9 second version (rulings 80, 81),
`products/board/`. **Merge request:** `fix-products-board-1` (raised);
`board-2` merged.

## Done

- Search tab, at the old address `/?q=&p=` (saved paths open): left pane
  with a check box per register in catalogue order (not held greyed,
  uncheckable), "search all" at the top, the search box; a GET form.
  Ruling 81 on both tabs (`search.Boxes`, `boxes_of`, `selection`): the
  first view has "search all" ticked and no register; while it is ticked
  every held register is searched whatever is ticked; unticked, only the
  ticked registers; none ticked searches nothing and says "tick a
  register, or search all". `all=` and `r=` ride every href (results,
  panes to the right, pin and save forms, the graph's re-centre and cite
  hrefs, the tab links), so turning "search all" off and on loses no
  tick. A hidden `all=0` tells an unticked box from an old address; an
  address with neither opens as the first view. Board-2's "nothing ticked
  means all" and its `was_all` mark are gone.
- Results pane: every matching row of the registers searched, up to 50
  per view with the count, every field, date, source address and
  citation, the term marked under the search's own fold.
- Graph tab `/graph?q=&all=&r=&c=`: matching rows (16 at most) as nodes,
  one hop of catalogue `Relation` and `pub.links` edges, server-written
  SVG, key below. No address edge; a suppressed row draws no same-person
  edges. Product reader.
- `bin/fast products/board` green (40 fast; five new ruling-81 pane tests,
  each shown to fail on its broken rule); slow tests green; `python -m
  products.board check` green against the live tables.

## Not done, by choice

- Regulator parties, court parties, gazette `register_key` matches and
  grants → publishers are not drawn: not among the ruling's types.
- Saved paths keep the term and path, not the boxes (the table is
  unchanged); they reopen as the first view, search all.

## Next

1. The integrator merges `fix-products-board-1` and restarts `qv4-board`.
2. Lanes mirror their relation lines in `pane.md` (board-2's request).
