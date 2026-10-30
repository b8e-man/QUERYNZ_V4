# The scheduler's fast tests read the live night marker and go red while a window is open
kind: finding
state: open
use-case: -
session: integrator-9d788fb
opened: 2026-10-30
closed:

30 October 16:0x, with the night window open on node2 (`<live>/scheduler/night-window.json` present):
`QV4_INTEGRATOR=1 bin/fast support/scheduler` fails with `AttributeError: 'FakeWorker' object has no attribute
'alarm'` at cards.py:682. The Manager's default marker path is `NIGHT_MARK` under the live folder, and a test that
builds a Manager without passing `mark=` sees the box's real marker, so `night_recover` runs on the fake worker.
The tier went green with `QV4_LIVE` pointed at an empty scratch folder. A gate that happens to run during a window
would refuse a sound branch for the same reason.

Owed (`bin/fix support/scheduler`): the fake worker, or the tests' conftest, gives every Manager a marker path in
the test's own temporary folder; no test reads anything under `QV4_LIVE` unless it says so.
