# sanctions: where the three step 5.3 lanes stand

Session sanctions-1 (Opus), 21 October 2026, node2. Merge request `sanctions-1`.

## The four questions, per source (positions in each lane's `position/`)

| Source | Open? | Lawful copy? | Terms | Statute, privacy | Outcome |
| --- | --- | --- | --- | --- | --- |
| MFAT Russia register | page yes; file behind a bot wall | CC BY 4.0 | no automated access | names public by law | **held** for script; by hand allowed |
| UN consolidated list | yes | personal, non-commercial only | no compiling | listings public | **held** |
| Police TSA list | yes (10 s crawl delay) | non-commercial private only | permission needed | listings public | **held** |
| NZBN, limited partnerships | own key | public by statute (LP Act s 55) | portal's, no limit stated | limited partners confidential (s 115) | **captured** |
| LBP register | yes | Crown copyright, copy freely | none barring | **s 307: search only for s 299 purposes** | **held** |
| Board decisions | yes | Crown copyright | none barring | Privacy Act fairness; 3-year view | **captured** |

## Done

- `registers/limited_partnerships`: built; 15 real answers (proof, through the gate, 5 s apart) read into 15
  partnerships and 18 general partners; 19 tests, 9 mutants caught. The interface states no partner dates.
- `registers/building_practitioners`: decisions list built; 3 documents and 4 of about 80 pages landed, 80 of 80
  decisions read (1,600 stated); 17 tests, 8 mutants. Register half held, no reader (its shape is unseen).
- `registers/sanctions`: built and held; the UN and Police readers proven in memory on today's lists (1,010 and
  826 items reconcile; Police 1373: 21 read against 22 stated); 22 tests, 12 mutants. MFAT reader unverified.
- Fast tier green on all three. Checks red with reasons, correctly (nothing loaded).

## Half-done

- No first night was run: the proofs were daytime and small (under 30 requests in all). The full captures are sized
  and left to the proposed jobs (card `the-partnerships-and-board-decisions-jobs-into-the-catalogue`).

## Waits on Arthur

- Queue, no default: the UN, Police and MFAT-script items; the LBP register item.
- Queue, default applied: Board decisions shown for three years.
- MFAT by hand: download the workbook, run `capture.py --file` (queue item says how).
