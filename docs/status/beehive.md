# beehive and mcpsource: where they stand

Session mcp-1 (Opus), 26 to 27 October 2026, node2. Ruling 96. Merge request
`mcp-1` (in `/home/user/querynzv4-work/scratch/mcp-1/mcp-1.md`: the fence
refused the inbox link).

## Done

- `support/mcpsource`: stdlib client; the pull (cursor per corpus, 200 a
  page, one request at a time, each record landed whole by hash as source
  `query-nz`, named `<corpus>/<id>` and by url), then the MCP's change feed;
  red when the MCP counts fewer records than taken; resumable `--rewalk`
  (the MCP re-renders `text` without moving `updated_at`); arrivals, catch
  log, drift against `shapes.json` (eleven corpora). Tests on a fake server;
  live shape test.
- Pulls into `querynz_v4_sample.scratch_mcp_1_pull2`, 27 October 05:30:
  958,097 records, 1,411,057 documents, eleven corpora; nothing caught, no
  drift; the last run green with cursors held where nothing arrived.
- `registers/beehive`: built in `scratch_mcp_1_beehive`, check green: 56,211
  releases (52,273 MCP records, 24,405 captured not yet read by the provider,
  24,368 of those read from the old estate's page; 3,938 old-estate-only);
  10,254 older versions; topics and quotes kept as the source's model output.
- Old estate's Beehive pages exported once (55,358 lines, e6511b9f…, pinned).
- Position `registers/beehive/position/beehive.md` for docs/legal/positions/.

## Next

- The integrator: schemas, profiles, the position, the jobs
  (`qv4-mcp-adopt` once, `qv4-mcp-pull`, `qv4-mcp-rewalk`, `qv4-beehive-load`).
- `parliament-1`, `diaries-2`, `hansard-2` read the other corpora from the
  same pull record, each taking a record's current version as the one the
  pull saw last (never the highest `seq`).
