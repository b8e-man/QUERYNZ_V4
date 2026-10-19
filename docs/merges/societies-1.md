# societies-1: the societies lane, from the old estate's tables and the register's entity detail
branch: session/societies (pushed; 6ba92c7)
session: societies (session 1)
raised: 2026-10-20
claims: registers/societies/ (capture, read, check, tables, publish, sample, spec, pane; new `load.py`, `profile-proposed.jsonl`, `position/nzbn-register-entities.md`, tests `test_societies_lane.py`; `test_societies_shape.py` removed, its check is the first test of the new file); cards `the-societies-capture-job-into-the-catalogue` (blocker, yours), `the-fetch-gate-returns-no-response-headers`, `the-nzbn-api-terms-and-the-copying-of-register-contents`, `stray-societies-tables-in-the-sample-scratch-schema`; lesson `a-lane-s-tables-in-the-shared-scratch-schema-carry-its-prefix`; docs/status/societies.md

Step 4.1. The old estate never kept the register's answers: its sweep
(`ops/backfill_society_officers.py`, C531) parsed each society's NZBN API
entity detail into `nzbn_canonical.public.society_officers` and replaced a
society's rows on each ask. So the tables were exported once on 20 October
2026, 07:23:25 to 07:23:27 NZDT, through the old read-only login (300 s
statement limit, read-only transactions, server-side cursors; 2 s), into
three gzip JSON-lines parts pinned in `capture.EXPORTS`: societies 1a9e66b9…
(the August file's Incorporated Society rows with their vanished rows),
officers 64692937…, asks 0fab6783… (`society_sweep_log`). The read went to
node2's database, which has been the primary since the 17 October failover
(no standby answers). The officer table has no address column. Never run at
load; every row cites its part's hash and line.

Reading, on every real row (in memory, 3 s; and a full build into my
scratch schema, 6 s):

| Table | Rows | Catch log |
| --- | --- | --- |
| societies (registered 22,787; dissolved 28,534; removed 1,931; liquidation 19) | 53,271 | 0 |
| society_states (a July state, 326 vanished rows) | 326 | |
| officers (Active 100,245; Inactive 32,835, each with the register's end) | 133,080 | 0 |
| asks | 22,787 + 5 answers | 1 line: 3 officers kept from an earlier ask |

Every line is a row or a catch-log line, and each part equals the old
table's own count in its header (asserted). Across parts each society's
officers equal its last ask's count: 22,783 equal, 3 asked and given none,
1 whose last ask failed keeps an earlier ask's 3 (logged). A society is
keyed on its NZBN; an officer on society, names and start (the register
gives no role number; 416 roles share names and start and take /2, /3 in
a fixed order of their content). Windows are the register's own start and
end; `first_read_on` and `last_read_on` are the asks that listed it, never
an end.

Per-entity capture (ruling 61; the four questions in my status file, the
draft one-page position in `registers/societies/position/`). Five pages
only, the five party societies, through `support/fetchgate.open_url` with
Arthur's key in its header, 5 s apart, no challenge, all 200, landed by
hash (`capture.PROOF`). 51 roles, every one an officer with a person, no
address value; 51 of 51 take the same key as the export gives them. An
address, where an answer carries one, goes to
`societies_private.officer_addresses` and nowhere else (tested on an
invented one). About 20 further requests read the register's search for
the check below; nothing more was fetched.

Outside check (`check.py`, exits 1): the register's own search for
registered societies by a name term, as it answered (landed by hash; its
total caps at 10,000 so it cannot count all 22,787). Party 18 of 18;
hockey 189 of 189, plus one registered after the file's cut; tennis 430 of
431 (one restored since), and 1 of our 415 not on its list. Green.

Nightly job (`capture.py --night`, tested with a fake transport): the
party societies, then the stalest seventh (about 3,300), the clock moved by
every ask including a failed one (old C531), off-peak 01:00 to 06:00 NZDT and
never the API's Wednesday 21:00 to 23:00 window, stops at a block.
Proposed by card; not queued.

Fast tier: the lane's 21 tests green on the sample (11 societies, each a
named hard case, and the five answers). Whole repository: one red,
`tests/test_generators.py` (board and lessons index stale from my cards
and lesson; yours to rebuild; my working copy's `docs/board.md` is left
uncommitted). `tests/test_imports_one_way.py` caught my first draft reading
`docs.*`; fixed, green.

For the merge, please:
- The three edits on card `the-societies-capture-job-into-the-catalogue`:
  move the position to `docs/legal/positions/`, add the host's 5 s floor to
  `FLOORS`, add the job to `jobs.toml`.
- Append `registers/societies/profile-proposed.jsonl` (profiles
  `societies-register-export` v1 and `nzbn-entity-detail` v1) to
  `support/profiles/profiles.jsonl` and delete the proposed file.
- The three parts and the five answers are in the store (`/mnt/hdd2/qv4-docs/`),
  landed by my sample fill; the copies in
  `/home/user/querynzv4-work/scratch/societies/export/` can go once you have
  seen them there.
- Drop the seven `stray_societies_*` tables in my scratch schema (card).

Nothing new beyond the lesson filed.

## Result (integrator, 2026-10-20 08:25 NZDT)

Merged into main as d36df96 (merged main first). Done at the merge: the
position moved to `docs/legal/positions/nzbn-register-entities.md` and
`POSITIONS` set to the gate's default; `api.business.govt.nz` floored at
5 s in the gate; `qv4-societies-capture` in the catalogue at priority 35
(34 went to the charities capture the same morning), 01:00 NZDT nightly,
`check` green at 38 job types; the two profiles appended (the ledger at
51); the catalogue card closed; the lesson's rule cut from 257 to 235
characters; records regenerated. Fast tier and gate green; the gate's
load: 53,271 societies, 326 states, 133,080 officers, 22,787 asks, 22,783
reconciled; published. `societies_private` is readable by the owner
only. Arthur's to clear: the seven `stray_societies_*` tables in the
session's scratch schema and the export copies under
`querynz_v4-work/scratch/societies/export/`. The session ran headless
from the integrator, about 50 minutes.
