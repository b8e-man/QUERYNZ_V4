# The lanes' and the products' own checks are not on the checks board
kind: finding
state: closed
use-case: 0
session: founding
opened: 2026-10-20
closed: 2026-10-20

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

Closed 2026-10-20 by comparison-2. Built in comparison-1 as
`checks/module_checks.py` and registered on the board as `module-checks`
(`checks/board.py`): every `registers/*/check.py` with a main, bar track
E's two already on the board through `windowed.py`, and the board's and
the published site's own checks, run as commands with a 120 s timeout,
red on exit 1, a crash or a timeout. Today 14 run, all in under 9 s; 3
red, each under its lane's card: disclosures (National 2023 counted twice;
a May 2023 declaration linking a February scan), expenses (release totals
the publishers printed wrong), party-returns (NZ First 2019's misread
total; Labour 2017's handwritten correction). What stays: the integrator
regenerates the board after each merge; a red with no card is a new card.
