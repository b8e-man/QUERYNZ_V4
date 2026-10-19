# trial-2: pass one scored and carded; the scoring rewritten; the repeat argument
branch: session/trial (on top of main at 1d44d05)
session: trial (session 2)
raised: 2026-10-19
claims: support/trials (score.py rewritten with its rows stage and level comparison, piece.py `repeat` and `reader` args, readers.py prompt variants, queue.py `variant` and `repeat`; tests: 37 green, fast tier green under the venv), docs/trials/page-readers.md, docs/status/trial.md, three cards, two lessons

What it claims: pass one (`qv4-trial-read-glm-ocr` #54) is scored against
the keys and joined to the old estate's cache (2,013 of 2,124 equal; the
111 differences carded with their likely cause). The free key of 3.4
needed a quality test before it could be used, and the scoring now has
one (`score.key_quality`: form fields, scanner OCR layers, page-size
images, garbage layers), judges a run against both pdftotext orderings
and a bag-of-words rule, lets another family's reading show the key
lacked text, catches a loop inside one line, counts example names only,
and writes `scratch_trial.page_agreement`. `piece.py` takes `repeat` in
the job's args so a deliberate second reading is keyed apart (the second
try the 111-page card owes).

## For the integrator

1. The worker runs main's `support/trials`; the `repeat` argument in
   `piece.py` is the only change the scheduler executes, and it is inert
   without the argument. Pass two (#66 to #74) is running on main's code
   and is unaffected by this merge.
2. Two cards are outside the trial's fence and ask for a fix session on
   `support/scheduler`: `the-worker-s-lease-lapses-under-a-run-of-short-pieces`
   (a few lines in `worker.py`) and, from session 1,
   `teleocr-needs-a-patched-server-the-scheduler-cannot-choose`.
3. The fast tier from a working copy still falls back to the system
   python (carded by session 1); run with the venv on the path.
4. Nothing to install; no unit changes; no profile versions yet (3.8).

## Result (integrator, founding session, 19 October 08:05)

Merged into main as b87bf46 (integration branch integrate/trial-2 from
session/trial at dbdbeb2, main merged in for the generated board, gate
green). Out of the trial's fence, done here: card
the-worker-s-lease-lapses-under-a-run-of-short-pieces fixed in
support/scheduler/worker.py (the renewal clock lives on the claim, not the
piece) with a slow test that was red before the fix (11 runs, one killed)
and green after; the card is closed. One lesson rule shortened to the
index's 240 characters. The worker was restarted to take the fix (at most
the piece in flight replayed). Still open for a fix session on
support/scheduler: teleocr-needs-a-patched-server-the-scheduler-cannot-choose.
