# links-1: the two confirming rules on every published register, the old ledgers copied and mapped, the test pairs and the six measurements
branch: session/links (pushed; d18fba9)
session: links (session 1)
raised: 2026-10-20
claims: links/ (rows, rules, build, build_all, old, pairs, measure, review, check, tables.sql, publish.sql, spec.md, README, measurements.md, jobs-proposed.toml; tests test_rules, test_review_and_old, the existing test_links); cards `the-links-jobs-into-the-catalogue` (blocker, yours), `three-test-pair-kinds-the-registers-cannot-supply`, `old-decisions-that-could-not-be-mapped-to-new-rows`; queue `may-a-company-name-alone-confirm-a-donor`, `does-one-company-s-office-count-as-a-shared-address`; lessons `a-server-side-cursor-and-a-copy-cannot-share-one-connection`, `count-the-same-thing-two-ways-before-reporting-it`; docs/status/links.md

Step 4.2 and 4.3, built and measured in `scratch_links` on the real
published tables (nothing from the sample). A row is named
`<register>:<key>` as the board assumes; `pub.names` is the search table
across registers.

| Piece | Figures |
| --- | --- |
| rows (nine registers, `pub.*` only) | 2,748,195 person rows; 867,276 registered offices; 1,920,468 company names; 3 min |
| rule 1 `full-name@1` | 1,257,095 confirmed |
| rule 2 `name-and-address@1` | 942,014 confirmed (573,440 a director and a shareholder of one company) |
| `official-number@1`, `source-identifier@1` | 4,384; 142 |
| `organisation-name@1` (near), `name-only@1` (near) | 191; 410,160 |
| watch | 2,199,109 watched, 149,982 flagged (regions apart 141,447; very common name 8,549) |
| groups | 669,863 over 2,251,437 rows; 51,618 contested; largest 1,220 |
| old ledgers | 77,179 rows copied exactly; 5,355 decisions promoted (the last word only) |
| test pairs | 430 + 1 two-people; 142 one-person; three kinds unsupplied (card) |
| check.py | 8 of 8 green against the old database, the 18 November rule and the views |

Links are stored as a star per component (one link per row to the
component's smallest key), so each stored pair satisfies its rule and the
table is bounded by rows. `pub.links` applies the last decision on a pair
(a `not the same` or `contested` shows as near with the decision as the
reason) and carries the watch's flags.

The six measurements are in `links/measurements.md` and
`links.measurements`. The one that matters for Arthur: on the known
two-people pairs rule 2 confirms through the two roles' shared company's
own office (rare 30.5%, middling 15.5%, common 16.7% once identical full
names are set apart), queued with a default. The 100-link reading is the
session's judgment from the registers, no web search; the review job for
the local model is built and not run.

For the merge, please:
- Load in this order with `--schema links`: `python -m links.rows`,
  `python -m links.old` (copy, map, promote; needs the rows), `python -m
  links.build`, `python -m links.pairs`, `python -m links.measure`; then
  `publish.sql`. `links.build_all` runs all but `old`. About 15 minutes;
  `SET statement_timeout = 0` is in each `main`. The links table carries
  `vacuum_truncate = off` (autovacuum's truncation deadlocked the refill
  twice).
- The two catalogue entries in `links/jobs-proposed.toml` (card), then
  delete the file.
- `scratch_links` and `scratch_links_pub` in `querynz_v4` are mine to go
  once the load is in; `/home/user/querynzv4-work/scratch/links/` holds the
  logs and the two review JSON files.
- `bin/fast links` from this working copy found no `.venv` and fell back to
  the system Python (no pytest); the 32 tests (links plus the one-way,
  reading-limit and tier tests) ran green through the main checkout's
  `.venv`. `tests/test_generators.py` will be stale from my cards and lessons
  (yours to regenerate).

Two lessons filed.

## Result (integrator, 2026-10-20 10:35 NZDT)

Merged into main as 20936a0 (merged main first). Done at the merge:
`qv4-links-build` (priority 36; 40 was held) and `qv4-links-review`
(60) in the catalogue, the proposed file removed, the card closed; a
lesson's rule cut to the limit; records regenerated. Fast tier and gate
green. After the merge, the load into `links` as asked, 10:12 to 10:35:
rows, build (1,257,109 and 942,014 confirmed; 669,826 groups), pairs,
measurements; `links.old` failed first, because the live
`links.old_decisions` table predates this session's shape and `CREATE
TABLE IF NOT EXISTS` left it without `source`, `verdict` and
`mapped_how`; the integrator added the three columns (`ADD COLUMN IF
NOT EXISTS`) and reran old (77,179 copied, 5,359 promoted), then
publish and the measurements again. Carded for the lane: `tables.sql`
must migrate an existing table's columns, as the register lanes do.
Published: `pub.links` 2,614,066, `pub.groups` 2,251,287,
`pub.decisions` 5,359, `pub.names` 2,748,359, `pub.old_decisions`
77,179. The board restarted and shows links. `scratch_links` and
`scratch_links_pub` in `querynz_v4` and the session's scratch folder
are Arthur's to clear. The session ran headless as Fable, about 95
minutes.
