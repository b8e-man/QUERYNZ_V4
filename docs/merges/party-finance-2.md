# party-finance-2: the five expense returns, promoter returns, statement figures, party labels by registration
branch: session/party-finance (pushed; bb3442a)
session: party-finance (session 2)
raised: 2026-10-20
claims: registers/party_finance/ (new `promoter_returns.py`, `statements.py`; `expenses.py`, `read.py`, `load.py`, `check.py`, `tables.sql`, `publish.sql`, `sample.list`, `spec.md`, `pane.md`, tests); cards closed `five-party-expense-returns-are-unread-against-the-commission`, `the-promoter-expense-returns-are-not-read`, `the-party-financial-statements-figures-are-not-read`; cards opened `four-promoter-return-parts-are-unread`, `the-scanned-party-statements-figures-are-not-read`, `the-board-joins-party-finance-on-the-party-s-name` (blocker: your edit, below); lessons `a-form-box-can-read-below-its-label-in-whole-dollars`, `a-statement-s-columns-are-read-by-their-heads-and-edges`; docs/status/party-finance.md

Four tranches, each measured on every real file (all 116 documents, built
into `scratch_party_finance_full` in the sample database with the real
`pub.party_names`; nothing live written). No model called.

1. **The five unread expense returns.** NZ First and New Conservatives
   2023 replay row 115's readings under the contract's stamp with no
   change. Democratic Alliance 2023, Vision NZ 2020 and Aotearoa Legalise
   Cannabis 2023 needed two shapes the reader had not met: the figure on
   the line below its label, and whole dollars (`986`, `0`). A + B + C =
   total still gates every return. **Outside check:** 35 of 37
   party-elections equal the Commission to the cent, 2 explained (Part A
   alone), 0 differ, 0 unread (was 30 / 2 / 0 / 5). Every total read
   before is unchanged; six moved to the stronger parts-sum check.
2. **Promoter returns** (`promoter_returns.py`): each part from the
   declaration's box and the schedule's `TOTAL FOR PART <X>`, checked
   against each other, never added across parts. **Outside check:** 44 of
   49 Commission figures equal (28 confirmed by both statements), 0
   differ, 5 unread: PSA 2020's three handwritten N/As, Make It Legal
   2020's figure written in the N/A box (card), The Better NZ Trust 2023
   not held. Family First 2020's $141,224.34 in all three columns is the
   return's own statement (the form counts a cost in each).
   `pub.promoter_expense_returns` is new; `pub.promoter_expenses` gains
   six columns at its end (each part read, and `…_agrees`).
3. **Party labels** through `keys.parties.party_name(label, rows, on=…)`
   over `pub.party_names` joined to `pub.parties` (in a sample, the
   parties lane's own tables in the shared schema; none found is an
   error, never the snapshot). `on` is polling day for an election year,
   the balance date for a statement. `party` now holds the registration's
   key. Every label that resolved before resolves to the same party;
   37/37 expense rows, 39/39 returns, 47/47 statements, 78/89 allocation
   rows resolve (the 11 are five applicants never registered).
4. **Statement figures, text layer** (`statements.py`): income,
   expenditure, surplus; assets, liabilities, net assets. A pair publishes
   only where the statement's own arithmetic holds. 46 of 92 pairs (138
   figures); the rest are catch-log lines (card). Prior-year column
   against the year before's statement: 53 of 54 equal (Green 2025, an
   after-tax line, reported). `pub.party_statement_figures` is new.

Catch log reconciles on all 116 documents (1 `unread`, the allocation
decision). Lane fast tier green: 38 tests, about 2 s. Whole repository:
red on `tests/test_generators.py` only because my cards make
`docs/board.md` stale (the test rewrites it in my working copy; the
scope hook keeps it uncommitted), and on
`registers/mp_interests/…::test_a_rebuild_gives_every_row_the_same_key`
(7.7 s under load, not this lane).

For the merge, please:
- In `products/board/catalogue.py`, drop `key_column="name"` from the four
  `Join`s on `party_expenses`, `party_expense_returns`,
  `party_financial_statements` and `broadcasting_allocations` (card
  `the-board-joins-party-finance-on-the-party-s-name`); otherwise those
  panes join nothing under a registration.
- Load the lane: the staging load reads `pub.party_names` and
  `pub.parties`, so the parties lane must be published first (it is).
- Optionally add `party_statement_figures` and `promoter_expense_returns`
  to the board's catalogue.

Nothing new went ahead on a default. Nothing waits on Arthur.

## Result (integrator, 2026-10-20 09:40 NZDT)

Merged into main as 7df494e (merged main first). Done at the merge: the
four board joins on party finance now join on the registration key (the
card closed); the two new views went into the board's catalogue at the
next merge (party-returns-4), because the board's real check refuses a
catalogue entry before its view is published and a published view
without an entry; two lesson rules cut to the limit; records
regenerated. Fast tier green (464 s, the box under three sessions) and
gate green; the gate's load: 116 documents, 39 of 40 returns read, 1
set aside; published. The session ran headless from the integrator,
about 40 minutes.
