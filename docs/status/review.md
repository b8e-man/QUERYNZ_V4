# review (track C): where it stands

**Date:** 2026-10-20. **Track:** C, the review agent, `links/`. **Merge request:** `review-1` (not yet raised).

## Done (in `scratch_review`, on the real published tables)

- The lane's housekeeping: `tables.sql` adds each later column (`ALTER TABLE … ADD COLUMN IF NOT EXISTS`); the candidate-returns rows (donors and the filing candidate); the old candidate-donation anchors map; two amended-return pair kinds.
- The agent (`links/review.py`): evidence from the registers (offices and roles, no home address), a deterministic screen, the model under a verdict grammar, readings recorded with the run, the pair, the screen, the evidence and the served model; `--score`, `--report`, `--watched`, `--job` (QV4_ARGS), `--apply`.
- The apply path behind `links.SETTINGS["review_applies"]` (off); `check.py` fails if a reading ever became a decision while off, or without a passing score. 27 tests.

## Half-done

- The scratch build (`/home/user/querynzv4-work/scratch/review/build.log`): rows, old (5,383 promoted), links … pairs … measure.
- Live jobs: about to enqueue `qv4-rehearsal-review` once, so the scheduler puts the review profile on a card (hard limit 25: a recorded swap); the scoring then calls that card's server at the port the scheduler's cards table shows. Ticked when done: [x] (enqueued 13:1x NZDT)

## Next

1. Score the agent on every test pair; write the two figures here and in `links/measurements.md`.
2. Cards, lesson, `links/jobs-proposed.toml`, push, raise `review-1`.
