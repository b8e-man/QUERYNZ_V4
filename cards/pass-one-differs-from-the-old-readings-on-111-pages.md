# Pass one differs from the old estate's readings on 111 of 2,124 matched pages
kind: finding
state: open
use-case: Follow the Money (step 3.5, pass one: GLM-OCR alone through the scheduler)
session: trial
opened: 2026-10-19

Pass one (`qv4-trial-read-glm-ocr` #54, 255 documents, 2,698 pages, 200
dpi, 0 failures) was joined to the old estate's page cache by the sha256
of the rendered page image. 2,124 pages hit (1,838 scan pages, 286 text
pages the old estate had read as pixels); 2,013 are equal after
whitespace (94.8%); 111 pages of 70 documents differ. 574 pages had no
old reading at all (405 scan pages the old estate never rendered, mostly
financial statements and expense returns, and 169 text pages); a miss is
not a difference.

What the differences are (masked diffs, no page text read): 106 of 111
at 90% similarity or better: a word swapped (51), a digit (28), table
punctuation (13), mixed (14). Five below 90%: a near-blank page where
both readings are noise (one page image shared by two documents,
`14ba1fa0b15d`/`f95ba81d0b05` p10, a Markdown fence against a sentence);
`2f966d882745` p8, where the new reading loops sideways on an empty
expense table (1,446 amount tokens on one page; the old reading had 34);
`919d4fef5edb` p6, where the new reading holds 15 amounts and the old 3;
`bb593c50267d` p6 and `78441dc2a23e` p20, a line present in one and not
the other.

Likely cause, in the harness, not the model. Same weights (hash-equal),
same build (b10276 both: the frozen server runs
`/home/user/llama.cpp/build/bin/llama-server`, dated 5 August, and the
estate's copy records that build), same prompt (`OCR`), same 200 dpi,
same `max_tokens` 8000 and temperature 0, text before image. Two
differences remain. (1) The scheduler's `page-reader` profile adds
`--jinja` (the frozen unit has `-ngl 999 -c 32768 -np 1 --cache-ram 512`
and no template flag), so the prompt is tokenised through the model's
own chat template instead of the server's built-in one. (2) The card is
not reproducible at temperature 0: inside pass one itself, 97 page images
were read twice (pages shared by two documents) and 2 came back
different. That rate alone explains about forty of the 111.

Tries. First: the determinism check above (done, free). Second, owed: a
repeat reading of the 111 pages under the same settings (`piece.py` now
takes `repeat` in the job's args, keyed apart; it runs once trial-2 is
merged: `python -m support.scheduler enqueue qv4-trial-read-glm-ocr
--pieces <the 70 documents> --args '{"pass":"repeat","dpi":200,
"old_cache":true,"repeat":1,"pages":"selected"}'`), and a reading
without `--jinja`, which is a one-line change to a profile outside the
trial's fence (support/scheduler/profiles.toml).

Blocks: nothing. GLM-OCR's pass-two readings (300 dpi) and the
challengers' are scored against the keys, not against the old cache.
Accepted onto the trial's record once the repeat job has run: if the
repeat differs from the first trial reading at about the same rate, the
111 are the card's drift and the old readings are reproduced to within
it.
