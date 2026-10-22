# local-elections-1: the local election candidate returns lane: survey, position, listings captured and read, returns held by hash
branch: session/local-elections-1 (pushed; HEAD)
session: local-elections-1 (Opus)
raised: 2026-10-22
claims: registers/local_elections/ (survey.py, survey.md, listings.tsv, capture.py, read.py, load.py, check.py, tables.sql, publish.sql, sample.py, sample.list, spec.md, pane.md, README.md, profiles-proposed.jsonl, jobs-proposed.toml, views-note.md, position/local-election-candidate-returns.md, tests/ (5 files, 40 tests)); docs/status/local-elections.md; cards four-councils-terms-bar-automated-access-so-their-returns-are-not-held, nine-councils-challenged-or-refused-the-returns-survey, a-second-survey-for-the-councils-whose-returns-page-was-not-found, the-local-election-returns-need-their-reading (findings), the-local-elections-lane-position-profiles-floors-views-and-jobs-into-place (blocker, for this merge); queue whether-to-ask-the-councils-whose-terms-bar-automated-access (no default); lessons read-a-publisher-s-terms-in-a-pass-before-its-first-listing-request, a-seed-s-year-belongs-to-the-seed-page-alone

Step 6.3, local election returns, council by council. Ruling 79: no reader is built and no return is opened;
the table comes from the councils' structured listing pages only.

- **Survey** (`survey.md`): no collected source for 2019 on (electionz.com's returns pages stop at 2013; the
  other contractor, LGNZ and Vote Local hold none). The 78 councils' pages found by web search (addresses only),
  then every terms page and returns page asked through the gate: 410 requests, daytime, 5 s or the crawl delay.
  43 councils seeded (`listings.tsv`, 66 pages); 4 held on their terms (Auckland, Christchurch, South Waikato,
  Waimakariri bar scrapers: queue, no default); 9 failed reads, not retried (Incapsula, a CAPTCHA, 403s, a
  Radware redirect); 22 not found (carded). s 112F: the 2019 returns' seven years ended 12 October 2026, so
  the files pass takes the oldest election first.
- **Position** (`position/local-election-candidate-returns.md`, 82 hosts): the four questions; terms in four
  classes, each cited by sha256 and tested against the stored page.
- **Capture**: the listings pass, 110 requests, 89 pages, none blocked; 2,183 returns wanted. The files pass
  runs from the session tonight, 22:00 until it stops itself at 06:00, into `scratch_local_elections_capture` of
  `querynz_v4_sample` (each return once, oldest election first, one request at a time, 5 s or the crawl
  delay). At 22:32: 204 landed; 50 answered 404 though still listed (Central Hawke's Bay 2019, Hastings 2017 and
  others: taken down, it seems, as s 112F's seven years end); Dunedin and Northland answered 403 (failed reads,
  not asked again in the run); Hutt City's returns are on `hccpublicdocs.azurewebsites.net`, which the gate
  refused until the position named it (named since, alone). At about 5 files a minute the night will not finish:
  the run appends its final counts below, and what is still wanted goes to `qv4-local-elections-files`.
- **Profiles** (`profiles-proposed.jsonl`): `council-returns-listing`, `council-returns-results-table`,
  `council-returns-hub`, `local-candidate-return-file` (role hold).
- **Table** (`read.py`, `load.py`): 2,183 returns from 43 councils (2017: 13, 2019: 448, 2020: 7, 2021: 11,
  2022: 759, 2023: 9, 2024: 89, 2025: 839, 2026: 8); 204 combined files; council, year, by-election, the
  candidate as listed, the seat as listed, the kind as listed, the file's hash once held, the listing page
  cited by hash. No amount, no donor, no address.

## For the integrator

1. Add `local_elections` to `support/db` `LANES` (no private twin).
2. Move `registers/local_elections/position/local-election-candidate-returns.md` to `docs/legal/positions/`
   (the position test reads either place). It names `electionz.com`, `electionservices.co.nz`, `lgnz.co.nz`,
   `votelocal.co.nz`, `voteauckland.co.nz` and the councils' hosts; `legislation.govt.nz` and `dia.govt.nz` stay
   with their own positions.
