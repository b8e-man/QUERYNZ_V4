# fix-registers-ministers-diaries-1: ruling 102 on the ministers' diary register
branch: fix/registers-ministers-diaries-1 (pushed; c83cd7d)
session: fix-registers-ministers-diaries-1 (Opus)
raised: 2026-10-27
carries: diaries-2 whole (integrate/diaries-2 merged in at 224c1b6; not yet on main)
claims: registers/ministers_diaries/, docs/status/ministers-diaries.md, the deletion of queue item `may-a-diary-entry-show-a-bare-street-address`

Ruling 102: hard limit 15 binds the products, not the board or the published views.

## What changed

- `pub.minister_diary_entries` carries `meeting`, `attendees` and `location` whole, as released. Nothing is withheld or masked in a view; the release's own withholdings ("Withheld under s9(2)(f)(iv)" and the like) stay as printed and are counted in `withheld` as before.
- Four boolean flags beside them, set at the load by shape (read.py `location_flags`, `names_address`; `read.FLAGS`): `location_names_home` (the release's words name a home or residence), `location_street_only` (a street address with no place of business named), `meeting_names_address`, `attendees_names_address` (a street address in either). A product applies hard limit 15 at its own surface by these flags. The address shape is the street shape this lane already found (its `STREET`); the Gazette lane's legal-description and numbered shapes are not added, so the counts stay comparable with diaries-2's.
- Columns gone: `entries.location_held`, `entries.addresses_masked`; `releases.locations_held` is now `locations_flagged`. `ministers_diaries_private.entries` keeps only `key, text` (the provider's joined text, still never published).
- The load's line and `check.py` state the flagged entries by key; the check's other figures are unchanged. sample.list's comments and the sample's hard cases are updated; pane.md says the board shows the three columns whole with a note per flag.
- **Queue item closed**: `docs/decisions/queue/may-a-diary-entry-show-a-bare-street-address.md` deleted. Answer: on the board yes, in a product by the flag.
- `position/ministers-diaries.md`: the diaries paragraph now says the same (ruling 102), with a line for the lawyer.

## Full build in scratch (querynz_v4_sample.scratch_diaries_2_build, from scratch_mcp_1_pull2, rebuilt in 13 s)

`registers.ministers_diaries.check --owner`: green. 208,464 of 208,464 taken; 230,554 documents = 208,464 entries + 22,090 older versions; measure words 4,764,189 = 4,764,189; 2,560 releases. Withholdings 2,126 entries / 6,824 fields. Flagged entries (counted, never printed): location_names_home 115, location_street_only 3,096, meeting_names_address 32, attendees_names_address 11 (the 3,211 locations and the 43 addresses diaries-2 held back).

## Checks

`QV4_INTEGRATOR=1 bin/fast registers/ministers_diaries`: green, 25 tests in 59.7 s. Proven to fail: with `names_address` weakened to always false, three tests went red (one unit, two on the sample); the edit was reversed by hand. Whole-repository fast tier not run; diaries-2's request records its two unrelated reds.

## For the integrator at the merge

1. Merge this branch in place of `session/diaries-2` (it carries it); then do diaries-2's own list (its request, items 1–7): LANES, the profile, the position fold, the job.
2. Regenerate `docs/decisions/queue.md` (the item is deleted) and the lessons index.
3. The board pane for the two views comes in a later merge as diaries-2 said; it shows the columns whole (ruling 88, 102).
4. `scratch_diaries_2_build` and `scratch_fix_registers_ministers_diaries_1` are Arthur's to drop once merged.

Lesson: nothing new.

## Result (integrator, 27 October 12:10 NZDT)
Merged a48633c as `integrate/diaries-parliament` (diaries-2 with fix-registers-ministers-diaries-1, parliament-1 with fix-registers-parliament-1), gate green at the second run, 27 October 12:10 NZDT. The first run passed every test and failed in the staging load: the staging schema's name was cut at Postgres's 63 bytes, so `<schema>_private` was cut back to the public schema's name and the diaries' two `entries` tables collided; support/staging now leaves room for the suffix (a3dd295, with tests). Done at the merge: `ministers_diaries` and `parliament` in support.db's LANES (92 schemas applied on both databases); four profiles appended (`mcp-diary-entry`, `mcp-parliament-written-question`, `mcp-parliament-api-item`, `mcp-parliament-wayback-page`; count 146 with hansard-2's two); the diaries paragraph folded into docs/legal/positions/beehive.md and the parliament position moved to docs/legal/positions/parliament.md; `qv4-ministers-diaries-load` nightly 04:20 NZDT (priority 87) and `qv4-parliament-load` nightly 04:30 NZDT (88); the two deleted queue items gone from the roll-up. Released; the worker restarted for the two jobs. The staging load built both lanes from the adopted live documents (the fast adopt finished 11:20): diaries 2,560 releases, 208,464 entries (22,090 older versions, 2,126 entries with a withholding, 3,096 locations street-only, 115 naming a home, 0 set aside); parliament 695,115 rows in 69 s. Their five views go on the board in the next gate (fix-products-board-2, raised). Branches and the working copies retired.
