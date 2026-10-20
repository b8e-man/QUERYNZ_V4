# candidate-returns-2: Part A from candidate copies and pixels, the scanner-layer rule, the eleven differences judged, the re-read list
branch: session/candidate-returns-2 (pushed; 7d1b48e)
session: candidate-returns-2
raised: 2026-10-21
claims: registers/candidate_returns/ (new `pixels.py`; `donors.py`, `read.py`, `replay.py`, `sample.py`, `sample.list`, `spec.md`, tests); cards `eleven-candidate-returns-differ-from-the-commission-s-spreadsheet` (closed), `the-candidate-returns-sample-s-no-reading-case-is-read-by-the-live-job` (closed), `the-candidate-return-part-a-sets-aside`, `the-candidate-return-scans-need-their-page-readings` (updated); lessons `the-commission-s-spreadsheet-can-carry-an-amended-return-s-old-figures`, `a-full-page-picture-under-typed-text-is-not-always-a-scan`; docs/status/candidate-returns.md

Step 4.1, the sample tranche (ruling 62: no page reader queued; the 60
scans read on 20 October are the sample). Every change measured on all
1,105 in-window returns, replay only; no model called, nothing fetched.

- Part A on candidate copies of the form without the part's heading:
  known by `TOTAL FOR PART A`; 7 of 8 publish (26 rows); a money note in a
  cell never ends a name.
- Part A from pixels (`pixels.py`, the party-returns lane's stacked route
  copied): 12 scans publish (20 rows), each reconciled to its printed total
  and the declaration; pages read column by column are refused. A Part A
  the declaration left blank is no longer taken for nil (4 returns).
- A declaration on a scanner's text layer (pdfimages: a full-width image)
  stands only on its printed total: two misreads the Commission had right
  (`ca579c46524e`, `98161ad95f6d`, both looked at) are set aside. Measured
  against routing every picture page to the page reader, which cost 12
  rows equal to the Commission.
- The eleven-returns card closed with a verdict for each of 13 (5
  amendments the listing agrees with us on; 5 Commission typing; 2 the
  Commission's own figure; 1 return contradicting itself).
- Part D (one return, $140) and Part H (no loan declared) measured: no
  reader.
- `replay rereads RUN.json`: 668 returns, 6,287 pages, one line each with
  hash, stage and pages: the page-reader queue when the build is done.
- The sample's no-reading case is read against an empty store
  (`key: empty-store`), so the assertion is one outcome again; four new
  cases.

Totals: 412 rows (from 372), 391 equal to the cent, 13 differ; Part A 221
rows on 100 returns (from 175 on 81), 26 parts set aside.

Correction: commit 121300c's message says Part A from pixels on 15
returns; it is 12 (20 rows).

Fast tier: module green (27 tests, sample filled over 127.0.0.1: node2's
10.0.0.x link was down this session, so `db-primary` did not answer).
Whole repository with `QV4_NO_DB=1 --no-fill`: one red,
`checks/tests/test_windowed_check.py` (the tenancy_tribunal live check, "no
answer in 120 s"), outside this lane and down to the same link.

For the integrator: no profile change, no job. Load and publish as before.
The view's columns are unchanged.

## Result (integrator, 2026-10-21 10:28 NZDT)

Merged into main as 84f6b41 (merged main first). Done at the merge: the
live `candidate_returns` schema reloaded by the gate (1,105 returns: 412
rows, 693 set aside, reconciling; 30 Commission lines; 98 s) and published;
`qv4-board` restarted; board, lessons index and queue regenerated. No
profile, catalogue or job change; the `replay rereads` list (668 returns,
6,287 pages) is the page-reader queue for when the build is done (ruling
62). Two cards closed by the session carry their dates; two lessons
indexed (216 and 227 characters). The whole-repository red the request
reports (the windowed tenancy check) was the cable outage; the gate ran
with the link restored and was green first time.
