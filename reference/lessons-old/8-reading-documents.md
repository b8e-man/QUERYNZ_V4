> Part of [LESSONS](../LESSONS.md) — living memory, one section per file
> since 2026-10-04 so that "read the relevant section" is a thing a reader
> can do. The rules of the file, and why it exists, are in LESSONS.md.

> **SPLIT OUT OF SECTION 3 ON 2026-10-09 (C551).** Section 3 held 182 of the
> corpus's 439 rules and 192 KB against T7.38's 160 KB one-read ceiling — not
> because measurement is 41% of what this estate learns, but because its
> routing pattern (`^tests/|test_|gate|invariants|board|audit`) matches the
> thing EVERY card does. These are the rules about READING A DOCUMENT and about what a figure on a page is evidence of. Nothing was edited, summarised or
> dropped: the rules below are byte for byte what section 3 carried, and a
> citation's `#id` is unchanged because it is six hex of the claim.

## 8. Reading documents & what a figure is evidence of

- **A READER POINTED AT ONE DIRECTORY READS ONE DIRECTORY.** Before calling
  a document unreadable, check that the estate's reader was ever aimed at it.
  *Paid for by:* 2026-09-25 — twenty-one of forty staged party EXPENSE returns
  were reported as "no text layer" and put in front of Arthur as questions.
  The estate has had an OCR lane since 2026-09-23 (`docread`), and its corpus
  is `var/staging/ec-donations`; the expense returns are in
  `var/staging/ec-expenses`. Nothing had ever looked at them. Arthur, having
  answered all eight by hand: *"I am confused as to why the images with no
  text layer were not read with ocr."* Rendered at 300 dpi and read by
  tesseract, they are plain text — sixteen of the twenty-one read on the
  first pass.

- **A SEQUENCE MATCH OVER EMPTY KEYS IS ONE LONG "EQUAL" BLOCK, SO THE GUARD
  AGAINST POSITIONAL PAIRING NEVER FIRES WHERE THE NAMES ARE MISSING.** C463,
  closed 2026-10-10. C422 had already ruled that inside a `difflib` **replace**
  block a pair must EARN the pairing, after position served Arthur a donor from
  page 5 who is printed on page 4. The guard was sound and unreachable in the
  one case that needed it most: Part G of a party return is three banded
  AGGREGATES and prints no donor, so every key on both sides is the empty
  string, `SequenceMatcher` reports `equal` however the amounts actually line
  up, and no replace block ever forms. Equal row counts therefore paired BY
  POSITION — the exact chimera — and unequal counts sent the remainder to
  insert/delete, where `merge` keeps the unpaired row and **one printed line is
  emitted twice**, once addressed by its margin number and once by a donor key.
  That was 530 extra rows across 64 of 119 documents, and it reached a person
  as a queue of 49 for a page holding 38.
  **BEFORE TRUSTING A SEQUENCE ALIGNMENT, ASK WHETHER THE KEY IS INFORMATIVE AT
  ALL** — all-empty keys are not a match, they are an absence of evidence, and
  the honest branch is the evidence path the module already has.
  TWO MORE THINGS THIS COST. The defect needs TWO readers, and one has run here
  since 2026-09-25, so it had already stopped happening: measured over all 107
  party returns in scope, 147 gold rows and **0 twins**, while the append-only
  ledger still holds 375 from the two-reader era. A card can close itself
  without anyone noticing, and the withdrawal rule stays permanent work rather
  than a transitional patch. And `Row.key()` — docstring *"what makes two
  readings THE SAME ROW for comparison"* — has NO callers: the sentence that
  looked like the answer was dead code, and the real alignment is elsewhere.
  **A FIX FOR A DORMANT PATH IS WORTH MAKING WHEN THE PATH IS ABOUT TO REOPEN:**
  this one was built the day a second OCR model was being considered.

- **USE THE INSTRUMENT THIS ESTATE ALREADY CHOSE, AND CHECK WHAT IT NEEDS TO
  RUN.** Before reaching for a subprocess, look for the service that does the
  job — and then check that a hand-run gets the same configuration the timer
  does.
  *Paid for by:* 2026-09-25 — the expense returns were OCR'd with tesseract,
  by `subprocess`, when `querynz-vision-ocr` was running GLM-OCR on
  127.0.0.1:8032 on both boxes and C432 had already measured the pair on this
  exact corpus: *"NOT tesseract (removed: 0 wins vs GLM's 28)"*. Every defect
  the session then spent its time gating around was a CHARACTER error — a `$`
  read as a 9, a 1 read as a 4 — which is the failure GLM does not have and
  the reason it was chosen. Arthur: *"why are you using tesseract? shouldn't
  you be using GLM?"* The second half cost as much as the first: `PAGE_IMAGE_URL`
  is set in the unit, so the nightly derive had the good reader and a hand-run
  silently fell through to the weak one, producing a different figure for the
  same document depending on who started the job.

- **A RULE THAT BRANCHES ON PROSE BREAKS WHEN THE PROSE IS REWORDED.** What
  produced a figure is a field, not a phrase in a sentence written for people.
  *Paid for by:* 2026-09-25 — the publication rule asked whether
  `stated_basis` ended with `"read by OCR"` to decide whether a disagreement
  with the Commission was the document's fault or the reader's. Putting
  GLM-OCR in front of tesseract changed that string to `"read by glm-ocr"`,
  and every OCR disagreement would have published as though it came off a text
  layer. `stated_reader` is now a column.

- **THE FORM'S OWN ARITHMETIC CATCHES WHAT CHARACTER CHECKS CANNOT.** A
  reading that has both a stated total and the parts it is made of can check
  itself against the document it came from, with no second source.
  *Paid for by:* 2026-09-25 — ACT's 2020 total OCR'd as `$91,082,166.64`,
  the dollar sign read as a 9. The digit grouping is valid, the decimal point
  is in the right place, every glyph-level check passes, and the figure is
  eighty-nine million dollars wrong. What refuses it is the form: Part A plus
  B plus C is not that number, and $91m is above the $2,806,400 expenditure
  limit printed on the same page. The same gate turned NZ First's 2023
  reading from $4,513,080.37 (a 1 seen as a 4) into the right figure, by
  rejecting the pass and taking the next one.

- **A GREEDY GAP BETWEEN A LABEL AND ITS FIGURE EATS THE FIGURE.** A pattern
  that skips "whatever is between" and then matches money will start the money
  as late as it can.
  *Paid for by:* 2026-09-25 — `TOTAL FOR PART A 300476.58`, printed with no
  dollar sign, matched as **$6.58**: the gap consumed `30047` and the reading
  was 99.998% short with nothing about it looking wrong. Found only because a
  better recogniser read the same page and the two disagreed. The fix is a
  lazy gap AND a lookbehind — lazy alone still starts at the first digit it
  can reach.

