# readers-1: the three MCP names readers in one gate (beehive-2, hansard-3, parliament-2; ruling 130)

Merged 31 October 2026, 12:50 NZDT, as 4736b6a (integrate branch `integrate/readers-1`, 9094819 + the wayback shape). Each session's request and its result are in `/home/user/querynzv4-work/inbox/merge-requests/{beehive-2,hansard-3,parliament-2}.md`.

## What merged

- **beehive-2**: `registers/beehive/model_read.py`, profile `beehive-release-body` v1 (budget and split rule), `beehive.people`, `pub.beehive_people`; job `qv4-beehive-read` (priority 28).
- **hansard-3**: the deterministic split of every sitting day (`split.py`, profile `hansard-day` v1: 1,862 days, 0 unrecognised; 38,472 sections, 613,481 turns, 87.7 % with a member), the names reader (`model_read.py`, 40,000 characters a piece, one piece per section), `pub.hansard_day_sections`, `pub.hansard_people`; `pub.hansard_speeches` now carries the 1,725 MCP-only days; job `qv4-hansard-read` (priority 29).
- **parliament-2**: the archived pages and the written questions read by the text reader (`model_read.py`; 24,000 characters a piece, up to 16 questions of one year in one request), profiles `mcp-parliament-wayback-page` v2 and `mcp-parliament-written-question` v2, `parliament.readings`, `parliament.people`, `pub.parliament_people`; job `qv4-parliament-read` (priority 103).
- Integrator's own: the Radiance unit at `--max-model-len 32768 --host-pool-mib 20480` (KV cache 22,652 → 524,396 tokens; 1 to 8 tok/s a request → 190 to 207) with its tests and the profile geometry; ruling 130 in `docs/decisions/rulings.md`; the profile pin 155; `support/mcpsource/shapes.json` records the provider's six new `capture.*` fields on parliament-wayback records.

## The gate

Five runs. Refused outside the branches each time: the pinned Radiance shape tests and the flash-next geometry (moved with the unit); 30 s statement timeouts while the courts fix session built its corpus on live (run again); the live shape test on parliament-wayback (the provider began capturing snapshots on 31 October: recorded). The fifth run green through the fast tier, the slow tier and three staging loads (beehive 66 s, hansard 46 s, parliament).

## After the merge

Pushed; released; queued at 13:44: row 940 `qv4-hansard-read` 1,857 days, row 941 `qv4-parliament-read` 65,809 pieces (pages newest first, then the questions' batch leaders), row 942 `qv4-beehive-read` 66,399 releases. The first beehive reads: 2 to 3 s a release. The four views catalogued on the board in the merge after (`integrate/courts-2`). Worktrees beehive-2, hansard-3, parliament-2 retired; the remote branches `session/beehive-2`, `session/hansard-3`, `session/parliament-2` are Arthur's to delete; `querynz_v4_sample.scratch_hansard_3_full` (+ `_private`) is his to drop.
