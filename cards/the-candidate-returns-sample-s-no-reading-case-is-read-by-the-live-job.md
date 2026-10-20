# The candidate-returns sample's "no stored page reading" case is being read by the live job
kind: finding
state: closed
use-case: 1
session: founding
opened: 2026-10-20
closed: 2026-10-21

`sample.list` names one scan as "scan with no stored page reading: set
aside for a re-read", and the lane's test asserted it lands at stage
`read`. The scheduler job `qv4-read-pages-candidates` stored that
document's pages within minutes of being queued, so the sample read it
from pixels and the integrator loosened the assertion.

Closed by candidate-returns-2: `sample.list` carries `key: empty-store
<sha256>`, and `sample.fill` reads that return as if the store held
nothing for it (`read.stored_page` honours the store's `hidden` set). The
assertion is back to one outcome, stage `read`, and holds with the 11
readings the job has stored for it.
