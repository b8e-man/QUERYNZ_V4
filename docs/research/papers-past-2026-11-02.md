# Papers Past: the first batch and the projection (step 8.6, 2 November 2026)

## Where the archive is

- The dump: `/home/user/offload-2026-09-02/hetzner-recovery/local-docker_news-scraping-db_newsscraping_20260825_005138.sql.gz`.
  It is 132,692,104,796 bytes compressed and 579,165,692,933 bytes raw, in 195,306,107 lines. Its sha256 is in its own
  `dump.sha256`, and `verified.OK` dates it 29 August 2026. It was neither moved nor copied.
- Its `public.scraper_results` section holds 94,705,511 rows. **90,651,423 of them are Papers Past**
  (paperspast.natlib.govt.nz). The rest are 17 other hosts, counted by their URL's host only and never decoded.
- One full read-only pass at low priority takes 18 minutes. The first 10,000 Papers Past rows are reached in 36 seconds.
- The old estate's `incoming_news.articles` holds 4,648,837 Papers Past rows. They are a subset, joined by
  `upstream_id` = `scraper_results.id`.

## Batch 1 (`staging_papers_past`, not published)

The batch is the first 10,000 Papers Past rows in dump order: issues from 1864 to 1950, ids 7.7 M to 100.6 M.

| Stage | In | Out | Set aside | Why |
| --- | ---: | ---: | ---: | --- |
| in | 10,000 | 10,000 | 0 | |
| article id | 10,000 | 10,000 | 0 | |
| text | 10,000 | 9,031 | 969 | the archive holds no text: 952 `MIGRATION_ERROR`, 17 complete but empty |
| once | 9,031 | 9,031 | 0 | |
| landed | 9,031 | 9,031 | 0 | reconciles: 10,000 = 9,031 + 969 |

- **Outside check:** green. 1,995 of the items are also in the old estate's copy, with the same title and URL on every one.
  Only 31 have the same text length, so the old copy's text differs: the old pipeline cleaned or cut it. The dump's
  text is the fuller one.
- **Per item:**

  | Measure | Bytes or characters |
  | --- | ---: |
  | Dump line | 6,877 bytes |
  | Text | 3,638 characters (median 2,917, longest 63,629) |
  | Table, with its TOAST storage | 3,916 bytes |
  | Keyword index (GIN, `simple`, over the title and the whole text) | 3,570 bytes |

- 14% of the items with text are under 200 characters: adverts and small notices.
- `raw_content` repeats `text_content` on every row, so only one copy is kept.

## The projection, and why the run stopped

Assumption: 81.9 million items land, taking the batch's 9.6% with no text as the rate for the whole archive.

| What | GB |
| --- | ---: |
| Table, text included | 321 |
| Keyword index over whole documents | 292 |
| **Both** | **613** |
| Half of node2's 676 GB free (the stop line) | 338 |

The table alone fits under the line; the table with its keyword index does not. Neither figure counts the change log or
the off-site copy, which the table's growth also swells (7.2, "Landing"). So no batch past the first was run. Ways under
the line, for Arthur:

