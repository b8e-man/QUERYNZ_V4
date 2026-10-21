# tenders-1: the GETS award notices, read and checked (step 6.2, template 1's register)
branch: session/tenders-1 (pushed; 61ff9d9)
session: tenders-1 (Opus)
raised: 2026-10-21
claims: registers/tenders/ (capture, read, load, check, tables, publish, sample, pane, spec, six proposed profiles, the draft position, tests); docs/status/tenders.md; three cards; one queue question; one lesson

The Ministry of Business, Innovation and Employment's open data of GETS
award notices (CC BY 3.0 NZ, attribution required): eight CSVs, historic
(July 2014 to June 2019) and current (July 2019 on), and a schema workbook.

- **Capture.** The ministry's host answered 403 to the estate's
  User-Agent on 21 October and `www.data.govt.nz` showed an Incapsula
  challenge (hard limit 6: failed reads, logged in
  `tenders.capture_set_aside`, not got around). The catalogue answered and
  lists the same MBIE URLs, so there is no second copy. The lane therefore
  copied the old estate's raw files of 14 August (`~/source-raws/gets-2026-08-14/`,
  plan 1.10 case 1) by pinned hash, with the catalogue's description,
  into `querynz_v4` (`tenders.capture_*`, `docs.*` source `tenders`: 10
  documents). The old-path names of that run were written straight into
  `docs.names` before the one-way test caught it; the code now lands them
  through the wrapper. The quarterly refresh (case 3) is built and tested
  on a fake host; it asks nothing until 2 November and rests a week after a
  block.
- **Reading.** Six profiles proposed (`profiles-proposed.jsonl`), each
  recognising its file by its header line before anything is read. The full
  build gives 29,874 notices (7,314 + 22,560, the old estate's figure),
  31,264 suppliers and 3 set aside (one historic RFx ID the notices lack),
  in 2.4 s. No address, website or free text is read. The supplier file
  holds no valid NZBN (12,694 in exponent form, digits lost): kept as
  published, its shape named.
- **Check.** `check.py` green: every file's records counted afresh equal
  those read, the pinned files give 29,874, one report date per era, every
  CSV the catalogue lists is held.
- **Tests.** 43 in `registers/tenders` (3 slow), green, including a mutant
  check of 11 reading and 3 capture mutants, each caught. Whole repository
  fast tier: green except `test_generators` (the board and lessons index go
  stale from the new cards and lesson; regenerated in the tree, not
  committed, as at charities-3). 381 s, over the 300 s target.

At the merge, please (card `the-tenders-jobs-into-the-catalogue`):
1. Move the position to `docs/legal/positions/` and set `capture.POSITIONS = None`.
2. Append the six profiles to `support/profiles/profiles.jsonl`.
3. Floor `catalogue.data.govt.nz` at 10 s in the gate.
4. Add `qv4-tenders-refresh` and `qv4-tenders-load` to the catalogue (entries in the card).
5. Load and publish `pub.award_notices`, `pub.award_suppliers`; add the board views (`pane.md`).
6. Regenerate the board, the queue roll-up and the lessons index; drop `scratch_tenders_full`,
   `scratch_tenders_lane`, `scratch_tenders_slow` in the sample database.

Lesson: `a-published-identifier-column-can-hold-no-identifier-classify-its-shapes-before-keying-on-it`.

## Result (integrator, 2026-10-21 21:01 NZDT)

Merged into main as b051c04 (`merge integrate/tenders-1: gate green`). Branch `integrate/tenders-1` from `session/tenders-1` (61ff9d9), main merged. Card `the-tenders-jobs-into-the-catalogue`, now closed: the position moved to `docs/legal/positions/government-procurement-award-notices.md` and `capture.`POSITIONS`` set to None (the gate's own folder); the six file profiles appended as version 1 (92 slugs); `catalogue.data.govt.nz` floored at 10 s; `qv4-tenders-refresh` and `qv4-tenders-load` in the catalogue at priorities 57 and 58 (the card's 30 and 34 are taken), `support.scheduler check` green; the scan board views carried with it. Fast tier green in 462.5 s. The gate's first run was refused: the board's live check found `pub.award_notices` and `pub.award_suppliers` published and uncatalogued before the staging step, with the session's own read of the old estate's files in them (29,874 notices, 31,264 supplier rows); the session had run the lane's job path, which writes the live tables. The two views (Award notices, Award suppliers) were catalogued on this branch, the not-held line for tenders replaced by the register entry, and a finding card raised (`a-lanes-job-path-published-live-from-a-session-before-the-gate`); fast tier again green in 457.6 s. Gate green; staging loaded the lane from the held files: 29,874 notices, 31,264 supplier rows, 8 files, 3 set aside, 160,420 records in, 61,138 rows in 3 s, and published `pub.award_notices` and `pub.award_suppliers`; the two board views go in at the next merge. The drops of `scratch_tenders_full`, `scratch_tenders_lane` and `scratch_tenders_slow` in the sample database are Arthur's. Arthur's too: the letter to the ministry (the block on its files and the business numbers published in exponent form) and the queue item on keeping the old estate's copy (default: kept). Branches and the working copy retired.
