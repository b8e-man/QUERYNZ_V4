# The surname Lane trips the home-address check, and the report is refused
kind: finding
state: closed
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20
closed: 2026-10-20

`products/report/rules.py` rule 7 (`ADDRESS_SHAPE`) matches a street word
followed later by four digits. A donor row's statement "Gary Rodney Lane ·
$100,000.00 to The New Zealand National Party, in the party's return for
2022 (Part A); dates as printed: 31/3/2022" has "Lane" and "2022", so the
report on `party_returns:d87ba315…/A/10` is refused. Every person named
Lane, Place, Drive, Street or Terrace with a dated row is refused the same
way. For the report lane: test the street word against an address shape
(a number before it, a postcode after) rather than any four digits, and
keep the check on every statement. Found at the recruitment checkpoint.

Closed 2026-10-20 by the report session (report-2). The rule, not the row:
`rules.py` now recognises an address by its shape, a street number standing
alone before the street word (`12 Smith Street`, `2/14 Victoria St`) or a
comma, a locality and a postcode after it (`Queen Street, Auckland 1010`);
a number that is the tail of a money figure or a date does not count, and
the title and the statement are read apart so a candidate's `Lane · 2023`
is not a numbered street. Values are still read: a street in a name column
is the fault the rule exists for, and the fixture that plants one still
refuses. Measured: `python -m products.report check` builds a report on a
donor whose name carries a street word, taken from the tables at run time
(today `Gary Lane`), and fails on a rule 7 refusal; the card's own row
`party_returns:d87ba315…/A/10` prints.