- **A GOVERNMENT SUMMARY TABLE IS A READING TOO, AND IT CAN BE WRONG THE SAME
  WAY TWICE.** Check a published total against the document it summarises
  before treating the publisher as the authority.
  *Paid for by:* 2026-09-25 — the Electoral Commission's 2020 party-expenses
  table publishes **Part A alone** as the total for the Māori Party
  ($241,986.42 against a declared $301,517.96) AND for Advance NZ ($364,769.96
  against a declared $403,583.95). One is an error; two of the same shape in
  one table is a process. Both were found by reading the returns, and neither
  would have been found by any amount of internal consistency checking.

- **THE DOCUMENT'S OWN ARITHMETIC OUTRANKS "WHICH READER WAS IT".** A figure
  recognised from pixels is a guess about characters; four figures printed
  separately that add up are not.
  *Paid for by:* 2026-09-25 — the rule "an OCR reading that disagrees with a
  published figure is the suspect" is right, and applied alone it would have
  buried Advance NZ's finding. The declaration block prints Part A, Part B,
  Part C and their total; where those add up, the document corroborates itself
  across four separately rendered numbers, and that is stronger evidence than
  the reader's provenance is weak.

- **A PART THAT WAS NOT READ IS NOT A PART THAT IS ZERO.** Summing the parts
  a reading happens to have found publishes a number short by exactly the
  part nobody could see — and nothing on the page says so.
  *Paid for by:* 2026-09-25 — the first OCR pass over NZ First's 2023 return
  found parts B and C and not A, and the summing rule stated $202,639.75 for
  a party that spent $1,513,080.37. It is ruling 350's silent drop wearing
  arithmetic's clothes: the form prints every part, $0.00 included, so a
  reading holding two of three has missed one.

- **A FIGURE OFF PIXELS AND A FIGURE OFF A TEXT LAYER ARE NOT THE SAME
  EVIDENCE, AND A DISAGREEMENT MEANS DIFFERENT THINGS.** Where the characters
  were never in doubt, two sources that differ genuinely differ. Where they
  came from an OCR pass, the reading is the likelier suspect.
  *Paid for by:* 2026-09-25 — the Māori Party's 2020 return declares
  $301,517.96 in its text layer against the Commission's published
  $241,986.42, and the Commission is wrong (it published Part A alone). ONE
  Party's 2020 return OCR's to $30.43 against a published $30,433.35, and
  the OCR is wrong. One rule for both would have republished a party's
  campaign at a thousandth of its size, or hidden a real error in a
  government table.

- **A FIGURE A PERSON READ OFF THE PAGE NEEDS A HOME IN GIT.** The review
  ledger is per-box; both boxes run the nightly derive.
  *Paid for by:* 2026-09-25 — Arthur answered eight expense questions in the
  reviewer, two of them figures no reader on this estate can reach. Those
  answers live in `var/review/docreview/entries.jsonl`, which `.gitignore`
  excludes, so node1 would have loaded both rows without them the same night.
  That is C434 exactly, which ran seventeen days. The fix is the same one:
  `data-layer/registers/expense_readings.jsonl`, beside the package.

- **The same money can be declared three times, and the form says so.** The
  2020 promoter return has three heads — election advertising, cannabis
  referendum, End of Life Choice referendum — and its own instruction is that
  an advertisement which is both counts IN FULL under each. Family First
  declared $141,224.34 under all three and the Commission's table repeats all
  three; it spent $141,224.34 once. A row sum would have published $423,673.02
  that nobody spent, and every glyph-level check would have passed. Before
  summing ACROSS a form's columns, read what the form says they mean.
  (2026-09-26, C453.)

- **The form talking about money is not a declaration of it.** A return that
  states nothing has an empty field, so a reader that searches near a label
  finds the nearest printed figure instead — and the promoter form prints two:
  the $100,000 filing threshold and the spending cap. The Public Service
  Association's Nil return read as $100,000 under all three heads, consistent
  with itself and caught only by the Commission's own table. Threshold and cap
  sentences are blanked before a line is searched. (2026-09-26, C453.)

- **A header row written with `<td>` is a data row.** The Commission's 2020
  promoter-expenses page does exactly that, and its empty last cell read as
  `Nil` — a filer called "Registered promoter" declaring $0.00. An empty cell
  is not a declaration of zero. What caught it was a second count taken a
  different way: one linked return per filing, against the rows parsed.
  (2026-09-26, C453.)

- **Ask which document profile a reading belongs to BEFORE writing the
  reader.** Two EC form readings were built, debugged and shipped on one day
  without one, and the same fact about the form family — a fillable PDF puts a
  typed value where the widget sits, not beside its label — was found and
  solved twice, in two modules that do not know about each other, with two
  different implementations. The profile is where a fact about a form family
  lives; a reader is where one document's turn at it lives.
  (2026-09-26, C451 d / C453.)

- **A profile written after its reader is a description, not a contract, until
  it is pinned both ways.** `test_profiles_are_true.py` holds the party
  expenses profile to the loader's own constants in both directions, and that
  is the only reason it is worth reading. Both new profiles are pinned the same
  way; the first mutation caught drift immediately. (2026-09-26.)

- **A veto that nothing feeds vetoes everything.** Document profiles recognise
  partly on surface signals, and one unmeasured signal sinks the whole match —
  correct, and the catalogue carried no surface on any row, so 3,197 of 3,365
  documents reached no profile. The design was right and nothing fed it. When a
  matcher returns nothing, check its inputs exist before widening its rules.
  (2026-09-26.)

- **A marker must state IDENTITY, not completeness.** `pages_min: 7` on the
  candidate return excluded 955 of 1,609 — the shorter pre-2019 form, and six
  in-window PARTIAL filings that are a single scanned declaration page. A page
  count is a fact about how much was filed, not about what the document is.
  (2026-09-26.)

- **A profile claiming a document it will not read is worse than no profile.**
  Widened, the in-window candidate profile took all 947 pre-2019 returns and
  reported them as handled. A separate profile that says "held, out of window,
  not read" turns the same documents from unassigned into
  recognised-and-declined — which is a different and honest answer.
  (2026-09-26.)

