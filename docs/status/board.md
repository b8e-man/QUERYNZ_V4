# board: where it stands

**Date:** 2026-10-26. **Step:** 4.9 second version, ruling 92 item 1
(80 to 90 kept), `products/board/`. **Merge request:** `board-5` (raised).
Before it: `fix-products-board-1e`, `-1f` (rulings 88 to 90).

## Done (board-5)

- The graph is laid out like a family tree. The rows the search matched
  sit on one horizontal line in the middle, by register then title,
  evenly spaced. What they belong to or pay (company, party, return,
  electorate) is above. What belongs to them (directors, shareholders,
  officers, donors, declared interests) is below. A same-person row sits
  beside its match when the line has room, else below.
- A row joined to several matched rows is drawn once, between them, and
  its edges fan from it.
- Every edge is drawn with right angles: down or up from the row, along
  a channel, then to the far row. Runs that would overlap get different
  channels, ordered to cross least. Crossings are counted.
- Names sit above or below their node, never on a channel, each no wider
  than the gap to its neighbour. All text has a halo, so a line under a
  name no longer cuts it. On the four live graphs tried, every node
  keeps a name.
- Only the matched line widens the picture (16 rows: 1,880 px, the pane
  scrolls sideways). A full layer wraps into tiers instead.
- Crossings, old sector layout to layered, live 26 October: "hart" 7 to
  2; "smith" 6 to 11; "fletcher" 33 to 63; the known donor 0 to 0; a
  centred company 0. See known limits.
- Tests: matched rows on one y, organisations above, people below,
  right angles only, overlapping runs apart, and a fixture shaped like
  the live "hart" graph crossing no more than the sector layout did (7).
  The check adds right angles and one line for the matched rows on its
  three graphs. Each was broken in memory and went red.

## Known limits

- A node joined to matched rows far apart (a party many candidates
  share) runs a long bar that the drops between must cross. That is why
  "smith" and "fletcher" count more crossings than the sector layout's
  straight lines did, which passed through nodes and labels instead.
- Two rows filed under one name are drawn as one donor (ruling 86 (3)).
- Earlier limits stand: family-given names with no comma; lanes' pane.md
  name orders; card `an-address-search-on-the-board-cannot-also-name-the-company`.

## Next

1. The integrator merges `fix-products-board-1e`, `-1f`, then `board-5`,
   and restarts `qv4-board` at the release (graph.py and the stylesheet
   changed; no table, no unit change). board-6 touches panes.py and
   search; this branch touches panes.py's stylesheet lines only.
