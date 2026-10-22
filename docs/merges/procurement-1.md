# procurement-1: step 6.3's first line: live open tenders (not captured, terms), agency contract disclosures (ACC's file built), council procurement off GETS (a watch)
branch: session/procurement-1 (45706e3; NOT pushed: the push was refused by the session's permission classifier. The commits are in the shared repository, so the branch is visible from the main checkout)
session: procurement-1 (Opus)
raised: 2026-10-22 (written to the session's scratch folder: the session could not write the inbox; copy to inbox/merge-requests/)
claims: registers/tenders/ (the listing's position, its test, the terms in sample.list, the spec's reads line); registers/contract_disclosures/ (capture, workbook, read, load, check, tables, publish, sample, sample.list, spec, README, pane, survey, views, profiles-proposed.jsonl, position/, tests); registers/council_procurement/ (capture, read, load, check, tables, publish, sample, sample.list, spec, README, pane, survey, profiles-proposed.jsonl, position/, tests); docs/status/procurement.md; cards live-open-tenders-are-not-held-the-gets-terms-bar-a-robot, councils-own-award-lists-are-not-held (findings), the-procurement-lanes-positions-profiles-floors-and-jobs-into-place (blocker, for this merge); queue whether-to-ask-the-ministry-to-read-the-gets-listing, whether-to-ask-councils-for-their-award-lists (defaults applied: not captured); one lesson

## What each source came to

1. **Live open tenders (GETS listing).** Open without a login, but the terms of 7 March 2024 (landed, sha256
   `507f5b88…`) deem a visitor to accept them and bar "any spider or robot" that copies, collects or indexes the
   site (3.2(i)(e)). Not captured; no job asks the site. The award notices' capture, load, pins and tests are
   untouched and green.
2. **Agency contract disclosures.** The one collected file is the GETS award notices, already held. No agency of 24
   surveyed by spend lists its own awards as a structured page or file (nine answered 403 or Incapsula). The
   catalogue's ACC "Health contract data" (CC BY 3.0 NZ, an OIA answer: claims and costs by contract class, region,
   authority and year, no supplier named) is captured and read by shape into `pub.agency_contract_costs`: 80,860
   rows; check.py holds them to the file's own printed totals (837 compared, 0 wrong; claims at class level are
   never summable because ACC suppresses "<4" in every authority-year). MSD's 2019/20 file states no licence: not
   landed.
3. **Council procurement off GETS.** 45 councils surveyed; the GETS file already covers 76 councils. TenderLink and
   Queenstown Lakes challenged; VendorPanel needs registration; Clutha's and Tauranga's own lists are barred for
   commercial use and Dunedin's offered on request. Nothing captured; a monthly watch of the four deciding pages,
   red the day one changes.

No model and no PDF read (ruling 79). 122 requests through the gate: 121 survey by day, serial, at least 5 s apart
(the catalogue's 10 s, Clutha's 7 s); one file at 22:00. 13 failed reads, logged, none retried. Pages landed in the
document store with the sample database's docs tables; the GETS listing and the three councils' list pages read in
the survey were never landed and were removed from scratch.

## For the integrator (nothing else)

1. Add `contract_disclosures` (with its private twin) and `council_procurement` to `support/db` `LANES`; apply.
2. Move the three positions to `docs/legal/positions/`: `registers/tenders/position/government-electronic-tenders-listing.md`,
   `registers/contract_disclosures/position/agency-contract-disclosures.md`,
   `registers/council_procurement/position/council-procurement-platforms.md`. Nothing else to set: the two new
   lanes read `QV4_POSITIONS` or the gate's default folder, and each test looks in both places.
3. Append the two proposed profiles (version 1) to `support/profiles/profiles.jsonl`; remove the proposed files.
4. Gate floors: `www.cluthadc.govt.nz` 7 s, `www.tauranga.govt.nz` 5 s, `www.dunedin.govt.nz` 5 s, `www.vendorpanel.nz` 5 s.
5. Jobs as each spec proposes: `qv4-contract-disclosures-refresh` (daily 22:40 NZDT, asks only every 28 days),
   `qv4-contract-disclosures-load` (daily 06:40), `qv4-council-procurement-watch` (daily 22:50, asks only every 30
   days). Once, before the first refresh: `python -m registers.contract_disclosures.capture --copy` (lands the three
   pinned documents from the store; no request).
6. Staging: `contract_disclosures` makes empty tables until the copy run lands the file (then 80,860 rows, 1.4 s);
   `council_procurement` publishes nothing. Both checks are red on the live database until the first runs, correctly.
7. `pub.agency_contract_costs` on the board in the merge after this one (`registers/contract_disclosures/views.md`).
8. Regenerate the board, `docs/decisions/queue.md` and the lessons index.
9. Drop `scratch_procurement_1_cd`, `scratch_test_contract_disclosures`, `scratch_test_council_procurement` in the
   sample database when done.

## Fast tier

Lane folders green: tenders 41 s, contract_disclosures 48 s, council_procurement 53 s (with the fill). Whole
repository: RED in 611.5 s only on `tests/test_generators.py` (`docs/board.md` stale from the new cards; the queue and
lessons index likewise), which step 8 clears. Target 300 s missed (recorded). Slow tier for contract_disclosures
green (the six-mutant check).

Lesson: `a-council-s-own-site-is-its-copyright-under-its-own-terms-not-crown-copyright-under-nzgoal`.

## Result (integrator, 22 October 2026 23:35 NZDT)

Merged into main as de8ec54 (`merge integrate/procurement-1: gate green`). Branch `integrate/procurement-1` from `session/procurement-1` (45706e3, pushed by the integrator: the session's push and its inbox write were refused by its permission classifier, the known card), main merged, the integrator's commits 25a… to 6d9d66d. Card `the-procurement-lanes-positions-profiles-floors-and-jobs-into-place`, now closed: `contract_disclosures` and `council_procurement` in the lane list, schemas applied on both databases; the three positions moved to `docs/legal/positions/`; the two profiles appended as version 1 (128 slugs), the proposed files removed; floors for Clutha (7 s), Tauranga, Dunedin and VendorPanel (5 s); three jobs at priorities 74 to 76, `support.scheduler check` green (70 job types). Also at this merge: the iwi directory's three views catalogued on the board (settlements-1's merge after), and `pub.agency_contract_costs` catalogued now rather than in the merge after, because the view already stood on the live database and the gate's full tier runs the board's outside check. Why it stood: the worker reads the catalogue from the main checkout's working tree, so the three new jobs ran at 22:30 while the branch was under its fast tier; the refresh landed ACC's file (so the `--copy` run is not needed), the load published the empty schema, and the watch went red on VendorPanel's 302. Finding card `the-scheduler-s-worker-runs-the-main-checkout-s-working-tree-so-an-integrate-branch-s-jobs-ran-live-before-the-gate` and lesson `a-worker-that-reads-the-checkout-runs-the-branch`, filed with this record. The settlements watch job moved from a weekly interval (Thursday 13:00 NZDT, inside the capture's daytime refusal, so every slot failed) to 23:15 NZDT nightly. Fast tier green in 618 s (target 300 s missed, recorded). Gate: `contract_disclosures` published from staging (the refresh's file is held, the 06:40 load builds the 80,860 rows), `council_procurement` published nothing, `tenders` republished unchanged. Arthur's to drop in the sample database: `scratch_procurement_1_cd`, `scratch_test_contract_disclosures`, `scratch_test_council_procurement`. Branches and worktree retired.
