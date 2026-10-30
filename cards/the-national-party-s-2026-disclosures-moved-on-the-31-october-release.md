# The National Party's 2026 disclosures moved on the 31 October release
kind: finding
state: open
use-case: 1
session: integrator-9d788fb
opened: 2026-10-31

The disclosures lane's comparison with the frozen site
(`registers/disclosures/tests/test_disclosures.py::test_each_party_year_equals_the_frozen_site_or_has_a_card`)
went red in the gate of integrate/fix-support-scheduler-5 at 08:10 on 31 October:
The New Zealand National Party 2026, ours 2,291,751.20, frozen 2,790,751.20
(the frozen side higher by 499,000.00). The frozen site's figures file
(`var/pi-snapshot/current/data/home.json` in the old folder) was rewritten by
that morning's release at 06:15. The live lane is not behind it: `qv4-disclosures-load`
at 07:40 published 529 declarations (522 the day before) and its own National 2026
figure is 2,790,751.20, equal to the frozen. The test's `filled` rows are the
sample database's, fixed at the last `bin/fill-sample`, so the sample lags the
live by the 31 October declarations while the frozen figure moves daily; the
same shape as ACT New Zealand 2026 (21 October) and the Green Party 2026 (22 October).

This card answers the test's first assertion. Until the lane acts, every
branch's gate is red on each day the frozen release gains a declaration.

Owner: disclosures. Next: refill the sample's disclosures at each load, or compare
the live lane's figure (which the load already prints against the frozen release
each morning) instead of the sample's; the per-day card is not a fix.
