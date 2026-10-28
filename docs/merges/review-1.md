# review-1: track C, the review agent, measured on the test pairs before it acts
branch: session/review (pushed; 4d594c6)
session: review (track C)
raised: 2026-10-20
claims: links/ (review.py rewritten; tables.sql migrations, readings columns and the scores table; rows.py candidate-returns views; old.py candidate-donation map; pairs.py two amended-return kinds; check.py check 4; __init__.py the review_applies setting; spec.md, README.md, measurements.md, jobs-proposed.toml; tests test_review_agent, test_review_and_old, test_links); cards `the-fetch-gate-has-no-search-route` (support/, yours or a support session), `the-links-tables-do-not-migrate-an-existing-column` closed, `three-test-pair-kinds-the-registers-cannot-supply` and `old-decisions-that-could-not-be-mapped-to-new-rows` updated; queue `may-the-review-agent-s-splits-be-applied`; lessons `state-the-register-s-fact-in-the-evidence-…`, `a-session-s-reading-through-a-lent-card-must-wait-not-die`; docs/status/review.md

Built and measured in `scratch_review` on the real published tables.

| Piece | Figures |
| --- | --- |
| the agent `review-agent@2` | a screen (source identifier; middle names differ), then the review model under a verdict grammar; 22.5 s a reading on the review profile |
| scored, 575 test pairs | one person: 0 of 144 wrongly split (passes the default 1 in 100); two people: 361 of 431 caught (83.8 per 100; the model alone 61.3 on the 181 it was asked) |
| the caveat | 142 of the 144 one-person pairs are passed by the screen; the model kept 2 of 2. The model's own wrong-split rate is unmeasured until a charities lane supplies one-person pairs |
| apply path | `links.review --apply`, refused while `links.SETTINGS["review_applies"]` is off (it is) or the judgment's fingerprint has no passing score; `check.py` 4 fails if a reading ever became a decision while off |
| web | none: the gate has no search route (card); `web_query()` and `cite_check()` built and tested |
| housekeeping | `tables.sql` migrates (ALTER … ADD COLUMN IF NOT EXISTS); candidate-returns rows; 5,383 old decisions promoted (28 more, candidate donations); `candidate-across-amended-return` 2 pairs |
| checks | links fast tier green (30 tests); the whole-repository fast tier has two reds, neither mine to fix: `tests/test_generators.py::test_the_committed_records_generate_cleanly` says `docs/board.md` is stale (a new card; the board is yours to regenerate at the merge, the hook refuses it here) and `registers/candidate_returns … test_the_sample_s_cases_land_where_the_list_says`, red on main too |

For the merge, please:
- Load `links/` as before (`python -m links.rows`, `links.old`, `links.build`, `links.pairs`, `links.measure` with `--schema links`); `tables.sql` now adds the missing columns itself.
- Replace the `qv4-links-review` command in `support/scheduler/jobs.toml` with the one in `links/jobs-proposed.toml` (`python -m links.review --job`; QV4_ARGS picks the mode), run the catalogue's check, delete the proposed file.
- Queue it once with `--args '{"mode": "score"}'` so the live schema carries the score (`links.scores`); its default mode (`watched`, 200 flagged links a run) records and applies nothing.
- Drop `scratch_review` after the merge.
- Nothing here changes a confirming rule or applies a verdict.

## Result (integrator, written 29 October 2026 for the merge of 20 October 19:26 NZDT)
Merged 9fd5933 as `merge integrate/review-1: gate green` on 20 October. The result line and the copy under docs/merges/ were not written at the time; this integrator found the omission on 29 October and wrote both. The agent's later state is in docs/status.md (track C measured; the agent scores and applies nothing, ruling 69).
