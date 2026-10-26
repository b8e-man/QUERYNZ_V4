# fix-products-report-2: the report's search copy follows board-6's search; carries fix-products-report-1
branch: fix/products-report-2 (pushed; a608946)
session: fix-products-report-2 (fix, scope products/report/)
raised: 2026-10-26
carries: fix-products-report-1 (merged into this branch at 5382d1f; merge this one and that request is merged with it)
claims: products/report/ (search.py, tests/test_search.py); lessons/a-copy-that-cuts-an-arm-is-held-equal-by-running-both-sources.md
note: written to the session's scratch folder because the fence refused the inbox link (merge-requests/ resolves outside the working copy); the integrator moves it to /home/user/querynzv4-work/inbox/merge-requests/

1. **Why.** board-6 (ruling 92 items 4, 6) changed the board's search:
   `words_of` folds each word's alternatives ("garry|gary") through
   `_alternatives` and `word_re`, and `match_sql`/`view_sql` gained
   `mode` (ALL/ANY). The report's `tests/test_search.py` went red: the
   copied `words_of` differed, and the board's `view_sql` exec'd with
   NameError ALL (a `def` evaluates its defaults).
2. **The copy.** `products/report/search.py` copies `_alternatives`,
   `words_of` and `word_re` verbatim, and its `match_sql` uses `word_re`.
   The report's search stays mode ALL with no fields, as before.
3. **The test.** `_alternatives` and `word_re` are held verbatim with the
   other four. The exec namespace takes the board's literal module
   constants (ALL, ANY, LIMIT, …) from its source, never imported, then
   only the functions the no-fields path calls. Two alternative terms join
   the SQL cases. Checked red against mutated copies of the board's
   search in scratch: a changed `word_re`, `_alternatives` or LIMIT, or a
   new name on the no-fields path. Renaming ALL's value stays green,
   because the report's SQL does not change.
4. **Checks.** `QV4_INTEGRATOR=1 bin/fast products/report` green (44 s);
   `python -m products.report check` green against the live tables; the
   slow tests of products/report green (5); root tests not slow green
   with the lessons index regenerated in the working copy.
5. **The lessons index.** The lesson carried from fix-products-report-1
   had a 331-character rule, and `bin/lessons-index` refuses that. It is
   now one sentence under 240. `lessons/INDEX.md` is not committed (the
   hook refuses it), so `tests/test_generators.py::test_the_committed_records_generate_cleanly`
   is red on a clean checkout until the integrator regenerates the index
   at the merge.

Lesson: the carried one, amended (the namespace takes the original's
constants from its source). No card.

**The integrator must:** merge; regenerate the lessons index; restart
`qv4-report` at the release (node2, any directory:
`systemctl --user restart qv4-report`) so port 8440 serves the search.
Nothing else changes: no table, no unit file, no new job.

## Result (integrator, 26 October 14:45 NZDT)

Merged as ec3a46d through `fix-products-report-2`, which carries `fix-products-report-1` (3e9a4d6): the first fix's copy of the board's search went red when board-6 changed the board's `search.py` (word alternatives, the all/any mode), and the second re-copied it and widened the equality test's namespace. Gate green (the lessons index regenerated at the integrate commit 88e57fd). Released and `qv4-report` restarted 14:43; the start page answers 200, a name search lists report links and no page carries the "register:key" wording. Branches and working copies retired.
