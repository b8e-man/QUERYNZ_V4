# fix-products-report-1: the report's start page searches a name; no reader is asked for a row reference (ruling 92 item 7)
branch: fix/products-report-1 (pushed; 3e9a4d6)
session: fix-products-report-1 (fix, scope products/report/)
raised: 2026-10-26
claims: products/report/ (search.py new; server.py, memo.py, check.py, catalogue.py, spec.md; tests/test_search.py new); lessons/a-copy-that-cuts-an-arm-is-held-equal-by-running-both-sources.md
note: written to the session's scratch folder because the fence refused the inbox link (merge-requests/ resolves outside the working copy); the integrator moves it to /home/user/querynzv4-work/inbox/merge-requests/

1. **The search.** The start page and every template's page carry a GET
   form to `/` with one box, "a person, company or organisation name"
   (`?q=`), the template, since and the template's parameters. `/?q=`
   lists the matching rows of the 31 report views that name a person or an
   organisation (not company_addresses, charity_returns, mp_interests), up
   to ten a view with its count, each a link to `/report/<register>:<key>`
   carrying the chosen template, since and parameters. No script. One
   product-reader connection under the page's lock, one view after another:
   about 2 s a search on the live tables.
2. **The copy of the board's search.** The report may not import the
   board, so `products/report/search.py` copies `fold_sql`, `words_of`,
   `is_number` and `guard_sql` character for character, and `match_sql`
   and `view_sql` without the expanded search's fields (ruling 82).
   `tests/test_search.py` holds the four whole pieces equal to the board's
   source (AST segments), holds the SQL and parameters the report writes
   equal to what the board's own `view_sql` writes for every searched view
   and five terms (the board's source text exec'd, never imported), and
   holds `SEARCH` (search columns, numbers, order) equal to the board
   catalogue's `View(...)` keywords. A change to the board's search fails
   this test until it is copied again. `catalogue.fold_term` is an alias of
   the report's `fold` so `words_of` is verbatim.
3. **The memo** says where it starts in plain words, in HTML and text
   ("This report starts from ACME LIMITED, row companies/9429050975815 of
   the register Companies, directors and shareholders."), in place of the
   bare ref. A memo page offers "run with this template" (a GET form whose
   action is the row's own address). `/report/<register>:<key>` and
   `/report?ref=` still answer, so the board's "report from here" link is
   unchanged.
4. **Checks.** Fast tier: `QV4_INTEGRATOR=1 bin/fast products/report`
   green (42 s); root tests not slow green. `python -m products.report
   check` green against the live tables, with route 11 added: the
   done-when company's name searched over HTTP on the page's own server
   (loopback, a passing port) answers 200, no row-reference wording, and
   its first link answers 200 with a memo that says where it starts; every
   searched view carries its search columns. Slow tests
   (test_search, test_real) green.

Lesson filed (above). No card: the item was ruling 92's, handed to this
session.

**The integrator must:** merge; restart `qv4-report` at the release
(node2, any directory: `systemctl --user restart qv4-report`) so port
8440 serves the search. Nothing else changes: no table, no unit file, no
new job.

## Result (integrator, 26 October 14:45 NZDT)

Merged as ec3a46d through `fix-products-report-2`, which carries `fix-products-report-1` (3e9a4d6): the first fix's copy of the board's search went red when board-6 changed the board's `search.py` (word alternatives, the all/any mode), and the second re-copied it and widened the equality test's namespace. Gate green (the lessons index regenerated at the integrate commit 88e57fd). Released and `qv4-report` restarted 14:43; the start page answers 200, a name search lists report links and no page carries the "register:key" wording. Branches and working copies retired.
