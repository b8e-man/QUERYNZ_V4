A third-party source can reshape every record in one redeploy (the MCP did, mid-pull, 26 October): hold each page to the recorded shapes, land records whole, and restart a first pull rather than hold two shapes.
area: mcpsource, capture, third-party sources, shapes
paid-for-by: 2026-10-26, mcp-1, the first pull of the query-nz MCP

The server refused connections from 18:52 to 18:57 and came back with new
fields on every record and a changed description of itself. A pull that had
taken 4,000 beehive records would have resumed from its cursor and held two
shapes; the lane reading them would have needed both.

How to apply: support/mcpsource records drift per field and type and runs
red until a register carries the field; the live shape test
(`test_the_live_server_still_serves_the_recorded_shape`) fails by field name.
After a reshape, stop the pull, re-record the shapes, and start the first pull
again in a fresh schema; earlier documents stay in the store (never deleted).
A server whose records carry an `updated_at` may change them in place, where a
cursor never looks: re-walk weekly (`--rewalk`).

The same night the source removed 246 written questions (every later place
moved, so a cursor would have skipped the next 246 arrivals) and re-rendered
the `text` of about 420,000 without moving `updated_at`, so its own change
feed showed none of it. Hold the source's count against the cursor, re-walk on
a schedule and resumably, and take a record's current version as the one the
pull saw last, never the highest place.
