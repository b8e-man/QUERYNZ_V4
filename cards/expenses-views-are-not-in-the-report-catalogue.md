# MPs' and ministers' expenses are published but the report's catalogue does not know them
kind: finding
state: closed
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20
closed: 2026-10-20

`pub.mp_expenses`, `pub.minister_expenses` and `pub.expense_release_totals`
are published; `products/report/catalogue.py` has no entry for them, so
`template.load` refuses a template that names them. The recruitment brief
asks for expenses where the person is or was a member; the template says
"cannot read them yet" in its section and on its limits page. For the
report lane: catalogue entries (title, dating, the member the row sits on,
the statement) and a walk route from a member row to its expense rows.

Closed 2026-10-20 by the report session (report-2) for the two per-person
views. `catalogue.py` knows `mp_expenses` and `minister_expenses` (register
"MPs' and ministers' expenses"; a figure titled name · category, dated by
its period, money formatted, cited to the release's sheet and cell). The
releases print a name and no key to a member row, so the route is by name
(`walk.NAMED_ROWS`): from a seat or an interests return in the subject's
group, the rows whose printed name is the person's (folded whole, or first
and last word) are listed near, with the reason that the release prints a
name only; only the period totals and money printed outside the total are
listed, the per-category lines are named as not listed. The shape's own
template reads both in a section of its own. `pub.expense_release_totals`
is not catalogued: it has no row key (`expense-release-totals-has-no-
stable-key`, the lane's card) and is the lane's check, not a subject's row;
when the lane publishes a key the entry is one line here. Measured:
`python -m products.report check` builds a report on the latest seat whose
name an expense release prints, taken from the tables at run time, and
fails unless expense rows are listed near with their reason and no
per-category line among them.
