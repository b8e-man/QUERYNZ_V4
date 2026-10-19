# party-returns-1: the declaration read from the page reader's stored readings
branch: session/party-returns (pushed; 9285a43)
session: party-returns (session 1)
raised: 2026-10-19
claims: registers/party_returns/ (new `pixels.py`, `read.py` routed by shape, `year_from` column, sample list +10, tests); three finding cards; two lessons; docs/status/party-returns.md

Step 4.1, tranche 1. A return with image pages is no longer set aside at
recognition: each image page is replayed from GLM-OCR's stored reading
(Q8_0, 300 dots, `OCR`, the reader ruling 60 kept), never read by a model
here. The page reader writes a figure one space after its threshold and
drops the year from the declaration page, so `pixels.py` cuts the
threshold out first and takes the year from the loans page's balance date.

Measured over all 152 landed returns (replay only, nothing written):
99 rows (32 before; 34 text, 65 pixels); 49 party-years equal to the
frozen site (23 before); 0 differing; 3 other returns (originals whose
amendment the frozen site chose); 44 rows with no frozen party-year
(small parties, unresolved labels). Set aside: 41 at `read` (no stored
reading, 18 of them 2024 and 2025), 12 at the declaration (5 as before, 7
new, carded).

For the load: `tables.sql` adds `year_from` to the live table with `ADD
COLUMN IF NOT EXISTS`; `publish()` now names its columns; the view takes
`year_from` last, so `CREATE OR REPLACE VIEW` holds.

After the merge, please: queue a page-reader job for the 18 in-window
returns with no stored reading (`set_aside` stage `read`; card
`forty-one-party-returns-…`). The lane picks the readings up on its next
load unchanged. A build session does not queue live jobs.

Fast tier: `registers/party_returns` 26 passed with the sample filled
(7.2 s); whole repository green (27.6 s). The working copy holds a
regenerated `lessons/INDEX.md` and `docs/board.md`, not committed.
Lessons: `the-page-reader-drops-a-return-s-year`,
`probe-a-schedule-page-for-tokens-never-for-context`.

## Result (integrator, 2026-10-19 20:45)

Merged into main as bfde4af (merged main first; lessons index and board
regenerated). Fast tier and gate green; the gate's staging load put 99 rows
into its staging schema and published. Queued after the merge as asked:
`qv4-reread-pages` row 95 (the 18 in-window returns, 2024 to 2026) and
row 96 (the 23 for 2017 and 2018), one piece per document, page-reader
profile. The lane picks the readings up on its next load.
