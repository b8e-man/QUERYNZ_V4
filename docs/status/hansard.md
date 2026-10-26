# hansard: where it stands

**Date:** 2026-10-27. **Rulings:** 96, 97. **Lane:** `registers/hansard/`. **Session:** hansard-2.
**Merge request:** `hansard-2` (raised).

## Done

- hansard-1: the old estate's transcripts exported once (137 sitting days to 2026-09-23, 3,923 sections, 47,243
  turns); merged 1a35c33.
- hansard-2, the MCP (no model, nothing fetched): `read_mcp.py` reads `parliament-hansard-index` into
  `index_pages` and `parliament-hansard-debates` into `days` (one per sitting day: the PDF's address and the
  provider's hash, pages, words) with the text in `hansard_private.day_texts`; `pub.hansard_days`, no text;
  `pub.hansard_sittings` and `pub.hansard_days` each say where the day is also held. Two profiles proposed.
- Whole build from mcp-1's pull (`querynz_v4_sample.scratch_hansard_2_full`, 15 s): 1,862 days (2003-02-11 to
  2026-09-23), 137 both, 1,725 MCP only (1,724 before 2024-11-20, and 2026-07-30), 0 old days missing; 383 index
  pages, matching 0 sittings (the index holds www.parliament.nz pages only). Words 94,602,760, equal to the MCP's
  `measure`. Old subjects in the same day's PDF text 3,691 of 3,885 (95.0%), worst day 57.1%; floors 90% and 50%
  per day; the misses are eight urgency sittings whose later days the MCP lacks (card).
- `check.py` on that build: red only for 383 of 387 index records taken (four arrived after the pull).
- Fast tier `registers/hansard` green; root tests green; a mutation turns the reader's test red.
- Card `the-mcp-holds-no-pdf-for-an-urgency-sitting-s-later-days-and-its-hansard-index-names-no-transcript`;
  lesson `profile-a-corpus-s-addresses-before-joining-on-them-its-label-is-not-its-contents`.

## For the integrator

- Append the two profiles in `profile-proposed.jsonl`; queue `qv4-hansard-load` nightly 04:15 NZDT (spec).
- `hansard_private` is now used: keep it out of the session reader's grants.
- `pub.hansard_days` goes on the board in the merge after this one.

## Next

- Speech turns after 2026-09-23 wait on the provider splitting its debates text by section and speaker.
- Arthur asks the provider the card's two questions.
