# MPs' and ministers' expenses are published but the report's catalogue does not know them
kind: finding
state: open
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20

`pub.mp_expenses`, `pub.minister_expenses` and `pub.expense_release_totals`
are published; `products/report/catalogue.py` has no entry for them, so
`template.load` refuses a template that names them. The recruitment brief
asks for expenses where the person is or was a member; the template says
"cannot read them yet" in its section and on its limits page. For the
report lane: catalogue entries (title, dating, the member the row sits on,
the statement) and a walk route from a member row to its expense rows.
