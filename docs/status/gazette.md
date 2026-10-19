# gazette: where it stands

**Date:** 2026-10-20, 05:30. **Step:** 4.1, Gazette notices, `registers/gazette/`.
**Merge request:** `gazette-1`.

## Done

- Capture: every Gazette notice the old estate holds as text exported once
  (read-only login, 60 s statement limit, a server-side cursor) on 20
  October 2026 04:49 to `gazette-notices-2026-10-20.jsonl`, sha256
  47de7e09…, 208,461 lines, 207,133 notices 2000 to 16 October 2026;
  pinned in `capture.py`, landed in the store by the sample fill. Never
  run at load.
- Typing: every notice by the Gazette's own section code and its place in
  the year's one sequence; 1,328 notices captured twice (none identical)
  keep the copy the old classifier read, the other a catch-log line.
- Reading, the largest unread format first: the celebrant lists, 2,975
  notices, 2,941 read (110 with part set aside), 34 set aside whole;
  123,187 rows (55,339 from 2019) in six shapes; 8,943 addresses in
  `gazette_private` only; 320 catch-log lines. Adjacent rows in
  alphabetical order 98.0% to 99.4% by shape.
- Outside check (`check.py`, exits 1 on failure): the Gazette's own
  celebrant "Notice No." per series and year: every held numbered notice
  read (green on all 207,133); the year's highest notice number against
  numbers held, 95.7% to 99.3% for closed years, 2019 86.4%.
- Full load into a scratch schema: 12.4 s.

## Carded

- `the-gazette-lane-reads-only-the-celebrant-lists-so-far` (next session).
- `twelve-printed-celebrant-tables-are-unread`.
- `civil-union-celebrant-lists-without-stops-are-unread`.
- `the-old-capture-missed-a-seventh-of-2019-s-gazette-notices`.

## Next

1. Session 2: director prohibitions (one template, address private), then
   liquidator appointments (43,587 notices), each its own profile.
2. The printed tables, by the organisation vocabulary.
3. The parties lane takes this lane's `au` notices instead of its export.
