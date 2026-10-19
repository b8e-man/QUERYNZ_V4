# party-returns-3: the Commission's by-year table as the outside check; Part A's in-line rows
branch: session/party-returns (pushed; 8034427)
session: party-returns (session 3)
raised: 2026-10-20
claims: registers/party_returns/ (new `commission.py`, `tests/test_commission.py`; `schedule.py`, `donors.py`, spec, sample list label, `tests/test_schedules.py`); two new cards, two updated (one closed); one lesson; docs/status/party-returns.md

Step 4.1, the three items the brief named.

- **Frozen site, re-measured** on the live load after `qv4-read-pages`
  (rows 110, 111): 137 rows, none at stage `read`. 71 party-years equal
  (was 49), 1 differs: Labour 2017, the lane wrong (typed figures struck
  through and corrected in ink; the page reader drops the ink, the typed
  figures still add up). Card `labour-2017-…`.
- **The Commission's by-year table** (`commission.py`, the outside check
  plan 4.4 asks for): each current return's declared total and loans
  against the Commission's per-party-year figures, 2017 on, tied by the
  files the listing links (never a resolved party name), to the cent.
  Live: 117 equal, 5 differ, loans 0 differ. Four of the five are the
  table's (Green 2021, NZ Outdoors 2020 slips; HeartlandNZ 2021 shows the
  original's NIL; New Conservatives 2024 adds the non-monetary line), each
  page read by eye; card `the-commission-s-table-differs-…`.
  `python -m registers.party_returns.commission` exits 1 on a difference;
  the fast-tier test requires each difference to have a card.
- **Part A's refused pages:** `schedule._inline` reads the page reader's
  rows whose figure ends the line (where the stacked route saw no money
  and returned nothing), with four guards: row numbers must climb by one,
  a cell's name is its first line, "see attachment" is a pointer, and
  floor/shed/building open an address. Over all 152 returns, replay only:
  Part A published on 30 returns (679 rows; was 25, 580), nil 62, set
  aside 45 (was 50). No published name changes except two that lose an
  address word ("…, Floor", "…, Shed"). Column-order pages stay refused:
  their fix is a cell-scale re-read, the scheduler's job (card updated).

For the load: no table or view changes. A reload publishes 99 more donor
rows (5 returns) and the two cleaner names. The forty-one card is closed.

Fast tier: `registers/party_returns` 51 passed (19.4 s). Whole repository:
one red, `tests/test_generators.py`, because the working copy holds the
regenerated `docs/board.md` and `lessons/INDEX.md`, not committed
(generated files are the integrator's). Nothing new beyond the lesson
`ink-over-a-typed-figure-still-adds-up`.

## Result (integrator, 2026-10-20 07:30)

Merged into main as a4e606a (merged main first; board and lessons index
regenerated). Fast tier and gate green; the gate's load: 152 documents,
137 rows, 15 set aside, 679 donor rows, 10 loan rows, 14 replaced;
published. The frozen-site comparison stands at 71 equal, 1 differing
(Labour 2017, carded, the lane's); the Commission's table at 117 equal,
5 differing, each carded. The column-order pages' cell-scale re-read is
the scheduler's, carded. Session 4, if any, switches the lane to
`keys.parties.party_name(label, rows, on=date)` (`fix-keys-1`).
