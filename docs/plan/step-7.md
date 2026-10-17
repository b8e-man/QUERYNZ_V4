## Step 7: archive search

**Goal.** History search over the whole of Papers Past with every search tool, and keyword search over other journalism.

**Why it can start early.** Most of it is machine time. The embedding run begins as soon as the scheduler works and runs beside steps 4 to 6.

**Models.** Opus for the ingest. Fable for the index design and the recall proof.

### What is held

- 4,648,837 Papers Past articles in the news corpus, about 2.1 million of them in the old meaning index.
- A further archive of about 86 million items on the boxes, never ingested. Find it in the step 1 baseline.
- Every person, claim and mention drawn from Papers Past was deleted on Arthur's word on 27 September. It stays that way.

### Do

**7.1 Put the search-only rule in place before the first batch lands.** In the old estate only a status value kept Papers Past out of extraction. In the new estate it is a rule with a test: nothing from this archive can reach the links.

**7.2 Ingest the archive so that every catch is found exactly where it happens.** This is Arthur's instruction.

- **Named stages, each with its own count.** Items in, items out, items set aside with a reason. In must equal out plus set aside, on every batch.
- **A catch log.** One line per catch: the stage, the item, its place in the archive file, the reason, and the first failing example kept whole.
- **Small batches first:** ten thousand, then a hundred thousand, then a million. A batch that does not reconcile stops the run.
- **Nothing set aside silently.** A run that sets aside more than a stated share stops and says which stage. One old build stored 3.4 million of 10.65 million rows and reported nothing.

| Stage | Catch to expect |
| --- | --- |
| Reading the archive | Format, encoding, truncated files. Unknown until the first batch |
| Overlap with what is held | 4.65 million articles are already in; reprints between papers also collide |
| Landing | Table growth copies to the standby and swells the off-site copy |
| Keyword index | Needs sizing at this scale before an engine is chosen. Measure the first batch, then decide and record why |
| Meaning index | Cannot be built in memory at this size; see 7.4 |
| Serving | Filters and change-over-time queries have only run at the present size |

**7.3 Read whole documents.** The old keyword index read only the title and first 1,500 characters; 77.5% of articles are longer. Index the whole text.

**7.4 Build the meaning index.** The old method needs about 500 GB of memory at this size.

1. **Measure the first batch:** lengths, the share that is adverts or tiny notices, and how much is reprints. This decides what gets a vector.
2. **Split long columns into passages,** each with its own vector, so nothing past the lead is invisible.
3. **Speed up embedding before the long run.** The model (bge-m3) uses 0.7 GB of a 34 GB graphics card. Many copies per card, or larger batches, should raise the rate a great deal. Keep the server's prompt cache off: the prompts are unique, and with the cache off one card did 2.73 times as much in the same 90 minutes, 437,328 short texts, about 80 a second. The record's older figure of 25 a second and 40 days predates that test. Whole documents split into passages are more and longer texts, so measure before estimating.
4. **Embed in pieces by newspaper and year, into files on the hard disks,** at half precision. Each piece has its own count and catch log, and a stopped run resumes at the next piece.
5. **Share the graphics cards through the scheduler.** Embedding is bulk work that yields to document reading and to live questions.
6. **Build a compressed index:** each vector squeezed to about 64 bytes, so the whole set fits in under 10 GB of memory. It grows piece by piece, so search works while the run continues.
7. **Re-check the top candidates exactly** against the full vectors on disk. Seconds, not milliseconds, is acceptable for deep search to begin with.
8. **Serve it as its own small process,** blended with keyword results.
9. **Prove recall first** against exact search on a one-million sample.

The vectors stay out of the off-site copy, because they can be regenerated, and get a second copy on the other box, because regenerating costs weeks. The figures above assume one vector per item; passages will raise them, and the first batch says by how much. The old meaning index over news stops being rebuilt when the press jobs stop in step 1. Only its Papers Past part is rebuilt, in this design. The memory the old index holds is freed when the old app that loads it is stopped.

**7.5 Build the search tools.**

| Tool | State in the old estate | What it adds |
| --- | --- | --- |
| Matching that tolerates misread print | Not built | The scans turn Auckland into "Ancklaud". Without this most deep searches miss |
| Old and variant spellings, names without macrons, initials | Pieces exist | One query finds a person under every form the papers used |
| Date, newspaper and region filters | Built | Narrowing by place and decade |
| Change over time, and distinctive terms | Built | When a subject rises and falls |
| Reprint detection | A hand-run scan | Nineteenth-century papers reprinted each other; collapse the copies |
| Old place names | 54,667 official names loaded | Places by former and Māori names |
| Compound-word splitting | Written, wired to nothing | Old run-together words |
| A broad name index | New (ruling 43) | Which names appear in which articles: people, towns, roads, organisations. A search aid only. The method is decided by the measurement in track D.2 (ModernBERT-base against the deterministic path) |
| An agent that searches in rounds | A research agent exists with other tools | Follows leads across many searches and reports with citations |

**7.6 Keyword search over other journalism** (ruling 8).

- News capture keeps running. Every NZME masthead is excluded from the index and from capture; what to do with the NZME copies already held is a question for Arthur.
- Show the headline, masthead, date, a link, and a short extract around the matched words. Never the full text.
- Paywalled outlets are not captured and are never forged.
- No meaning index and no people or claims are built from current journalism while the press work is parked.

**7.7 The history-search template and its checkpoint.** Copyright on Papers Past varies by title and date; add it to the before-selling legal list.

### Done when

- [ ] Every ingest batch reconciles, and the catch log names each catch.
- [ ] The keyword index covers whole documents.
- [ ] Recall is proven on the one-million sample and recorded.
- [ ] The meaning index covers the archive, with its count against the archive's count.
- [ ] A test proves nothing from Papers Past can reach the links.
- [ ] The checkpoint is done and the known-limits page exists.

### Brief to paste

```text
You are a build session for QueryNZV4 on node2, running as the model
docs/briefs/next.md names, in the working copy the launcher made for
you. Read docs/PLAN.md, then docs/status.md, and continue where it
stops. Do the part of step 7 named here: <ingest, in
registers/papers-past/ | keyword index or meaning index or search
tools, in products/search/ | journalism keyword search, in
products/search/>. Papers Past is searched, never mined: build no
people, claims or links from it. Start with small batches; stop a
batch that does not reconcile; log every catch with its stage and its
place in the archive. Queue all graphics-card work through the
scheduler. Push your branch and raise a merge request. Finish by
telling Arthur what closed and what is carded.
```

