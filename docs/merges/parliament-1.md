# parliament-1: registers/parliament, the ingest MCP's seven parliament corpora
branch: session/parliament-1 (pushed, ad979ad)
session: parliament-1 (Opus)
raised: 2026-10-27
claims: registers/parliament/ (new lane), one lesson, one queue item, docs/status/parliament.md

Ruling 96. Every record of `parliament-written-questions`, `-bills`,
`-bills-historical`, `-sc-submissions`, `-sc-reports`, `-sops` and `-wayback`
read by hash from the documents support/mcpsource landed, from the version
the pull landed last (never the highest seq); every recorded API field a
column under its own name (a test fails if shapes.json records a field the
maps lack). A record the MCP no longer serves (holds no place below the
cursor) is kept and marked `served` false. Nothing fetched from
parliament.nz; no model.

## Proof (scratch build, `querynz_v4_sample.scratch_parliament_1_build` from `scratch_mcp_1_pull2`, 50 s)

| corpus | records | documents | words vs the MCP's measure |
| --- | --- | --- | --- |
| written questions | 683,524 | 1,104,140 (420,616 older versions) | 62,316,314 = 62,316,314 |
| bills | 92 | 92 | equal |
| bills historical | 3,542 | 3,542 | equal |
| sc submissions | 1,335 | 1,335 | equal |
| sc reports | 1,000 | 1,000 | equal |
| SOPs | 783 | 783 | equal |
| wayback | 4,839 | 4,839 | MCP now 5,415 records |

Written questions: numbers and years unique within each Parliament; 683,517
of 683,524 replied (floor 99%); 2003 to 2026; 0 withdrawn. `check.py` red on
one thing only: wayback 4,839 taken of the MCP's 5,415 (the corpus grew after
the last pull); green after the next `qv4-mcp-pull`.

Faults real data showed and the made records did not: places past the cursor
after the MCP's removal (check counts below the cursor); an id with a trailing
space (one call for submissions); NUL characters in two archived pages (kept
as U+FFFD; the document keeps the bytes). Lesson
`count-a-pull-s-places-below-its-cursor`.

Fast tier: `registers/parliament` green (16 tests, 43 s). Whole repository:
red only on tests/test_generators.py (lessons/INDEX.md and the queue are
stale by this branch's new lesson and queue item: the integrator's rebuild).
That test rewrote lessons/INDEX.md in the working copy; the hook refuses a
restore, so it is left uncommitted there.

## For the integrator

1. Schemas `parliament` and `parliament_private`: add `parliament` to
   support.db LANES; apply on both databases.
2. Profiles: append `registers/parliament/profile-proposed.jsonl`
   (`mcp-parliament-written-question`, `mcp-parliament-api-item`,
   `mcp-parliament-wayback-page`, v1).
3. Position: move `registers/parliament/position/parliament.md` to
   `docs/legal/positions/parliament.md` (hosts: parliament.nz). Note the fetch
   gate keeps refusing the host for the estate's own capture: the position
   records an off-estate capture through a challenge (hard limit 6).
4. Job, proposed, none queued: `qv4-parliament-load` (processor, 2 GB,
   nightly 04:30 NZDT after `qv4-mcp-pull` and `qv4-beehive-load`,
   `python -m registers.parliament.load`, deadline 60 min, query time limit
   600 s).
5. Views `pub.parliament_written_questions`, `pub.parliament_api_items`,
   `pub.parliament_wayback_pages` carry no question, reply or page text.
   Queue item `publish-the-written-questions-question-and-reply-text`
   (default no).
6. Sample database: drop `scratch_parliament_1_build` when done (about
   1 GB of rows).

## Result (integrator, 27 October 12:10 NZDT)
Superseded by fix-registers-parliament-1, which carried it. Merged a48633c as `integrate/diaries-parliament` (diaries-2 with fix-registers-ministers-diaries-1, parliament-1 with fix-registers-parliament-1), gate green at the second run, 27 October 12:10 NZDT. The first run passed every test and failed in the staging load: the staging schema's name was cut at Postgres's 63 bytes, so `<schema>_private` was cut back to the public schema's name and the diaries' two `entries` tables collided; support/staging now leaves room for the suffix (a3dd295, with tests). Done at the merge: `ministers_diaries` and `parliament` in support.db's LANES (92 schemas applied on both databases); four profiles appended (`mcp-diary-entry`, `mcp-parliament-written-question`, `mcp-parliament-api-item`, `mcp-parliament-wayback-page`; count 146 with hansard-2's two); the diaries paragraph folded into docs/legal/positions/beehive.md and the parliament position moved to docs/legal/positions/parliament.md; `qv4-ministers-diaries-load` nightly 04:20 NZDT (priority 87) and `qv4-parliament-load` nightly 04:30 NZDT (88); the two deleted queue items gone from the roll-up. Released; the worker restarted for the two jobs. The staging load built both lanes from the adopted live documents (the fast adopt finished 11:20): diaries 2,560 releases, 208,464 entries (22,090 older versions, 2,126 entries with a withholding, 3,096 locations street-only, 115 naming a home, 0 set aside); parliament 695,115 rows in 69 s. Their five views go on the board in the next gate (fix-products-board-2, raised). Branches and the working copies retired. Open against this lane: 10 of the 4,839 archived pages are parliament.nz's "Unauthorized Request Blocked" page held as a good read (found by fix-products-board-2); hard limit 6 says a challenged read is a failed read, so a fix sets them aside: `bin/fix registers/parliament`, launched by the integrator.
