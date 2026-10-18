# Baseline: the boxes as measured

Step 1.3. Measured on node2 between 00:50 and 01:20 NZDT on 18 October 2026,
by the founding session, from what is actually there. node1 was down the
whole time (no answer on 10.0.0.1), so every node1 figure here is "not
measured"; the first session after node1 returns re-measures it and updates
this file. The plan's expectations are in `docs/plan/reference/old-estate/`;
where the boxes differ, the boxes win and the difference is listed at the
end.

## The boxes

| | node2 (measured) | node1 (not measured) |
| --- | --- | --- |
| Processor | AMD Ryzen 9 9950X, 16 cores, 32 threads | — |
| Memory | 125 GB; 32 GB swap file plus 8 GB zram, both unused | — |
| Graphics cards | Two AMD Radeon AI PRO R9700, 31.9 GB each (34,208,743,424 bytes); card 0 26 GB in use, card 1 24 GB | — |
| System disk | 1.9 TB NVMe, 773 GB used, 1.1 TB free; holds `/` and `/home`, the database data directory (`/var/lib/pgsql/data`) and the Papers Past dump | — |
| `/mnt/hdd` | 3.6 TB, 1.2 TB used, 2.5 TB free: `backups/` 618 GB (nightly dumps since 19 September), `pg/wal-archive` 298 GB, `pg-scratch` 206 GB (a second cluster's data folder), `restore-rehearsal` 36 GB, `querynz-quarantine` 106 MB | — |
| `/mnt/hdd2` | 3.6 TB ext4, mounted 17 October, empty (3.4 TB free) | — |
| Addresses | 10.0.0.2, and the floating database address 10.0.0.10 (held here since the 17 October failover); Wi-Fi 192.168.68.54; a tailnet address | 10.0.0.1, not answering |
| System | Fedora 44, kernel 7.2.10; up since 21:50 on 17 October | — |
| Role now | Primary database, every old job, the Follow the Money app and publisher | Down. Rejoins as the standby after a rewind (Arthur's) |

## Programs the jobs depend on

- **Text extraction:** poppler 26.01.0 (`pdftotext`, `pdftoppm`, `pdfinfo`), tesseract 5.5.3, `xvfb-run`, Google Chrome (the headed browser the declarations job uses). No `ocrmypdf`, no Chromium package; Playwright's own Chromium 1228 is in the user cache.
- **Model server:** one build of llama.cpp at `/home/user/llama.cpp/build/bin/llama-server`, commit `6ea215d17` of 5 August 2026. Every model unit on node2 runs this binary. The new estate installs its own build beside it (hard limit 23).
- **Model files** (`/home/user/models`, 68 GB in all): `Qwen_Qwen3.6-35B-A3B-Q4_K_M.gguf` 21 GB (the chat model, served as `qwen3.6-35b-a3b-q4km`); `Qwen3.8-27B-Q4_K_M.gguf` 16 GB (not served); `bge-m3-Q8_0.gguf` 606 MB (embeddings); `vision-glm-ocr/` 1.4 GB (the page reader, `GLM-OCR-Q8_0.gguf` with its projector); `vision-internvl3-14b/` 9.1 GB and `vision-qwen25vl-32b/` 20 GB (trial readers, not served). None of this is on `/mnt/hdd2` yet.
- **Python:** the live old folder's environment is Python 3.12.13 with 129 packages pinned in `ops/requirements-factory.lock` and 24 editable packages; the reference copy's environment matches it (`lessons/old-requirements-file-is-short.md`). The system Python is 3.14.8.
- **Database server:** PostgreSQL 18.6 (the plan said 18.3), `max_connections` 100, `wal_level` replica, `max_wal_size` 1 GB, `archive_mode` **off**, no synchronous standby, no streaming client. The data directory is on the system NVMe; `pg_wal` is under `/mnt/hdd/pg/wal` (postgres-owned, so its size could not be read with this login); the old WAL archive mirror holds 298 GB, last written 14:33 on 17 October.

## The old databases

Sizes are exact. Row counts are the planner's estimates from the last analyse (the live-row statistics were reset when node2 was promoted, so every `n_live_tup` reads 0).

| Database | Size | Plan said | Main tables, estimated rows |
| --- | --- | --- | --- |
| `nzbn_canonical` | 24 GB | 21 GB | `public.entities` 1.82 M, `entity_history` 1.83 M; `director_roles` 1.19 M (+1.19 M history); `shareholder_roles` 1.58 M (+1.60 M history); `bulk.wikidata_labels` 91.9 M (11 GB, the largest thing in it), `bulk.geonames` 13.5 M, `bulk.gleif` 3.45 M; `registers.linz_title_owners` 5.74 M, `registers.press_appointments` 631 k; `gazette.insolvency_appointments` 400 k, `gazette.notices` 207 k; `charities.charity_officer_roles` 282 k, `public.charity_annual_financials` 422 k; `bulk.gets_award_notices` 29,874 (exact). Schemas: bulk, charities, corpus, courts, elections, gazette, legislation, mp_interests, parks, parties, public, registers |
| `incoming_news` | 63 GB | 25 GB | `articles` 7.30 M (20 GB), `article_embeddings` 6.66 M (35 GB), `content_index` 13.7 M, `article_ledger` 7.35 M, `documents` 4,912, `hansard_sections` 3,923. Exact count by source: paperspast.natlib.govt.nz 4,648,837; nzherald.co.nz 779,394; odt.co.nz 567,462; scoop.co.nz 527,099; rnz.co.nz 397,400; gazette.govt.nz 208,461; stuff.co.nz 82,522; beehive.govt.nz 55,346; fyi.org.nz 32,584 |
| `extractions` | 257 GB | 211 GB | `v3.claim_entities` 257 M (54 GB), `candidates.candidate` 163 M (72 GB), `candidates.background` 171 M (40 GB), `v3.alias_sighting` 79.8 M, `v3.mentions` 29.8 M, `v3.alias` 26.5 M, `v3.entities` 13.1 M, `v3.claims` 12.4 M. Parked |
| `querynz_v4`, `querynz_v4_sample` | 8 MB each | — | Empty, owned by the owner role (step 0) |

## Every scheduled job on node2

55 user timers plus 7 system ones. Each line: last scheduled run and its result, from the journal (the unit states themselves were reset by the 17 October reboot). The groups are the plan's.

**The carve-out** (keep, and watch):

- `ec-disclosures` daily 03:3x: ran 17 October 03:40, finished (8 expense readings refused, 6 declared gaps, both ordinary). Reads only `factory-db.env`; the model address in force is the script default, the gateway on port 8090, and the page reader at 8032 is the code default. Both match the plan.
- `querynz-gpu-gateway` (8090), `querynz-agent-llm` (8020, card 0, 2 slots of 50 k), `querynz-vision-ocr` (8032, card 0 by default, 4.8 GB): all running. The gateway's status page routes to 8020 and 8001 for the chat model and 8032 for `glm-ocr`.
- `querynz-pi-publisher` (8301), `querynz-pi-web` (8300): running. `ftm-release` 06:15: 14 October green, 15 October **red** at 06:32 (re-run green by hand at 15:52), 16 October green, 17 October green, then eleven more runs by hand on 17 October (four red, the last two green at 23:21 and 23:39). `ftm-feedback-drain` hourly: running green; the reader-mail file holds one entry, an operator's test of 3 October.
- `offsite-push` 01:38: green every night (about 80 minutes). `wal-archive-mirror`: **failed** (node1 unreachable). `querynz-deploy-node1`: **failed** (same). `querynz-residue-mirror`: disabled on node2 (node1's job). `postgresql.service`: running, system level. No `querynz-vip` unit is listed on node2; the floating address is on its interface.

**Still collecting:** `newsscrapers` (every few hours; last 22:31 on 17 October, green), `newsscrapers-daily` 07:45, `gazette-capture` 03:10, `hansard-forward` (**failed**, exit 3, 22:23 on 17 October; a headed-browser capture), `legislation-backfill` 02:10, `comcom-capture` 05:20, `fma-capture` 05:40, `enforcement-capture` 03:40, `companies-office-capture` 06:00, `courts-capture` 05:00, `tribunals-capture` 07:00, `querynz-charities` (weekly; activating at 23:39 on 17 October, still running at measurement), `society-officers` 01:54 (unit disabled, timer live), `parties-capture` 04:20, `party-sites-recapture` weekly, `linz-titles-pull` weekly (unit disabled, timer live), `mp-expenses` and `minister-expenses-capture` and `motu-repec-capture` monthly, `pdfpipe` (a daemon, running), `docpipe-daily` 04:40, `querynz-coverage` 02:11. All green at their last run unless marked.

**Candidates to stop:** the press graph `v3-extract` (every 15 minutes), `querynz-crawler` (3-hourly), `querynz-mint-lane` (activating), `querynz-research` (daemon, running), `querynz-sweep` (two-daily, 17 October green), `querynz-llm@1` (8001, card 1, 23.8 GB), `nzme-archive-backfill` (activating; it **captures the NZ Herald back-catalogue**, see differences); the meaning index `querynz-embed-backfill` (every 20 minutes), `querynz-embed` (8002, processor only), `querynz-embed-index-ship` 05:18; the derive chain `gazette-derive` 04:10, `feed-parties` 04:51, `mp-tenure-derive` weekly, `hansard-register` 07:17, `hansard-reprocess` 06:30, `companies-office-derive` 06:50 (these were node1's and have run on node2 since the failover); old apps `querynz-api` (8100, running), `querynz-pi-web` (8300; in the carve-out table above because the publisher is its twin), `querynz-serving-precompute` 05:40, `querynz-feed-filters` (every 15 minutes), `querynz-paper-images` hourly, `querynz-ec-results`, `robots-audit` weekly, the four `querynz-ref-*` downloads (weekly or yearly), `querynz-db-maintenance` weekly, `querynz-verdict-sync` (**failed**, node1 unreachable); the old board `v3-audit` 06:44.

**On node1 by the manifest** (`ops/systemd/MANIFEST.json`, 75 units): seven enabled there (`feed-parties`, `gazette-derive`, `querynz-charities`, `querynz-embed-index`, `querynz-vip`, `querynz-vision-ocr`, `wal-archive-prune`), ten absent, the rest disabled. Not measured.

## The old checks board

`v3-audit` ran at 06:44 on 17 October and failed as designed: 10 of 76 arms red (the plan said 11 of 73 on 10 October). The reds and whether each touches the daily release:

| Arm | Red since | Touches the release? |
| --- | --- | --- |
| T7.12 essential units enabled and healthy on both boxes | 20 September | Yes, in the sense that node1's half of the carve-out (standby, mirrors) is down |
| T7.13 no host OOM kill; memory pressure in bounds | 12 October | No |
| T7.25 every register feed idempotent | 7 October | No |
| T7.35 no unreviewed unit failure | 12 October | No (it is the alarm path's own ledger) |
| T7.43 ingestion coverage fresh | 12 October | No |
| T7.38 live documents fit one read; unit suite ran this week | 10 October | No |
| T7.60 proxy pool visible | 5 October | No |
| T7.64 gazetteer decision waiting on a rebuild | 7 October | No |
| T7.65 a big job has the right kind of ceiling | 8 October | No |
| T7.71 no disclosure line below the $20,000 floor | 9 October | Touches the published figures: 22 live lines below the floor, from the Commission's own table; the release has run green with them since |

## How a failure reaches Arthur

Every essential unit carries `OnFailure=querynz-failed@%n`, whose handler (`ops/production/unit-failed.sh`) appends a line to `var/audits/unit_failures.jsonl` and, because `ops/config/alert-channel.env` exists (72 bytes, written 5 September), posts a high-priority ntfy notification. The last five ledger lines are 17 October's node1 failures. Whether a notification reaches Arthur's phone is proven by the watcher's test alarm in 1.6, not here.

## The old repository

- Live folder `/home/user/Git Repos/QueryNZ_V3` at `29f0412a` (17 October 23:56), working tree clean at measurement, GitHub `origin/main` at the same commit, no tags. The plan's `2d3874e` is 13 commits behind it. node1's mirror: not measured.
- Reference copy `/home/user/qnz3-ref` at the same commit (1.2); it moves to the freeze tag in 1.5.

## Captured documents (`var/staging/` in the live folder)

| Folder | Files | Size | Note |
| --- | --- | --- | --- |
| `ec-donations` | 7,562 | 6.8 GB | The **captured** files are in `archive/` (2,875: 2,736 PDF, 29 cut short at 1 MiB, 15 xlsx, 6 csv, 3 xls, with a sha256 manifest) and `residue/` (931, Arthur's browser download of 19 August with its own manifest). `pageread/` (3,647) and `index/` (108) are derived |
| `party-sites` | 46,843 | 11 GB | Whole-site crawls, one folder per party |
| `linz` | 1,728 | 4.5 GB | |
| `party-boards` | 1,061 | 91 MB | Has an `archive/` of its own |
| `ec-results` | 158 | 3.6 MB | |
| `ec-expenses` | 113 | 140 MB | |
| `ec-financials` | 93 | 98 MB | Has a `pageread/` |
| `minister-expenses` | 74 | 1.9 MB | |
| `ec-promoters` | 35 | 24 MB | |
| `mp-expenses` | 35 | 936 KB | |
| `party-constitutions` | 20 | 11 MB | Has a `pageread/` |
| `icij-offshore-leaks` | 13 | 71 MB | |
| `letters` | 8 | 32 KB | |
| `boundaries` | 6 | 74 MB | |
| `ec-candidate-list` | 5 | 2.5 MB | |
| `ec-broadcasting`, `ec-byelections` | 4 each | | |
| `ec-party-register` | 3 | 252 KB | |

The site versions (`var/pi-snapshot/v/`): 70 kept, 5.8 GB, newest `2026-10-17T2325` (current), each with a `<version>.manifest.jsonl` of 14,435 lines mapping every page-data file to the API read that made it. `RELEASES.jsonl` records each flip and publish (host `cloudflare-workers`).

## The Papers Past archive

`/home/user/offload-2026-09-02/hetzner-recovery/local-docker_news-scraping-db_newsscraping_20260825_005138.sql.gz`: a gzipped PostgreSQL dump, 132,692,104,796 bytes (124 GiB), with `dump.sha256` and a `verified.OK` of 29 August; the whole offload (644 files, 251 GB) was verified against its `/mnt/hdd` source on 6 September. It sits on node2's system NVMe, not on a hard disk. The old lesson records the dump's corpus at 90.65 million items, of which the 4.65 million held in `incoming_news` are a subset. Never ingested.

## Three facts, now confirmed

1. **The ultimate-holding-company field is not loaded.** No column in `nzbn_canonical` carries "ultimate" or "holding"; the `bulk.companies_*` tables hold addresses, GST, industry, trading names, websites and insolvency only, and no loader mentions it.
2. **Only awards are captured, not live tenders.** `ingestion/gets/sync.py` loads MBIE's open-data CSVs (`bulk.gets_award_notices`, 29,874 rows, and three companion tables); nothing fetches the GETS tender listings.
3. **The Gazette's liquidation and receivership rows** (`gazette.insolvency_appointments`, 400,069): liquidation 51,617, receivership 6,211, voluntary administration 2,392, appointment 58,813, application 28,661, removal intent 252,375. Years 2001 to 2026 run at 6,000 to 20,000 rows each with no gap; 53,790 rows (13%) have no event date and two have impossible ones (2104, 2106). They are derived from 207,133 notices published between 13 January 2000 and 16 October 2026, so the register is as complete as the notice capture, with those dateless rows as the known hole.

## Where the boxes differ from the plan

1. node2 has 125 GB of memory and node1 is down; the plan's "primary on node1, standby on node2" is the target, not the state (step 0 records why).
2. The graphics cards report 31.9 GB each, not 34 GB, and are "AMD Radeon AI PRO R9700".
3. PostgreSQL is 18.6, not 18.3. `incoming_news` is 63 GB, not 25; `extractions` 257 GB, not 211; `nzbn_canonical` 24 GB, not 21.
4. **`archive_mode` is off on the promoted primary**, so no change-log file has been archived since the failover. The off-site dump still runs nightly, but point-in-time recovery between dumps is gone until node1 returns or Arthur turns archiving on here. Nothing in the new estate changes this; it is for Arthur, under track A.
5. Ten of 76 checks-board arms are red, not eleven of 73.
6. In `ec-donations` the captured files live in `archive/` and `residue/`; the plan's note that both are derived output is wrong for this folder (`pageread/` and `index/` are the derived ones). The count of returns the plan gives, 3,091, is close to the 2,875 + 931 held minus the derived manifests.
7. `nzme-archive-backfill` is still enabled and was activating at measurement: it captures the NZ Herald network's back-catalogue, which hard limit 8 forbids. It is on the stop list for the first batch of 1.4, and `incoming_news` already holds 779,394 NZ Herald articles and 32,584 fyi.org.nz rows (the waiting decision "what to do with NZME copies" covers them).
8. The nightly chain the plan places on node1 (`gazette-derive`, `feed-parties`, `querynz-charities`, `companies-office-derive`) has run on node2 since the failover, so stopping it is a node2 change for now.
9. The Papers Past dump is on node2's system disk, not on a hard disk, and `/mnt/hdd2` is empty; the model files are also on the system disk.
10. No `querynz-vip` unit exists on node2; the floating address is simply configured on its interface.
11. The old `querynz-api` unit file carries a database connection string with its password in an `Environment=` line, visible to anyone who can read the unit. It is not in the credential folder. Noted for track H; not repeated here.
12. The reader-mail file has had nobody reading it since 4 October, as the plan expected; it holds only a test entry.

## What normally changes between two releases

Measured with `checks/release_compare.py` on the scheduled releases of 16 and
17 October (`2026-10-16T0616` to `2026-10-17T0616`, 12,011 to 12,013 files),
before any old job was stopped. This is the yardstick for step 1.4: a
difference outside this shape means a stopped job was needed.

| Kind of page data | Files | Changes every day | Why |
| --- | --- | --- | --- |
| root (`SNAPSHOT.json` and four others) | 6 | 5 | the stamp, `at`, `written`, `files`, `bytes` |
| `assets/` | 2 | the bundle is renamed by its hash | a rebuilt bundle |
| `data/board-member/` | 106 | all | `generated_at`, `history`, `press` |
| `data/cite/` | 8,773 | about 3,280 added and 3,280 removed | citation files carry the row id, and the old derive chain renumbers rows nightly |
| `data/donor/` | 2,033 | all | `generated_at`, `history` |
| `data/subject/` | 960 | all | `coverage`, `coverage_note`, `freshness`, `party_window`, `donations_received`, `anchored` |
| `data/size-bands/` | 17 | 8 | `bands` |
| `home.json`, `parties.json`, `pickers.json`, `search-index.json`, `political-donations` | 1 each | all | the day's figures and stamp |
| `data/electorate/`, `data/electorates/`, `fonts/`, `ATTRIBUTION.md`, the geojson | 111 | none | static |

So "nothing changed but new data" reads as: the same kinds change, by the same
keys, and no kind that is static moves. When the derive chain stops (batch 2),
the cite renumbering should stop too, which is the ruling's intent: the
totals freeze as they stand while declarations keep arriving.

**Addendum, 18 October, before batch 2.** The site's window widened to 2017
on 17 October (ruling 364), so the 16-to-17 October yardstick above
understates a day's shape: the 17 October 06:16 to 18 October 06:17
comparison adds 2,457 files (donors, subjects, electorates, citations). The
yardstick for 1.4 from here is the 17 October 23:25 to 18 October 06:17
comparison, one day with the window already widened and node1 down: the same
kinds change by the same keys (`generated_at`, `history`, `freshness`,
`bands`); `data/cite` still renumbers (3,921 added, 3,921 removed) with
node1 down, so that churn comes from node2's side or the carve-out's own
derive; nothing static moved. Batch 2 was stopped at 11:35 on 18 October;
the 19 October release is compared against `2026-10-18T0617`.

**Addendum, 18 October, ruling 55.** Node1 is out of the plan. The "not
measured" column above stays as it is and is not owed; the estate is node2.
Batch 3 (`v3-audit`) was stopped at 16:04 on 18 October on the 13:34 release
run by hand (ruling 56: a timer is not a blocker); the comparison of that
release with `2026-10-18T0617` is the one described in the addendum above.

**Addendum, 18 October, the first release with every batch off.** Arthur
started the release by hand at 16:17 (ruling 56); it ran green and published
`2026-10-18T1617`. Against `2026-10-18T1334`: 14,470 files each side, nothing
added or removed; only `at`, `stamp` and `generated_at` changed; `data/cite`
10,569 same, 0 changed; nothing static moved. Fewer keys change than the
yardstick measured, never more: the nightly citation renumbering came from the
old derive chain, stopped in batch 2. 1.4 item 7 does not apply. The scheduled
06:15 releases from 19 October are watched by `checks/frozen_product.py`.
