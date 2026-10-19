# The charities draft position moves to docs/legal/positions/
kind: blocker
state: open
use-case: -
session: charities-capture
opened: 2026-10-20

The fetch gate refuses a host with no position on file, but ruling 61 lets
charities be captured before its position. The capture therefore points the
gate at a draft held in its own folder, `registers/charities/position/`, with
the four answers in it. The fence keeps a build session out of `docs/legal/`.
At the merge, the integrator moves `registers/charities/position/charities-register.md`
to `docs/legal/positions/charities-register.md` and sets `POSITIONS` in
`registers/charities/capture.py` back to the gate's default (`None`, so
`positions_dir` is not passed). It may also add `"www.odata.charities.govt.nz": 5.0`
to the gate's `FLOORS`; the lane already rests 5 s itself.
