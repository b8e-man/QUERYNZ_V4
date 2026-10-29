# board: where it stands

**Date:** 2026-10-29. **Step:** 4.9 second version, rulings 80 to 120,
`products/board/`. **Session:** board-14 (ruling 119, three tranches).
**Merge request:** `board-14` (inbox).

## Done

- Rulings 80 to 118 and 120: as before (board-8 to board-13,
  fix-products-board-1 to -6).
- Ruling 119 (1): each organisation entity in the results carries a tick
  box. That means a group the links lane reads as organisations, a row of
  an organisation register, a shareholder whose holder type is "company",
  or a row pub.names reads as an organisation. A person has none. The
  collapse section's "collapse the ticked into one" folds the ticked into
  one entry. The entry is named by the fullest name among them and says
  "collapsed here by hand; not a link"; it has an unfold link.
- (2): the dossier lists the members as the entities they are. The graph
  draws the fold as one node with the same words, on the search's graph and
  on a graph centred on any member.
- (3): the fold is carried in the address (`hf=`). A saved path keeps it in
  a new `boxes` column of `board.paths`. It is never a link, a decision or
  written anywhere else. A person named in a crafted address is never folded.
- Measured live, main against this branch over HTTP: "Rank Group" searched
  1.74 to 1.84 s both; folded 1.73 s; the fold's click graph 0.12 s (13
  nodes, one fold); its dossier 0.21 s (7 members). The search offers 21
  organisations: the 7 folded (the group, five RANK GROUP LIMITED holder
  rows, the Commerce Commission party) and 14 others, which stay apart.

## Known limits

- The brief said twenty other Rank Group companies; the pane offers 14
  distinct ones (the twenty counted repeats across the field tabs).
- A folded page is larger (78 KB to 153 KB on Rank Group): every link
  carries the fold.
- A fold by hand cannot be extended by ticking it; unfold and tick again.
- No claims section: no claims lane publishes yet.
- A group past 40 rows is drawn from its first 40 (connections first).
- 32 registers share 14 colours (queue item `graph-node-colours-by-family`).
- A minister's name searched takes the page past two seconds (card).

## Next

1. The integrator merges `session/board-14`, runs `python -m products.board
   state` (adds `board.paths.boxes`, `ADD COLUMN IF NOT EXISTS`), and
   restarts `qv4-board` at the release (`graph.js` changed).
