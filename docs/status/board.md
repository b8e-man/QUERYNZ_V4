# board: where it stands

**Date:** 2026-10-25. **Step:** 4.9 second version (ruling 80),
`products/board/`. **Merge request:** `board-2` (raised).

## Done

- Search tab, at the old address `/?q=&p=` (saved paths open): left pane
  with a check box per register in catalogue order (not held greyed,
  uncheckable), "search all" at the top, the search box; a GET form,
  nothing checked = all (`search.selection`, hidden `was_all` mark).
  Results pane beside it, wider: every matching row of the checked
  registers, up to 50 per view with the count, every field, date, source
  address and citation, the term marked under the search's own fold
  ("Maori" marks "Māori" and the reverse). Row, person and link panes
  open to the right as before; pins and paths unchanged.
- Graph tab `/graph?q=&r=&c=`: matching rows (16 at most) as nodes, one
  hop of edges from 22 catalogue `Relation` lines (money, role,
  candidacy, declaration, dealing) and `pub.links` (confirmed solid, near
  dashed); server-written SVG, deterministic sector layout, a node
  re-centres, an edge label opens the asserting row; key below with
  drawn and not-drawn counts; an edge list as the table view. No address
  edge; a suppressed row draws no same-person edges. Product reader.
- Outside check grown (search tab with and without the register; graph
  of a donor row draws money, every far end real, no address type,
  relation columns in both views): green against the live tables, and
  shown to fail on a broken relation. Board tests 40 (fast 35, slow 5)
  green; root fast tests green; `bin/fast products/board` green.

## Not done, by choice

- Regulator parties, court parties, gazette `register_key` matches and
  grants → publishers are not drawn: not among the ruling's types.
  Adding one is a catalogue line.
- Saved paths keep the term and path, not the registers checked (the
  table is unchanged); they reopen over all registers.

## Next

1. The integrator merges `board-2` and restarts `qv4-board`.
2. Lanes mirror their relation lines in `pane.md` (merge request lists them).