- **A document has many names and one set of bytes, and the recogniser did not
  know it.** The catalogue labels a row with its SHORTEST path, so filename
  markers written against the long name matched nothing for 424 returns held
  under both. Match every name the caller holds, not the label. (2026-09-26.)

- **An unassigned document is not proof that no profile covers it.** It may be
  proof that a marker is misspelt. Twenty ministerial workbooks reached no
  profile, so a profile was written for them — fragmenting one whose own
  `applies_to` already declared it covered members AND the Executive. The
  markers simply missed `min-expenses`, `membersoftheexecutive` and the
  publisher's own typo `executive-expense-discosure`. Read what already claims
  a class before writing one for it. (2026-09-26.)

- **Two profiles can both be right about the same document, and then the rule
  must be able to say what it is NOT.** A party's site yields pages rendered to
  PDF by the crawler and PDFs the party published; both live under the same
  path, and a ranking by number of reasons — deliberately unweighted — cannot
  settle it. Only the producer can. That is what a negative signal is for, and
  an unmeasured producer must never satisfy one: "we did not look" is not "it
  is not one". (2026-09-26.)

- **A profile can be wrong about its own corpus, confidently.** `captured-web-page`
  said "344 held from the party sites"; measuring the producers showed 73 made
  by Word and 148 by Adobe, so ~20 were the rendered pages it describes. A count
  in a description is a claim like any other. (2026-09-26.)

- **A number you did not hold is not a number you missed.** A guard that asks
  "is there money on this page the reader did not claim" must compare against
  everything the reading ACCOUNTS FOR, not the values it happens to store. The
  candidate form prints the total of Parts F and G; a reader holding F and G has
  explained that total completely without ever holding it. Comparing against the
  parts alone made 17 of the guard's first 24 firings false, and every one of
  those 17 was a reading that agreed with the Commission to the cent. Take the
  subset sums. (2026-09-26.)

- **Two numbers agreeing is not a catch.** I reported the Allington return as a
  confirmed true positive because the guard's figure, $3,110.01, matched the
  Commission's exactly. It matched because it was `part_f + part_g` — already
  read, already right. Before calling an agreement evidence, ask whether the
  instrument could have got that number from what it already had. (2026-09-26.)

- **An author a client supplies is not evidence of authorship.** The review
  comment route took `by` from the request body, and the first live POST — my own
  smoke test — wrote a comment attributed to Arthur that Arthur had never
  written. A ledger meant as evidence cannot take the author's name from
  whoever is calling it. The server stamps the role; the agent's own records are
  written from a CLI where the author IS the process. (2026-09-27.)

- **A truncation inside an evidence string deletes the basis of the figure beside
  it.** The PI harness recorded `rendered 13 route(s), 632,839 chars` and then
  `json.dumps(routes)[:260]` — three routes of ten, silently. When the total
  moved to 1,267,425 no stored audit could say which route grew, so the number
  was auditable and its basis was not (ruling 324). A breakdown is a sibling key,
  never a slice of a capped string. The right response to an unexplained figure
  is to fix the instrument, not to publish a cause it cannot support.
  (2026-09-28.)

- **A total proves how much was read, never who it was read against.** A party
  return reconciles when the donor rows sum to the printed Part A. Labour's 2023
  return is $510 out on $1.88m and every other in-scope return is out by less than
  $12,015 — and none of that says whether WILLIAMS ARENA's $7,385.96 is hers. A
  shift of one row across a run is invisible to a total: it cancels everywhere
  except its two ends. The second test — pair each printed donor with the amount
  printed beside them — is a different instrument, and where it can run (National's
  one-row-per-line layout, 175 rows) it says the rows are right, which the total
  never could. (2026-09-29.)

- **A line-order heuristic cannot pair a wrapped table, and it will not tell you
  so.** Pairing donors to amounts by "the next amount after the name" reported
  thirteen mis-paired rows on Labour 2023, in two tidy consecutive runs — the most
  convincing shape a false positive can take, because a real shift looks exactly
  like that. In that layout the amount precedes its donor's name line as often as
  it follows it. What killed it was checking ONE row against the page and then the
  arithmetic: the deltas of a real shift telescope to the document's own gap, and
  these summed to $1,695 against a $510 gap. Read the coordinates or say the rows
  are unpaired; never let a heuristic have an opinion about a layout it cannot
  resolve. (2026-09-29.)

- **A RECONCILIATION THAT COMPARES SUMS IS BLIND TO ONE IMPOSSIBLE LINE — AND THE
  MARKER OF A BAD READ GETS MISTAKEN FOR A FORMATTING INCONSISTENCY.** The
  disclosure loader gates each document on "the form's legal shape (one donor, over
  $20,000, party read)" and stamps `reconciled` per file, which compares the
  document's SUM against its stated total. Measured 2026-10-09: **22 live rows sit
  below the $20,000 floor the form legally exists for, $113,061.22 in all, the
  smallest $0 and the next $5 — and 19 of the 22 are `reconciled = TRUE`.** Nine OCR
  lines that happen to add up pass a sum check however absurd each one is, so the
  existing flag is not a weaker version of the missing gate; it answers a different
  question. 16 of the rows ($79,644) come from five PHOTOGRAPHED forms, which this
  module's own comment predicted — *"the OCR of a photographed form splits one
  declaration into twenty rows and misreads $24,500 as $7"* — and nothing enforced.
  `G_Harrison_30_June_2023.jpg` yielded NINE rows: $5, $2,500 three times, $2,590,
  $4,999, $5,150, $20,254. **Every photographed form that produced ONE row is sound**
  ($500,000, $62,000, $38,000, $20,000), so rows-per-document is the tell and the
  photograph is not.
  **AND THE DATES INVERT THE CARD THAT RAISED THIS.** C544 read `date_received` as
  "a text column holding two formats… needs one date format": 288 prose values, 16
  ISO. The prose values are the Commission's own text and **the ISO-shaped ones are
  the OCR's output** — two of them, `2023-05-34` and `2023-06-50`, are a day 34 and
  a day 50. Normalising the column would have laundered the unreadable rows into the
  same shape as the good ones and destroyed the only signal separating them. When
  one format is rarer, ask which PRODUCER writes it before calling it inconsistency.
  *Paid for by:* 2026-10-09 (C544), on a customer-facing money surface. T7.71 reads
  the floor from `registers.donations.DISCLOSURE_FLOOR` so the arm cannot drift from
  the lane it judges.

