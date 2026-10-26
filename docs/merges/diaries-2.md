# diaries-2: the ministers' diary register (registers/ministers_diaries)
branch: session/diaries-2 (pushed; 3a7e07f)
session: diaries-2 (Opus)
raised: 2026-10-27
claims: registers/ministers_diaries/ (the lane whole), docs/status/ministers-diaries.md, queue item `may-a-diary-entry-show-a-bare-street-address`, lesson `a-third-party-source-url-field-can-hold-a-file-name`

Step 6.2 template 4(a), ruling 96. Every record of the MCP's `parliament-diaries`
corpus (one meeting of a minister's monthly diary release, read from the
Beehive's PDF by the provider off-estate) read by hash from the version the
pull saw last (`mcpsource.arrivals` by `landed_at`). No model, nothing fetched,
no person looked up or linked.

## Full build in scratch (querynz_v4_sample.scratch_diaries_2_build, from mcp-1's `scratch_mcp_1_pull2`)

`registers.ministers_diaries.check`: green. Taken 208,464 of the MCP's 208,464;
230,554 documents = 208,464 entries + 22,090 older versions + 0 set aside;
`measure` n_docs 208,464, corpus_words 4,764,189 against 4,764,189 held. 2,560
releases, every one's entries counted, one minister each; 78 minister names (one
is "No Minister"). Stated: 2,126 entries / 6,824 fields withheld as printed;
3,211 locations held back (115 name a home, 3,096 a street address with no place
of business named); 43 street addresses masked in meetings or attendees; 119
releases with a file name only (no address made up); 52 with no single month;
30,803 entries before 2019 (the corpus starts 1 October 2017). Against
`pub.members` by title words only: 67 of 78 found, 11 not. Full build 16 s.

## For the integrator

1. **Schemas**: `ministers_diaries` and `ministers_diaries_private` in support.db's LANES; apply on both databases.
2. **Profile**: append `registers/ministers_diaries/profile-proposed.jsonl` (`mcp-diary-entry` v1); the profile count test moves by one.
3. **Position**: `registers/ministers_diaries/position/ministers-diaries.md` is docs/legal/positions/beehive.md with the diaries' paragraph added; fold that paragraph into beehive.md (or keep it as its own page) and remove the folder copy.
4. **Job** (none queued by this session): `qv4-ministers-diaries-load`, processor, 1 GB, nightly 04:15 NZDT after `qv4-mcp-pull` (and after `qv4-beehive-load` at 04:00), `python -m registers.ministers_diaries.load`, deadline 30 min, query time limit 600 s.
5. **Order**: the live `mcpsource` was empty at 08:00 (the adopt queued); the gate's staging load publishes 0 entries until `qv4-mcp-adopt` has run. The check run bare would then be red on `taken`, correctly.
6. **Board**: the two views go on the board in a later merge (gate-order lesson); names are not links; the catalogue's suppression column is not needed (the source marks no suppression; its withholdings are the `withheld` column).
7. Sample-database schema `scratch_diaries_2_build` is Arthur's to drop once merged.

## Checks

Fast tier for the lane: green, 23 tests in 51 s; `test_the_sample_holds_its_hard_cases` failed as it should when the home rule was weakened by hand, then the edit was reversed. Whole-repository fast tier: RED in 783.5 s (target 300 s missed, recorded) on two tests, neither in this lane: `tests/test_generators.py::test_the_committed_records_generate_cleanly` (the lessons index and the decision roll-up are stale by one lesson and one queue item each, which the integrator regenerates; the first run also caught my lesson's rule at 288 characters, fixed in 3a7e07f) and `registers/expenses/tests/test_expenses.py::test_a_rebuild_gives_every_row_the_same_key` (13.5 s on a loaded box; 0.4 s run alone). The test rewrote `lessons/INDEX.md` and `docs/decisions/queue.md` in this working copy; the fence refuses a session either file, so they are left uncommitted and the branch carries main's.

Generated files (board, queue roll-up, lessons index) not regenerated.

## Result (integrator, 27 October 12:10 NZDT)
Merged a48633c as `integrate/diaries-parliament` (diaries-2 with fix-registers-ministers-diaries-1, parliament-1 with fix-registers-parliament-1), gate green at the second run, 27 October 12:10 NZDT. The first run passed every test and failed in the staging load: the staging schema's name was cut at Postgres's 63 bytes, so `<schema>_private` was cut back to the public schema's name and the diaries' two `entries` tables collided; support/staging now leaves room for the suffix (a3dd295, with tests). Done at the merge: `ministers_diaries` and `parliament` in support.db's LANES (92 schemas applied on both databases); four profiles appended (`mcp-diary-entry`, `mcp-parliament-written-question`, `mcp-parliament-api-item`, `mcp-parliament-wayback-page`; count 146 with hansard-2's two); the diaries paragraph folded into docs/legal/positions/beehive.md and the parliament position moved to docs/legal/positions/parliament.md; `qv4-ministers-diaries-load` nightly 04:20 NZDT (priority 87) and `qv4-parliament-load` nightly 04:30 NZDT (88); the two deleted queue items gone from the roll-up. Released; the worker restarted for the two jobs. The staging load built both lanes from the adopted live documents (the fast adopt finished 11:20): diaries 2,560 releases, 208,464 entries (22,090 older versions, 2,126 entries with a withholding, 3,096 locations street-only, 115 naming a home, 0 set aside); parliament 695,115 rows in 69 s. Their five views go on the board in the next gate (fix-products-board-2, raised). Branches and the working copies retired.
