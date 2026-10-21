# The Green Party's 2026 disclosures moved on the 22 October release
kind: finding
state: open
use-case: 1
session: fix-support-db-1
opened: 2026-10-22

The disclosures lane's comparison with the frozen site
(`registers/disclosures/tests/test_disclosures.py::test_each_party_year_equals_the_frozen_site_or_has_a_card`)
went red in the fast tier on 22 October:
The Green Party of Aotearoa New Zealand 2026
ours 496,694.56, frozen 524,208.56 (the frozen side higher by 27,514.00). The frozen site's figures file (`var/pi-snapshot/current/data/home.json`
in the old folder) was rewritten by that morning's release at 06:16, so the
frozen side gained a declaration the sample's disclosures do not hold, or
counted one differently. Not looked at: the cause is the disclosures lane's.

Found by fix-support-db-1 (a change to `support/db` that does not touch the
lane). This card answers the test's first assertion; its second, at least
14 party-years equal, now finds 13 and stays red until the lane's test
lowers the floor to 13, as it did for ACT New Zealand 2026 on 21 October
(one line, `registers/disclosures/tests/test_disclosures.py:385`, outside
that session's fence). Until then every branch's gate run is red on it.

Owner: disclosures. Next: read the frozen site's Green 2026 declarations
against the lane's, then fix, accept onto the known-limits page, or drop.