1. **The text outside the database.** The archive stays the dump. A batch writes its items to compressed files per paper
   and year on the hard disks, and the database keeps only key, paper, date, title, length and place, about 0.3 KB each
   or about 25 GB. The keyword index is built outside PostgreSQL over those files, sized by a 1-million-item sample before
   an engine is chosen (7.2's keyword-index row).
2. **The text in the database, the keyword index elsewhere.** The 321 GB table with lz4 or zstd column compression (not
   yet measured), and the index as in 1.
3. **Both in the database on a second disk.** Not on node2's system disk.

The batch's ids span the dump's whole order, but the batch comes from its first rows only. A 1-million sample spread over
the dump comes before any of these.

## Option 1 built: the text on the 4 TB disk, the catalogue in the database (2 November 2026, later)

Arthur: "use the 4tb HDD". Option 1, on `/mnt/hdd2` (ext4, 3,341 GB free), never `/mnt/hdd`, no tablespace.

**Layout.** `/mnt/hdd2/qv4-papers-past/<database>.<schema>/text/<PAPER>/<YYYY>.zst`: zstd (Python 3.14's own
`compression.zstd`, level 9) frames of about 256 KB of records, appended and never rewritten. A record is
`key \t bytes \t sha256 \n`, the text, `\n`, so a file read alone says what it holds. The catalogue
(`papers_past.items`) holds key, paper, date, title, length, sha256, dump line, and the file, frame offset and length,
and the text's offset and length inside the frame; `papers_past.files` the file paths; `papers_past.batches` the dump's
hash, the reader, the store folder and the stride. The keyword-index trials sit in the store's `index/`. The dump was
only streamed, never moved, copied or changed. (Measured on batch 1: 256 KB frames at level 9 compress 2.47 to 1; 128 KB
frames 2.31; one frame per item 1.85.)

**Batch 1, re-landed this way** (sample database, `scratch_papers_past_b1`): 10,000 in = 9,031 landed + 969 set aside
(952 `MIGRATION_ERROR`, 17 complete but empty); 1,995 held by the old estate, title and URL the same; 3,638 characters an
item; every item read back from the files against its sha256. 303 catalogue bytes and 1,613 disk bytes an item (207
small files, so block overhead counts).

**The 1-million sample spread over the dump** (`scratch_papers_past_s1m`: every 90th Papers Past row, 99.3% of the
section's rows passed, dump lines 99.2 M to 193.0 M, issues 1840 to 2001, 188 papers; 28 minutes at low priority):

| Measure | Figure |
| --- | ---: |
| In / landed / set aside | 1,000,000 / 956,344 / 43,656 (38,459 `MIGRATION_ERROR`, 5,196 empty, 1 not an article id) |
| Held by the old estate | 51,633, title and URL the same on every one |
| Text an item | 2,302 characters, 2,325 bytes (median 1,411; 9.5% under 200) |
| **Disk an item (files)** | **1,046 bytes** (5,390 files, 11,655 frames) |
| **Catalogue an item** | **255 bytes** (table and its key index) |

The batch-1 rate of rows with no text (9.6%) was the dump's first rows; spread over the dump it is 4.4%, so 86.7 M items
land, not 81.9 M.

**Projection for the whole archive (86.7 M items):** files 91 GB on `/mnt/hdd2`; catalogue 22 GB in the database
(node2's system disk, 668 GB free). The stop line, half of `/mnt/hdd2`'s free space, is 1,670 GB: well under it.

**The keyword index, sized on the sample** (whole text and title, positions kept so phrases work; text not stored; files
on `/mnt/hdd2`; tantivy 0.27's wheel installed to a scratch folder, not into the venv; the full index not built):

| Engine | Bytes an item | Whole archive | Build (956 k items) | Query, warm (first run) |
| --- | ---: | ---: | ---: | --- |
| SQLite FTS5 3.51 (contentless) | 1,761 | 153 GB | 259 s | 2 to 105 ms with an exact count of every hit (rare word 5, phrase 58, common word 105) |
| tantivy 0.27 | 1,066 | 92 GB | 142 s, 2 threads | 0.03 to 4 ms for the top 20 and the count (first run off the disk 0.1 to 1,500 ms) |

The two engines find the same number of hits on every query tried (`wellington` 178,497; `kauri` 7,840;
`"bank of new zealand"` 9,041; `gold` and `otago` 4,237; `whare` 3,535). Files plus either index: 183 to 244 GB.

## The full run made streaming and resumable; tantivy chosen (2 November 2026, evening)

Arthur: "for papers past use tantivity and go". `registers.papers_past.load` now makes one pass of the dump in chunks of
1,000,000 rows. At each chunk's end the store is flushed and synced, the catalogue rows are COPYed (the catalogue's key
refuses a second row of an article, which is set aside at `once`; no set of every key is held), the catches, each file's
committed length and the chunk's checkpoint (last dump line, the stride's count) are written, 200 items are read back,
and the chunk commits. A stopped run resumes after its last committed chunk: files are cut back to their committed
lengths, and the dump is gunzipped again up to the checkpoint without decoding (gzip cannot seek). The old copy's
4,648,837 Papers Past ids are read once into a sorted array (about 37 MB).

| Measure, 2 November 2026 | Figure |
| --- | ---: |
| 1,000,000 consecutive rows, one chunk: wall time | 297 s (CPU-bound in Python: 298 s user) |
| Peak resident memory of the load | 0.95 GB |
| Landed / set aside | 972,633 / 27,367; disk 1,000 bytes and catalogue 286 bytes an item (the upstream-id index included) |
| Resume after that chunk, 50,000 rows more | 270 s, of which about 230 s gunzipping to the checkpoint (line 103.5 M) undecoded; peak 0.32 GB |
| tantivy over the 1,022,377 items (1.5 GB heap, 2 threads) | 71 s; 1,095 bytes an item; peak resident 1.87 GB; warm queries 0.03 to 4.4 ms |

**Projected for the whole dump** (90.65 M Papers Past rows at 297 s a million): about **7.5 hours** for the ingest, 88 to
90 GB of files and about 25 GB of catalogue; then the index at 71 to 142 s a million (the consecutive run and the
spread sample), **1.7 to 3.5 hours**, about 95 GB. A resume costs one chunk at most (about 5 minutes) plus the gunzip
up to the checkpoint: up to one full pass, which took 28 minutes on the spread sample.

Jobs: `qv4-papers-past-ingest` (priority 134) then `qv4-papers-past-index` (priority 135). Neither has a clock: the
integrator queues the ingest. Nothing is published until `registers.papers_past.check` passes on the whole run.
