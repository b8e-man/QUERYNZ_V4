# board-15: ruling 122, a permanent chat pane on the board
branch: session/board-15 (pushed, 27b14bb; four commits on 09ad055: two tranches, the record, one slow-test fix)
session: board-15 (Opus, build, scope products/board/)
raised: 2026-10-29
claims: products/board/ (chat.py and static/chat.js new; server.py, panes.py, assets.py, document.py, check.py, spec.md,
units/qv4-board.service; tests/test_chat.py and test_chat_check.py new, test_canvas.py, test_panes.py, test_uses.py,
test_real.py); lessons/a-product-reader-tool-that-reuses-a-pane-s-gatherer-meets-the-session-reader-s-reads-inside-it.md;
docs/status/board.md.
publish: nothing. tables: none. **units: qv4-board.service changed** (adds `QV4_CHAT_URL=http://127.0.0.1:8060/v1/chat/completions`
and `QV4_CHAT_MODEL=qwen4exp`). **After the merge: install the unit and restart `qv4-board` at the release.**

## What it does

1. **The pane** (`panes.chat_pane`): fixed to the right-hand edge of every page `panes.page` renders (search, a dossier,
   use cases, pinned, saved paths), 26rem, always open; `body.chat-on` pads the page so its own panes use the width left.
   The thread sits above and the question box at the foot (Enter asks, Shift+Enter makes a new line), with the newest turn
   scrolled into view. The colours come from the sheet; `contrast_problems` is still clean.
2. **`static/chat.js`** (listed in `assets.FILES`, no library): keeps the thread in sessionStorage and posts it whole to
   `/chat`. It builds the answer from parts as text nodes and links, with no innerHTML. A citation opens the row's pane;
   an unknown one is struck "not a row". The content security policy is unchanged.
3. **`POST /chat`** (`server.send_chat`): JSON only (a form post gets 415) and always 200. Nothing is kept, and the log line
   is the path alone. `chat.respond` calls `support.modelclient.chat` (lane `board-chat`, which checks the model by name)
   with four tools on the product reader, pub only:
   - `registers`: the catalogue with row counts, cached for 10 minutes.
   - `search`: `search.search` with a term, registers and fields, 8 rows a view, plus the `people.gather` entity groups.
   - `row`: fields through `panes.shown`, a column named for an address only from `ADDRESS_COLUMNS`, flagged texts
     withheld, then the citation and far rows.
   - `dossier`: what `dossier.gather` returns, as rows and money.

   The model gets at most six calls; the sixth has `tool_choice: none`, so it must answer. Each tool's answer is cut to
   6,000 characters, because the model holds 16,384 tokens. If the model is down or a different model answers, the pane
   reads "the chat model is not running".
4. **`document.records`** returns None when the grant is refused (`InsufficientPrivilege`), so the documents read as
   closed inside the dossier tool. Before this, every dossier tool call failed.

## Tests: fail on main, pass on the branch

- **Tranche 1:** `test_chat.py`, 11 tests (pure: fake model, real HTTP server on a closed port). On main (an archive of
  HEAD with the file copied in) they fail at import, because main has no chat module.
- **Tranche 2:** `test_chat_check.py`, 3 tests. Same result on main.
- **Older tests:** three assert a page carries no script or only the graph's scripts. They now expect `chat.js` as well.
- **Runs:** `bin/fast products/board` green in 43.7 s; root tests (fast) green; board slow tests green after the
  `test_real.py` line.
- **`python -m products.board check`:** green. Item 28 answered in 9.9 s with 9 citations resolved. With `QV4_CHAT_URL`
  at port 1 it prints "model not running, chat item skipped" and stays green.

## Measured live (qwen4exp on Radiance, node2)

| Question | Seconds | Model calls | Citations resolved |
| --- | --- | --- | --- |
| which registers hold Rank Group Limited? | 8.0 | 5 | 6 |
| How much did Rank Group Limited give to ACT, by year? | 11.8 | 6 | 4 |
| Does the estate hold a register of land titles? | 5.2 | 3 | 3 |

Lesson filed (above).


## Result

MERGED 29 October 2026 19:21 NZDT (4bfad35; `integrate/board-15` off main, the session's lesson rule cut from 322 to 220
characters so `bin/lessons-index` would write, index regenerated; gate green first run, ~8 min). Unit installed and
`qv4-board` restarted at the release (QV4_CHAT_URL, QV4_CHAT_MODEL). Nothing loaded: no tables.
