When a product copies another module's function but cuts an arm it does not need, hold the copy equal by executing the original's source text in a namespace of its own and comparing what both write (the SQL, for every view), not by comparing text: the one-way rule forbids the import, and a text comparison cannot see past the cut.
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
