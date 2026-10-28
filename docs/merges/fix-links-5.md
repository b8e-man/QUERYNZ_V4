# fix-links-5: one order of refs (bytes) in Python and SQL; check item 9 in the budget
branch: fix/links-1 (pushed, 2f6cbf5; one commit on main's 4bc9a2b)
session: fix-links-1 (Opus, fix weight, scope links/)
raised: 2026-10-28
claims: links/ (__init__.py, tables.sql, build.py, pairs.py, measure.py, check.py, tests/test_ref_order.py new); one lesson, lessons/INDEX.md (regenerate at the merge if main's lessons moved); docs/status/links.md
publish.sql: **unchanged**. tables.sql: **the migration block changes three CHECKs**, applied by `links.ddl()` at the job's own start (no DDL by hand).
job after the merge: queue `qv4-links-build`, then `python -m links.check` live, and read the run's `peak_mb`.

## The fault

`links.pair` orders two refs by code point (Python). `links_pair_order
CHECK (row_a < row_b)` ordered them by the database's collation
(en_NZ.UTF-8), which ignores spaces and punctuation and folds case at its
first level. The people and member views of rulings 114 and 116 brought
refs with capitals, spaces and punctuation, and a near link Python ordered
broke the CHECK. The same split sat in every SQL `least`, `greatest`,
`min(ref)` and `ORDER BY ref`, so a star centre or the group id (the
smallest row key) chosen in SQL could differ from the one chosen in Python.

## The fix

- **The CHECKs.** `links_pair_order`, `decisions_pair_order` and
  `test_pairs_order` compare `(row_a COLLATE "C") < row_b`. For UTF-8,
  `"C"` is byte order, which is Python's order. The migration block
  replaces each CHECK once, where it lacks `COLLATE "C"`. A stored link or
  test pair that bytes order the other way is turned round in place (the
  same `link_id`). On live, read-only: **3 links** (`full-name@1`,
  confirmed), **0 of 650 test pairs**, **0 of 5,743 decisions**, 0
  old decisions and 0 readings are out of byte order. A decision is never
  edited: one out of order would stop the job at the migration, loudly.
  The swap and the check each scan `links.links` once under a lock at the
  job's start. That is seconds, while `pub.links` waits.
- **The SQL.** Every `least`/`greatest` of two refs in build.py (21 places)
  and pairs.py (8) is `COLLATE "C"`. So is every star centre `min(ref)` (6)
  and every `ORDER BY ref` that feeds a choice (near names' `array_agg`,
  `same_party` rows, bodies). So is the pair dedupe `a.ref < b.ref`
  (pairs.py, build.py `refiled_links`, measure 9). A smallest ref joined on
  again is handed back `COLLATE "default"`. Measured on the engine: an
  equality join on a `"C"` value loses the column's index (an index serves
  only its own collation). `ON CONFLICT` keys, `UNIQUE (row_a, row_b,
  rule)`, publish.sql's `DISTINCT ON (row_a, row_b)` and every join on a
  ref are equality, which is byte equality under a deterministic
  collation, so they did not change. Group ids come from the union-find in
  Python (smallest by code point), which was already right. No SQL outside
  links/ orders refs (grepped products/, checks/, registers/, support/,
  keys/).
- **Found in the audit, not changed:** `declared_links` second UNION
  branch joins `i.ref = least(row_a, row_b)` with `i.view =
  'mp_interests'`, but `companies:` sorts before `mp_interests:` in either
  order. So it never matched: a number-declared company has never fed
  `declared-directorship@1`. Rewritten to `l.row_a` (the same rows, by the
  CHECK) and left dead. Whether to make it live (more confirmed links) is
  a rule change, so it is for a ruling.

## How this was proved

- `links/tests/test_ref_order.py`, slow, real engine, a rolled-back
  schema of the sample database. The `pub.` reads go to empty scratch
  stubs, because the sample publishes none of them. Fixture refs `x:a b`,
  `x:a-b`, `x:a c`, `x:ab`, `x:A`, `x:a`, `x:B`, `x:Hawke's`, `x:hawkes`.
  The test first confirms on the engine that the database's order and
  Python's disagree on four of the pairs. Steps:
  - Tables made the old way, holding a link and a test pair in locale
    order. Python's pair for a decision is refused there (the fault,
    reproduced).
  - `links.ddl` migrates them: each CHECK carries `COLLATE "C"`, and the
    link is turned round under the same id. Run again, it is a no-op.
  - `build.build_all` runs, then `publish_ddl`. Every link is in byte
    order; the full-name stars centre on `x:A` and `x:Hawke's`; the group
    ids are `x:A`, `x:Hawke's` and `x:a c` (by the decision); and Python's
    `min` and SQL's `min(row_key COLLATE "C")` agree on each group.
    `check_published` passes.
  - In the same test, the same build with every `COLLATE` taken out of the
    SQL raises `CheckViolation`.
