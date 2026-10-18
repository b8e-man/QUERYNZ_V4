The old estate's page readings are keyed by the sha256 of the rendered page image, not the document: render the same bytes with the same renderer at 200 dots per inch and the old reading joins by hash and page; a file name joins nothing.
area: reading documents, page readers, the trial, re-reads
paid-for-by: 2026-10-18, trial session, step 3.5

`ec_pageread.vision_ocr` cached every GLM-OCR page text under
`var/ocr-cache/glm-ocr-<sha256 of the PNG>.txt` (12,838 pages); its
document-level records (`pageread/<year>/<name>.json`) carry the document
sha256 but only rows and totals. So pass one's "reproduce the old
readings, matched by hash and page" is: page set hash → bytes → `pdftoppm
-r 200` → PNG hash → old text, compared with the new reading
(`support.trials.piece.old_cached_text`). Poppler is 26.01.0 on this box;
a different renderer version may change the PNG bytes and miss the cache,
which would look like a model difference and is not one.
