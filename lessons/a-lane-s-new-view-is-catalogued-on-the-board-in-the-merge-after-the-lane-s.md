A lane's new pub view is catalogued on the board in the merge after the lane's: the gate tests the live tables before staging publishes, so a view named early fails as unpublished and one named late turns the board's live check red.
area: integrator, board, merge gate, staging
paid-for-by: 2026-10-21, charities-3 (two red gates: the charities views too early, the companies lookup views too late)

Rule: when a merge request publishes a new `pub.*` view, the integrator
adds its board catalogue entry in the next integration branch, not in the
lane's own; and when a lane's merge has just published views, the next
branch to be gated carries their entries before it is gated. The board's
outside check (`products/board/check.problems`) is the test that fails
either way: `pub.X missing` too early, `pub.X is published but the board
has no entry` too late.

Why: `bin/merge-gate` runs the full tier against the live `pub` schema and
only then loads the branch's lanes into staging and publishes them at the
merge, so a view does not exist on live until the merge commit, and from
the merge on every later gate sees it.
