# The lanes' and the products' own checks are not on the checks board
kind: finding
state: open
use-case: 0
session: founding
opened: 2026-10-20

`checks/board.py` runs five checks (the frozen product, the full tier,
session times, the scheduler, the two windowed lanes). Every register
lane has its own `check.py` with an outside check that exits 1, and the
house, societies, board and site requests each asked for theirs to be
registered; none is. A lane that goes short against its source is seen
only when someone runs its check by hand. Fix, in `checks/` (the
comparison session's second tranche): a module like `windowed.py` that
runs every `registers/*/check.py` with a main, and the board's and the
published site's `check`, as commands with a timeout, and reports each
as an item.
