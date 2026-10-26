# The board has no entry for the three Hansard views
kind: blocker
state: closed
use-case: none
session: board-7
opened: 2026-10-26
closed: 2026-10-27

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

Closed 27 October by fix-products-board-1 (merge request
fix-products-board-1h): the register "Hansard: who spoke in Parliament"
after MPs' interests, in the House's family and colour, and the three
views as the lane's pane.md states them; `hansard` leaves NOT_HELD. The
check and `tests/test_real.py` are green against the live tables. No
pointer and no edge from a turn to the House's member row: `pub.members`
carries no member id, so the join would be a name match (plan 4.9). The
lane's "a name the estate holds as suppressed is suppressed in the text"
has nothing to read: no published view carries a suppressed-name list or a
flag on these rows, so the board shows the text as published.
