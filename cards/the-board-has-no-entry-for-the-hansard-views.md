# The board has no entry for the three Hansard views
kind: blocker
state: open
use-case: none
session: board-7
opened: 2026-10-26

`python -m products.board check` against the live tables, 26 October:
`pub.hansard_sittings`, `pub.hansard_sections` and `pub.hansard_speeches`
are published and the board's catalogue has no entry for them, so the
check, and `tests/test_real.py`, are red on three lines. They were red
before board-7 touched anything (main at 0bf98c9); board-7's own cases are
green.

The fix is a board fix after the Hansard lane's merge: three `View`
entries in `products/board/catalogue.py` read from the lane's own
`pane.md` (title, names, suppression, order), and a register line. Not
done in board-7: its brief was the graph canvas, and the views' rules on
names are the lane's to state. Owner: the board fix session.
