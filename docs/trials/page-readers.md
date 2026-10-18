# The page-reader trial (plan step 3)

Written by the trial session as it goes; the verdict (3.8) goes at the
top when it exists. Everything below is keyed to the document's hash and
page (condition 2), runs under the existing document profiles with only
the page reader swapped (condition 1), and decides text or scan per page
(condition 3).

## Verdict

Not yet. Pass one has run and is scored; pass two is on the card (queued
19 October 07:16). The incumbent stays alone until the decision.

## The models, as served

| Reader | Family | Files served (`/mnt/hdd2/qv4-models/…`) | Levels | Licence | Prompt (its own) |
| --- | --- | --- | --- | --- | --- |
| GLM-OCR (incumbent) | Zhipu | `/home/user/models/vision-glm-ocr/` Q8_0 (hash-equal to ggml-org's); f16 from ggml-org | Q8_0, f16 | MIT | `OCR` (the old estate's; the card's `Text Recognition:` recorded as a variant) |
| TeleOCR | Qwen 2.5-VL (Qwen3-style decoder) | `teleocr/NaviDC-OCR-*` from nandraj (the model's former name; its own GGUF is not for llama.cpp) | Q8_0, f16 | Apache-2.0 | `Please output the text content from the image.` with the card's system line; tables come as OTSL under the table prompt |
| OvisOCR2 | Qwen 3.5 (0.8B) | `ovisocr2/` from Abiray | Q8_0, F16 | Apache-2.0 | the card's Markdown instruction |
| Chandra OCR 2 | Qwen 3.5 (mid) | `chandra-ocr-2/` from mradermacher (base named as the mirror vasu-12) | Q8_0, Q4_K_M | modified OpenRAIL-M (on the legal list, ruling 49) | the package's `OCR_LAYOUT_PROMPT` |
| Infinity-Parser2-Pro | Qwen 3.5 (35B mixture, `qwen35moe`, 256 experts, 8 used) | `infinity-parser2-pro/` Q8_0 from glebkudr (36.9 GB, larger than a card); Q4_K_M (21.2 GB) made here from it in 507 s, twice-quantised | Q4_K_M (card), Q8_0 (experts on the processor) | Apache-2.0 | the package's `PROMPT_DOC2MD` |

Every reader: temperature 0, one slot, 32k context, the document
profile's dots per inch (300; pass one at the old estate's 200), the
Qwen 3.5 bases with thinking off. The settings stamped on each reading are
in `support/trials/readers.py`; the scheduler profiles in
`support/trials/scheduler/profiles-additions.toml`.

Read from each file's own metadata (18 October): OvisOCR2 and Chandra
OCR 2 are `qwen35` with a `qwen3vl_merger` projector, TeleOCR `qwen2vl`
with `qwen2.5vl_merger`, GLM-OCR f16 `glm4`; every one an architecture
and projector the b10276 server build knows. The 35B is `qwen35moe` per
its converter, converted at a later commit than the box's server (its
loader metadata was adjusted for compatibility; whether b10276 loads it
is found at the first swap).

TeleOCR loads only on a server patched as its conversion's PATCHES.md
says; built beside the estate's servers at `<live>/llama/built-teleocr/`
(the patch is in `libllama.so`; the server binary is byte-identical). The
scheduler cannot yet pick a server per profile (card).

## The page set (3.3)

`support/trials/pageset.jsonl`, version 1: 1,522 captured files in the
window (2019 on, ruling 347) → 1,521 distinct documents → 255 in the set,
2,698 pages: 2,243 scan pages (all of them) and 455 text pages (capped at
four per document, as free keys). Every 2019+ party donation return is in
(a return is the product); candidate returns, 20k disclosures, party
expense returns, financial statements and promoter returns are sampled
twelve per kind-year, scans first, plus the raster photographs. Shapes:
text, image first page, scan, mixed, raster; the handwritten case by
name. Named cases, whole: NZ First 2023 (`11490261631b`), ONE Party 2020
(`cada3e957a11`, the amended return is what is held), the Māori Party 2020
(`5e34999d1ccc`), Vision NZ 2020 handwritten (`24edf34f65bb`). Two pages
sit between the profile's 50-character rule and the contract's 80; the
contract's 80 is used and both are recorded.

## The keys (3.4)