- **"PARTY + DONOR + AMOUNT + YEAR" IS NOT A DONATION'S IDENTITY — THE DATE IS PART
  OF IT, AND A BIG DONOR GIVES THE SAME ROUND SUM TWICE.** This corrects the key
  this very section prescribes above (*"the identity is party+donor+amount+year"*,
  2026-08-26). That key was derived from folding a >$20k disclosure onto its matching
  annual-return row, where it is right. Applied to the disclosure register itself it
  is catastrophic: measured 2026-10-09, **11 groups share party+donor+amount+year,
  and 9 of them are genuinely distinct donations worth $713,500.** RANK GROUP gave
  National $250,000 on 2026-08-14 AND $250,000 on 2026-08-05; ACT took $100,000 from
  Nicholas Mowbray in February and again in April; Troy Bowker gave $50,000 in May
  and in September. Round numbers from committed donors REPEAT, so amount-and-year is
  a coincidence generator, not a fingerprint. A naive dedupe on it would have deleted
  three quarters of a million dollars of real money from a published surface.
  **The discriminator is `declared_date_iso`, and where it is NULL the pair is
  UNDECIDABLE and must be reported, never folded.** The two real duplicates in the
  register are exactly the two groups where a copy has no ISO date — both JPGs: one
  document contributing four identical $2,500 rows (+$7,500), and one $23,800 gift
  held from both a JPG disclosure and the Commission's HTML index (+$23,800). Real
  over-count **$31,300**, not the card's $28,800 and not the $744,800 my own
  amount-and-year query first reported.
  *Paid for by:* 2026-10-09 (C544). Same shape as the 2026-08-26 entry it corrects —
  a key that is right for one join and wrong for the table it was carried to.

- **A PARSER'S ABSTAIN PILE IS A DOCUMENT CENSUS, NOT A LIST OF HARD CASES — GROUP IT
  BY SOURCE DOCUMENT BEFORE INVENTING A REPAIR.** C226 said the gazette appointment
  parser abstains on "fused name lists and table-form notices", and its 2026-10-08
  restatement named three classes with *"(b) not names at all, the biggest share"*
  and the instruction *"screen (b) first or no recovery number means anything"*.
  Measured over all 208,304 notices: 87,508 candidates, 51,570 kept, **35,938
  abstained (41.1%)** — the counts reproduce exactly — and then every class figure
  is wrong. Classifying all 35,938 by signal: **(b) never-a-name is 1,458, FOUR PER
  CENT and the SMALLEST class.** The tranche the card prescribed would have
  addressed 4% of the problem.
  **Grouping by the DOCUMENT instead of by the string found it in one query:
  90.9% of every abstain comes from ONE notice class** — the marriage and civil-union
  celebrant lists, 24,969 under a title containing "celebrant" and another 7,690 from
  THREE notices whose captured title is just `LIST OF MARRIAGE`. And they are not
  fused name lists at all. The source reads:

      Eliu, Eliu Papa, Seventh Day Adventist.Erika, Etuati Eddie, Seventh Day
      Adventist.Faalogo, Denny, Church of Jesus Christ of Latter-Day Saints.

  `Surname, Given Names, Organisation.` records run together, with the
  record-ending full stop swallowed into the next surname. So
  `Neil Seventh Day AdventistThompson` is **Neil Thompson, Seventh Day Adventist** —
  one person with an organisation fused into the middle of their name, not two people
  with a lost separator. **The commas survive, so the names are recoverable EXACTLY
  rather than probabilistically**, and the "given-name lexicon" the card wanted is
  not needed for any of it.
  **The repair is a PROFILE for that notice class** (Arthur's standing rule,
  2026-09-26: profile and recognition markers before the reading), and the generic
  appointment parser abstaining on them is CORRECT and should keep doing it —
  a wrong row is worse than a missing one. The marker must be the SHAPE, not the
  title: three of these documents are titled `LIST OF MARRIAGE`, and a probe for the
  record shape matches 11,976 notices against the ~30 the title finds.
  *Paid for by:* 2026-10-09 (C226). The lesson generalises past this card: an abstain
  pile is evidence about the CORPUS, and its modal document is usually one format
  nobody has read yet.

- **A CLAIM RECORDS WHAT ITS OBJECT IS AND NEVER WHERE IT CAME FROM, SO AN
  ADJACENCY DEFECT CANNOT BE MEASURED FROM THE GRAPH — AND A NAME SEARCH OVER THE
  EVIDENCE SYSTEMATICALLY OVER-REPORTS IT.** C459's defect is real and its examples
  are real: the press tier binds a role to whatever organisation was nearby
  (`prime minister of India`, `of RNZ`, `of post-Cabinet` on Christopher Luxon). The
  card then measured it — *"of 6,000: 49.2% object immediately BEFORE the role
  (correct), 12.4% FAR = the defect"* — and that figure cannot be what it says.
  `v3.claims` keeps `object_entity_id`, `evidence_text` and the evidence's offsets
  IN THE DOCUMENT; it keeps no offset for the OBJECT inside the evidence.
  `object_text` looks like the missing piece and is not: measured 2026-10-09, it is
  populated 248,642 times for ROLE against 2,141,720 rows carrying an object entity,
  and the two are complementary — **the span text is the fallback for an UNRESOLVED
  object, and once the object resolves the span is discarded.**
  So any adjacency figure is reconstructed by searching the evidence for the
  ENTITY'S CANONICAL NAME, which is not the span that bound it (`Air NZ` resolves to
  `Air New Zealand`). The reconstruction therefore reports "far" or "not in the
  evidence" whenever the surface differed, and it does so MORE for the paths that
  resolve best. My own run of it says so out loud: the `appositive` path, whose
  object comes from a regex group that is adjacent BY CONSTRUCTION
  (`PERSON, <title> of ORG`), scored **54.8% FAR** — worse than `title_prefix`,
  which is structurally the suspect. A measurement that ranks the regex-bound path
  as the worst offender is measuring its own join, not the defect.
  **The prerequisite is to record the object's span, or to re-run the extractor over
  the evidence.** Until one of those exists, the screen cannot be validated and no
  percentage of it should be quoted — including the card's.
  **And check which paths the denominator holds.** Requiring a `title` qualifier
  silently dropped two of the four methods that emit a role object: `register`
  (1,337,098 rows) and `dep_svo` (67,862) returned ZERO, so a figure that reads as
  "the press tier" was two paths of four, and `register` is not press at all.
  *Paid for by:* 2026-10-09 (C459), where the card's own number and mine disagreed
  by a factor of four and the reason was that neither could see what it claimed to.

