# The old estate's weekly charities job and the new capture fetch one feed
kind: finding
state: open
use-case: -
session: charities-capture
opened: 2026-10-20

The old `querynz-charities` job (weekly; running at the baseline, 17
October) reads the same OData feed outside any fetch gate. Once
`qv4-charities-capture` runs, the publisher gets two readers from us. Step
4.1 gives charities a capture of its own, so the old job is not needed by the
new estate. If the frozen site does not read the old charities tables, the
old job is outside the carve-out and can be stopped under step 1.4, with
proof. Otherwise it stays until the switch.
