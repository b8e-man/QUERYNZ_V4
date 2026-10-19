# The page-reader trial (plan step 3)

Written by the trial session as it goes. Everything below is keyed to the
document's hash and page (condition 2), runs under the existing document
profiles with only the page reader swapped (condition 1), and decides text
or scan per page (condition 3).

## Verdict (3.8, under ruling 60)

**GLM-OCR stays the page reader, alone.** Q8_0, the prompt `OCR`, the
profiles' dots per inch as written (300 for party returns, 200 for
candidate, disclosure and promoter returns). **There is no second
reader**: no challenger reached zero loop or invented-text failures on
the pages it shares with the incumbent (card
`no-second-reader-qualifies-under-the-trial-s-rules`). The eleven
profiles that name a page reader carry this as a new version each
(`ocr.second_reader` null, `ocr.trial` naming this write-up).

The trial was halted part-way through pass two on 19 October at 18:48 by
ruling 60 (Arthur: halt the test with the results in hand and come back
to it once the plan is complete). Every page read stays in the reader
store and the scores below are of what was read. **Step 3 is not
finished**: the "Done when" list has the pass-one differences carded and
the readers written into the profiles, but two scheduler proofs are owed
and the TeleOCR arm, the rows pass, the GLM-OCR prompt variant and the
repeat of the 111 differing pages never ran. What ran and what did not is
under "Pass two as run" and "What did not run".

## The models, as served

| Reader | Family | Files served (`/mnt/hdd2/qv4-models/…`) | Levels | Licence | Prompt (its own) |
| --- | --- | --- | --- | --- | --- |
| GLM-OCR (incumbent) | Zhipu | `/home/user/models/vision-glm-ocr/` Q8_0 (hash-equal to ggml-org's); f16 from ggml-org | Q8_0, f16 | MIT | `OCR` (the old estate's; the card's `Text Recognition:` recorded as a variant, not run) |
| TeleOCR | Qwen 2.5-VL (Qwen3-style decoder) | `teleocr/NaviDC-OCR-*` from nandraj (the model's former name; its own GGUF is not for llama.cpp) | Q8_0, f16 | Apache-2.0 | `Please output the text content from the image.` with the card's system line |
| OvisOCR2 | Qwen 3.5 (0.8B) | `ovisocr2/` from Abiray | Q8_0, F16 | Apache-2.0 | the card's Markdown instruction |
| Chandra OCR 2 | Qwen 3.5 (mid) | `chandra-ocr-2/` from mradermacher (base named as the mirror vasu-12) | Q8_0, Q4_K_M | modified OpenRAIL-M (on the legal list, ruling 49) | the package's `OCR_LAYOUT_PROMPT` |
| Infinity-Parser2-Pro | Qwen 3.5 (35B mixture, `qwen35moe`, 256 experts, 8 used) | `infinity-parser2-pro/` Q8_0 from glebkudr (36.9 GB, larger than a card); Q4_K_M (21.2 GB) made here from it, twice-quantised | Q4_K_M (card), Q8_0 (experts on the processor) | Apache-2.0 | the package's `PROMPT_DOC2MD` |

Every reader: temperature 0, one slot, 32k context, the document
profile's dots per inch, the Qwen 3.5 bases with thinking off. The
settings stamped on each reading are in `support/trials/readers.py`; the
scheduler profiles in `support/trials/scheduler/profiles-additions.toml`.
The b10276 server build loads all four served models, the 35B included
(Q4_K_M ready in 124 s at its first load, Q8_0 with its experts on the
processor in 202 s; 2 s thereafter from the page cache). TeleOCR loads
only on the patched server built beside the estate's at
`<live>/llama/built-teleocr/`, which no profile can yet name (card
`teleocr-needs-a-patched-server-the-scheduler-cannot-choose`).

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
amendment: the table and the file are different filings). The free key
of the text pages is partial on 298 of 455 (lesson
`a-text-layer-is-a-partial-key-on-most-form-pages`).

## Pass one (3.5)

Rehearsed first on `qv4-reread-pages` (queue 52: 115 scan returns'
declaration pages at 300 dpi, 123 runs ok, peak 1,044 MB, 6.5 s a piece).
Then the pass proper, `qv4-trial-read-glm-ocr` #54, queued by the
integrator on 18 October at 22:47 and done at 02:34: 255 documents, 2,698
pages at the old estate's 200 dpi, 264 runs (6 killed by a lease lapse and
re-run: card `the-worker-s-lease-lapses-under-a-run-of-short-pieces`,
fixed by the integrator at trial-2), 0 pages unread, 5.0 s a page, peak
676 MB a piece. Joined to the old estate's cache by the rendered image's
hash: 2,124 hits, 2,013 equal after whitespace (94.8%), 111 different on
70 documents, 574 never read by the old estate (405 scan pages, mostly
financial statements and expense returns, and 169 text pages). The 111
are carded with their likely cause
(`pass-one-differs-from-the-old-readings-on-111-pages`): the same build,
weights, prompt, resolution and token limit as the frozen server, one flag
apart (`--jinja`), and a measured floor of run-to-run drift on the card (2
of 97 page images read twice inside the pass came back different; lesson
`temperature-zero-is-not-reproducible-on-the-card`). The second try, a
repeat reading of the 111 under the same settings, did not run (below).

