# The catalogue's not-held list lacks unincorporated entities and MPI; its limited partnerships entry overstates
kind: finding
state: closed
use-case: subject report (5.1); 4 agriculture counterparty
session: agriculture
opened: 2026-10-20
closed: 2026-10-21

A template may name only `catalogue.NOT_HELD` keys in a section's
`not_held`, and two registers an agriculture check reads are not there:
the business-number register's entities outside the companies file (sole
traders, general partnerships, trusts; reachable one at a time through the
interface of step 5.5), and MPI's prosecutions and animal-tracing (NAIT)
enforcement. The agriculture template states both in its section text and
flags only. And `limited_partnerships` prints "Limited partnerships
register" as not held while pub.companies carries 6,678 "NZ Limited
Partnership" rows (status and dates); what is not held is their general and
limited partners. For the report lane: add `unincorporated` and `mpi`
keys, and name the LP entry "Limited partnerships' partners".

Closed 2026-10-21 by the report session (report-3). `unincorporated`
("Sole traders, general partnerships and other business-number entities
outside the companies file") and `mpi` ("Ministry for Primary Industries
prosecutions and animal-tracing enforcement") are in `catalogue.NOT_HELD`,
and `limited_partnerships` now prints "Limited partnerships' partners (the
partnerships themselves are rows of the companies register)". A fixture
test holds the keys and the wording. The agriculture template names the
two keys (a fix in its folder).
