# The two readings of the party expense returns disagree on which reconcile
kind: finding
state: open
use-case: 1
session: comparison-2
opened: 2026-10-20

The home page's party-spend section counts the expense returns whose own
total, as read, differs from the Commission's tabulated figure. The frozen
site found three: two in 2020 and one in 2023, $118,345.53 between them.
The party-finance lane finds the two of 2020 ($98,345.53) and reads the
2023 return ($20,000 apart on the frozen side) as reconciling. The spend
and broadcast figures themselves agree to the cent on both sides; only
the reconciliation count and its money differ. Four figures today.

Which side is right: neither is shown; the 2023 return decides. Owner:
party-finance, to open that return.

site-3 (2026-10-20): the shape counts the `pub.party_expense_returns` rows
whose read total differs from the Commission's figure, as the lane publishes
that check, and adds nothing of its own; 4 figures today, unchanged. The
2023 return is the lane's to open; the card stays with party-finance.
