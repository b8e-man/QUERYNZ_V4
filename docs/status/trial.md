# trial: where step 3 stands

Session 2 (Fable), 19 October 2026, node2, branch `session/trial`.
Scope `support/trials`, `support/profiles`, `docs/trials`.

**Halted under ruling 60** (19 October 18:48): the trial stops with the
results in hand and resumes once the plan is complete. Step 3 is not
finished. The verdict is at the top of `docs/trials/page-readers.md`.

## Done

- 3.1 to 3.4 (session 1, merged as trial-1): models on `/mnt/hdd2/qv4-models`,
  profiles and job types in the catalogue, the page set (255 documents,
  2,698 pages), the keys.
- 3.5 pass one: `qv4-trial-read-glm-ocr` #54, 2,698 pages, 0 unread;
  2,013 of 2,124 old readings reproduced, the 111 differences carded.
- 3.6 pass two, part-run (queue 66 to 73, cancelled at the halt): OvisOCR2
  2,327 pages, Chandra 191, Infinity-Parser2-Pro Q4_K_M 445, GLM-OCR at
  300 dpi 2,063, the four twenty-page compression comparisons whole.
- 3.7 scores of everything read (`scratch_trial.page_scores`,
  `page_agreement`, `level_pairs`); 37 tests green.
- 3.8 verdict: GLM-OCR Q8_0 stays the reader, alone; no second reader
  (card `no-second-reader-qualifies-under-the-trial-s-rules`); eleven
  profiles versioned (`support/profiles/profiles.jsonl`, 56 lines).
- Cards this session: the 111 differences; GLM-OCR's loops on empty
  expense tables; no second reader; the lease lapses while a large model
  loads (scheduler); the card manager loads a profile for a job no box can
  claim (scheduler). Lessons: the partial key; temperature zero on the
  card; a measure judged against another reading.

## Running

Nothing. Card 1 is released (`scheduler.swaps` 327).

## Next (when the trial resumes, after the plan)

1. A profile that names its server (fix session on `support/scheduler`,
   with the two scheduler cards above), then the TeleOCR arm.
2. `python -m support.trials.queue two` again for the unread pages (stored
   readings replay; only the rest is read), `rows`, `repeat`, `variant`,
   `urgent` while the 35B holds the card; the `--hide-program` rehearsal;
   the two-box proofs on node1.
3. The loop measure counting cells, not lines; the invention measure with
   the page's letterhead in its bag; then `score --pages --rows --levels`
   and the second-reader card closes either way.
