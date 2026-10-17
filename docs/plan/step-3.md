## Step 3: the page-reader trial over the election documents

**Goal.** Choose the page reader, and a second reader from a different family, for the rebuilt Follow the Money. Prove the scheduler on a real job while doing it.

**Why here.** Five models over the same pages forces the graphics cards to swap, which has only ever run in rehearsal. The election documents come with known answers. The result is needed by step 4.

**Model.** Fable sets up the page set, the scoring and the first pass. Opus can run the second pass.

### The models

GLM-OCR is the incumbent. It was chosen on 22 September because it invented nothing; it even reproduced a filer's typo. The old estate recorded the question as settled for electoral returns. Arthur has reopened it (rulings 49 and 50).

| Model | Family, for choosing a second reader | Size | Licence | Why it is in | Caution |
| --- | --- | --- | --- | --- | --- |
| GLM-OCR (incumbent) | Zhipu | 1.3B; 4.8 GB on a card; 4.4 seconds a page | MIT | The reference | Files at `/home/user/models/vision-glm-ocr/`; served today by `querynz-vision-ocr` on port 8032 |
| [TeleOCR](https://huggingface.co/bbsai/TeleOCR), formerly NaviDC-OCR | Qwen 2.5 base | 1.2B | Apache 2.0 | Top published score on the main document benchmark; reads photographed and bent pages | Served here only through a community conversion; tables come out in a tag format that needs converting; weaker on degraded pages |
| [OvisOCR2](https://huggingface.co/Abiray/OvisOCR2-GGUF) | Qwen 3.5 base, small | 0.8B | Apache 2.0 | Nearly the same score, smallest; one Markdown page out, the same shape GLM-OCR gives | Community conversion; no data on poor scans |
| [Chandra OCR 2](https://huggingface.co/datalab-to/chandra-ocr-2) | Qwen 3.5 base, mid | 5.3B | Weights free under US$2M revenue or funding; use that competes with its maker's own service is restricted | Strongest published claim on handwriting and forms | In by ruling 49. Its licence goes on the before-selling legal list. Weakest on old scans |
| [Infinity-Parser2-Pro](https://huggingface.co/infly/Infinity-Parser2-Pro) | Qwen 3.5 base, large | 35B | Apache 2.0 | Highest score on the other main benchmark | English and Chinese only; weak on rotated tables. September's rejected large model put a printed total in among the rows |

For the second reader, GLM-OCR is one family and every Qwen-based model is another. Two Qwen-based models agreeing is weaker confirmation than GLM-OCR agreeing with one of them.

Already rejected and not to be re-run: Qwen2.5-VL-32B (one of three on controls) and PaddleOCR-VL-1.6 (repeated one line eleven times and invented a sentence). Looked at on 11 October and left out: DeepSeek-OCR 2 (lower scores), Unlimited-OCR (needs an unmerged build of the model server and loops on dense pages), MinerU 2.5 Pro (a whole toolkit with extra licence terms), Xiaomi-OCR-0 (no published benchmark). No public benchmark measures invented text, which is the test that matters here.

### Three conditions from Arthur

1. **The document profiles come first.** The trial runs under the existing profiles and swaps only the page reader a profile names. Everything else is held fixed.
2. **A reading is tied to the document's bytes, never to its name.** Last time readings were attached to the wrong documents. The old corpus was 4,020 files but 3,325 distinct documents; 424 returns were held under two names; one return, byte-identical under two names, would have filed 1,469 rows ($40.07m) twice. Record every reading against the file's hash, the page number, the model, its build, its settings and the profile version. Draw the page set from distinct hashes. Join the known answers by hash.
3. **Text or scan is decided per page.** Some files mix scanned pages with pages that carry text. A whole-document test once called a return readable while its declaration page was an image, so it read as having no total. The rule in the profiles: a page with under 50 characters of text goes to the page reader; a page with a text layer stays with the text reader, which outranks any page reader.

### Do

**3.1 Get the models onto both boxes.** Download each once, off-peak, and copy it to the other box over the local link through the installer. Use each model in the form the boxes' model server can load, with its image projector file. For each model fetch two levels of compression and compare them on twenty pages, because community conversions vary; keep the smaller only if it reads the same. If a model needs a newer build of the model server, install that build beside the old one (hard limit 23).

**3.2 Serve each as a scheduler profile.** Use each model's own documented prompt and input format; these models are trained on specific prompts and do poorly on generic ones. Temperature 0. Record every setting. If a model cannot be served on these cards within two days of trying, card it, record why, and carry on without it.

**3.3 Build the page set,** from distinct hashes of the captured election documents.

- Every shape: all text, image first page, full scan, handwritten, two-column donor tables. Of the 56 live party returns, 24 were all text, 23 had an image first page and 9 were full scans; across all 125 staged party returns, 84 had no usable text layer.
- Every kind: party donation returns, loan returns, party and candidate expense returns, large-donation disclosures, party financial statements.
- The returns that failed in the old estate for want of a text layer.
- Three named cases as fixed tests: NZ First 2023 (a first pass found parts B and C and not A, and stated $202,639.75 for a party that spent $1,513,080.37); ONE Party 2020 (a pixel reading gave $30.43 against a true $30,433.35); the Māori Party 2020 (the text layer's $301,517.96 is right and the Commission's published $241,986.42 is wrong).

**3.4 Build the answer keys.** None needs a person.

- **Text pages as a free key.** Render a page that has a text layer to an image at the document profile's resolution and give it to each page reader. The text layer is the answer. This is the only key that can show invented text directly.
- **Each return's own printed total.** Every return prints one, so a reading's rows can be summed against it.
- **Declared totals from outside:** the Commission's own published table, and the frozen site's figures. The old register matched the Commission's table to the cent on $14,560,581.38 on 10 October. **Known exceptions, where the Commission's table is wrong and must not be used as the key:** its 2020 figures for the Māori Party and Advance NZ, which give Part A alone.
- **The old answer set** in `data-layer/docread/docread/gold.py`. Use only entries a person confirmed; 379 of the 381 stored corrections are machine-agreed and are not truth.

**3.5 Pass one: GLM-OCR alone, through the scheduler.** Use the same build and the same settings the old estate used, as recorded in its readings. Matched by hash and page, it should reproduce the readings the old estate already holds. A difference here points first at the scheduler or the harness, not the model. Try twice to remove each difference; then card what remains, with its likely cause, and go on to pass two. Some old readings were attached by file name and will not match for that reason alone.

**3.6 Pass two: add the four challengers.** Queue all five over the same page set as bulk jobs, with one small urgent job injected part-way to exercise the queue rules.

**3.7 Score per page.** Amounts and tables are scored after the text reader has turned each page reader's text into rows, using the text-reader profile from step 2.15, the same for every page reader.

| Measure | Rule |
| --- | --- |
| Invented text | On a text page used as a key: any run of five or more words in the reading that is not on the page fails the page. On a true scan there is no page key, so invention is judged three ways: an amount that appears in no other reader's output and breaks the printed total; a row that only one family of reader produces; a name that matches the form's own printed example or instructions |
| Loops | The same line three or more times in a row, where the text layer or the other readers show it once, fails the page. Genuinely repeated donor rows are not loops |
| Amounts | Every money amount exact, to the cent |
| Tables | Row count and column alignment. The row-number column sits outside the ruled border on these forms, and readers disagree on whether it belongs |
| Completeness | A part not read is not a part that is zero. A reading holding two of three parts has missed one |
| Agreement | Where two readers from different families agree, and where they differ |

**3.8 Decide.**

- A challenger replaces GLM-OCR only with zero invented-text and loop failures across the set and a better score on amounts.
- The second reader is the best model from a different family with zero inventions.
- If no challenger qualifies, GLM-OCR stays alone and the lack of a second reader is carded.
- Record the choice as a new version of each profile, and the whole trial in `docs/trials/page-readers.md`.

### What the run proves about the scheduler

| Proof | How it shows |
| --- | --- |
| One model per card at a time, every swap recorded | The swap ledger matches what the cards actually held |
| A swap pays for itself; a small job never waits for ever | The small models and the injected urgent job are not starved behind the 35B one |
| Long work is cut into pieces that record progress | A worker stopped mid-run loses at most one piece |
| Either box can take the work | One box's worker is stopped on purpose and the other finishes |
| The profile is probed, not typed | A box missing a program a model needs is never given that job |
| Peak memory is recorded | Each model's profile is filled from this run |

The run reads the captured documents and writes to its own scratch tables. It publishes nothing and does not touch the frozen site or its two model servers.

### Done when

- [ ] Pass one reproduces the old readings, or each difference has a card.
- [ ] Every model has a score per shape, or a card saying why it could not be served.
- [ ] Every scheduler proof in the table above has passed and is recorded.
- [ ] The primary reader and the second reader are chosen and written into the profiles.
- [ ] The lessons are filed.

### Brief to paste

Launcher: `bin/start-session trial support/trials support/profiles docs/trials`

```text
You are a build session for QueryNZV4 on node2, in the working copy
the launcher made for you. Read docs/PLAN.md, then docs/status.md and
your own status file, and continue where it stops. Do step 3: the
page-reader trial over the election documents, as the scheduler's
first real job. Search the lessons for reading documents, document
profiles and page readers first. Key every reading to the file's hash
and page, never its name. Decide text or scan per page. Run GLM-OCR
alone before adding the challengers. Write only to scratch tables;
put nothing on the public site; leave the frozen product's servers
alone. Push your branch and raise a merge request for each finished
piece. Update your status file at every close. Finish by telling
Arthur which reader won, which is the second reader, what is carded,
and whether step 3 is finished.
```

