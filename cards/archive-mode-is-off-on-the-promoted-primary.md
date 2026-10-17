# archive_mode is off on the promoted primary, so no change-log archive is kept
kind: finding
state: open
use-case: -
session: founding-2
opened: 2026-10-18

Found measuring node2 for `docs/baseline.md` (1.3). Since the 17 October
failover node2 is the primary with `archive_mode = off`: write-ahead
segments are recycled, not archived, so there is no point-in-time recovery
beyond the nightly dumps, and node1 cannot catch up from an archive when it
returns; it needs a rewind or a rebuild. Arthur's call: turn it on now
(a restart of the server, outside the plan's three kinds of change, so his
word) or leave it until node1 is back and the pair is rebuilt. Hard limit
22: not applied by a session.
