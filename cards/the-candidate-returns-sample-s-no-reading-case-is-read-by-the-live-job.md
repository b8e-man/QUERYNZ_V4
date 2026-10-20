# The candidate-returns sample's "no stored page reading" case is being read by the live job
kind: finding
state: open
use-case: 1
session: founding
opened: 2026-10-20

`sample.list` names one scan as "scan with no stored page reading: set
aside for a re-read", and the lane's test asserted it lands at stage
`read`. The scheduler job `qv4-read-pages-candidates` (queued by the
integrator on 20 October, 713 pieces, lowest hash first) stored that
document's pages within minutes, so the sample fill read it from pixels
and the whole-repository fast tier went red on the comparison-1 gate. The
integrator loosened the assertion to "set aside at `read`, or read from
pixels" and said so in the test. Fix, the lane's: the case should be
read against an empty store (as `test_pixels.py` already does with
`rd.Store(tmp_path / "empty")`), so the sample proves the set-aside path
whatever the shared store holds; then the assertion goes back to one
outcome. A sample case must not depend on what a running job has not yet
done.