- **A FINDER NAMED FOR ONE FORMAT SILENTLY EXCLUDES THE CLASS THAT NEEDS READING MOST
  — AND TWO CARDS DESCRIBING DIFFERENT SYMPTOMS WERE READING THE SAME DAMAGED
  DOCUMENTS.** C308's blocker read *"the gold corpus run holds 327 documents, every
  one `kind='party'`, zero disclosures"*, and that is true but not the obstacle:
  `docread.corpus` already takes `--kind disclosure` and **264 disclosure documents
  are ready to read**. The run was simply never made. The real blocker is one line:
  `find_pdf(stem)` globs `STAGING.rglob(f"{stem}.pdf")`, and `targets()` appends
  only `if pdf is not None` — so of the **12** documents behind C308's 31
  no-address rows, the **4 PDFs are targets and all 8 JPGs are silently absent.**
  **The exclusion is in the FINDER, not the reader:** `tatr.py` opens its input with
  `Image.open(path).convert("RGB")`, so a photographed form is natively readable;
  only `review.py`'s crop step needs `pdftoppm`, which an already-raster document
  does not need at all. The same `rglob(f"{stem}.pdf")` appears in both modules, so
  the restriction is stated twice and enforced nowhere on purpose.
  **And the photographed class is exactly the damaged one.** C308 ("no address",
  31 rows, $668,052.68) and C544 ("below the $20,000 floor the form exists for", 22
  rows) name **12 and 10 documents, 7 of them the same** — `G_Harrison_30_June_2023
  .jpg`, `R_Nauhira_10_October_2023.jpg`, `W_J_Deihl_6_September_2023.jpg` among
  them. Two cards, two symptoms, one cause: OCR of a photographed form. So the
  instrument built to adjudicate a disputed reading cannot reach the documents whose
  readings are actually in dispute, and each card had been triaged as its own rule
  problem — an address rule, a threshold rule — rather than as the one capture
  problem underneath.
  **When a card names a corpus as its blocker, check what the corpus FILTER
  excludes before believing the corpus is the wrong shape.** The shape was right;
  the finder dropped a third of the subject without a word.
  *Paid for by:* 2026-10-09 (C308, with C544). Fix scoped and NOT taken at the tail
  of a long session: find the document by any supported extension in both modules,
  skip the rasterise step for a document that is already a raster, and keep the
  gold corpus's existing 327 rows untouched while the 8 are added.

- **A RETURN DECLARES ITS OWN TOTAL ON PAGE 1, AND A DOCUMENT WITH NOTHING TO
  RECONCILE AGAINST LOOKS EXACTLY LIKE A CLEAN ONE.** C418, 2026-10-10. The
  per-part totals came from the geometric reader reading the ruled table
  footer; it was retired on 2026-09-25 (one recogniser) and **15 of the 107
  party returns in scope lost EVERY stated total with it** — Labour 2021, Te
  Pāti Māori 2025 and NZ First's amended return among them — so no invariant
  could say anything about their arithmetic, and the corpus row for an
  unchecked document was indistinguishable from the row for a clean one. Every
  one of them prints `Total Party Donations (A + C + D + F + G) $N` on page 1,
  and **106 of the 107 do**; nothing had ever read it. Ten spellings measured
  across those 107 — with and without "Party Donations", `$`, `$ `, `=`,
  nothing, `NIL`, and amounts with no thousands separators at all (NZ First
  prints `1877416.69`). Take the PARTS FROM THE LINE, so a return declaring a
  different combination is held to the one it declared. Documents with nothing
  to reconcile against fell **29 to 6**. Only **30 of 101** match the total
  they declare, which is the finding and not the failure: the reconciliation
  was always absent, not passing. Two traps: `Total (H + I)` on the same page
  is party LOANS and must never be read as this, and because cents are
  OPTIONAL the pattern needs an explicit `(?![\d,])` — the estate's other
  money patterns are saved by a mandatory `.NN` that forces backtracking, and
  without the lookahead `1877416` reads as `187`.

- **A BARE MONEY LINE IS NOT RELIABLY FURNITURE — THE LABEL IS THE WHOLE
  DISCRIMINATOR, AND DROPPING THE LINE COSTS MORE THAN IT SAVES.** C418,
  2026-10-10, extending the rule below. C464 dropped part totals by anchoring
  to the form's LANGUAGE, which works while the label survives the read. It
  does not always: GLM-OCR transcribes the footer CELL alone, so Labour 2021's
  Part G carries a row whose entire raw text is `$730,520.63` and the read is
  over the return's declared total by **exactly that amount**. The same defect,
  with no words left to anchor to — and the obvious fix is wrong. Excluding
  every row with no donor AND no date was measured over the 101 party returns
  that declare a total: matching fell **30 to 19**. It repairs exactly one
  document (AJP 2025, $25,415.90 to $12,707.95, a clean halving) and breaks
  twelve, because a real donation whose donor the reader never transcribed is
  byte-for-byte the same shape as a subtotal. This is the `unreadable`-versus-
  `furniture` distinction of the rule below, met where the evidence that
  separates them has been destroyed by the read. So the discriminator must be
  something other than emptiness — position as the LAST row of its part,
  equality with a stated subtotal, or the cell's geometry — and until there is
  one the row stays IN and the reconciliation reports the discrepancy rather
  than a guess being made silently. Abstain is the design.

- **A PART'S TOTAL IS NOT A DONATION, AND THE DIFFERENCE FROM "UNREADABLE" IS A
  DOUBLE COUNT.** C464: Part G of a party return is three aggregate CATEGORIES and
  not a row table, so the reader read its headings as donations — ACT 2023 Part G
  gave six "rows": the three real categories, the part's own stated total
  ($1,719,674.24) as a donation, and two shreds of instruction text carrying $8.17
  and $8.10, **which is exactly the $16.27 that was published as Part G's total.**
  Run over every row of all three donation tables: **12 rows, $120,062.78**, all in
  `party_donations`, led by `TOTAL FOR PART A` at $98,561.77 — 82% of the money in
  one row — with `Total Party Donations (A+ C+D+F+G)`, `Total (A+G +D+F`,
  `Part G: Other party donations up to $5,000`, `Partl: Party loans between $1,500 —
  $15,000` (OCR for Part I) and four `Date anonymous donation received` labels.
  **The estate already had the right machinery and the wrong bucket for it.**
  `line_kind` had `example` (dropped, rulings 190/191) and `unreadable` (KEPT,
  because the money is real and only the name was lost). Furniture had to be a
  fourth kind rather than either: a part total is **the sum of rows already counted
  one by one**, so marking it unreadable keeps the amount and adds the same money
  twice. `TOTAL FOR PART A` is not a donor whose name we failed to read — it is
  arithmetic the form printed.
  **ANCHOR THE PATTERN TO THE FORM'S SHAPE, NEVER TO A WORD.** "Total" sits inside
  real company names and "Part" inside real surnames, so each alternative requires
  the printed shape — a total naming its part, a bracketed part algebra, a
  `Part <letter>:` heading, a band phrase, a field label. `Total Recall Ltd`,
  `Totara Holdings Limited`, `Gerald Totalise` and `Partridge Family Trust` are
  donors, and the tests say so: a screen that ate them would delete money to tidy a
  view.
  **The fix is at LOAD because the register is a DERIVE** — no DELETE, no data
  mutation: the next re-derive drops them. And the screen was validated by running
  it over the whole corpus's history rather than over the card's examples, which is
  how 8 became 12 (the four extras are $0.00 labels, the money unchanged) with zero
  false positives.
  *Paid for by:* 2026-10-09 (C464). Same family as #a5bc39 — *a form is not the
  filer, a form's own furniture is not data* — now with the money attached.

