# party-returns-2: Part A donors, Part H loans and the Commission's amendments
branch: session/party-returns (pushed; 39c8562)
session: party-returns (session 2)
raised: 2026-10-19
claims: registers/party_returns/ (new `schedule.py`, `donors.py`, `loans.py`, `amendments.py`, `private.sql`, `tests/test_schedules.py`; `read.py`, `load.py`, `sample.py`, `tables.sql`, `publish.sql`, spec, pane, sample list +3); four cards (one updated); one lesson; one queued decision; docs/status/party-returns.md

Step 4.1, tranche 2, as the status file planned it.

- **Part A.** Each return's donor rows from the stored page texts, by the
  route the page's shape calls for (text-layer geometry, the page
  reader's tables, numbered lists, stacked rows). A page the reader read
  column by column is refused, never paired by order (lesson
  `a-shifted-name-still-adds-up`). A part is published whole only when
  its rows add, to the cent, to the declaration's Part A and to `TOTAL
  FOR PART A` where read; else set aside whole (stage `part-a`).
- **Addresses.** The name is cut before the first figure or address
  word; the rest of the cell goes only to
  `party_returns_private.addresses` (staged as `<staging>_private`, no
  grants). A test checks the read login sees neither, and that no
  published column is an address.
- **Part H.** The declared H, I and total (checked against each other),
  then one row per lender block, the loan amount only; never the unpaid
  balance, the running total or a guarantor.
- **Amendments.** From the Commission's by-year listing, landed by hash
  from the old folder's `index/`: a file it marks amended replaces the
  others in that party-year; two amendments by their stated dates.

Measured over all 152 landed returns (replay only): Part A published on
22 returns (476 rows), nil on 44, set aside on 33; Part H published on 6
(9 rows), nil on 87, set aside on 6; 14 returns replaced, one listed
amendment not held (ALCP 2025). Return rows unchanged: 99, the frozen-site
comparison as before.

For the load: `tables.sql` adds five columns to the live `returns`
(`ADD COLUMN IF NOT EXISTS`) and three tables; `pub.party_return_totals`
gains them and `replaced_by` at its end, so `CREATE OR REPLACE VIEW`
holds; two new views. `publish()` also fills
`party_returns_private.addresses` from the staging twin.

After the merge, please: the forty-one card is corrected. Rows 95 and 96
ran `qv4-reread-pages`, which reads one page per document, so the lane
still lacks 645 image pages and the 41 stay at stage `read`. A job that
reads every image page under the stamp the lane replays is the
scheduler's module, not this lane's.

Fast tier: `registers/party_returns` 43 passed with the sample filled by
the module's fixture; whole repository green (35.5 s). The working copy
holds regenerated `docs/board.md`, `lessons/INDEX.md` and
`docs/decisions/queue.md`, not committed, and one stray untracked
`stateD.json` at the root (a scratch file of mine: return-hash prefixes
and verdict words, no names or text; the scope hook would not let me
delete it). Please delete it when you remove the working copy.

## Result (integrator, 2026-10-20 03:30)

Merged into main as d99d65b (merged main first; board, lessons index and
queue regenerated). Fast tier and gate green; the gate's staging load:
152 documents, 99 rows, 53 set aside, 476 donor rows, 9 loan rows, 14
returns replaced by an amendment; published, the private twin filled.
After the merge, the page-reader job the lane asked for is built in the
scheduler's module (a5a682f): `qv4-read-pages` reads every image page of
a document under the stamp the lane replays, on the card the worker
holds, one piece per document. Queued as row 110 (the 18 in-window
returns, 2024 to 2026) and row 111 (the 23 for 2017 and 2018). The lane
picks the readings up on its next load. `stateD.json` goes with the
working copy when it is retired.
