# candidate-returns-1: the candidate returns lane: capture by hash, the Commission's listing and spreadsheets, totals, Part A
branch: session/candidate-returns (pushed; 88269a0)
session: candidate-returns
raised: 2026-10-20
claims: registers/candidate_returns/ (new `commission.py`, `join.py`, `declaration.py`, `donors.py`, `load.py`, `replay.py`, `private.sql`, `profile-proposed.jsonl`, tests `test_candidate_returns.py`; capture, read, check, tables, publish, sample, sample.list, pane, spec); cards `the-candidate-return-scans-need-their-page-readings`, `eleven-candidate-returns-differ-from-the-commission-s-spreadsheet`, `the-candidate-return-part-a-sets-aside`, `the-2022-tauranga-by-election-has-no-commission-figures-held`; lessons `every-lane-fills-one-sample-schema-so-its-tables-carry-its-name`, `keep-the-hash-of-a-form-s-example-row-never-its-text`; docs/status/candidate-returns.md

Step 4.1, built. Every change measured on all 1,105 in-window returns,
replay only (`python -m registers.candidate_returns.replay run|compare|shape`;
readings it stores go to the session's scratch; `shape` shows a page with
every name and address as `x`). No model is called.

- Capture (case 1 of 1.10): the 2020 and 2023 general elections' and the
  2022 Tauranga by-election's returns under the old folder's
  `var/staging/ec-donations/` (1,714 files, 1,105 documents by hash), read
  only; 2011 to 2017 left where they are (ruling 347). Landed beside them:
  the Commission's 58 listing pages and the newest summary spreadsheet per
  election that is a table (the 22 August 2024 `.csv` is a challenge page,
  refused).
- Profiles before readers: four proposed in `profile-proposed.jsonl`
  (`ec-candidate-return-text`, `-scan`, `ec-candidate-returns-listing`,
  `-summary`).
- Join: by the listing row that links the file (1,049), else by name on
  one listing row (15) or spreadsheet row (29), else the by-election's file
  name (12); two answers abstain; a path with no year takes the printed
  title's. Replaced only as the Commission states it (its listing
  publishes the amended version): 15.
- Totals: text layer or the page reader's stored reading, replayed; figures
  given to labels by each section's own arithmetic. 372 rows, 733 set
  aside (713 scans without a stored reading, carded as a scheduler job);
  the catch log reconciles.
- Outside check: current returns against the spreadsheet to the cent: 353
  equal, 11 differ (carded with both figures).
- Part A: 175 donor rows on 81 returns, each part adding to its own printed
  totals; the form's example row dropped by the hash of its cell; addresses
  only in `candidate_returns_private.addresses`; 20 parts set aside.
- Published: `pub.candidate_return_totals` (the Commission's figures beside
  ours, status, `replaced_by`), `pub.candidate_return_donors` (no address).

For the integrator:

- Append the four lines of `registers/candidate_returns/profile-proposed.jsonl`
  to `support/profiles/profiles.jsonl` (each version 1) and remove the file.
- Load: `registers.candidate_returns.load.load(conn, staging)`, then
  `publish(conn, staging)`. No job yet.
- In the shared sample schema the lane's tables carry its name. Four stale
  unprefixed tables in `scratch_candidate_returns` were renamed
  `zz_stale_candidate_returns_*` (DROP is refused); they go when that
  scratch schema is next made.

Fast tier: module green (22 tests, 1.2 s); whole repository green with
`--no-fill` (255 s).

## Result (integrator, 2026-10-20 12:26 NZDT)

Merged into main as 2704623 (merged main first). Done at the merge: the
four profiles appended to the ledger (`ec-candidate-return-text`,
`-scan`, `ec-candidate-returns-listing`, `-summary`, each at version 1);
a lesson's rule cut to the limit; records regenerated. Fast tier and
gate green; the gate's load and publish: `pub.candidate_return_totals`
372, `pub.candidate_return_donors` 175. In the records commit after the
gate: the two views in the board's catalogue (`candidate_returns` moved
from "not held"), and the job `qv4-read-pages-candidates` (priority 25,
profile `ec-candidate-return-scan`, 300 dots, prompt "OCR") in the
scheduler's catalogue with the 713 documents set aside at stage `read`
queued as its pieces; the lane rebuilds when they land. Arthur's to
clear: the `zz_stale_candidate_returns_*` tables in the session's scratch
schema and the scratch folder. The session ran headless from the
integrator as Opus, about 95 minutes.
