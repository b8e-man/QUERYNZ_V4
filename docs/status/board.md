# board: where it stands

**Date:** 2026-10-27. **Step:** 4.9 second version, rulings 80 to 102,
`products/board/`. **Session:** fix-products-board-2, carrying
`integrate/diaries-parliament` and 1i's board commit (f43b5d1, as 5e3584f).
**Merge request:** `fix-products-board-2`.

## Done

- Hansard, Beehive, Hansard's daily PDF (1h, 1i): as before.
- Parliament (ruling 101, 102): "Parliament: written questions, bills,
  papers and archived pages" just before Hansard. Written questions (main
  view), API items, archived pages; texts whole with an address-flag note;
  withdrawn rows struck; versions said; hash plus Parliament's id where
  no address. One Relation, member_id to Hansard's member_id.
- Ministers' diaries (ruling 102): "Ministers' diaries: who met the
  minister" after the Beehive. Releases (main view) cite the PDF or "file
  name only: no address served"; meetings whole as released, four flag
  notes, the release as parent, no person and no edge.
- New View data: `flags`, `served`, `cite`, `no_url`.
- Proof on the scratch builds in the sample: every column present, panes
  render. Fast tier green in 47 s.

## Known limits

- 32 registers share 14 colours, by family (queue item
  `graph-node-colours-by-family`).
- No pointer and no edge from a Hansard turn or a written question to the
  House's member row: `pub.members` carries no member id.
- Section text, question and reply text are not searched; a diary's
  location is not searched.
- A release's meetings are in day, then the provider's row order (the
  times are text as released).
- No published suppressed-name list covers Hansard's or Parliament's text.

## Next

1. The integrator gates this after hansard-2 with 1i, and restarts
   `qv4-board` at the release. No table or unit changes.