- **A DETECTOR OVER FILED NAMES NEEDS A THIRD ANSWER, AND THE COLUMN'S NULL MUST
  MEAN "NOT ASKED" RATHER THAN "NO".** C430(c) had to flag a joint filed name
  (`Brendan & Jocelyn Lindsay`) as naming more than one person — Arthur, 2026-09-30:
  *"one row, both names as filed, the amount once, flagged, never split or
  doubled."* Of 2,369 `party_donations` rows, 77 carry an `&`, and an ampersand is
  **four** different things: two people, a company whose registered name contains
  one, a partnership, and an OCR artefact. So the function returns
  `True | False | **None**`, and the 30 rows ($585,503.79) it abstains on — mostly
  the initials form, `J & M Smith`, where a two-person reading and a trading-name
  reading are equally available — stay NULL rather than being called single. A
  two-valued detector would have written `joint = false` over all thirty and a
  later page-read would have had nothing to correct.
  **THE WIRING IS THE OTHER HALF:** the detector fires at the load chokepoint only
  `if r.get("joint") is None`, so a human reading or a correction verdict is never
  overwritten by a regex on the next derive. A derived column that overwrites an
  observation is not a derive, it is a data loss.
  **AND A DETECTOR OF PEOPLE MUST EXCLUDE ORGANISATIONS FIRST.** The first version
  flagged three UNIONS as couples, because a union's registered name conjoins
  trades, not spouses — found only by running the rule over the whole register
  rather than over the card's example, and `_ORG_WORD` was widened until they were
  single again. The three unions are now pinned as test cases, which is the only
  way the widening stays.
  *Paid for by:* 2026-10-09 (C430c). 25 rows / 20 distinct names, $2,065,864.54,
  against a column that was TRUE on 3 of 2,369 before today.

