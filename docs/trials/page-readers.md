# The page-reader trial (plan step 3)

Written by the trial session as it goes; the verdict (3.8) goes at the
top when it exists. Everything below is keyed to the document's hash and
page (condition 2), runs under the existing document profiles with only
the page reader swapped (condition 1), and decides text or scan per page
(condition 3).

## Verdict

Not yet. Pass one and pass two have not run over the page set: the job
types that run them wait on the integrator (the catalogue patch in merge
request `trial-1`). The incumbent stays alone until then.

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

Begun through the scheduler with the catalogue as it stands:
`qv4-reread-pages` over the 115 scan returns in the document store (queue
52): GLM-OCR Q8_0 on the built server, 300 dpi, page 1 only, 123 runs all
ok, peak 1,044 MB against 1,536 declared, 6.5 s a piece; card 1 loaded in
2.0 s, drained and released when the queue emptied; nothing on card 0.
Scored (`score --pass reread`, 92 pages in the set): no loops, no example
names; 4 text pages with a key, 2 of them flagged for invented runs,
under investigation (each has one ten-word run with four words not on the
page at all, on a declaration page: a stamp or a signature block the text
layer lacks, or an invention; decided when pass one has every page). The
full pass (every page, 200 dpi, joined to the old cache by image hash)
waits on the patch. The join itself is proven: 80 of 80 scan pages from
40 returns, rendered at 200 dpi, hash to a reading in the old estate's
cache; at 300 dpi none do (`python -m support.trials oldcache`, and a
test).

## Pass two (3.6), scores (3.7), decision (3.8)

Not run. See `docs/status/trial.md` for the queue commands.

## What the run proves about the scheduler

| Proof | Shown? |
| --- | --- |
| One model per card at a time, every swap recorded | Partly: load, drain, release of `page-reader` on card 1 for queue 52 in `scheduler.swaps`; card 0 untouched |
| A swap pays for itself; a small job never waits for ever | Not yet: needs the bulk passes and the injected `qv4-trial-urgent-page` |
| Long work is cut into pieces that record progress | Shown: 115 pieces, `pieces_done` advancing per piece |
| Either box can take the work | Owed on node1 (rulings 55 to 57) |
| The profile is probed, not typed | Partly: the TeleOCR job types require a program the probe lacks and are never claimed; the full proof with the hidden program waits for the passes |
| Peak memory is recorded | Shown: `peak_mb` on every run of queue 52 |
