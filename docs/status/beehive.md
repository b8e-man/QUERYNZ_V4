# beehive and mcpsource: where they stand

Session mcp-1 (Opus), 26 October 2026, node2. Ruling 96. Merge request `mcp-1`.

## Done

- `support/mcpsource`: stdlib client (handshake, event stream split on
  newlines only, error text kept, waits and retries incl. a cut-off answer),
  the pull (cursor per corpus, 200 a page, one request at a time, each record
  landed whole by hash as source `query-nz`, named `<corpus>/<id>` and by url),
  then the MCP's change feed `changes` (a record re-read in place lands as a
  second document); arrivals, catch log, drift against `shapes.json`;
  `--retry-caught`, `--rewalk`, `--adopt`. Tests on a fake server; live shape.
- First pull, all seven corpora, into `querynz_v4_sample.scratch_mcp_1_pull2`
  (records/documents): beehive 48,212/51,928, written questions 683,770,
  diaries 208,464, wayback 3,425, hansard debates 1,221, hansard index 377,
  bills 92. Nothing caught, no drift.
- `registers/beehive`: the lane, built in `scratch_mcp_1_beehive`: 56,207
  releases (48,212 MCP records; 26,881 of them captured, not yet read by the
  provider, 26,632 of those read from the old estate's page beside them;
  7,995 old-estate-only pages); 103,708 topics, 86,437 quotes (model-made).
- Old estate's Beehive pages exported once (55,358 lines, e6511b9f…, pinned).
- Position `registers/beehive/position/beehive.md` for docs/legal/positions/.

## Half-done

- The second run (arrivals and changes only) and `check.py` against the MCP:
  waiting on the provider's server (refusing since 26 October 23:13).

## Next

- The integrator: the merge request lists schemas, profiles, the position,
  the jobs and the adopt.
- `parliament-1`, `diaries-2`, `hansard-2` read the other corpora from the
  same pull record (ruling 96).
