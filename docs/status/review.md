# review (track C): where it stands

**Date:** 2026-10-20. **Track:** C, the review agent, `links/`. **Merge request:** `review-1`.

## Done (in `scratch_review`, on the real published tables)

- The agent (`links/review.py`, `review-agent@2`): evidence from the registers (offices and roles, no home address), a deterministic screen, the model under a verdict grammar on the review profile, readings recorded with run, pair, screen, evidence and served model; `--score`, `--report`, `--watched`, `--job` (QV4_ARGS), `--apply`; a reading waits for a model the planner lent away.
- Scored on every test pair the registers supply (575): 0 of 144 one-person pairs wrongly split (passes the default mark); 361 of 431 two-people pairs caught (83.8 per 100; the model alone 61.3 on the 181 it was asked). `links/measurements.md`, `links.scores`.
- Apply path behind `links.SETTINGS["review_applies"]` (off); `check.py` fails if a reading ever became a decision while off or without a passing score. 30 tests; module fast tier green.
- Lane housekeeping: the column migrations (card closed); candidate-returns rows; the old candidate anchors mapped (5,383 decisions promoted, 28 more); `candidate-across-amended-return` (2 pairs) supplied.
- Live jobs: `qv4-rehearsal-review` queued twice (13:10, 13:45) to bring the review profile onto a card; both ran. Nothing else touched. [x]

## Carded / queued

- `the-fetch-gate-has-no-search-route` (support/); `the-links-tables-do-not-migrate-an-existing-column` closed; the two pair cards updated.
- Queue: `may-the-review-agent-s-splits-be-applied` (default no); `the-review-agent-s-pass-mark` (founding) now has data.

## Next

1. Integrator: load `links/` as before (`tables.sql` now migrates), append the `qv4-links-review` command from `jobs-proposed.toml`, run the job once in mode `score` on the live schema.
2. When a charities lane publishes: `links.pairs`, then score again; the model's one-person rate is measured on 2 pairs today.
3. The search route (card), then the web arm of the agent.
