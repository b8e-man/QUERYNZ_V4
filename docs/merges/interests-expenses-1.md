# interests-expenses-1: MPs' and ministers' expenses, and the register of pecuniary interests
branch: session/interests-expenses (pushed; 76d9fcf)
session: interests-expenses (session 1)
raised: 2026-10-20
claims: registers/expenses/ (new `sheet.py`, `biff.py`, `table.py`, `load.py`, `profile-proposed.jsonl`, tests `test_expenses.py`; capture, read, check, tables, publish, sample, sample.list, pane, spec); registers/mp_interests/ (new `parse.py`, `load.py`, `profile-proposed.jsonl`, tests `test_mp_interests.py`; capture, read, check, tables, publish, sample, sample.list, pane, spec); cards `eleven-members-expense-workbooks-the-catalogue-lists-are-not-held`, `the-april-june-2018-ministers-expense-release-was-overwritten`, `expense-releases-published-only-as-pdf-are-not-held`, `short-party-labels-in-the-expense-and-interests-registers-do-not-resolve`, `the-old-interests-reading-filed-minor-party-declarations-under-the-member-before`, `expense-release-totals-the-publishers-printed-wrong`; queue item `may-the-interests-register-s-real-property-declarations-be-shown`; lesson `a-publisher-s-printed-total-is-checked-not-trusted-and-a-hand-written-reader-is-checked-against-libreoffice`; docs/status/interests-expenses.md

Step 4.1, two lanes, case 1 only; nothing fetched. Every number below was
measured on the full real sets in my scratch schema
(`scratch_interests_expenses_full` in the sample database; nothing live
written).

**Expenses** (`var/staging/mp-expenses/`, `minister-expenses/`, by hash):

1. Readers: the estate has no spreadsheet package, so xlsx and xls (BIFF8)
   are read with the standard library. Both equal LibreOffice's conversion
   of all 100 held workbooks on 64,137 cells (16 differ: error cells
   LibreOffice recalculates).
2. Tables found by their labels: a two-row header joined into heading
   paths ("Accommodation / Wellington"); the first total heading is the
   total, columns left of it the categories, right of it money outside it
   (the IPO's, Cabinet-approved international travel). A sheet may hold a
   table per government. Period from the table's own title row; the
   publisher's label kept beside it (one 2017 workbook is labelled
   January–March and titled October–December).
3. 103 documents: 100 workbooks read into 104 release tables, 6,229
   lines, 40,291 figures. 6,206 lines add to their own printed total
   (3,865 of 3,865 members'); 23 ministers' lines do not and are set
   aside, never published. 4 working sheets (2009) are catch-log lines.
4. **Outside check** (`python -m registers.expenses.check`): each release
   table's printed grand total against the sum of its lines. Members: 31
   of 31 equal in the total column; two releases print a category total
   that differs (card). Executive: 64 of 72 equal; 8 differ. Every case
   looked at is the publisher's arithmetic; the check exits 1 on them, by
   design (card asks accept or a known-differences list).
5. The publishers' listings: 112 workbooks listed, 100 held, 12 not (11
   catalogue links on www.parliament.nz, 1 quarter overwritten in the old
   folder); each a catch-log line.

**Interests** (`var/mp_interests/`, 21 editions 2006–2026, held: Arthur
downloaded them by hand; no publisher URL recorded):

1. Text layer per page; the category keyed on the heading (23 wordings,
   14 categories), the number kept as printed; the reprinted rules cut at
   their heading after the last member; wraps joined only on a lower-case
   start or an open bracket; independents ("Name (Electorate)"),
   nicknames in headers and "No interests declared" statements read.
2. 2,526 returns, 24,931 declarations, every one found verbatim in its
   edition; 0 set aside.
3. **Outside check** (`python -m registers.mp_interests.check`): no edition
   prints a count, so the figure is each edition's own numbered category
   list: 271 of 271 numbers the returns file under agree, by heading.
4. Real property (5,452 declarations) can place a member's home: its text
   is in `mp_interests_private.declaration_text` only, the published row
   says withheld (queue item; default withheld; a setting).

Catch logs reconcile on both full sets. Fast tier green (37 tests, 5 s
together, through the main checkout's Python: the `bin/fast` card). Root
checks run green: imports, reading limits, sample and tiers, lane, row
contract, profiles.

For the merge, please:
- Append both `profile-proposed.jsonl` files to `support/profiles/profiles.jsonl`
  with `add_version` and delete them: `parliamentary-expenses-workbook`
  (becomes v3: the members' workbook only, recognised by shape, no 2019
  window), `ministerial-expenses-workbook` (v3: revived from its v2
  retirement, the two layouts differ), `data-govt-catalogue-package` v1,
  `dia-ministers-expense-listing` v1, `parliament-pecuniary-interests-summary`
  v1. The rows carry those versions; `read.profile` takes the higher of
  ledger and proposed.
- Regenerate `docs/board.md` and `lessons/INDEX.md` (six cards, one lesson).
- New published views: `pub.mp_expenses`, `pub.minister_expenses`,
  `pub.expense_release_totals`, `pub.mp_interests`, `pub.mp_interest_returns`,
  `pub.mp_interest_editions`. `mp_interests_private` must never be granted
  to a reader; `expenses_private` is empty.
- The load writes run records through `support.jobrun` as
  `qv4-expenses-load` and `qv4-mp-interests-load`.

## Result (integrator, 2026-10-20 06:50 NZDT)

Merged into main as 673995c (merged main first). Done at the merge: the
five profiles appended with `add_version` (the two workbook profiles as
v3, three new slugs; the shipped-profiles test at 47), both proposed
files removed; the lesson's rule cut from 281 to 238 characters (the
index refuses over 240); board, lessons index and queue regenerated.
Fast tier and gate green; the gate's loads: expenses 103 documents, 100
workbooks read, 104 release tables, 6,206 lines published and 23 set
aside, 12 listed workbooks not held; interests 21 editions, 2,526
returns, 24,931 declarations published with 5,452 withheld, 0 numbers
differing; both published. `mp_interests_private` is readable by the
owner only, checked after the publish. The ten releases where the
publisher's own total is wrong fail the check by design; the card asks
Arthur to accept them onto the known-limits page or name a skip list.
The scratch schema `scratch_interests_expenses_full` in the sample
database is Arthur's psql (no session may DROP). The session ran
headless from the integrator, about 70 minutes.
