# local-elections-1: where the lane stands

**Date:** 2026-10-22, 22:4x NZDT. **Lane:** `registers/local_elections` (step 6.3), Opus, node2.

## Done (each a tranche with real-data tests: 40 green, fast tier 39 s)

- (a) Survey: no collected source for 2019 on (electionz.com stops at 2013); 78 councils' pages and terms
  asked through the gate (410 requests). 43 councils seeded (`listings.tsv`, 66 pages); 4 held on terms
  (Auckland, Christchurch, South Waikato, Waimakariri: no scrapers); 9 failed reads (challenge, CAPTCHA,
  403); 22 not found. Position drafted in `position/` (82 hosts). `survey.md` is the record.
- (b) Listings pass: 110 requests, 89 pages landed, 0 blocked; 2,183 returns wanted. Four profiles in
  `profiles-proposed.jsonl`.
- (c) `read.py` over the listings only: 2,183 rows (2019: 448, 2022: 759, 2024: 89, 2025: 839, by-elections
  45), 204 combined files; no return opened (ruling 79).
- (d) `load.py` on the staging contract; `pub.local_election_returns` and `_coverage` proven in
  `querynz_v4_sample`; `views-note.md`; three jobs proposed in `jobs-proposed.toml`, not installed.

## Half-done

- The files pass runs 22:00 to 06:00 into `scratch_local_elections_capture` of `querynz_v4_sample` (at 22:32:
  204 landed, 50 gone (404), Dunedin and Northland 403). It will not finish tonight (about 5 a minute). When it
  stops, `tools/after-night.sh` in the scratch folder writes `capture-list.jsonl` and appends the counts to the
  merge request; the integrator adopts it (no second fetch) and the files job asks the rest.

## Next

- Merge request raised (`merge-requests/local-elections-1.md`).
- Cards: a second survey (22 councils, Tasman's folders, the HTML-only returns), the returns' reading (after
  node1), the held and the failed councils. Queue: `whether-to-ask-the-councils-whose-terms-bar-automated-access`
  (no default).
