# The graph tab's fold is mislabelled in rows mode and cites the superseded filing
kind: finding
state: closed
use-case: -
session: integrator-cd72cb5
opened: 2026-10-29
closed: 2026-10-29

Seen by the founding session on 29 October while fixing the fold's dossier
(fix-products-board-5), on the search "Arthur Falls" with "a shared first
and last name" ticked. Three faults in the board's display, none in the
registers or the links:

1. The graph tab opens in rows mode, so the fold there is made from the
   seven raw rows and reads "7 entities, 7 rows", typed and coloured as a
   charities row because the member that stands for the fold is picked by
   id order. Entities mode reads "2 entities, 7 rows", which is right.
   Default the tab to entities when a collapse is ticked.
2. Folding merges the two Simply Industrial shareholder causes into one
   edge and keeps the first, the July filing that is not in the latest
   file. Prefer the latest filing when causes merge.
3. The note "1 matching rows drawn; 6 more match: narrow the search" is
   false under a fold: all seven are drawn, folded into one.

Owner: board. One fix session covers the three: `bin/fix board`.

Closed by fix-products-board-6 (29 October). (1) Overtaken by ruling 120: the
graph has one state, entities; the rows mode, its switch and `g=` left, and
an address naming `g=rows` opens the entities graph. A graph fold is typed and
coloured by the register most of its members' rows are in, its name the
fullest of them all (`collapse.drawn_as`). (2) Causes merging into one edge
cite the latest filing, never one marked not in the latest file
(`people.cite_latest`). (3) The "more match" note counts a fold's members'
rows as drawn. Also ruling 118: "a shared full name, with middle names" left
the collapse section; `cl=full` is read without it. Measured live, "Arthur
Falls" with "a shared first and last name" ticked: the fold reads "2 entities,
7 rows", typed companies; the Simply Industrial edge cites the August
shareholding (in the latest file); the note reads "7 matching rows drawn as 1
nodes", no "more match"; no switch on the page.
