# board: where it stands

**Date:** 2026-10-29. **Step:** 4.9 second version, rulings 80 to 122,
`products/board/`. **Session:** board-15 (ruling 122, two tranches).
**Merge request:** `board-15` (inbox).

## Done

- Rulings 80 to 120: as before (board-8 to board-14, fix-products-board-1
  to -6).
- Ruling 122: a chat pane fixed to the right-hand edge of every page,
  26rem, always open; the thread in the browser tab (sessionStorage),
  posted whole to `POST /chat`. The server (`chat.py`) asks the chat model
  through `support.modelclient` (lane `board-chat`; `QV4_CHAT_URL`,
  `QV4_CHAT_MODEL`, set in the unit) with four tools on the product
  reader, pub only: `registers`, `search`, `row`, `dossier`; at most six
  model calls. `[view:key]` becomes the row's link; an unknown one is
  struck "not a row". Model down or another model: "the chat model is not
  running". No table; no question text in the log or the calls ledger.
- Check item 28; `python -m products.board check` green with the model up
  (9.9 s, 9 citations resolved) and skips with a note without it.

## Measured live (node2, qwen4exp on Radiance, real pub tables)

| Question | Seconds | Model calls | Citations, all resolved |
| --- | --- | --- | --- |
| which registers hold Rank Group Limited? | 8.0 | 5 | 6 |
| How much did Rank Group Limited give to ACT, by year? | 11.8 | 6 | 4 |
| Does the estate hold a register of land titles? | 5.2 | 3 | 3 |

## Known limits

- A citation resolving proves the row exists, not that it says what the
  sentence says; answers are the model's and not checked against sources.
- The model holds 16,384 tokens: each tool answer is cut to 6,000
  characters and the thread to its newest 12 turns.
- The money question used all six calls; a harder question may end on
  the forced answer with less read.
- A document's state reads closed inside the chat's dossier tool (the
  product reader may not read the store's records); the row pane is
  unchanged.
- No claims section: no claims lane publishes yet.
- 32 registers share 14 colours (queue item `graph-node-colours-by-family`).

## Next

1. The integrator merges `session/board-15`, installs the changed unit
   (two new environment names) and restarts `qv4-board` at the release.