- Fast: `links.pair` against byte order; all six pair CHECKs (create and
  migration) carry `COLLATE "C"`; a static audit of the lane's SQL fails
  on any `least`/`greatest`/`min`/`ORDER BY`/`<` over a ref without it.
- **Mutations, run and restored by copy:** (1) every `COLLATE` taken out of
  build.py: the build test red (`CheckViolation` on `links_pair_order`),
  and the audit red. (2) The CHECKs in tables.sql plain again: the CHECK
  test red, and the build test red.
- `QV4_INTEGRATOR=1 bin/fast links`: green, 43 s. All of `links/tests`,
  slow included: pass.

## Check item 9 (`check_ruling_114`) in the budget

It died at the check's 300 s because its window and aggregate ran over all
2,023,258 `links.bodies` rows. Now `c` (the confirmed links' rows) comes
first. The bodies are read only for those name keys (`bodies_key`), and the
window only over the rows of those bodies (`bodies_body`). A body's
liveness reads its own rows alone, so the answer is the same. **Measured
read-only on live, through the read login: the old query 388.2 s (past
300 s), the new 4.9 s, figures identical** (292 confirmed, 30 one of
several, every count 0, `ok`).

**Its second line is red on live, from the data, before and after:** "no
NZBN names two bodies" counts 2:
- 35 charities carry the placeholder NZBN `0000000000000`.
- CC58580 and CC61425 (two dance academies, 2020 and 2023) carry one real
  NZBN.

The first is a reading fault: an all-zero NZBN is no NZBN, in
`rows.BODY_SQL` and the check. The second asks whether two charity rows of
one NZBN are one body. That is a rule question, so it is not done here.
Neither is changed: they were outside this brief, and a card costs two
closures (ruling 323).

## Live state, for the record (the integrator's)

links.links was rebuilt in place to the confirmed step (3,073,500
confirmed, 127,278 near before the failure, 953 related). links.groups is
from 17:36, so pub.groups lacks the new rows until the next build. Peak
1,208 MB, under the 4 GB figure. Nothing here prints a home address or a
suppressed name. The figures are counts, the fixture refs are invented,
and the two charities are organisations.

## Result (integrator, 29 October 06:02 NZDT)
Merged cf1d71f as `integrate/fix-links-5`, gate green at the fourth run. The first run (28 October 22:30) fell on readers' live tests that main also failed on the rebuilt tables; the second after the hand build likewise; the third died at collection on conflict markers the integrator's own chain committed when main (board-13) and this branch both touched the board's live test, resolved to main's file. In between, the readers were fixed in their own merges: fix-products-board-4 (the many-rows dossier), fix-products-templates-1, fix-products-scan-1, fix-products-report-4 (the star read through its centre), and board-13 (ruling 117). At the merge the links spec gained the near-link contract for readers, reworded as fix-products-templates-1 measured it. The live tables were built from this branch by hand on 28 October 22:47 (the constraint migration applied then), so no rebuild is queued now. Released. Branch and working copy retired. Open: the two charities sharing an NZBN and the thirty-five all-zero NZBNs (card); Arthur's observation that near links are an entity relation and belong between group ids (decision queue, with the scan's item).
