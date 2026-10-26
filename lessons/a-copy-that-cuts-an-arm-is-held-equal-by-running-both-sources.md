A copy that cuts an arm of another module's function is held equal by exec'ing the original's source beside it and comparing what both write, never by comparing text, which cannot see past the cut.
area: products, one-way import, copied code, search, tests
paid-for-by: 2026-10-26, fix-products-report-1 (ruling 92 item 7)

The report's name search is the board's (`products/board/search.py`), but
the board's `match_sql` and `view_sql` carry the expanded search's fields
(ruling 82), which the report does not offer. Pieces copied whole
(`fold_sql`, `words_of`, `is_number`, `guard_sql`) are held by their AST
source segments, as `products/board/tests/test_fold.py` holds keys/. The
two cut functions are held by `exec`ing the board's own source segments
(read from the file, never imported) with a stub `cat`, then asserting the
report's `view_sql` returns the same SQL and parameters for every searched
view and several terms. The board catalogue's search columns are read the
same way, by `ast.literal_eval` of its `View(...)` keywords.

How to apply: products/report/tests/test_search.py is the pattern. Copy
the original's pieces whole where you can; where you must cut, compare
outputs over the real catalogue, so a change on the board's side fails the
copy's test the next time the fast tier runs.

The namespace carries the original's module constants, read from its
source (every assignment whose value is a literal), not supplied by hand:
an exec'd `def` evaluates its defaults when it runs, so board-6's
`mode: str = ALL` made every case a NameError until the board's own
`ALL, ANY = "all", "any"` was exec'd first (fix-products-report-2). Exec
only the functions the cut path calls; a helper the path comes to need
then fails as a NameError, which is the signal to copy again.
