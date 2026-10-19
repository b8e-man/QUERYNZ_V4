# companies-1: the companies lane, from the old estate's loaded monthly files
branch: session/companies (pushed; 20df32c)
session: companies (session 1)
raised: 2026-10-20
claims: registers/companies/ (capture, read, check, tables, publish, sample, spec, pane; new `load.py`, `profile-proposed.jsonl`, tests `test_companies_lane.py`); cards `the-companies-office-statistics-file-has-no-legal-position`, `the-old-loader-folded-shareholdings-and-kept-no-role-numbers`, `no-monthly-company-file-is-held-for-the-18-november-step`; queue `the-company-package-carries-sole-traders`; lesson `a-loader-s-own-run-counts-are-the-items-in`; docs/status/companies.md

Step 4.1. No raw monthly file survives on either box: the old runbook
deleted each package after loading. So the loaded tables of the two files
the old estate holds (`companies-2026-07`, loaded 14 July; `companies-2026-08`,
16 August, cut 3 August) were exported once on 20 October 2026 05:56 to
05:57 NZDT through the old read-only login (statement limit, read-only
transaction, server-side cursors; 48 s) into four gzip JSON-lines parts,
pinned in `capture.EXPORTS`: entities 736d1f81…, directors 62d0a8e1…,
shareholders a466343d…, addresses e3f3cf09…. Nothing runs the export at
load; every row says "taken from the old estate's tables; original not
held" and cites its part's hash and line. `bulk.director_addresses` is not
read; no part carries a person's address.

Reading, measured on every real row, not the sample:

| Table | Rows | Catch log |
| --- | --- | --- |
| entities (companies 1,821,454; other incorporated 59,981; charitable trust boards 35,599; public sector 2,922; retirement villages 512) | 1,920,468 | 0 |
| entity_states (a July state the August file changed) | 5,629 | |
| directors | 1,185,805 | 15 NZBN-API rows, 2 with no name; folds 168 (July), 172 (August) |
| shareholders | 1,581,955 | folds 20,725 (July), 20,688 (August) |
| registered_offices | 867,277 | 82 empty, 1,328 exact repeats |

Every export line is a row or a catch-log line, and each file's rows plus
its folds equal the old loader's own count for that file (asserted; a file
giving more rows than it had raises). Keys: an entity's NZBN, else its
register number; a role is the company plus its filed content (the file
gives no role or allocation number); a registered office is the entity,
its start and a hash of its lines. No end date is carried: the old
loader's import-day ceasings are dropped, and a role's window is the files
it is in (`first_file`, `last_file`, `in_latest`). 314 shareholdings name
204 NZBNs the entity file does not hold; kept and counted.

Outside check (`check.py`, exits 1): the Companies Office's own statistics.
Live companies on the last quarter end before the cut, 30 June 2026:
756,999 against 756,821 (+0.02%; tolerance 0.1%). Monthly incorporations,
April 2025 to July 2026: equal, or within one. Removals within 1%
(tolerance 2%). Green on all real rows (computed from the full reading;
the SQL path is tested on the sample). The figures are pinned from the
Office's page because no legal position yet covers its host (card).

Fast tier: the lane's 20 tests green on the sample (20 NZBNs or numbers,
each a named hard case). Whole repository: one failure,
`tests/test_generators.py`, because my cards and lesson make the board and
lessons index stale (generated; yours to rebuild). The test rewrote
`docs/board.md` in my working copy and the fence will not let me restore
it; it is left uncommitted.

For the merge, please:
- Append `registers/companies/profile-proposed.jsonl` (profile
  `companies-register-export` v1) to `support/profiles/profiles.jsonl` and
  delete the proposed file.
- The four parts are in the store (`/mnt/hdd2/qv4-docs/`), landed by my
  sample fill; the copies in `/home/user/querynzv4-work/scratch/companies/export/`
  can go once you have seen them there.
- The full load is about 5.6 million rows (the reading takes about 60 s
  and 7 GB of memory); I did not load it into a scratch schema, so its
  load time and the SQL check on it are first measured at your staging
  step.

Nothing new beyond the lesson filed.

## Result (integrator, 2026-10-20 06:37 NZDT)

Merged into main as 7042a65 (merged main first). Done at the merge: the
profile `companies-register-export` v1 appended to the ledger, the
proposed file removed, the shipped-profiles test at 44; board, lessons
index and queue regenerated. Fast tier and gate green; the gate's staging
load, the first full one: 1,920,468 entities, 5,629 states, 1,185,805
directors, 1,581,955 shareholders, 867,277 registered offices, in 171 s
after about 60 s of reading; published. `companies_private` is readable
by the owner only, checked after the publish. The legal-position card
for the Office's statistics page is covered by ruling 61 (before product,
not before capture). The export copies under
`querynz_v4-work/scratch/companies/export/` are another session's
scratch: Arthur's to remove. The session ran headless from the
integrator, about 60 minutes.
