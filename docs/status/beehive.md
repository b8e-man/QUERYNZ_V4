# beehive and mcpsource: where they stand

Session mcp-1 (Opus), 26 October 2026, node2. Ruling 96. Merge request `mcp-1`.

## Done

- `support/mcpsource`: stdlib client (handshake, SSE, error text kept, waits
  and retries), the pull (cursor per corpus, 200 a page, one request at a
  time, each record landed whole by hash as source `query-nz`, named
  `<corpus>/<id>` and by url, arrivals and catch log, drift against
  `shapes.json`), `--rewalk`, `--retry-caught`, `--adopt`. Tests on a fake
  server; a slow live-shape test.
- First pull (in progress at drafting): `querynz_v4_sample.scratch_mcp_1_pull2`.
- `registers/beehive`: the lane (tables, read, load, publish, check, pane,
  sample, profile proposals, position page `position/beehive.md`).
- Old estate's Beehive pages exported once (55,358 lines, sha256 e6511b9f…,
  pinned), read for addresses the MCP lacks.

## Next

- The integrator: see the merge request (schemas, profiles, position, jobs).
