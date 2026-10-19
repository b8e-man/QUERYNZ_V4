# party-finance-1: party expenses, broadcasting allocations, promoters and the financial-statements roster
branch: session/party-finance (pushed; 7b83360)
session: party-finance (session 1)
raised: 2026-10-20
claims: registers/party_finance/ (new `listing.py`, `expenses.py`, `broadcasting.py`, `promoters.py`, `financials.py`, `load.py`, `profile-proposed.jsonl`, tests `test_party_finance.py`; capture, read, check, tables, publish, sample, pane, spec); cards `five-party-expense-returns-are-unread-against-the-commission`, `keys-dates-does-not-read-a-day-month-word-two-digit-year`, `the-party-financial-statements-figures-are-not-read`, `the-promoter-expense-returns-are-not-read`, `party-rules-are-not-in-this-lane-s-folders`; lesson `look-at-a-page-that-holds-addresses-by-counting-its-labels`; docs/status/party-finance.md

Step 4.1. Case 1 only: every file in `ec-expenses`, `ec-financials`,
`ec-broadcasting`, `ec-promoters`, and the Commission's own listing pages
for these kinds under `ec-donations/index/`, copied by hash, read-only.
Nothing fetched. Each folder's manifest is read for the Commission's URL
of each hash, because the listing pages name a document by its link and
the link is the join, never a file name.

Six tranches, each measured on the full real set in my scratch schema
(`scratch_party_finance` in the sample database; nothing live written):

1. Capture: 116 documents. Two catch-log lines: the register-of-promoters
   captures the old job's manifest lists and has since overwritten.
2. The Commission's party-expenses tables (2020, 2023) and promoter-
   expenses tables: 58 rows, none set aside; 61 links, one not held (The
   Better NZ Trust's 2023 return).
3. Each expense return's own `Total (A + B + C)`, from its text layer or
   the page reader's stored readings (GLM-OCR Q8_0, 300 dots, replayed):
   40 linked, 34 read, 6 set aside. **Outside check** (`check.py`): of 37
   party-elections, 30 equal the Commission to the cent, 2 differ where
   the Commission printed Part A alone (Advance NZ and Māori Party 2020;
   the return's parts reconcile), 0 unexplained, 5 unread (card).
4. Broadcasting allocation: 89 rows; every round's rows add to the page's
   own printed `TOTAL allocated` to the dollar (2 + 3 rounds), or the
   page would publish nothing. Every party joined by registered name
   agrees with the expense table's allocation column; eight do not join
   by name (the `keys.parties` card).
5. Register of promoters: 69 promoters, 303 people in the register's
   public roles. Email and address go to `party_finance_private` only.
   17 of 21 promoters on the expense tables join the register by
   organisation key; four differ in wording.
6. Financial-statements roster: 47 rows over 2024–2026; all 46 held
   statements linked. The statements' figures are not read (card).

Catch log reconciles on the full set: 116 documents held = read, a row's
source, or a line (21 `unread`: 20 promoter returns, 1 allocation
decision). Fast tier green for the lane (25 tests, 1.5 s). Whole
repository green except `tests/test_generators.py`, red only because my
cards and lesson make `docs/board.md` and `lessons/INDEX.md` stale.

For the merge, please:
- Append `registers/party_finance/profile-proposed.jsonl` to
  `support/profiles/profiles.jsonl` with `add_version` and delete the
  proposed file: `ec-party-expenses-listing`, `ec-promoter-expenses-listing`,
  `ec-broadcasting-allocation-page`, `ec-promoter-register-page`,
  `ec-financial-statements-listing`, each v1. `read.profile` takes the
  ledger's first.
- Regenerate `docs/board.md` and `lessons/INDEX.md`. The test run
  rewrote both in my working copy and the fence will not let me restore
  them; they are not committed.
- `publish.sql` adds views `pub.party_expenses`, `pub.party_expense_returns`,
  `pub.promoter_expenses`, `pub.broadcasting_allocations`, `pub.promoters`,
  `pub.promoter_people`, `pub.party_financial_statements`. The spec's
  first draft named `pub.promoters` only for promoters; it now names all
  seven. `party_finance_private.promoter_contacts` must never be granted
  to the session reader or the product login.
- The sample's register-page hashes are this morning's: the old job
  overwrites those pages nightly; `sample.fill` finds a landed capture by
  its old path when the folder's bytes have moved on.
- Note for the record: inspecting the promoter register's markup, this
  session printed part of one individual promoter's published street
  address into its own transcript (hard limit 11). It went nowhere else:
  no file, card, commit or log carries it. The lesson filed is the rule
  that prevents it.

## Result (integrator, 2026-10-20 07:30)

Merged into main as a81c9da (merged main first). Done at the merge: the
five profiles appended to `support/profiles/profiles.jsonl` with
`add_version`, the proposed file removed, the shipped-profiles test at
30; board and lessons index regenerated. Fast tier and gate green; the
gate's load: 116 documents, 58 listing rows, 107 links (1 not held), 40
returns linked (34 read, 6 set aside), 89 allocation rows, 69 promoters
and 303 people, 47 roster rows; published. `party_finance_private` is
readable by the owner only, checked after the publish. The session's
note on hard limit 11 (part of one promoter's published street address
printed into its own transcript, nowhere else) is reported to Arthur in
this record and nowhere else. Five cards stand; the party-rules card
says the rules are not in these folders.
