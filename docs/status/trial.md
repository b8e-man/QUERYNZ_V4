# trial: where step 3 stands

Session 2 (Fable), 19 October 2026, node2, branch `session/trial`.
Scope `support/trials`, `support/profiles`, `docs/trials`.

## Done

- 3.1 to 3.4 (session 1, merged as trial-1): models on `/mnt/hdd2/qv4-models`,
  profiles and job types in the catalogue, the page set (255 documents,
  2,698 pages), the keys.
- 3.5 pass one: `qv4-trial-read-glm-ocr` #54 done, 2,698 pages, 0 unread.
  Joined to the old cache by image hash: 2,013 of 2,124 equal; the 111
  differences carded with their cause (`pass-one-differs-from-the-old-readings-on-111-pages`).
- 3.7 scoring rewritten after the free key failed on first use: key
  quality (form fields, OCR layers, images, garbage), two orderings, a
  bag-of-words rule, cross-family support, within-line loops, names-only
  examples, a pairwise agreement table. 31 tests green. Pass one scored.
- Cards: the 111 differences; the worker's lease lapse under short pieces
  (scheduler, fix session); GLM-OCR's loops on empty expense tables.

## Running

- Pass two, queued 07:16 on card 1: #66 OvisOCR2 (5.2 s a page), #67
  Chandra, #68 Infinity Q4_K_M, #69 GLM-OCR at 300 dpi; twenty-page
  comparisons #70 to #73; #74 TeleOCR one piece (unclaimable, the probe
  proof). The worker runs main's code: anything in `piece.py` or `rows.py`
  takes effect after a merge.

## Next

1. Inject `python -m support.trials.queue urgent` while #68 (the 35B) holds
   the card; record the swap there and back (proof: a small job never
   waits for ever). Rehearse `--hide-program` for the probe proof.
2. After the reads: `python -m support.trials.queue rows`; then the rows
   stage of the scoring (amounts against the printed total, rows only one
   family produces, example names in donor rows).
3. The repeat job of the 111 pages (needs trial-2 merged); the GLM-OCR
   "Text Recognition:" prompt variant (queue item, default: run after pass
   two).
4. 3.8: decide, write the verdict at the top of `docs/trials/page-readers.md`,
   version the profiles (`support/profiles`), file the lessons.
