# gazette-5: mortgagee entries into possession; the Registrar's rectifications, amalgamations, transfers out and deeds under ot

Branch `session/gazette-5`: 2 commits, on top of a merge of `session/gazette-4` (d955d08), which was not yet on
main when this session started. **Merge gazette-4 first.** This branch then adds only its own two commits. Scope
`registers/gazette/`, plus this session's cards, lessons and the lane's status file.

## What it claims

Everything was measured on every notice, through a full load of all 207,133 notices through this branch into
`scratch_gazette_5_full` in `querynz_v4_sample` (127 s). The register rows came from `querynz_v4`'s `pub.companies`
through the read-only login. `python -m registers.gazette.check --schema scratch_gazette_5_full --database
querynz_v4_sample` exits 0. Unread notices fell from 80,865 to 76,803.

**1. Mortgagee entries into possession (`gn`)**, card `mortgagee-entries-into-possession-in-the-gazette-are-unread`,
now closed. Reader `possessions.py`, proposed profile `gazette-mortgagee-possession`.

- New table `gazette.possessions` and view `pub.gazette_possessions`: one row per notice.
- New private table `gazette_private.possession_details`, owner-only like the bankruptcy addresses. It holds the
  property (often a home's address), the goods' description and registration/VIN numbers, and every person's name.
- 3,002 notices. The lender is named on 2,899 (96.6%) and the day of entry on 2,951 (98.3%).
- 2,449 of 2,864 company lenders are joined to the companies register (85.5%). The rest are mostly custodian
  companies renamed or removed since, and building societies, which that register does not hold.
- Borrowers: 339 are companies (330 shown, 306 joined), 136 are people (private only), and 2,441 notices name none.
- In one template the borrowers' names run straight into the lender's ("in the matter of <persons> <lender>
  Limited"). Such a name is shown only as the tail the register holds, else not at all (37 rows).
- A lender printed without its "Limited" ("GE Custodians") is joined with it added. This is a new tier,
  `register.NAME_LIMITED`, 248 rows.
- A possession notice's title is published cut before any property it names.
- Check floors: 95% named, 95% with a day, 82% joined. The check also fails if any published possession title
  carries a digit, or if any person is shown as a borrower.
- Receivers' appointments over mortgaged property stay with the appointment profile.

**2. The Registrar's other `ot` notices**, card `amalgamations-and-the-registrar-s-rectifications-under-ot-are-unread`,
now closed. Reader `companyacts.py`, four proposed profiles, all into `gazette.company_notices`:

| Kind | Profile | Notices read | Rows | Joined | Floor |
| --- | --- | --- | --- | --- | --- |
| rectification | `gazette-register-rectification` | 486 of 503 | 2,877 | 99.7% (85.1% agree by name) | 97%, name 80% |
| amalgamation | `gazette-amalgamation-proposal` | 369 | 1,000 | 73.1% | 70% |
| transfer out | `gazette-transfer-out` | 167 | 168 | 95.8% | 92% |
| deed of company arrangement | `gazette-deed-of-company-arrangement` | 21 | 39 | 89.7% | 85% |

- **Rectifications.** What is corrected is kept only as words from a fixed list (`ground`), never the sentence.
  The people a correction names (`people_named`, 867 rows) and an applicant who is a person (`party`, 467) are
  kept by initials and surname only; a name that doesn't reduce to that form is dropped. A unit test asserts no
  given name or address survives. On the full load every `people_named` value has that form.
- **Amalgamations.** `role` marks the company that continues (163). 205 proposals name none to continue (a new
  company is formed); each is a catch-log line and its companies are kept. Most unjoined amalgamation rows are from
  2000-2009, under names the register no longer holds.
- **Transfers out.** `ground` is where the company goes (the British Virgin Islands 21, Australia 17, …).
- **Deeds of company arrangement.** The deed administrators are practitioner rows (20).
- 198 `ot` notices stay unread: extensions of time to register a charge, court applications, and industrial and
  provident society notices.
- **Schema change.** `company_notices` gains two columns, `role` and `people_named`. They are last in
  `pub.gazette_company_notices`, so `CREATE OR REPLACE VIEW` holds on the live view.
- **check.py.** A kind whose titles are company names (transfers out, most amalgamations) is seen by its rows.
  A restoration that also corrects the register stays a restoration.

**Profiles.** Five lines appended to `registers/gazette/profile-proposed.jsonl`, all version 1, after gazette-4's
three, which are untouched. Please append all eight to the ledger.

## For the board and the templates (not edited; yours)

- `products/board/catalogue.py` has no entry for `pub.gazette_possessions`. A pane can follow its `pane.md`
  paragraph: lender and company borrower with their register keys, asset, action, day and basis, and
  `property_held`. It has no address column to leave out.
- `gazette_company_notices` now carries `role` and `people_named`. The catalogue may want both, and the kinds'
  words (the pane has them).
- Agriculture's `register-removals` flag reads every non-insolvency company notice as a removal or restoration.
  Rectifications, amalgamations, transfers out and deeds now reach it and will be described that way.
- The report walk joins company notices by `register_key`, so a company report will list its rectifications.
  `people_named` there is initials only.

## A hard-limit slip in this session, for Arthur

While counting the possession notices' titles, before masking titles, I printed about five raw titles into this
session that name a property by street address. Some may be homes. They were not repeated, and none went into any
file, test, card, lesson or commit. Separately, one unmasked list of unmatched lender names printed a family's names
as joint lenders (no address). Both mistakes are now guarded against in the scratch tools, and the lesson
`a-gazette-title-can-carry-the-property-s-address` records them.

## Card raised

`published-gazette-titles-can-carry-a-street-address`: `pub.gazette_notices` publishes titles as printed, and 1,642
`ln` titles and 57 others (`al`, `ds`, `ar`, `go`, `md`, `ot`) look like street addresses. This branch cuts only the
possession titles. Recommended for the next gazette session: cut every section the same way and add a check.

## Notes for the gate

- The fast tier for `registers/gazette` is green (67.7 s, over the 60 s target; recorded). The whole repository is
  red on one test only, `test_generators`: `docs/board.md` and `lessons/INDEX.md` are stale (one new card, two
  closed, two new lessons). Both are generated and yours to rebuild. The test run rewrote `docs/board.md` in this
  working copy and the scope hook won't let me restore it. It is uncommitted and not part of the branch.
- The gate's load needs `pub.companies` and `pub.members` published first, as before. Nothing fetches and no job
  is added.
- New scratch schemas in `querynz_v4_sample`: `scratch_gazette_5_full` and `scratch_gazette_5_full_private` (the
  second holds possession details, owner-only). A pickle of the register rows sits in
  `/home/user/querynzv4-work/scratch/gazette-5/`. Drop all three when you like.
- Lessons: `a-gazette-title-can-carry-the-property-s-address`, `keep-a-correction-as-fixed-words-and-its-people-as-initials`.
- Left alone, as briefed: disciplinary findings and confiscation orders (queue item, default no), and the cards
  `appointment-notices-whose-appointees-run-together-are-unread` and
  `annulled-bankrupts-the-reader-cannot-name-stay-published-on-earlier-rows`.

## Result (integrator, 2026-10-21 07:28 NZDT)

Merged to main at ea7f5ad, gate green. The eight proposed profiles are in
the ledger (67 to 72), the proposal retired; two lessons' rules cut to the
limit. The board's entries for `pub.gazette_possessions` and the two new
company-notice columns are the integrator's next board commit. The
session's hard-limit slip (about five raw titles naming a property by
street address printed into its own transcript, and one list of lender
names) is reported to Arthur. The titles card goes to gazette-6, launched
now. Worktree and branch retired.
