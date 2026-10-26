# hansard-1: the old estate's Hansard, exported once by hash and read (ruling 96)
branch: session/hansard-1 (pushed; 57fa7d4)
session: hansard-1
raised: 2026-10-26
claims: registers/hansard/ (capture, read, tables, load, publish, check, sample, pane, spec, profile-proposed.jsonl,
position/hansard.md, tests); lessons/an-honorific-after-the-comma-survives-the-shared-name-reader.md;
docs/status/hansard.md

The export (`capture.py --export`, 26 October 18:43, old read-only login, 60 s limit per statement): sha256
c912d9bc23c54c2593cfc512f422d29d1856b65e091239687e2fca497f66ac3b, 16,081 lines, 76 MB, at
`/home/user/querynzv4-work/scratch/hansard-1/hansard-2026-10-26.jsonl` and in the document store (the sample fill
landed it). 394 members, 3,923 sections of 137 sitting days (2024-11-20 to 2026-09-23), 137 sittings, 11,627 old
speech rows. Every row "taken from the old estate's tables; original not held". No model; nothing fetched.

Measured on the whole export, built into `querynz_v4_sample.scratch_hansard_1_full` (2.1 s) with `check.py`:
137 of 137 sitting days agree with the old sitting rows' own counts; 0 of 11,552 live old speech rows differ;
47,243 speech turns (40,098 with a member id, 7,145 role-only); every section's text hashes to the old SHA-1;
members matched to `pub.members` by name 118 of 128 (92.2%), turns 38,832 of 40,098 (96.8%); floors 90% and 95%.
The ten not matched are mid-term list members, already carded against house
(`who-left-the-house-mid-term-is-not-in-the-results-files`).

Fast tier `registers/hansard`: 17 passed, none skipped. A mutation (drop role-only turns) turns the real-data test
red. Root tests: all green except `tests/test_generators.py`, red only because the lessons index lacks the new
lesson (generated; mine to leave). That run left `lessons/INDEX.md` modified, uncommitted, in the working copy; the
fence refuses me restoring it.

For you at the merge:
1. Move `registers/hansard/position/hansard.md` to `docs/legal/positions/hansard.md`.
2. **Add `hansard.parliament.nz` to `HELD` in `support/fetchgate`** ("ruling 78: not captured by the estate;
   challenge since about 5 October"), and `parliament.nz` too unless another lane's position needs it: the position's
   `hosts:` line would otherwise open the gate to them.
3. Append `profile-proposed.jsonl` (`hansard-export` v1) to `support/profiles/profiles.jsonl`.
4. Load: `registers.hansard.load` (`qv4-hansard-load` is its run record). No live job queued; hansard-2 proposes the
   nightly one after `qv4-mcp-pull`.

Lesson: an-honorific-after-the-comma-survives-the-shared-name-reader.

## Result (integrator, 26 October 19:45 NZDT)
Merged 1a35c33 (gate green at the second run; the first was refused by the profile count test alone, now 138 with `hansard-export`). Done at the merge: the position moved to `docs/legal/positions/hansard.md`; `hansard.parliament.nz` and `parliament.nz` held in the fetch gate (ruling 78; no other position names them); the profile appended; the lessons index regenerated. Loaded by the gate's staging step and published: `pub.hansard_sittings` 137, `pub.hansard_sections` 3,923, `pub.hansard_speeches` 47,243, set aside 0. Released; `qv4-board` restarted. Ruling 97 recorded on the branch: the old estate's parliament.nz pages are these 2,892 transcripts, so the parliament half of 97 is this export; 120 Ombudsman PDFs left aside. hansard-2 (the MCP's index join; the provider is asked for a `parliament-hansard-debates` corpus by pdftotext) after mcp-1. Branches and the working copy retired.
