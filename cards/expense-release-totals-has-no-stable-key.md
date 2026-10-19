# pub.expense_release_totals has no stable key
kind: finding
state: open
use-case: -
session: board
opened: 2026-10-20
closed:

The register-row contract (1) gives every published row a stable key. The
expenses lane's `pub.expense_release_totals` carries `release, document,
page, place, publisher, …` and no `key` column; every other published view
has one. The board uses `release` as the row's key for that view
(`catalogue.py`, `key_col="release"`), which works while a release is one
row. For the expenses lane (a fix session, `registers/expenses`): publish a
`key`, and the board's catalogue entry drops its `key_col`. Met in the
board's outside check, which lists every column it reads against the view.
