# The old estate's corpora: the inventory (ruling 160)

Stream I, 10 November 2026. Read-only: the old databases through the old-estate reader (`bin/q --old`), the
new database through the session reader, file stores by listing and hashing on node2. Nothing was written to
the old estate or to any database. The machine-readable copy, read by the copier (`support/oldcopy`), is
`docs/research/old-estate-inventory.json`.

## For Arthur

1. **The two news sources.** The NZME mastheads are in (ruling 161): `incoming_news.articles` holds 779,702
   nzherald.co.nz and 2,885 businessdesk.co.nz rows, classed NEW with the rest of the table. The recovered news
   dump is **OUT**: `/home/user/hetzner-recovery/local-docker_news-scraping-db_newsscraping_20260825_005138.sql.gz`
   on node1 (124 GiB). node2 holds the same dump (same name, size and `dump.sha256`) at
   `/home/user/offload-2026-09-02/hetzner-recovery/`, with a parquet sample beside it in `hetzner-sample/`. All
   three are marked OUT. Something you should know: the new estate's `papers_past` lane (86.7 M items) was loaded
   from the node2 copy of this dump before ruling 154. That is a fact from the new catalogue; nothing in the
   dump itself was read.
2. **The press graph is classed DERIVED and not copied.** That is `extractions` `v3` (145 GB: claims, mentions,
   entities, aliases) and `candidates` (112 GB). It is model output read from the articles. Regenerating it
   would take the local models weeks. Its 25 decision, verdict and quarantine tables (0.7 GB) are NEW and get
   copied. If you want the graph itself kept, it fits as a dump on `/mnt/hdd` (2.8 TB free), not in the
   database. The same applies to `article_embeddings` (38 GB of bge-m3 vectors).
3. **4,072 PDFs exist nowhere.** These are the PDFs behind `incoming_news.documents` (regulation.govt.nz,
   legislation disclosures, OIA releases, motu and others). They are not on disk and not in the store. Their
   text survives in the rows. They are a gap for the provider (stream K); each row carries its url.
4. **fyi.org.nz.** Removed from the estate (Arthur, 11 November, ruling 168): the copy leaves it out, and the rows
   already copied are in `quarantine_private` (support/oldcopy/quarantine.py).
5. **Files that are not PDFs or images** fall outside ruling 160's file kinds. Not copied: 4,027 raw LINZ API
   pages (11 GB; their rows are held), 19 EC spreadsheets and CSVs, the ICIJ offshore-leaks zip, 6 boundary
   files, 5 Word files and the 98 GB of bulk reference downloads (wikidata and others). Each one is listed under
   `other_files`.
6. **The old jobs still write.** `society_officers` was reloaded with new ids between 13 October and today, and
   `articles` gained rows on 10 November. The copy is a snapshot as of the night it runs.