`support/trials/keys.jsonl`: figures and hashes only. Declaration totals
from the text layer (35 returns); the Commission's by-year table (89
matched; its 2020 Māori Party and Advance NZ figures marked `excepted` and
never a key); the frozen site's series (59, by source file name → hash);
the old page-read records by their own sha256 (155, Part A only); the
confirmed tier of the old answer set (142 cells, 32 of the set's
documents), read from the old folder at scoring time because it carries
donors. Cross-check where two keys meet: declaration = frozen on 24 of
24; declaration = Commission on 25 of 28 (the three differences are the
Labour 2020 amendment, Green 2021's cents, Women's Rights 2023's
amendment: the table and the file are different filings).

## Pass one (3.5)

Rehearsed first on `qv4-reread-pages` (queue 52: 115 scan returns'
declaration pages at 300 dpi, 123 runs ok, peak 1,044 MB, 6.5 s a piece).
Then the pass proper, `qv4-trial-read-glm-ocr` #54, queued by the
integrator on 18 October at 22:47 and done at 02:34: 255 documents, 2,698
pages at the old estate's 200 dpi, 264 runs (6 killed by a lease lapse and
re-run: card `the-worker-s-lease-lapses-under-a-run-of-short-pieces`), 0
pages unread, 5.0 s a page, peak 676 MB a piece. Joined to the old estate's
cache by the rendered image's hash: 2,124 hits, 2,013 equal after
whitespace (94.8%), 111 different on 70 documents, 574 never read by the
old estate (405 scan pages, mostly financial statements and expense
returns, and 169 text pages). The 111 are carded with their likely cause
(`pass-one-differs-from-the-old-readings-on-111-pages`): the same build,
weights, prompt, resolution and token limit as the frozen server, one flag
apart (`--jinja`), and a measured floor of run-to-run drift on the card (2
of 97 page images read twice inside the pass came back different). The
second try, a repeat reading of the 111 under the same settings, runs once
`piece.py`'s `repeat` argument is merged.

## Scores (3.7)

`python -m support.trials score` scores every stored reading of the page
set and writes `scratch_trial.page_scores` (one row per reading per page)
and `scratch_trial.page_agreement` (every pair of readers on a page). The
free key needed a quality test before it could be used (lesson
`a-text-layer-is-a-partial-key-on-most-form-pages`): 298 of the 455 text
keys are partial (form fields 226, text over an image 44, scanner OCR
layers, garbage), and a run on a partial key is undecided until another
family has read the page. Under the measures as now written, GLM-OCR at 200
dpi on the 161 complete keys: 4 pages fail the invented-text rule (the
form's printed instructions and an auditor's paragraph the layer lacks;
decided by pass two), 139 exact to the cent, 0 loops. On the 2,243 scan
pages: 27 loop failures (card `glm-ocr-loops-on-empty-expense-tables`:
seven pages repeat a line 650 to 1,324 times, one loops sideways, the old
readings carry the same loops), 0 lone amounts (no other reader yet).

## Pass two (3.6) and the decision (3.8)

Queued 19 October 07:16 on card 1, in the scheduler's own order:
OvisOCR2 (#66, 5.2 s a page), Chandra OCR 2 (#67), Infinity-Parser2-Pro
Q4_K_M (#68), GLM-OCR at 300 dpi (#69), then the twenty-page compression
comparisons (#70 to #73) and a one-piece TeleOCR job (#74) that no box
can claim (its program is missing: the probe proof). The urgent page is
injected while the 35B holds the card. Not decided yet.

## What the run proves about the scheduler

| Proof | Shown? |
| --- | --- |
| One model per card at a time, every swap recorded | Shown: `scheduler.swaps` rows 84 to 89 (load, handover, drain, release of `page-reader` for queues 52 and 54) and the unload/load to `trial-ovisocr2` at 07:16; card 0 untouched throughout |
| A swap pays for itself; a small job never waits for ever | Not yet: `qv4-trial-urgent-page` is injected while the 35B holds the card |
| Long work is cut into pieces that record progress | Shown: 255 pieces, `pieces_done` advancing per piece; six pieces killed by a lease lapse lost one page each and re-ran |
| Either box can take the work | Owed on node1 (rulings 55 to 57) |
| The profile is probed, not typed | Partly: queue row 74 (`qv4-trial-read-teleocr`, requires `qv4-llama-server-teleocr`) sits unclaimed with no log noise; the rehearsal with `--hide-program` is owed |
| Peak memory is recorded | Shown: `peak_mb` on every run of queues 52 and 54 (676 MB a piece against 1,536 declared) |