## Pass two as run (3.6)

Queued 19 October 07:16 on card 1: OvisOCR2 (#66), Chandra OCR 2 (#67),
Infinity-Parser2-Pro Q4_K_M (#68), GLM-OCR at 300 dpi (#69), the
twenty-page compression comparisons (#70 to #73) and one TeleOCR piece
(#74). The scheduler rotated the card among the four bulk jobs about
hourly as the waiting jobs' priority aged past the holder's (the policy's
hour is a ceiling): sixteen loads, every one in `scheduler.swaps`, card 0
untouched throughout. Halted at 18:48 under ruling 60 with:

| Job | Pages read (of 2,698) | Documents | Kinds reached | Rate | Peak a piece |
| --- | --- | --- | --- | --- | --- |
| #66 OvisOCR2 Q8_0 | 2,327 | 217 | every kind but the promoter returns; 1,423 of 1,715 party-return pages | 5.8 s a page | 675 MB |
| #67 Chandra OCR 2 Q8_0 | 191 | 24 | candidate returns only | 47.1 s a page | 674 MB |
| #68 Infinity-Parser2-Pro Q4_K_M | 445 | 85 | candidate returns, disclosures, 208 financial-statement pages | 13.5 s a page | 676 MB |
| #69 GLM-OCR Q8_0 at 300 dpi | 2,063 | 162 | financial statements, party expenses, 1,396 party-return pages | 5.4 s a page | 231 MB |
| #70 to #73, twenty pages each | 80 | 20 | the twenty-page set | f16: 6.6 s (GLM, Ovis); Chandra Q4_K_M 17.3 s; Infinity Q8_0 36.5 s | 121 MB |
| #74 TeleOCR | 0 | 0 | never claimed (attempts 0) | | |

Five pieces were lost and re-run: two worker restarts by other sessions
(08:01 the lease fix, 10:33 the probe fix), two lease lapses while the 35B
loaded (card `the-lease-lapses-while-a-large-model-loads`), and the piece
in flight at the halt. The TeleOCR row was never claimed, but the policy's
rule 6 tried to load its profile three times, discarding the working
profile each time (card
`the-card-manager-loads-a-profile-for-a-job-no-box-can-claim`).

## Scores (3.7)

`python -m support.trials.score --pages --levels` scores every stored
reading of the page set: `scratch_trial.page_scores` (7,896 rows, one per
reading per page), `scratch_trial.page_agreement` (every pair of readers
on a page), `scratch_trial.level_pairs` (the compression comparison).
Measures: invented text (a run of five words nowhere on the page's text
layer, in both of pdftotext's orderings, nor in another family's
reading, with two or more of its longer words absent), loops (a line
repeated three or more times, or one amount token twelve or more times
in a line, beyond what the reference shows), amounts to the cent against
the key, example names, agreement by family.

**The incumbent.** GLM-OCR at 200 dpi over the 2,698 pages: 0 invented
pages on the 160 complete keys (the 4 of the first scoring were form
instructions and an auditor's paragraph that pass two's other family also
read), 1 on the partial keys with 6 undecided; 27 loop pages (8 runaways
of 100 or more repeats, all on expense returns: card
`glm-ocr-loops-on-empty-expense-tables`); 138 of 160 complete keys exact
to the cent, 234 of 295 partial. At 300 dpi on the 2,063 pages both
resolutions read: loop pages 20 to 18, exact amounts 122 to 121 of 139
keys. The higher resolution buys nothing measurable; the profiles keep
what they say.

**The challengers, on the pages each shares with the incumbent at 200 dpi:**

| Reader | Pages | Loop pages (runaways 100+) | Invented pages (on complete keys) | Exact amounts on complete keys | Example names |
| --- | --- | --- | --- | --- | --- |
| GLM-OCR, same pages | | 27 (8) | 1 (0) | 123 of 142 | 43 |
| OvisOCR2 | 2,327 | 68 (18) | 68 (19) | 128 of 142 | 42 |
| GLM-OCR, same pages | | 9 (1) | 1 (0) | 28 of 33 | |
| Infinity-Parser2-Pro Q4_K_M | 445 | 24 (5) | 12 (5) | 33 of 33 | 30 |
| GLM-OCR, same pages | | 9 (2) | 0 | 2 of 3 | |
| Chandra OCR 2 | 191 | 17 (9) | 1 (0) | 3 of 3 | 32 |

Read with the lesson
`a-measure-judged-against-another-reading-counts-layout-as-failure`: the
runaways are real (OvisOCR2 repeats one line 1,900 times on
`05da1deaca84` p4), but 14 of Infinity's 24 loop pages are a table's empty
cells printed one to a line, and the challengers' inventions on complete
keys, inspected on expense and financial-statement pages, are letterhead
and instruction text the layer lacks and the incumbent skips, plus
Infinity's Markdown fence. The counts are what the plan's rule measures;
the buckets are what the resumption refines.

**Agreement.** Amount-for-amount agreement between families on the same
page: GLM-OCR and OvisOCR2 agree on 47% of scan pages and 50% of mixed;
GLM-OCR and Infinity on 46% and 30%; the two Qwen readers with each other
on 58% and 54%. Readers of one family agree with each other more than
with the other family, as the plan expected.

**Compression levels (the twenty-page comparison).** GLM-OCR Q8_0 against
f16: 17 of 19 pages equal after whitespace, mean similarity 0.986, amounts
agree on 19 of 19. OvisOCR2 Q8_0 against F16: 18 of 18 equal. Infinity
Q4_K_M against Q8_0: 4 of 5 equal (0.986), amounts agree on 5 of 5.
Chandra Q8_0 against Q4_K_M: the one shared page 0.992 similar, amounts
agree. Nothing in the twenty pages separates a level from its neighbour;
Q8_0 stays, and the Q4_K_M made here for the 35B is a fair stand-in.

**The rows stage** (`score --rows`: amounts against the declared total,
rows only one family produces, example donors, the gold cells) has no
input: the rows pass did not run.

## What did not run

- The rest of pass two: OvisOCR2's last 371 pages, Chandra OCR 2's 2,507,
  Infinity-Parser2-Pro's 2,253, GLM-OCR at 300 dpi's 635.
- The TeleOCR arm (#74): needs the patched server a profile can name.
- The rows pass (`queue rows`) and so the rows stage of the scores.
- The urgent `waiting`-class page injected while the 35B holds the card
  (proof: a small job never waits for ever); the `--hide-program`
  rehearsal; the two-box proofs on node1 (rulings 55 to 57).
- The repeat reading of the 111 differing pages (`queue repeat`) and the
  GLM-OCR `Text Recognition:` prompt variant (`queue variant`): both
  commands exist and run on the merged code.

## What the run proves about the scheduler

| Proof | Shown? |
| --- | --- |
| One model per card at a time, every swap recorded | Shown: `scheduler.swaps` rows 84 to 327 (16 loads, 16 unloads, 14 releases, 3 failed loads on 19 October, every one on card 1; card 0 untouched) |
| A swap pays for itself; a small job never waits for ever | Partly: the four bulk jobs shared the card hourly without starving; the urgent injection was not made. Rule 6 fired three times for a job the box could not claim (card) |
| Long work is cut into pieces that record progress | Shown: `pieces_done` advancing per piece; five stops (two restarts, two load-time lapses, the halt) each lost one piece, re-run |
| Either box can take the work | Owed on node1 (rulings 55 to 57) |
| The profile is probed, not typed | Partly: row 74 was never claimed (attempts 0); the card manager still tried its profile (card) |
| Peak memory is recorded | Shown: `peak_mb` on every run (675 MB a piece for the readers against 1,536 declared) |