7. **26 bulk tables have no key** (the NZBN extras: trading names, websites, GST, industry codes, addresses for
   service and the like, plus their histories; 0.9 GB). The integrator chose to copy each whole in one checked
   batch (its md5 over the rows' md5s sorted); a keyless table over 1 GB is still refused.
8. **`querynz_v4` and `querynz_v4_sample` are not leftovers.** The first is the new estate's live database
   (245 GB, loaded daily). The second is its sample database (ruling 54, plan 1b.6). Neither is an old-estate
   database, so neither is inventoried here.

## Totals by class

"To copy" is the size of each table without its indexes. A copied table also gets its key's index, which adds
about 10 to 25%.

| Database | Class | Tables | Size (tables, no indexes) | To copy (estimate) |
| --- | --- | ---: | ---: | ---: |
| extractions | DERIVED | 57 | 134.445 GB | 0 GB |
| extractions | NEW | 25 | 0.685 GB | 0.685 GB |
| incoming_news | DERIVED | 9 | 40.393 GB | 0 GB |
| incoming_news | HELD | 4 | 0.037 GB | 0 GB |
| incoming_news | NEW | 10 | 19.209 GB | 19.209 GB |
| nzbn_canonical | DERIVED | 44 | 0.49 GB | 0 GB |
| nzbn_canonical | HELD | 41 | 3.045 GB | 0 GB |
| nzbn_canonical | NEW | 62 | 13.953 GB | 13.953 GB |
| nzbn_canonical | PARTLY | 2 | 0.235 GB | 0.0 GB |


Two tables are PARTLY, and the JSON names their missing key ranges. `public.director_roles` has 17 ids that
`companies.directors.old_id` does not hold. `public.society_officers` has 894 rows whose natural key (NZBN,
name, role, start date, compared as md5 on both sides) the new table lacks, given as 458 id ranges. Some tables were
measured PARTLY but are classed NEW and copied whole, because their overlap cannot be cut on the key:
`elections.candidates`, the party and candidate donation tables, `party_board_asserted` and `articles` (whose
Papers Past, Beehive and Gazette rows, about 4.9 M of 7.5 M, overlap the new lanes but with different text or
shape).
Each one's note says what overlaps.

## The file stores

The old estate's captured documents are in `var/staging/` of the live old folder (listed and hashed there,
never run from), in `var/mp_interests/`, and in `/home/user/querynz-data/documents/`, the old news lane's
`DOCUMENT_STORE` (settings in the reference copy: `data-layer/extractor/extractor/settings.py`,
`news_canonical`). `var/staging` is 39 GB. Every PDF, image and HTML page outside `party-sites` was hashed in
full (5,373 files plus 1,314 HTML pages), and party-sites' 102,227 HTML pages were sampled. Each hash was
checked against `docs.documents` (the store's index, root `/mnt/hdd2/qv4-docs`, `support/docstore`).

| Store | Files | Held by sha256 | Missing (to copy) | Class |
| --- | --- | --- | --- | --- |
| staging/ec-donations | 3,753 PDF (3,056 distinct), 11 JPG, 29 cut at 1 MiB, 82 HTML; 7.2 GB | 2,329 PDF files, 11 JPG, 68 HTML | 1,420 PDFs (1.94 GB, all in `archive/`), 29 cut files, 14 HTML | PARTLY |
| staging/party-sites | 102,227 HTML (20.7 GB), 438 PDF (1.48 GB), 219 XML, 5 DOCX | 1 PDF, 0 of 20 sampled HTML | 437 PDFs (1.48 GB); HTML not needed for 101,418 pages, see below | PARTLY |
| staging/party-boards | 1,060 HTML (92 MB) | 870 | 189 HTML (7 MB) | PARTLY |
| staging/party-constitutions | 7 PDF, 1 HTML (10 MB) | 0 | all 8 | NEW |
| querynz-data/documents | 857 PDF (1.62 GB) | 417 | 440 PDFs (281 MB) | PARTLY |
| staging/ec-party-register, minister-expenses | 2 + 2 HTML; 69 spreadsheets | spreadsheets all | 4 HTML | PARTLY |
| staging/ec-expenses, ec-financials, ec-promoters, ec-broadcasting, ec-candidate-list, ec-byelections, ec-results, mp-expenses, var/mp_interests | 107 PDF, 101 spreadsheets, 167 HTML | all | none | HELD |
| node1 `/home/user/hetzner-recovery`, node2 `offload-2026-09-02/hetzner-recovery` and `hetzner-sample` | 1 dump each (124 GiB), 1 parquet | n/a | n/a | **OUT** |

Not copied, and listed in the JSON's `other_files`: raw LINZ pages, EC spreadsheets, ICIJ, boundaries,
party-site Word files and sitemaps (all outside ruling 160's file kinds); `var/ocr-cache` and `var/pi-snapshot`
(DERIVED); `/mnt/hdd/backups` (dumps of the same databases); `var/sealed` (the old seal: not opened, hard
limits 11 and 12); a personal downloads folder inside the offload (not a corpus).

## HTML: is the page needed?

| Source | Verdict | Evidence |
| --- | --- | --- |
| News articles (`incoming_news.articles`, every outlet) | No HTML was ever kept | The old estate stored no HTML for articles. Each row holds url, title, post date (missing for a few outlets, for example linz.govt.nz, hrc.govt.nz, teaonews), scrape and fetch time, and body. 115 kiwiblog rows and 4 council rows have no body. There is nothing to keep apart |
| Party sites | **RETAINED** for the 101,418 pages that landed as articles. **LOST** for 7,850 page rows (landed `thin` 7,573, `unsupported` 236, `pdf-queued` 41; about 1,383 distinct pages, 0.8 GB) | 20 sampled pages, each traced from `registers.party_site_documents` to its `articles` row. All 20 rows have url, title and fetch time. 11 of 20 have a published date; the other 9 pages state none in the row. The body's last 80 characters are on the page in 20 of 20; its first 80 in 15 of 20 (the 5 National pages put a heading first). 72 to 100% of the body's 8-word runs are on the page (median 0.92). The 7,850 rows have no article and no body. The copier's store flag is all-or-nothing, so these pages are not copied: the JSON names them (`html_lost_rows`) for stream J to land from a list if Arthur wants them |
| Party boards | **LOST** | `party_board_asserted` keeps person, role and source url per snapshot, not the page's title, date or body. The 189 missing pages are copied |
| EC listing pages (ec-donations index, ec-party-register, minister-expenses) | **LOST** | `disclosure_documents` keeps ref, url and sha256 only. The 18 missing pages are copied |
| EC results, by-elections, candidate list, promoters, broadcasting | Held | Every page is already in the store |

## Disk

The tables land in `querynz_v4`, whose data directory is on the primary's system disk. node1 is primary with
771 GB free. node2 is the standby with 484 GB free on the btrfs `/home`. The standby's disk is the one that
binds. The files land in the document store, `/mnt/hdd2/qv4-docs` on node2 (2.5 TB free).

| What | Size | Where |
| --- | ---: | --- |
| incoming_news NEW (articles 17.9 GB, ledger 1.1 GB, the rest small) | 19.2 GB (24 GB with keys) | /home |
| nzbn_canonical NEW: registers, histories, NZBN extras | about 2 GB | /home |
| nzbn_canonical NEW: reference sets (wikidata 10 GB, geonames 2.2 GB, gleif, ror) | about 12 GB (17.5 GB with their old indexes; less with the key only) | /home, or a tablespace on `/mnt/hdd2` (the one path that exists on both boxes) if /home is to stay lean |
| extractions NEW: decisions and verdicts | 0.7 GB | /home |
| PARTLY ranges (911 rows) | under 2 MB | /home |
| Files: PDFs and images 3.7 GB, HTML 10 MB (0.8 GB more if the 7,850 thin party-site pages are taken) | 3.7 to 4.5 GB | /mnt/hdd2/qv4-docs |
| **Total** | **about 38 GB in the database (under 45 GB with keys), about 4 GB of files** | |
| Only if Arthur keeps the DERIVED press graph and embeddings | about 300 GB | a dump on /mnt/hdd (2.8 TB free), not the database |

Proposal: everything goes to /home, which uses under 10% of the standby's free space. The reference sets move to
a `/mnt/hdd2` tablespace only if Arthur wants /home kept lean. The copy writes about as much WAL again, and the
standby replays it.

## Per database

Rows are pg_class estimates unless the JSON says `exact`. Size is the table without and with its indexes.
Content columns were not read beyond the samples named. No address, birth or contact column was selected.

### incoming_news

| Table | Class | Rows | Size (table / with indexes) | Key | Held in / what is missing |
| --- | --- | ---: | --- | --- | --- |
| public.alembic_version | DERIVED | 1 | 0.0 / 0.0 MB | version_num | bookkeeping |
| public.article_embeddings | DERIVED | 6670603 | 37.619 / 38.101 GB | article_id | bge-m3 vectors of the articles (38 GB); regenerable on the boxes |
| public.article_images | NEW | 772 | 0.1 / 0.2 MB | article_id | 3 and 772 rows |
| public.article_ledger | NEW | 7469727 | 1.089 / 2.466 GB | upstream_id | 7.47 M rows: the ingest ledger of the articles (status, failures) |
| public.articles | NEW | 7509635 | 17.938 / 22.004 GB | id | papers_past.items (Papers Past), beehive.releases, gazette.notices: 7.51 M rows. NEW for every outlet but three: Papers Past 4,648,837 rows matched by upstream_id (papers_past.items.held_in_old, all 4,648,837; titles 5/5 equal, text lengths differ: the old text is another rendering); beehive.govt.nz 55,347 (15/15 urls in beehive.releases); gazette.govt.nz 208,914 (gazette.notices.article). These overlaps are not cut on the key (id is a uuid), so the table is copied whole; the overlap is about 4.9 M rows, 10 GB of text. NZME mastheads in (ruling 161): nzherald.co.nz 779,702, businessdesk.co.nz 2,885 |
| public.benchmark_questions | NEW | 192 | 0.1 / 0.3 MB | id | small tables people or the old research agent wrote (questions, reports) |
| public.benchmark_sweeps | DERIVED | n/a | 0.2 / 0.3 MB | id | bookkeeping |
| public.comcom_cases | HELD | 89 | 0.2 / 0.3 MB | case_id | commerce_commission.cases, fma.actions: 89 vs 1,728; 15 vs 804 |
| public.companies_office_notices | NEW | 3 | 0.4 / 0.4 MB | notice_id | 3 and 772 rows |
| public.content_collisions | DERIVED | 612 | 0.2 / 0.3 MB | day, loser_source, owner_source | hash index over the articles |
| public.content_index | DERIVED | 14168554 | 2.771 / 4.553 GB | content_hash | hash index over the articles |
| public.documents | NEW | 5136 | 0.171 / 0.173 GB | id | 5,132 PDFs' rows with their text; only 1,064 of the PDFs are on disk or in the store; 4,072 PDFs are nowhere (gap for the MCP) |
| public.feed_filter_hits | DERIVED | 1731 | 1.5 / 3.4 MB | filter_name, article_id | bookkeeping |
| public.feed_filter_runs | DERIVED | 2867 | 0.4 / 0.5 MB | id | bookkeeping |
| public.feed_filters | NEW | 4 | 0.0 / 0.1 MB | name | small tables people or the old research agent wrote (questions, reports) |
| public.fma_warnings | HELD | 15 | 0.1 / 0.2 MB | case_id | commerce_commission.cases, fma.actions: 89 vs 1,728; 15 vs 804 |
| public.gazette_residue | DERIVED | 14 | 0.1 / 0.1 MB | year | bookkeeping |
| public.hansard_members | HELD | 394 | 0.3 / 0.3 MB | member_id | hansard.sections, hansard.members: 3,923 = 3,923 (old_id); 394 = 394 |
| public.hansard_sections | HELD | 3923 | 36.3 / 36.8 MB | id | hansard.sections, hansard.members: 3,923 = 3,923 (old_id); 394 = 394 |
| public.ingest_state | DERIVED | 5 | 0.0 / 0.1 MB | key | bookkeeping |
| public.oia_requests | NEW | 302 | 2.3 / 2.4 MB | oia_id | 302 fyi.org.nz requests (fyi stays held at the fetch gate, old ruling 321; this is a copy, not a fetch) |
| public.research_gaps | NEW | 2480 | 4.8 / 5.4 MB | id | small tables people or the old research agent wrote (questions, reports) |
| public.research_jobs | NEW | 481 | 3.2 / 3.2 MB | id | small tables people or the old research agent wrote (questions, reports) |

### nzbn_canonical

| Table | Class | Rows | Size (table / with indexes) | Key | Held in / what is missing |
| --- | --- | ---: | --- | --- | --- |
| bulk.bic_backfill | DERIVED | 292 | 0.1 / 0.2 MB | id | the old jobs' bookkeeping |
| bulk.charitable_trust_boards_core_data | HELD | 35599 | 8.8 / 8.8 MB | none | companies.entities (register column), companies.villages: 35,599/59,981/2,922/512 vs 35,779/60,267/2,926/514 |
| bulk.charitable_trust_boards_core_data_history | NEW | 599 | 0.2 / 0.2 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_abn | NEW | 1008 | 0.2 / 0.2 MB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.companies_abn_history | NEW | 12 | 0.0 / 0.0 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_address_for_service | NEW | 759476 | 0.149 / 0.197 GB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.companies_address_for_service_history | NEW | 12688 | 2.5 / 2.5 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_business_industry_classification | NEW | 632212 | 0.098 / 0.136 GB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.companies_business_industry_classification_history | NEW | 4467 | 0.7 / 0.7 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_gst | NEW | 66554 | 8.4 / 12.6 MB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.companies_gst_history | NEW | 703 | 0.1 / 0.1 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_insolvency | HELD | 108646 | 24.8 / 24.8 MB | none | companies.insolvencies: 108,646 vs 109,586 |
| bulk.companies_insolvency_history | NEW | 45 | 0.1 / 0.1 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_public_address | NEW | 318465 | 0.063 / 0.076 GB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.companies_public_address_history | NEW | 5134 | 1.1 / 1.1 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_registered_office_address | HELD | 759477 | 0.15 / 0.238 GB | none | companies.registered_offices: 759,477 vs 892,809 |
| bulk.companies_registered_office_address_history | NEW | 12131 | 2.4 / 3.2 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_trading_area | NEW | 252269 | 33.5 / 33.5 MB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.companies_trading_area_history | NEW | 1721 | 0.3 / 0.3 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_trading_name | NEW | 350668 | 0.047 / 0.083 GB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.companies_trading_name_history | NEW | 2678 | 0.4 / 0.4 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.companies_website | NEW | 336718 | 43.9 / 43.9 MB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.companies_website_history | NEW | 2626 | 0.4 / 0.4 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.director_addresses | NEW | 12 | 0.0 / 0.0 MB | id | 12 rows; home addresses (private by the destination schema's suffix) |
| bulk.geonames | NEW | 13446596 | 1.549 / 2.062 GB | geonameid | reference datasets loaded from public downloads (originals in /home/user/offload-2026-09-02/bulk); no counterpart in the new estate |
| bulk.geonames_alternate | NEW | 8172299 | 0.67 / 1.226 GB | alternateid | reference datasets loaded from public downloads (originals in /home/user/offload-2026-09-02/bulk); no counterpart in the new estate |
| bulk.gets_award_notices | HELD | 29874 | 31.8 / 31.8 MB | none | tenders.*: 29,874 = tenders.notices 29,874; suppliers 31,265 vs 31,264; categories and regions are columns of tenders.notices |
| bulk.gets_product_categories | HELD | 52306 | 7.2 / 7.2 MB | none | tenders.*: 29,874 = tenders.notices 29,874; suppliers 31,265 vs 31,264; categories and regions are columns of tenders.notices |
| bulk.gets_region_by_tender | HELD | 46975 | 4.4 / 4.4 MB | none | tenders.*: 29,874 = tenders.notices 29,874; suppliers 31,265 vs 31,264; categories and regions are columns of tenders.notices |
| bulk.gets_register_meta | DERIVED | n/a | 0.0 / 0.0 MB | none | the old jobs' bookkeeping |
| bulk.gets_supplier_data | HELD | 31265 | 5.6 / 6.2 MB | none | tenders.*: 29,874 = tenders.notices 29,874; suppliers 31,265 vs 31,264; categories and regions are columns of tenders.notices |
| bulk.gleif | NEW | 3461799 | 0.417 / 0.593 GB | lei | reference datasets loaded from public downloads (originals in /home/user/offload-2026-09-02/bulk); no counterpart in the new estate |
| bulk.gleif_names | NEW | 496269 | 0.089 / 0.124 GB | id | reference datasets loaded from public downloads (originals in /home/user/offload-2026-09-02/bulk); no counterpart in the new estate |
| bulk.import_log | DERIVED | 37 | 0.0 / 0.1 MB | id | the old jobs' bookkeeping |
| bulk.linz_place_names | HELD | 54731 | 6.0 / 9.8 MB | name_id | linz.place_names: 54,731 vs 54,736 |
| bulk.maori_business_identifier | NEW | 3553 | 0.6 / 0.6 MB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.maori_business_identifier_history | NEW | 25 | 0.0 / 0.0 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.other_incorporated_entities_core_data | HELD | 59981 | 15.7 / 25.6 MB | none | companies.entities (register column), companies.villages: 35,599/59,981/2,922/512 vs 35,779/60,267/2,926/514 |
| bulk.other_incorporated_entities_core_data_history | NEW | 380 | 0.1 / 0.1 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.public_sector_entities_core_data | HELD | 2922 | 0.5 / 0.5 MB | none | companies.entities (register column), companies.villages: 35,599/59,981/2,922/512 vs 35,779/60,267/2,926/514 |
| bulk.public_sector_entities_core_data_history | NEW | n/a | 0.0 / 0.0 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.retirement_villages_core_data | HELD | 512 | 0.3 / 0.3 MB | none | companies.entities (register column), companies.villages: 35,599/59,981/2,922/512 vs 35,779/60,267/2,926/514 |
| bulk.retirement_villages_core_data_history | NEW | 8 | 0.1 / 0.1 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.ror_names | NEW | 333405 | 41.1 / 48.6 MB | id | reference datasets loaded from public downloads (originals in /home/user/offload-2026-09-02/bulk); no counterpart in the new estate |
| bulk.unincorporated_entities_core_data | NEW | 227984 | 27.9 / 27.9 MB | none | NZBN bulk extras with no counterpart (companies.lookups holds trading names for 14,637 looked-up companies only) No usable key: copied whole, in one checked batch. |
| bulk.unincorporated_entities_core_data_history | NEW | 670 | 0.1 / 0.1 MB | none | the old import's change history of the NZBN bulk sets No usable key: copied whole, in one checked batch. |
| bulk.wikidata_attrs | NEW | 7647862 | 0.636 / 0.939 GB | id | reference datasets loaded from public downloads (originals in /home/user/offload-2026-09-02/bulk); no counterpart in the new estate |
| bulk.wikidata_labels | NEW | 92232688 | 8.966 / 11.859 GB | qid | reference datasets loaded from public downloads (originals in /home/user/offload-2026-09-02/bulk); no counterpart in the new estate |
| bulk.wikidata_names | NEW | 4078658 | 0.431 / 0.62 GB | id | reference datasets loaded from public downloads (originals in /home/user/offload-2026-09-02/bulk); no counterpart in the new estate |
| bulk.worksafe_annual | NEW | 78 | 0.0 / 0.1 MB | dataset, year | 78 rows |
| charities.charity_entities | HELD | 19653 | 9.0 / 11.8 MB | charity_number | charities.charities: 45,924 / 19,653 rows vs 46,174; same OData source |
| charities.charity_officer_roles | HELD | 283221 | 0.102 / 0.171 GB | id | charities.officers: 283,221 vs 590,183; 20/20 sampled officer_id held |
| charities.import_runs | DERIVED | n/a | 0.0 / 0.0 MB | id | the old jobs' bookkeeping |
| corpus.observations | NEW | 2 | 0.0 / 0.1 MB | id | 2 rows |
| corpus.promoted | DERIVED | n/a | 0.0 / 0.0 MB | id | the old jobs' bookkeeping |
| courts.case_parties | HELD | 373 | 0.1 / 0.2 MB | id | courts.*: 116/118 judgment PDFs held by sha256; rows read from them |
| courts.cases | HELD | 118 | 0.1 / 0.1 MB | id | courts.*: 116/118 judgment PDFs held by sha256; rows read from them |
| elections.candidates | NEW | 8985 | 2.1 / 2.9 MB | id | house.candidates: measured PARTLY: 1999 to 2017 (7,812 rows) not held; 2020/2023 partly in house.candidates (old 1,128/950 vs new 585/495). The overlap is not cut on the key (id), so the whole 3 MB table is copied |
| gazette.bankruptcies | DERIVED | 62917 | 12.3 / 26.6 MB | id | gazette.*: read from the Gazette notices' text, which the new gazette lane holds and re-reads |
| gazette.celebrants | DERIVED | 88551 | 19.4 / 34.2 MB | id | gazette.*: read from the Gazette notices' text, which the new gazette lane holds and re-reads |
| gazette.company_aliases | DERIVED | 2198 | 0.3 / 1.1 MB | id | gazette.*: read from the Gazette notices' text, which the new gazette lane holds and re-reads |
| gazette.derive_runs | DERIVED | 28 | 0.3 / 0.3 MB | id | the old jobs' bookkeeping |
| gazette.director_prohibitions | DERIVED | 530 | 0.2 / 0.3 MB | id | gazette.*: read from the Gazette notices' text, which the new gazette lane holds and re-reads |
| gazette.insolvency_appointments | DERIVED | 400069 | 0.051 / 0.146 GB | id | gazette.*: read from the Gazette notices' text, which the new gazette lane holds and re-reads |
| gazette.notices | HELD | 207133 | 0.069 / 0.088 GB | notice_id | gazette.notices: 207,133 vs 207,871; 20/20 sampled notice ids held |
| gazette.party_events | DERIVED | 168 | 0.1 / 0.2 MB | id | gazette.*: read from the Gazette notices' text, which the new gazette lane holds and re-reads |
| gazette.public_appointments | DERIVED | 10615 | 4.5 / 7.1 MB | id | gazette.*: read from the Gazette notices' text, which the new gazette lane holds and re-reads |
| legislation.instruments | NEW | 42657 | 10.3 / 19.8 MB | id | 42,657 instrument titles (years 1267 to 2026), seen 25 to 30 July 2026; no legislation lane |
| mp_interests.interests | HELD | 25147 | 13.3 / 19.0 MB | id | mp_interests.*: 21/21 register PDFs held by sha256; 25,147 vs 24,931 declarations re-read |
| mp_interests.registers | HELD | 21 | 0.1 / 0.1 MB | register_id | mp_interests.*: 21/21 register PDFs held by sha256; 25,147 vs 24,931 declarations re-read |
| parks.park | NEW | 7 | 0.0 / 0.0 MB | id | 7 rows |
| parties.register | HELD | 17 | 0.1 / 0.1 MB | party_name | parties.registrations: 17 vs 77 |
| public.alembic_version | DERIVED | 1 | 0.0 / 0.0 MB | version_num | the old jobs' bookkeeping |
| public.charity_annual_financials | HELD | 421633 | 0.048 / 0.094 GB | annual_return_id | charities.returns: 421,633 vs 431,908; 20/20 sampled annual_return_id held |
| public.charity_orgs | HELD | 45924 | 4.5 / 6.5 MB | organisation_id | charities.charities: 45,924 / 19,653 rows vs 46,174; same OData source |
| public.charity_register_meta | DERIVED | n/a | 0.0 / 0.0 MB | none | the old jobs' bookkeeping |
| public.director_role_history | NEW | 1194878 | 0.145 / 0.318 GB | id | the old import runs' per-row snapshots (recorded 14 Jul to 16 Aug 2026); the new lane keeps first/last file only, companies.changes has 8 rows |
| public.director_roles | PARTLY | 1185822 | 0.203 / 0.649 GB | id | companies.directors: 1,185,822 rows; 1,185,805 held by old_id (20/20 sample); 17 ids not held, named as single-key ranges |
| public.entities | HELD | 1821454 | 0.285 / 1.264 GB | id | companies.entities: 1,821,454 rows; companies.entities.old_id holds all 1,821,454; 20/20 sampled nzbn match on name md5 and status |
| public.entity_filings | DERIVED | 16 | 0.1 / 0.2 MB | id | the old jobs' bookkeeping |
| public.entity_history | NEW | 1826096 | 0.252 / 0.516 GB | id | the old import runs' per-row snapshots (recorded 14 Jul to 16 Aug 2026); the new lane keeps first/last file only, companies.changes has 8 rows |
| public.govt_org_events | NEW | 569 | 0.1 / 0.2 MB | event_id | no government-organisations register in the new estate |
| public.govt_org_groupings | NEW | 29 | 0.0 / 0.1 MB | ps_id | no government-organisations register in the new estate |
| public.govt_orgs | NEW | 317 | 0.1 / 0.1 MB | org_id | no government-organisations register in the new estate |
| public.govt_register_meta | DERIVED | n/a | 0.0 / 0.0 MB | none | the old jobs' bookkeeping |
| public.import_runs | DERIVED | 2 | 0.0 / 0.1 MB | id | the old jobs' bookkeeping |
| public.persons | DERIVED | n/a | 0.0 / 0.0 MB | none | a view |
| public.shareholder_role_history | NEW | 1599191 | 0.208 / 0.439 GB | id | the old import runs' per-row snapshots (recorded 14 Jul to 16 Aug 2026); the new lane keeps first/last file only, companies.changes has 8 rows |
| public.shareholder_roles | HELD | 1581955 | 0.253 / 0.567 GB | id | companies.shareholders: 1,581,955 rows = 1,581,955 old_id; 20/20 sampled ids held |
| public.society_officers | PARTLY | 133968 | 0.033 / 0.051 GB | id | societies.officers: 133,968 rows (reloaded by the old job since, ids renumbered); 894 rows' natural key (nzbn, name, role, start) not in societies.officers, named as 458 id ranges |
| public.society_sweep_log | DERIVED | 22787 | 1.6 / 3.4 MB | nzbn | the old jobs' bookkeeping |
| registers.body_aliases | NEW | 39 | 0.1 / 0.1 MB | id | small hand-made or catch tables with no counterpart |
| registers.candidate_donation_totals | DERIVED | 2477 | 1.8 / 2.1 MB | id | joins and totals built from other old tables or the press graph |
| registers.candidate_donations | NEW | 3455 | 1.1 / 1.3 MB | id | party_returns.*, disclosures.*, candidate_returns.*: measured PARTLY: the new EC lanes hold 1,315 party donors vs 2,359 and 482 candidate donors vs 3,455; 1,420 of the old EC PDFs (by bytes) are not in the store. Small, copied whole |
| registers.candidates_announced | NEW | 1129 | 0.6 / 0.8 MB | id | small hand-made or catch tables with no counterpart |
| registers.charity_officers | DERIVED | n/a | 0.0 / 0.0 MB | none | a view |
| registers.colocations | DERIVED | n/a | 0.0 / 0.0 MB | none | a view |
| registers.directorship_discrepancies | DERIVED | 9162 | 2.0 / 2.6 MB | id | joins and totals built from other old tables or the press graph |
| registers.directorships | DERIVED | n/a | 0.0 / 0.0 MB | none | a view |
| registers.disclosure_documents | NEW | 869 | 0.6 / 0.7 MB | ref | party_returns.*, disclosures.*, candidate_returns.*: measured PARTLY: the new EC lanes hold 1,315 party donors vs 2,359 and 482 candidate donors vs 3,455; 1,420 of the old EC PDFs (by bytes) are not in the store. Small, copied whole |
| registers.disclosure_statements | NEW | 904 | 0.9 / 1.2 MB | id | party_returns.*, disclosures.*, candidate_returns.*: measured PARTLY: the new EC lanes hold 1,315 party donors vs 2,359 and 482 candidate donors vs 3,455; 1,420 of the old EC PDFs (by bytes) are not in the store. Small, copied whole |
| registers.donation_disclosures | NEW | 304 | 0.2 / 0.2 MB | id | party_returns.*, disclosures.*, candidate_returns.*: measured PARTLY: the new EC lanes hold 1,315 party donors vs 2,359 and 482 candidate donors vs 3,455; 1,420 of the old EC PDFs (by bytes) are not in the store. Small, copied whole |
| registers.donation_lines_dropped | NEW | 112 | 0.1 / 0.1 MB | id | small hand-made or catch tables with no counterpart |
| registers.donor_anchors | HELD | 71391 | 0.054 / 0.096 GB | id | links.old_decisions: 71,391/5,479/381 vs 71,383/5,479/381 copied |
| registers.donor_exposure | DERIVED | 1281 | 2.7 / 2.8 MB | donor_key, weights_version | joins and totals built from other old tables or the press graph |
| registers.donor_vehicles | DERIVED | 8 | 0.0 / 0.1 MB | company_nzbn, weights_version | joins and totals built from other old tables or the press graph |
| registers.hansard_sittings | HELD | 137 | 0.1 / 0.1 MB | sitting_date | hansard.old_speeches, hansard.sittings: 11,627 = 11,627; 137 = 137 |
| registers.hansard_speeches | HELD | 11627 | 7.1 / 9.9 MB | id | hansard.old_speeches, hansard.sittings: 11,627 = 11,627; 137 = 137 |
| registers.linz_company_matches | DERIVED | 737156 | 0.121 / 0.232 GB | pull_id, corporate_name | joins and totals built from other old tables or the press graph |
| registers.linz_pulls | DERIVED | n/a | 0.0 / 0.0 MB | pull_id | the old jobs' bookkeeping |
| registers.linz_title_owners | HELD | 5743459 | 1.937 / 3.821 GB | id | linz.owners: 5,743,459 vs 5,745,328; 20/20 sampled lds_id held as linz.owners.id |
| registers.metrics | DERIVED | 1030 | 0.4 / 0.5 MB | id | joins and totals built from other old tables or the press graph |
| registers.minister_expense_documents | HELD | 70 | 0.1 / 0.1 MB | sha256 | expenses.*: every source spreadsheet held by sha256 (31/31, 69/69); rows re-read |
| registers.minister_expenses | HELD | 1581 | 0.8 / 1.2 MB | id | expenses.*: every source spreadsheet held by sha256 (31/31, 69/69); rows re-read |
| registers.mp_aliases | NEW | 992 | 0.4 / 0.6 MB | id | small hand-made or catch tables with no counterpart |
| registers.mp_expense_documents | HELD | 31 | 0.1 / 0.1 MB | sha256 | expenses.*: every source spreadsheet held by sha256 (31/31, 69/69); rows re-read |
| registers.mp_expenses | HELD | 3745 | 2.0 / 2.9 MB | id | expenses.*: every source spreadsheet held by sha256 (31/31, 69/69); rows re-read |
| registers.mp_org_resolutions | DERIVED | 1655 | 0.5 / 0.7 MB | id | joins and totals built from other old tables or the press graph |
| registers.mp_tenure_events | NEW | 28 | 0.1 / 0.1 MB | id | small hand-made or catch tables with no counterpart |
| registers.party_board_asserted | NEW | 10512 | 4.3 / 4.8 MB | id | party_boards.roles: measured PARTLY: 10,512 asserted roles vs 2,876; 189 of the 1,058 board pages not in the store. Copied whole (5 MB) |
| registers.party_donations | NEW | 2359 | 1.2 / 1.4 MB | id | party_returns.*, disclosures.*, candidate_returns.*: measured PARTLY: the new EC lanes hold 1,315 party donors vs 2,359 and 482 candidate donors vs 3,455; 1,420 of the old EC PDFs (by bytes) are not in the store. Small, copied whole |
| registers.party_election_expenses | HELD | 37 | 0.1 / 0.1 MB | id | party_finance.*: source PDFs held by sha256 (ec-financials 46/46, ec-expenses 40/40, ec-promoters 20/20); 69=69 promoters, 305 vs 303 people |
| registers.party_financial_documents | HELD | 46 | 0.1 / 0.1 MB | id | party_finance.*: source PDFs held by sha256 (ec-financials 46/46, ec-expenses 40/40, ec-promoters 20/20); 69=69 promoters, 305 vs 303 people |
| registers.party_financials | HELD | 78 | 0.1 / 0.1 MB | id | party_finance.*: source PDFs held by sha256 (ec-financials 46/46, ec-expenses 40/40, ec-promoters 20/20); 69=69 promoters, 305 vs 303 people |
| registers.party_return_totals | DERIVED | 151 | 0.3 / 0.3 MB | id | joins and totals built from other old tables or the press graph |
| registers.party_rule_documents | NEW | 7 | 0.0 / 0.1 MB | id | party constitutions: 0 of 7 PDFs in the store |
| registers.party_rules | NEW | 133 | 0.2 / 0.2 MB | id | party constitutions: 0 of 7 PDFs in the store |
| registers.party_site_documents | NEW | 109762 | 0.044 / 0.068 GB | id | 104,713 party-site pages and files, none in the new estate (0/40 PDFs, 0/20 pages by sha256) |
| registers.pi_residue | DERIVED | 8084 | 5.7 / 7.6 MB | kind, source_ref | joins and totals built from other old tables or the press graph |
| registers.pi_residue_builds | DERIVED | 129 | 0.2 / 0.2 MB | id | the old jobs' bookkeeping |
| registers.pi_residue_pursuit | DERIVED | 146 | 0.1 / 0.1 MB | id | joins and totals built from other old tables or the press graph |
| registers.press_appointments | DERIVED | 631036 | 0.178 / 0.218 GB | none | joins and totals built from other old tables or the press graph |
| registers.press_enforcement | DERIVED | 147530 | 38.6 / 49.4 MB | none | joins and totals built from other old tables or the press graph |
| registers.press_transactions_ownership | DERIVED | 119836 | 30.5 / 40.1 MB | none | joins and totals built from other old tables or the press graph |
| registers.promoter_expenses | HELD | 21 | 0.0 / 0.1 MB | id | party_finance.*: source PDFs held by sha256 (ec-financials 46/46, ec-expenses 40/40, ec-promoters 20/20); 69=69 promoters, 305 vs 303 people |
| registers.promoter_people | HELD | 305 | 0.1 / 0.2 MB | id | party_finance.*: source PDFs held by sha256 (ec-financials 46/46, ec-expenses 40/40, ec-promoters 20/20); 69=69 promoters, 305 vs 303 people |
| registers.promoters | HELD | 69 | 0.1 / 0.1 MB | id | party_finance.*: source PDFs held by sha256 (ec-financials 46/46, ec-expenses 40/40, ec-promoters 20/20); 69=69 promoters, 305 vs 303 people |
| registers.registered_offices | DERIVED | n/a | 0.0 / 0.0 MB | none | a view |
| registers.retired_party_officials_2026_10_01 | NEW | 38 | 0.1 / 0.1 MB | id | small hand-made or catch tables with no counterpart |
| registers.review_verdicts | HELD | 381 | 0.2 / 0.2 MB | id | links.old_decisions: 71,391/5,479/381 vs 71,383/5,479/381 copied |
| registers.roster_fold_watch | DERIVED | 5154 | 0.8 / 1.1 MB | fold_id | joins and totals built from other old tables or the press graph |
| registers.roster_identity_folds | HELD | 5479 | 2.7 / 3.4 MB | id | links.old_decisions: 71,391/5,479/381 vs 71,383/5,479/381 copied |
| registers.shareholder_anchors | DERIVED | 204156 | 17.0 / 29.9 MB | shareholder_role_id | joins and totals built from other old tables or the press graph |
| registers.shareholdings | DERIVED | n/a | 0.0 / 0.0 MB | none | a view |
| registers.suppressed_names | NEW | 2 | 0.0 / 0.0 MB | id | small hand-made or catch tables with no counterpart |
| registers.trading_names | DERIVED | n/a | 0.0 / 0.0 MB | none | a view |
| registers.trust_boards | DERIVED | n/a | 0.0 / 0.0 MB | none | a view |
| registers.worksafe_documents | HELD | 143 | 0.2 / 0.2 MB | ref | worksafe.actions: 145 vs 665 |
| registers.worksafe_enforcement | HELD | 145 | 0.3 / 0.4 MB | id | worksafe.actions: 145 vs 665 |

### extractions

| Table | Class | Rows | Size (table / with indexes) | Key | Held in / what is missing |
| --- | --- | ---: | --- | --- | --- |
| candidates.background | DERIVED | 171078480 | 21.158 / 43.111 GB | id | entity-resolution candidates built from the registers |
| candidates.build | DERIVED | 6 | 0.0 / 0.0 MB | build_id | entity-resolution candidates built from the registers |
| candidates.candidate | DERIVED | 162743856 | 30.573 / 76.933 GB | id | entity-resolution candidates built from the registers |
| tg_96cf7cd31c89.alias | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.alias_link | DERIVED | n/a | 0.0 / 0.0 MB | alias_id, entity_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.alias_sighting | DERIVED | n/a | 0.0 / 0.0 MB | article_id, alias_id, entity_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.claim_entities | DERIVED | n/a | 0.0 / 0.0 MB | claim_id, entity_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.claim_heals | DERIVED | n/a | 0.0 / 0.0 MB | heal_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.claim_object_detachments | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.claim_splits | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.claims | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.detector_signals | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entities | DERIVED | n/a | 0.0 / 0.1 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_key_proposal_articles | DERIVED | n/a | 0.0 / 0.0 MB | authority, source_id, entity_id, article_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_key_proposals | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_keys | DERIVED | n/a | 0.0 / 0.0 MB | authority, source_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_merges | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_prominence | DERIVED | n/a | 0.0 / 0.0 MB | none | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_quarantine | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_renames | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_splits | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_type_changes | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.entity_type_overrides | DERIVED | n/a | 0.0 / 0.0 MB | norm_form | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.er_candidates | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.er_split_candidates | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.extraction_log | DERIVED | n/a | 0.0 / 0.0 MB | article_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.gazetteer_blocklist | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.guard_drops | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.mentions | DERIVED | n/a | 0.0 / 0.0 MB | article_id, entity_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.mint_lane_state | DERIVED | n/a | 0.0 / 0.0 MB | k | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.mint_review | DERIVED | n/a | 0.0 / 0.0 MB | entity_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.review_decisions | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.source_policy | DERIVED | n/a | 0.0 / 0.0 MB | outlet | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.watchlist_entities | DERIVED | n/a | 0.0 / 0.0 MB | watchlist_id, entity_id | an empty test copy of the press graph's schema |
| tg_96cf7cd31c89.watchlists | DERIVED | n/a | 0.0 / 0.0 MB | id | an empty test copy of the press graph's schema |
| v3.alias | DERIVED | 26483344 | 1.631 / 4.718 GB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.alias_cleanup_log | NEW | n/a | 0.0 / 0.0 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.alias_link | DERIVED | 7230880 | 2.181 / 4.315 GB | alias_id, entity_id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.alias_refold_quarantine | NEW | 19471 | 1.4 / 2.0 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.alias_sighting | DERIVED | 76293184 | 9.316 / 20.381 GB | article_id, alias_id, entity_id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.anchor_review | NEW | 4918 | 8.2 / 8.6 MB | entity_id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.claim_entities | DERIVED | 238956560 | 30.483 / 57.881 GB | claim_id, entity_id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.claim_heals | NEW | 1227 | 0.4 / 0.5 MB | heal_id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.claim_object_detachments | NEW | 33740 | 3.5 / 4.3 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.claim_splits | NEW | n/a | 0.0 / 0.0 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.claim_suppressions | NEW | n/a | 0.0 / 0.0 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.claims | DERIVED | 11662369 | 8.838 / 10.415 GB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.detector_signals | DERIVED | 12074572 | 2.332 / 4.146 GB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.document_quarantine | NEW | 9153 | 0.052 / 0.053 GB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.enterprise_forms | NEW | n/a | 0.0 / 0.0 MB | form | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.enterprise_members | NEW | 5 | 0.0 / 0.1 MB | enterprise_id, nzbn | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.entities | DERIVED | 6674413 | 2.316 / 6.412 GB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.entity_key_proposal_articles | DERIVED | 40746248 | 3.543 / 7.936 GB | authority, source_id, entity_id, article_id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.entity_key_proposals | DERIVED | 487248 | 0.527 / 0.784 GB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.entity_keys | DERIVED | 4088202 | 0.347 / 0.784 GB | authority, source_id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.entity_merges | DERIVED | 2181866 | 1.344 / 1.459 GB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.entity_prominence | DERIVED | 2571127 | 0.114 / 0.172 GB | none | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.entity_quarantine | NEW | 560452 | 0.108 / 0.12 GB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.entity_renames | DERIVED | 481098 | 0.072 / 0.083 GB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.entity_splits | NEW | 104 | 0.2 / 0.3 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.entity_type_changes | DERIVED | 60236 | 7.0 / 8.4 MB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.entity_type_overrides | NEW | 58550 | 5.6 / 7.7 MB | norm_form | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.er_candidates | NEW | 38 | 0.1 / 0.1 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.er_split_candidates | DERIVED | n/a | 0.0 / 0.0 MB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.extract_policy | NEW | n/a | 0.0 / 0.0 MB | key | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.extract_queue | DERIVED | 5651501 | 0.775 / 1.264 GB | article_id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.extraction_log | DERIVED | 5708487 | 0.738 / 0.98 GB | article_id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.gazette_feed_state | DERIVED | 8 | 0.0 / 0.1 MB | family | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.gazetteer_blocklist | NEW | 928 | 0.2 / 0.3 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.guard_drops | DERIVED | 6143425 | 1.17 / 2.079 GB | id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.identity_refusals | NEW | n/a | 0.0 / 0.1 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.lexicon_entries | NEW | 3990 | 1.1 / 1.8 MB | list_name, form | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.mentions | DERIVED | 28572000 | 16.981 / 31.421 GB | article_id, entity_id | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.merge_refutations | NEW | 4486 | 9.1 / 9.2 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.mint_lane_state | DERIVED | 1 | 0.0 / 0.1 MB | k | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.mint_review | NEW | 1159075 | 0.494 / 0.571 GB | entity_id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.model_claims | DERIVED | n/a | 0.0 / 0.0 MB | none | the press graph: model readings of the articles (claims 1981 to 2026-11-02), and its build state |
| v3.reread_log | NEW | 1185 | 0.3 / 0.3 MB | entity_id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.review_decisions | NEW | 52 | 0.1 / 0.2 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.source_policy | NEW | 237 | 0.6 / 0.6 MB | outlet | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.watchlist_entities | NEW | 6 | 0.0 / 0.1 MB | watchlist_id, entity_id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
| v3.watchlists | NEW | 2 | 0.0 / 0.1 MB | id | decisions, verdicts, quarantines and policies of the old press graph: the cannot-be-regenerated class |