3. Append the four lines of `profiles-proposed.jsonl` to `support/profiles/profiles.jsonl` (version 1 each);
   remove the file.
4. Gate floors: 5 s for every host in `listings.tsv` (43 councils; the robots crawl delays of 7, 10 and 30 s
   still bind where larger). One line in `FLOORS` per host, or one comment block.
5. Adopt the session's capture into the live database, with no request to any host:
   `QV4_INTEGRATOR=1 python -m registers.local_elections.capture adopt /home/user/querynzv4-work/scratch/local-elections-1/capture-list.jsonl`
   (written when the night's run stops; pages and files land from the document store by hash, with their states).
6. Load: `registers.local_elections.load.load(conn, staging)`, then `publish(conn, staging)`.
7. Jobs: append `jobs-proposed.toml`'s three (`qv4-local-elections-listings`, `-files`, `-load`, priorities
   74 to 76: renumber if another lane took them); remove the file.
8. The two `pub.local_election_*` views on the board in the merge after this one (`views-note.md` has the
   catalogue entries).
9. Regenerate the queue, the card board and the lessons index.
10. Arthur's to clear later: the scratch schemas `scratch_local_elections_capture`, `_full`, `_1` in the sample
    database, and the scratch folder (it holds the survey's unlanded bytes of the four held councils' pages).

## Fast tier

Lane folder green: 40 tests, 39 s with the fill (`bin/fast registers/local_elections`); 4 mutants of the reader
each caught by a real-data test. Whole repository with `--no-fill`: RED in 546.5 s, only on
`tests/test_generators.py` (`docs/board.md` stale: blockers open 7 → 8 from this lane's blocker card; the queue
and lessons index likewise), which step 9 clears. Target 300 s missed (recorded).

## The night's files pass (appended by the session's run when it stopped, 2026-10-23T01:13+13:00)

- pass 2: 2026-10-22 22:00 to 2026-10-23 01:13, 1793 requests, 1603 landed, 190 failed; every wanted file asked
- files by state: landed 1603, wanted 391, not found 185, blocked 4
- landed of listed, by election year: 2017: 1 of 13, 2019: 330 of 448, 2020: 4 of 7, 2021: 11 of 11, 2022: 543 of 759, 2023: 9 of 9, 2024: 89 of 89, 2025: 609 of 839, 2026: 7 of 8
- landed by kind: pdf 1595, image 7, other 1
- the capture list for step 5: /home/user/querynzv4-work/scratch/local-elections-1/capture-list.jsonl (2272 lines); files still 'wanted' are asked by qv4-local-elections-files once installed

## Result (integrator, 23 October 2026 02:12 NZDT)

Merged into main as 153215b (`merge integrate/local-elections-1: gate green`). Branch `integrate/local-elections-1` from `session/local-elections-1` (9ee97ca), main merged. Card `the-local-elections-lane-position-profiles-floors-views-and-jobs-into-place`, now closed: `local_elections` in the lane list, schema applied on both databases; the position moved to `docs/legal/positions/` (the lane's test reads the moved place); the four profiles appended as version 1 (137 slugs), the proposed file removed; floors 5 s for 40 of the 43 councils' hosts (Clutha at 7 s, Dunedin and Tauranga already floored by procurement-1) and for Hutt City's document host; three jobs at priorities 81 to 83 (renumbered from the proposal's 74 to 76), `support.scheduler check` green (77 job types). The jobs entered the catalogue disabled, because a job new to the catalogue runs at once from the main checkout's working tree (the worker finding card); after the merge the integrator ran the adopt (89 listing pages and 2,183 return files carried from the night's capture list, every hash in the store, no request to any host) and enabled the jobs in the records commit. Fast tier: green in 616 s (target 300 s missed, recorded); the first gate was refused by the board's outside check on councils-1's three uncatalogued views, catalogued on this branch, the second gate green. The two views go on the board in the merge after this one. Arthur's to drop in the sample database: `scratch_local_elections_capture`, `scratch_local_elections_full`, `scratch_local_elections_1` and the lane's test scratch schema; and the session's scratch folder, which holds the survey's unlanded bytes of the four held councils' pages. Branches and worktree retired.
