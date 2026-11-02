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
