# The surname Lane trips the home-address check, and the report is refused
kind: finding
state: open
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20

`products/report/rules.py` rule 7 (`ADDRESS_SHAPE`) matches a street word
followed later by four digits. A donor row's statement "Gary Rodney Lane ·
$100,000.00 to The New Zealand National Party, in the party's return for
2022 (Part A); dates as printed: 31/3/2022" has "Lane" and "2022", so the
report on `party_returns:d87ba315…/A/10` is refused. Every person named
Lane, Place, Drive, Street or Terrace with a dated row is refused the same
way. For the report lane: test the street word against an address shape
(a number before it, a postcode after) rather than any four digits, and
keep the check on every statement. Found at the recruitment checkpoint.
