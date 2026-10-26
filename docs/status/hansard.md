# hansard: where it stands

**Date:** 2026-10-26. **Ruling:** 96. **Lane:** `registers/hansard/`. **Session:** hansard-1.
**Merge request:** `hansard-1` (raised).

## Done

- The once-only export of the old estate's Hansard tables (`capture.py --export`, 26 October 18:43): sha256
  c912d9bc…, 16,081 lines, 76 MB: 394 members, 3,923 sections of 137 sitting days (2024-11-20 to 2026-09-23),
  137 sittings, 11,627 old speech rows. Pinned in `capture.py`; written to
  `/home/user/querynzv4-work/scratch/hansard-1/` and landed in the document store by the sample fill.
- Profile `hansard-export` v1 (`profile-proposed.jsonl`), tables, reader, load, publish
  (`pub.hansard_sittings`, `pub.hansard_sections` with text, `pub.hansard_speeches` one per turn), check, sample
  (six days by case), pane, position `position/hansard.md`. No model.
- Whole export into scratch (2.1 s) and `check.py` on it: 137 of 137 days agree with the sitting rows' own counts;
  0 of 11,552 live old speech rows differ; 47,243 turns (40,098 member, 7,145 role-only); every text hashes to its
  SHA-1; members matched to `pub.members` 118 of 128, turns 38,832 of 40,098 (96.8%). The 10 not matched are
  mid-term list members (existing card `who-left-the-house-mid-term-is-not-in-the-results-files`).
- Fast tier `registers/hansard`: 17 passed; a mutation (role-only turns dropped) turns the real-data test red.
- Lesson: `an-honorific-after-the-comma-survives-the-shared-name-reader`.

## For the integrator

- Move `position/hansard.md` to `docs/legal/positions/`, append the profile, add `hansard.parliament.nz` (and
  `parliament.nz` unless another lane's position needs it) to `HELD` in `support/fetchgate` (ruling 78).
- Regenerate the lessons index (`tests/test_generators.py` is red only for the new lesson).

## Next

- hansard-2, after mcp-1 merges: land `parliament-hansard-index` records, fill `hansard.index_pages`, join by url
  (the sittings' url is `https://hansard.parliament.nz/hansard-transcript/<day>`); propose `qv4-hansard-load`
  nightly after `qv4-mcp-pull`. The speeches stay held at 23 September until the MCP carries text.
