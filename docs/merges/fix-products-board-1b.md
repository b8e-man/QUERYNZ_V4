# fix-products-board-1 (25 October): "search all" and the register ticks kept apart (ruling 81)
branch: fix/products-board-1 (pushed, 945a0a9; one commit on 252a83f)
session: fix-products-board-1 (Opus, fix weight, scope products/board/). The name was used before: its 20 October request
(`fix-products-board-1.md`, merged at bbba72b) is left untouched; this is a new request on the same branch name. Written to
the session's scratch folder because the fence refused the inbox link again (card
`a-fix-session-cannot-write-its-merge-request-into-the-inbox`); the integrator moves it into merge-requests/.
raised: 2026-10-25
claims: products/board/ (search.py, panes.py, server.py, graph.py, check.py, spec.md, tests); lessons/a-script-free-select-all-box-is-a-state-of-its-own-sent-beside-a-hidden-off.md (corrects and replaces board-2's `was_all` lesson, renamed; lessons/INDEX.md regenerated); docs/status/board.md

## The change

Ruling 81, on both tabs:

1. The first view shows "search all" ticked and every register unticked.
2. "search all" ticked searches every held register whatever is ticked; unticked, the ticked registers alone (`search.selection`).
3. `search.Boxes(all, ticked)` rides every href as `all=` and `r=`: the results, every pane to the right, the pin and save
   forms, the graph's node and edge-label hrefs, and the two tab links. Turning "search all" off and on loses no tick.
4. "search all" off with nothing ticked searches nothing; the results pane (and the graph pane) says "tick a register, or search all".
5. An address with neither `all` nor `r` (a saved path, a pin, an old address) opens as the first view. An address with `r`
   alone (board-2's narrowed link) opens narrowed, as before.

The form sends a constant hidden `all=0` before the box's `all=1`, so an unticked box is told apart from an old address
(`search.boxes_of`). Board-2's "nothing ticked means all" rule and the `was_all` mark are removed.

## Checked

- `QV4_INTEGRATOR=1 bin/fast products/board` green (40 tests, 41 s). Five new pane tests, one per point, render the form and
  read back the ticked boxes and what each href carries through the server's own parser. Each was shown to fail with its rule
  broken in memory (nothing-means-all, a missing `all` read as off, hrefs dropping the all state, every box ticked under all).
- `python -m products.board check` green against the live tables; its search-tab case now runs with "search all" off and the
  one register on, and with it off and the others on.
- Slow tests (`-m slow`, 5) green, the full outside check among them.
- A scratch server on 127.0.0.1:18421 against live data: first view of `/` and `/graph`, all on with a tick, all off with a
  tick, all off with none (both tabs say so), an old address: each as above.
- tests/test_lessons_search.py green. Known to fail: nothing. Lesson: corrected (above), not new.

## What the integrator does after the merge

Restart `qv4-board` at the release (expected; the running server holds the old code). No tables, no units, no other module.

## Result (integrator, 25 October 15:05 NZDT)

Merged as 5671719: fast tier green (619 s), gate green, nothing to load.
Moved from the session's scratch folder into the inbox by the integrator
(the fence refused the session's write; the standing card). Working copy
and branches retired; release copy moved; `qv4-board` restarted; the first
view shows "search all" ticked and no register ticked. `board-3` (rulings
82 and 83) launched from this main.
