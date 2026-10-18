# trial: where step 3 stands

Session 1 (Fable), 18 October 2026 night, node2, branch `session/trial`.
Scope `support/trials`, `support/profiles`, `docs/trials`.

## Done

- 3.1 models on `/mnt/hdd2/qv4-models/` (ledger `downloads.jsonl`, every
  file hash-equal to the hub's): OvisOCR2 Q8_0+F16 with projectors;
  TeleOCR as NaviDC-OCR Q8_0+f16 with projectors; GLM-OCR f16 (the Q8_0 in
  the models folder is hash-equal to the hub's); Chandra OCR 2 Q8_0+Q4_K_M
  with projectors; Infinity-Parser2-Pro Q8_0 (36.9 GB, larger than a card)
  with projectors, its Q4_K_M made here by `models quantise` (see the
  ledger for whether it has run). A patched server for TeleOCR built beside
  the others: `<live>/llama/built-teleocr/` (PATCH.json).
- 3.2 the profiles and job types, as additions beside the trial's code
  (`support/trials/scheduler/`), checked on the merged catalogue; the
  patch is in merge request `trial-1`. The readers' own prompts and
  settings: `support/trials/readers.py`.
- 3.3 the page set: `support/trials/pageset.jsonl`, 255 distinct documents
  (from 1,522 files, 2019 on), 2,698 pages: 2,243 scan pages, 455 text
  pages as free keys; every kind and shape; the four named cases whole.
- 3.4 the keys: `support/trials/keys.jsonl`: declaration totals (35), the
  Commission's table (89, the two wrong 2020 figures marked), the frozen
  site (59), the old page-read records (155), confirmed gold cells (32
  documents, read at scoring time, never copied).
- 3.5 begun through the scheduler: `qv4-reread-pages`, 115 scan returns'
  declaration pages by GLM-OCR at 300 dpi (queue 52, 123 runs ok, peak
  1,044 MB, 6.5 s a piece, the swap and release in the ledger).
- 3.7 the scoring (`score.py`, tested) and the rows pass (`rows.py`).

## Half-done

- Pass one proper (every page, 200 dpi, joined to the old estate's cache
  by image hash) and pass two cannot be queued until the catalogue patch
  is applied on main: card `the-trial-s-profiles-and-job-types-live-outside-its-fence`.
- TeleOCR's arm waits on a per-profile server binary in the scheduler:
  card `teleocr-needs-a-patched-server-the-scheduler-cannot-choose`.
- The scheduler proofs: swap recorded, peak memory recorded, pieces that
  record progress: shown on queue 52. The other three wait for the passes
  (small job not starved; a worker stopped mid-run; the probe hiding a box
  without a program).

## Next

After the merge: `python -m support.scheduler enqueue qv4-trial-read-glm-ocr
--pieces <the page set's hashes> --args '{"pass":"one","dpi":200}'` (pass
one), score it, card the differences; then the challengers and
`qv4-trial-urgent-page` injected part-way; `qv4-trial-rows`; the
twenty-page compression comparisons; then 3.8.