- **A DOCUMENT NOBODY COULD OPEN IS NOT A DOCUMENT WITH NOTHING IN IT — AND THE
  "UNREADABLE" FIELDS WERE PRINTED IN PLAIN TYPE ALL ALONG.** C308 asked whether a
  no-address disclosure row naming a bare `'John Smith'` was a real donor, and was
  carried as BLOCKED for three days behind another card's queue. The documents read
  in seven seconds each once anything could open them. `R_Nauhira_10_October_2023
  .jpg` transcribes to donor `Roshan Nauhria`, address `39 Hobill Ave, Wiri,
  Auckland 2104`, total `$29,500.00`, received 9 October 2023 — while the register
  holds **four** rows for that one document, no address, **$159,500.00**, under
  `NES Roshan Nauhria`. Of the four photographed forms whose donor block resolved,
  the register's NAME is damaged on four (`NATHAN EDWARD SCHICK` for Jonathan,
  `Nile William James Deihl` for William), its AMOUNT wrong on three ($20,000
  against $55,000; $1,000 against $20,500) and the ADDRESS it calls absent is
  printed on all four. **The register's "unreadable" was never about the document.**
  **THREE LAYERS, EACH INVISIBLE BEHIND THE ONE ABOVE IT.** (1) The finder globbed
  `{stem}.pdf`, so eleven `.jpg` disclosures were not candidates — and the SAME line
  dropped `AOTEAR1.PDF`, because the glob is case-sensitive: 3,585 targets became
  3,597, eleven rasters and one shouted extension (#3603e8). (2) The one recogniser
  takes BYTES and handed them to `pdftoppm`, which cannot open a JPEG: every page
  came back honestly unread. (3) `read_one` called `arbitrate([one_reading])`, which
  refuses a single reading — correctly — so after the second reader was retired on
  2026-09-25 **every document errored**, and the store's last row is dated 09-24.
  Nobody saw layer 3 because layers 1 and 2 meant the run was never attempted.
  **WHEN A CARD SAYS "BLOCKED BY A RUN THAT HAS NOT HAPPENED", OPEN THE INSTRUMENT
  AND POINT IT AT ONE DOCUMENT.** The blocker was never the queue order.
  *Paid for by:* 2026-10-09 (C308). Arm T7.73 holds the direction; the repair is a
  re-derive needing a profile for this form (#4c2944: a profile is assigned before a reader is written — C544/C226).

- **A VOCABULARY DETECTOR FOR "DAMAGED NAME" IS A DECISION ABOUT WHOSE NAMES COUNT,
  AND IT FINDS THE WRONG PEOPLE — THE SECOND READING OF THE SAME PAGE IS THE
  INSTRUMENT.** C171 asked for a detector that does not rely on a name LOOKING
  wrong, and prescribed the part-total check. A total cannot see this class and
  this file already said so (*a total proves how much was read, never who it was
  read against*): Labour 2020's 25 garbled names sat on a return that reconciled
  exactly. So the obvious alternative was the register's own vocabulary — and
  measured against the Companies Office (6,826 given names, 49,497 surnames),
  **15.9% of the 1,151 person rows in the seven-party scope are out-of-vocabulary
  and essentially none is OCR damage.** They are honorifics (`Dame`, `Hon`, `Sir`,
  `QC`), annotations (`(deceased)`, `via Matariki Trust`), diacritics breaking
  tokenisation (`Chlöe` → `chl`, `Māori` → `ori`) and, overwhelmingly, correctly
  read non-Anglo names: Golriz Ghahraman, Teanau Tuiono, Priyanca Radhakrishnan,
  Anahila Kanongata'a, Vanushi Walters, Hinurewa Te Hau, Naisi Chen, Tirath Singh
  Atwal, Jiayang Hao. **Such a rule would condemn those at a far higher rate than
  it finds a garble** — the same shape as #c34847's threshold lesson, one level up:
  not the cut, the vocabulary. Grouping by document adds nothing: 20.1% OOV among
  names in one document against 16.4% among names in two or more, **1.23×**, the
  same nothing as C167's variant map.
  **WHAT WORKS IS TWO READINGS AND NO JUDGMENT OF THE NAME AT ALL.** A register
  name with no match on a fresh read of its own page, sitting beside a page cell
  ONE EDIT away whose amount agrees to the cent: `DHE Trust (Doug Catley)` against
  the page's `DHC Trust (Doug Catley)` at $50,000; `Zhao, Hanging` against
  `Zhao, Hanqing` at $5,950; `N S| Management Limited` against `N S I Management
  Limited`. No vocabulary, no plausibility, no bias — and `Hanging` is an English
  word, so no spelling rule could ever have flagged it.
  **THE INSTRUMENT BUILT FOR THIS HAD BEEN READING 0.2% OF ITS INPUT.** Of 12,726
  cached page transcriptions, **25** are in the delimited `| 35 Trevor Farmer … |`
  form the audit's row regex expects and 418 are `<table class="table
  table-bordered">`; National's 2024 return — 15 scanned pages, 96 register rows —
  parsed to ZERO pairs and the audit reported no disagreements. **A parser written
  against one of a model's output shapes is a parser that silently stops working
  when the model's shape changes**, and nothing downstream distinguishes "no
  disagreement" from "nothing compared" unless the comparison ABSTAINS out loud.
  *Paid for by:* 2026-10-09 (C171). 22 headline documents, 181 pairs, 133 donors
  compared, 3 near misses and 2 amount errors (one $2,000); 14 of the 22 still
  abstain, which is now reported rather than read as agreement.

- **A RECORD SHAPE IS NOT A RECOGNITION KEY — A BANKRUPTCY LIST HAS A CELEBRANT
  LIST'S SHAPE, AND THE SUBJECT WORD IS 93% OF THE ANSWER.** C226's own filed rule
  said recognise by SHAPE, not by a phrase, and that rule was written about SCANS —
  documents with no text to match on. Applied to gazette notices, which are all
  text, a shape-only key (three `Surname, Given, Something.` records) recognised
  **24,875 of 208,304 notices and 23,139 of them were not celebrant lists at all**:
  1,358 liquidation advertisements, 550 bankruptcies, 547 no-asset procedures, 473
  trade-name applications, company restorations. Requiring the subject word in the
  title, the operative sentence or the printed column header — **plus** a shape —
  takes it to 1,736 notices, 59,476 records and one false positive. **A rule's scope
  is part of the rule: "recognise by shape" means "where no text exists", and
  carrying it into a corpus that has text is how a 93% error rate looks principled.**
  The subject word is also bounded to the notice's HEAD (3,000 chars), because a
  400 KB polling-place list says `celebrant` once, three hundred records in.
  **AND THE ACTION IS NOT THE SHAPE.** 1,084 of the recognised notices say neither
  "appointed" nor "removed" — they say *"the following names … are published for
  general information"*, which is a PUBLICATION of who holds the office, not an
  appointment event. 443 are removals under s 13. Reading the class as appointments
  would have minted 59,000 appointment events on dates nobody was appointed, and
  reading a consolidated list that publishes the register and THEN strikes names off
  as a publication would re-publish the people it removed — so removal outranks
  publication, and 30 notices holding 33,193 records say more than one thing and are
  read as none of them.
  **THE CARD'S "RECOVERABLE EXACTLY" IS TRUE OF TWO SHAPES AND FALSE OF THE THIRD.**
  `Surname, Given Names, Organisation.` and `Surname, Given Names.` are delimited.
  The 12 consolidated tables print `Abbott, Bryant Sidney Lawrence Methodist` under
  the header `Name of Celebrant Name of Organisation` with **nothing between the
  given names and the organisation** — is `Lawrence` a third given name or the first
  word of a church? That shape abstains with its reason, and the vocabulary that
  would settle it is derivable from the delimited notices: the documents that say
  where the boundary is teaching the ones that do not.
  *Paid for by:* 2026-10-09 (C226). The profile recognises the notices holding
  **32,642 of the generic parser's 35,938 abstains — 90.8%**, which is the card's
  90.9% census reproduced from the other end.

- **THE FORM'S STATED TOTAL IS THE AUTHORITY FOR A DISCLOSURE TOO, AND NOTHING WAS
  ASKING IT — WHICH IS WHY NINE ROWS ADDING UP COULD BE BLIND TO ONE DECLARATION.**
  C544 found 22 live disclosure rows below the $20,000 floor the s 210C form exists
  for, 19 of them `reconciled = TRUE`, and recorded that a SUM check cannot see a
  line-level impossibility (#c188b8). What it could not say was what the documents
  actually declare. Once the photographed forms were readable (C308), the forms
  answered:
  `G_Harrison_30_June_2023.jpg` prints **Total amount $20,254.00**, received
  30 June 2023, with the aggregation grid EMPTY — one donation. The register holds
  **nine** rows summing $42,998: the right $20,254 plus eight artefacts ($5,150,
  $4,999, $2,590, $2,500 ×4, $5) with dates `2023-06-50` and `2023-05-34`, a day
  50 and a day 34. **Over by $22,744.**
  `Christopher_and_Michaela_Meehan_26_August_2023.jpg` prints **$103,260.00** and
  itemises it as $3,260 on 9 JUN and $100,000 on 23 AUG. The register holds
  $100,000 + $10,000 + $2,600 = $112,600, one of them dated **2025**-08-22.
  **Over by $9,340**, and the donor filed as `Christopher and Michaela Meehan` is
  held as `MICHAELA MEEHAN` alone.
  **THE LESSON IS NOT THAT OCR SPLITS A ROW — IT IS THAT THE DOCUMENT CARRIES ITS
  OWN ANSWER AND NOTHING WAS READING IT.** A party return's reading is checked
  against the Part A total it prints; a DISCLOSURE's reading was checked against
  nothing but itself, so a reader that split one declaration into nine lines passed
  every gate the estate had. **Where a form states a total, store it and compare —
  the comparison is free and it is the only check that does not depend on the rows
  being plausible.**
  *Paid for by:* 2026-10-10 (C544 tranche 2). 10 documents hold sub-threshold
  lines; the two read so far account for $32,084 of the $31,300 over-count the card
  measured from the other end.

- **THE AUTHORITATIVE FIGURE WAS ALREADY IN THE ESTATE, PUBLISHED AND UNJOINED —
  BECAUSE THE LINK TO IT HAD TO BE A `.pdf`.** C544's money defect looked like an
  OCR problem for three days, and the loader had been built to beat OCR: *"THE
  COMMISSION'S OWN TABLE FIRST… The OCR of a photographed form splits one
  declaration into twenty rows and misreads $24,500 as $7."* The authority existed
  and never reached eleven documents. `ec_disclosure_index` took a row's document
  link with `href="([^"]+\.pdf)"`, and **the Commission links a `.jpg` for eleven
  of its 271 declarations** — a photograph of the filed form — so those rows had no
  `href`, counted as `unlinked`, keyed on `donor_date` instead of the file, and
  matched no document. `key_of` in the SAME MODULE had already been fixed for this
  exact thing — *"ANY extension, not just .pdf: half the 2023 declarations are
  staged as `.jpg`"* — and the href half was not. **Two halves of one rule, one
  fixed and one not, in one file.**
  **WHAT IT COST, AND IN BOTH DIRECTIONS.** Over the eleven: the register held 24
  rows / $983,698 where the Commission publishes 11 rows / $1,027,314. `R_Nauhira`
  four rows at $159,500 against a published **$29,500**; `G_Harrison` nine rows at
  $42,998 against **$20,254**; and **two declarations the register held NOTHING
  for, $178,000** (`P_Adams` $28,000, `Rank Group` $150,000). Under-counting as
  well as over: Schick $20,000 held against $55,000, Deihl $1,000 against $20,500.
  **AND THE SAME PATTERN SAT IN TWO MORE LANES.** `promoters` and `party_expenses`
  held the identical PDF-only href, losing nothing TODAY because their captured
  pages link no returns at all — which is exactly how a latent copy stays broken
  quietly until the Commission publishes one photograph. One home now
  (`registers/ec_links.py`), and a test that greps for a fourth.
  **THE TRANSFERABLE PART: when a reading disagrees with a figure, ask whether the
  estate already holds the publisher's own statement of it before improving the
  reader.** Three days of this card went to reading scans better. The scans
  confirmed the index — two independent sources agreeing — but the index was free.
  *Paid for by:* 2026-10-10 (C544 tranche 3). `unlinked` 11 → 0; the derive at
  03:34 applies it, on the estate's own timer, with the Commission's published text
  as the source and therefore no new `row_basis` tier to rule on.

- **A READ THAT FINDS NOTHING KEEPS THE OLD READING AND SAYS "FOUND NONE" — SO A
  LANE THAT CANNOT SEE THE PAGES LOOKS LIKE A LANE THAT READ THEM.** On
  2026-10-17 every 2017 party return re-read through `ec_pageread` came back
  "KEPT the previous read: this one found none". The model was never shown the
  schedule: `read_text` called `pdfpipe.convert.convert_path` WITHOUT a reader,
  so a mixed document (National 2017: five text pages of auditor's report in
  front of fourteen scanned schedule pages) read as "text" and the model saw the
  auditor's report alone, and a whole scan (ACT 2017: 21 characters in 21 pages)
  read as "none". The keep rule did its job and hid the cause. Three rules: the
  plain read hands the converter the one recogniser, or says in its own output
  that it did not; a "kept the previous read" verdict names WHY the new read was
  empty (chars, method, the model's note), because the discarded reading is the
  only evidence; and a required field in the row schema (`date_received`) is how
  a schema-constrained model is made to decide — the same lesson the expense
  fields paid for on 1,674 candidate returns.
  *Paid for by:* 2026-10-17 — three lane runs before the cause was found by
  calling `read_file` directly and printing the model's note.

- **A RULE ONE LOADER PAID FOR IS NOT A RULE ITS SIBLINGS HOLD — "A DOCUMENT IS
  ITS BYTES" WAS BUILT INTO THE CANDIDATE LOADER ON 2026-09-25 AND THE
  DISCLOSURE LOADER NEVER HEARD OF IT.** The Commission publishes one declaration
  under two names: `Vision_New_Zealand_27_July_2023-v2.pdf` is the table's link
  and `Vision_New_Zealand_27_July_2023.pdf` the same sha256 from an earlier pull.
  The table's key reached the first and loaded the Commission's own text; the
  second had no key, so its OCR of a handwritten form was loaded BESIDE it — a
  donor who does not exist ("Charles Dave", from the address line), double the
  money ($92,057.53 against $47,052.53), dated 2017 — and it was the first thing
  the 2017 window surfaced (the residue gate: *two receiver lines are one
  party*). The fix is the candidate loader's, moved: the table's documents are
  known by their bytes before any scan is read, and a scan of bytes the table
  names is never loaded, whatever it is called; two scans of one sha load once.
  When a loader learns a rule about document identity, grep the sibling loaders
  for the same key before closing — the fault is the same shape in every one.
  *Paid for by:* 2026-10-17, the ruling-364 release refused at its residue gate.
  Beside it, unfixed and recorded: the WITHDRAWN amendment of that declaration
  (`Vision_New_Zealand_25_July_2023.pdf`, struck-through figures) loads as its
  own 2023 disclosure of $49,525.38 to Freedoms New Zealand (party-unresolved,
  residue only); tying a withdrawn amendment to its declaration needs the
  Commission's own assertion, and its file name carries the party's receipt
  date, not the one the table names.

- **THE THIRD CORRECTION OF ONE SHAPE IS A RULE — A CORRECTION FIXES ONE
  DOCUMENT, AND THE CLASS STAYS.** On the morning of 2026-10-17 Te Pāti Māori's
  2018 return had six "donors" that were the form's own checklist ("Auditor
  stamped or initialled the front", "letter enclosed," $2,000); they got six
  `drop` corrections and the card closed. That night the same class was still
  in the register twelve more times, $112,168 in the window — "Auditor stamped
  or initialled a copy of the return to keep for own records" carrying
  $54,619.17 twice on TEA Party 2020, "Party secretary signed and dated the
  return" on three returns, "Enter YES or NO" on five — and on the public
  residue page. The corrections ledger is for a READING that went wrong on one
  page; a line the FORM prints on every return is a class, and a class is a
  `line_kind` arm (furniture), on the one chokepoint every load path passes,
  with a test per held phrase and a near-miss test per word a real donor might
  share. The tell: when the second correction of a shape is written, grep the
  register for the shape before writing the third. *Paid for by:* 2026-10-17 —
  six corrections in the morning, a rule and twelve rows at midnight.
