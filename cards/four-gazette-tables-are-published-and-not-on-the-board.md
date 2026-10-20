# Four gazette tables are published and not on the board
kind: finding
state: open
use-case: -
session: comparison
opened: 2026-10-20

`python -m products.board check` is red: `pub.gazette_bankruptcies`,
`pub.gazette_company_notices`, `pub.gazette_practitioners` and
`pub.gazette_appointments` are published and the board's catalogue
(`products/board/catalogue.py`) has no entry for any of them. The gazette
lane's third session published them; the catalogue was last extended for
the candidate-returns views at the same merge and these four were not
added. The lane's `pane.md` describes each.

Which side is right: the check. The catalogue is the integrator's at the
merge (the gazette-3 record), filled from the lane's pane. Owner: the
board, at the next integrator sitting. Found by `checks/module_checks.py`,
which runs every lane's and product's own check for the checks board; this
is the only red among the fourteen that no card already names (the other
three, disclosures, expenses and party-returns, sit under
`national-2023-the-frozen-site-counts-one-declaration-twice`,
`expense-release-totals-the-publishers-printed-wrong` and
`labour-2017-the-page-reader-drops-a-handwritten-correction`).
