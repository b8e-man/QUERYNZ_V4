# node1 is down and unmeasured, so the baseline covers one box
kind: finding
state: closed
use-case: -
session: founding-2
opened: 2026-10-18
closed: 2026-10-18

`docs/baseline.md` (1.3) measured node2 only; node1 has been down since the
RAM install on 17 October and its half says "not measured". Until it
returns: no standby, no second copy of the model servers, and the baseline
cannot say what the old estate ran there. When Arthur brings it back
(fence it first, then the rewind as the failover note says), a founding
session re-measures it and fills the node1 column.

Closed by ruling 55 (18 October): node1 is out of the plan. The baseline
stays a one-box measurement and that is the estate. Nothing is owed on
node1's account.
