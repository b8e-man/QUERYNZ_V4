# The board joins party finance's rows to a party by its name
kind: blocker
state: closed
use-case: 1
session: party-finance
opened: 2026-10-20
closed: 2026-10-20

From `party-finance-2` the lane resolves every party label with
`keys.parties.party_name(label, rows, on=…)` against the parties lane's
published names, so `party` in `pub.party_expenses`,
`pub.party_expense_returns`, `pub.party_financial_statements` and
`pub.broadcasting_allocations` holds the registration's key
(`ec-party/…`), not its registered name. `products/board/catalogue.py`
joins those four views under a registration with `key_column="name"`.
At the merge the integrator drops `key_column="name"` from those four
`Join`s (the default, `key`, is right) and the board shows each party's
filings under its registration, renamed and cancelled parties included
(36 labels more than before). Outside this lane's fence.

Closed at the merge of `party-finance-2`: the four joins on the party's registration key, and the two new views in the board's catalogue.
