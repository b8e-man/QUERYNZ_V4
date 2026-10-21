# The OpenLaw lane is held: its API terms forbid copying case records without OpenLaw's written authorisation
kind: blocker
state: open
use-case: 2 legal counterparty and conflict check; step 5.4 item 1
session: openlaw-1
opened: 2026-10-21

The OpenLaw NZ API terms (`apiterms.pdf`, sha256 `d327cea0…`, read 21 October
2026 through the fetch gate) were accepted when the key was issued on 15 August.
Clause 3.6(a) bars "scrape, build databases, or otherwise create permanent
copies" of interface content without OpenLaw's express authorisation, and 3.7
bars charging for a service built on it. The brief's capture (every record
verbatim, landed by hash, tables and `pub` views built from it) is exactly
what 3.6(a) forbids, so hard limit 4 stops it. Built and held: `registers/openlaw`
refuses to land a case record until the position page carries an `authorised:`
line. Tested on invented records, and in memory against the real interface
(nothing kept). The interface states 46,545 cases, probed by offset on 21 October
2026, the same figure the old estate probed on 15 August 2026.

Closes when Arthur's decision (`docs/decisions/queue/whether-openlaw-api-content-may-be-copied.md`)
is made. If OpenLaw authorises: add the `authorised:` line to the position, run
`python -m registers.openlaw.capture --mode sample` on the first night (2,000
cases), size the capture, fill sample.list, put the two jobs in the catalogue.
If OpenLaw refuses or does not answer: drop the lane, and the courts lane
carries the judgments.
