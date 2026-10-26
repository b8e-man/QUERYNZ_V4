# mcp-1: the ingest MCP as a source (support/mcpsource) and the Beehive lane (registers/beehive)
branch: session/mcp-1 (pushed)
session: mcp-1 (Opus)
raised: 2026-10-26
claims: support/mcpsource/ (new module), registers/beehive/ (new lane), two lessons, one queue item, docs/status/beehive.md
note: written to the session's scratch folder: the permission check refused the write through the inbox link (merge-requests/ resolves outside the working copy). The integrator copies it to the inbox.

Ruling 96. Every record of every corpus of `query-nz-ingest` landed whole as
a document (its JSON, keys sorted, no spaces, without `seq`; source
`query-nz`; names `<corpus>/<id>` and the record's url); a record the MCP
serves changed lands as a second document. The Beehive lane reads them by
hash, with the old estate's Beehive pages (exported once) where the MCP has
not read a page. No model, nothing fetched from beehive.govt.nz.

## What the first pull landed (sample database, `scratch_mcp_1_pull2`)

Records taken / documents, 26 October 19:00 to 23:12, nothing caught, no
field outside the recorded shapes:

| corpus | records | documents |
| --- | --- | --- |
| beehive | 48,212 | 51,928 (3,716 re-read by the provider since, from the change feed) |
| parliament-written-questions | 683,770 | 683,770 |
| parliament-diaries | 208,464 | 208,464 (was 5,000 at the survey) |
| parliament-wayback | 3,425 | 3,425 |
| parliament-hansard-debates | 1,221 | 1,221 (a seventh corpus, new at 20:23) |
| parliament-hansard-index | 377 | 377 |
| parliament-bills | 92 | 92 |

(first pull; seven corpora then. Eleven by the second run.)

The bytes are in the store (`/mnt/hdd2/qv4-docs`, about 1.6 GB); the rows
are in the sample database only (the owner login on the live database is
fenced from sessions). About 1.2 GB of table rows; the server-wide
write-ahead log grew 23.5 GB from 19:00 to 21:16, of which this pull is a
part that cannot be told apart from the server's other work.

## What the source did during the session (for parliament-1, diaries-2, hansard-2)

- The provider redeployed twice (18:52 to 18:57, and about 20:23), and was
  down again from 23:13. The first redeploy reshaped every record (a
  `capture` block, an `annotation` block naming the model-made fields, an
  `updated_at`); the 4,000 beehive records landed before it stay in the store
  under `scratch_mcp_1_pull` (never deleted) and nothing reads them. The
  second added `parliament-hansard-debates`, capture blocks on bills, diaries
  and the Hansard index, and a change feed tool `changes`, which the pull now
  follows after the cursor (`cursors.changes_since`).
- 26,881 beehive records are captures the provider has not yet read (the
  page's whole text, no title, date, ministers or body); they fill in as the
  provider reads them, through the change feed.
- The provider's model, named on each record: `deepseek/deepseek-v4-flash`
  mostly, `z-ai/glm-5.3-flash` and `deepseek/deepseek-v4.1-flash` on a few.

## For the integrator

1. **Schemas**: `mcpsource` (support module, not a lane: add it to
   `support/db` FIXED or as its own entry, readable by the session reader),
   `beehive` and `beehive_private` (lane list). Apply on both databases.
2. **Profiles**: append `registers/beehive/profile-proposed.jsonl`
   (`mcp-beehive-record` v1). The old export's profile
   `beehive-old-estate-export` v1 is named in `read.py` and wants a line too
   (one JSON line per old article: url, title, text, author, posted_nz,
   scraped, fetched; "original not held").
3. **Position**: move `registers/beehive/position/beehive.md` to
   `docs/legal/positions/beehive.md` (hosts: beehive.govt.nz).
4. **Jobs** (none queued by this session):
   - `qv4-mcp-adopt`, once, before the first nightly pull:
     `python -m support.mcpsource --adopt scratch_mcp_1_pull2` (re-lands about
     950,000 documents into the live `docs` from the store and copies the
     cursors, arrivals and stamps; no request to the MCP; long, so a job).
   - `qv4-mcp-pull`: processor, 0.3 GB, nightly 02:30 NZDT,
     `python -m support.mcpsource --budget-s 12600`, deadline 4 h (interval 24 h), query time
     limit 60 s, call limit 180 s; red on a failed corpus, a caught record or a
     new field; follows the change feed after the cursor.
   - `qv4-mcp-rewalk`: processor, 0.3 GB, weekly Sunday 01:00 NZDT,
     `python -m support.mcpsource --rewalk --budget-s 12600`, deadline 4 h,
     query time limit 60 s; resumes where the last stopped; also the fix when
     the pull reports the MCP counting fewer records than taken.
   - `qv4-beehive-load`: processor, 1 GB, nightly 04:00 NZDT after the pull,
     `python -m registers.beehive.load`, deadline 30 min, query time limit
     600 s (13 s for the full build in scratch).
5. **The queue item** `the-mcp-first-pull-is-a-bulk-load-before-the-election`
   (default: the adopt goes ahead).
6. **Sample database wart**: 200 `docs.documents` rows of source `query-nz`
   (written questions seq 500,000 to 500,199) carry a temporary-folder `path`
   from a profiling run of mine; reads go by hash to the store, so nothing
   breaks, and the adopt lands them with the right path. Arrivals mark those
   200 `new = false`.
7. Arthur's to drop in the sample database: `scratch_mcp_1_pull` (old-shape
   4,000), `scratch_mcp_1_beehive`, `scratch_test_mcpsource`; keep
   `scratch_mcp_1_pull2` until the adopt has run.
8. The board views `pub.beehive_releases`, `pub.beehive_release_ministers`,
   `pub.beehive_release_annotations` go on the board in the merge after this
   one (gate-order lesson). The annotations view is the source's model output
   and must never feed links.

## Where the pull stands at the close (27 October 05:30)

Last run green: nothing caught, no drift, cursors held where nothing
arrived; the change feed now asks strictly after its stamp (3 calls where a
one-second margin re-served 203,464 diary records sharing one stamp).

| corpus | records | documents |
| --- | --- | --- |
| parliament-written-questions | 683,524 | 1,104,140 (about 420,000 re-rendered `text`, `updated_at` unmoved, found by the re-walk) |
| parliament-diaries | 208,464 | 230,554 (22,090 re-read, from the change feed) |
| beehive | 52,273 | 62,527 |
| parliament-wayback | 4,839 | 4,839 |
| parliament-bills-historical | 3,542 | 3,542 |
| parliament-hansard-debates | 1,862 | 1,862 |
| parliament-sc-submissions | 1,335 | 1,335 |
| parliament-sc-reports | 1,000 | 1,000 |
| parliament-sops | 783 | 783 |
| parliament-hansard-index | 383 | 383 |
| parliament-bills | 92 | 92 |
| all eleven | 958,097 | 1,411,057 |

**For every lane over these documents**: a record's current version is the
document the pull saw last (`mcpsource.arrivals` by `landed_at`), never the
highest `seq`: after the removal, re-rendered written questions came back 246
places lower than their first versions. `registers/beehive` does this; its
check over the rebuild is green (52,273 taken of 52,652, n_docs 52,652, words
36,920,785 against 36,753,716).

## Checks

- Fast tier: `registers/beehive` green, `support/mcpsource` green (44 s each).
  The live shape test (slow) green on all seven corpora.
- `registers.beehive.check` on the scratch build (before the provider's
  second redeploy): green; taken 47,059 of 47,089, `measure` n_docs 47,089,
  words 38,169,497 against its 38,122,105.
- Failures on real data during the build: the made-by test caught the
  generator added to `made_by`; the old export read 55,344 of 55,358 lines
  while saying none was set aside (U+2028; lesson filed); the same character
  cut a `data:` line in the client's event stream; a cut-off answer
  (`IncompleteRead`) escaped the retry; all fixed with tests.

Lessons: `split-a-json-lines-file-on-newline-never-splitlines`,
`a-third-party-server-can-reshape-every-record-in-a-redeploy`.

## Second run (26 October 23:43 to 27 October 00:27, after the server returned)

Cursors held where nothing had arrived (bills, diaries, written questions);
the rest took only their arrivals: beehive 1,226, hansard debates 641,
wayback 444, hansard index 1. The change feed landed 1,227 beehive and 22,090
diary records the provider re-read in place (second documents), and found
the rest unchanged. Red for the right reason: four corpora new since 23:13
(`parliament-bills-historical` 3,542, `parliament-sc-reports` 1,000,
`parliament-sc-submissions` 1,335, `parliament-sops` 783) landed whole with no
recorded shape; their shapes are now recorded, for `parliament-1`.

**The MCP counts 683,524 written questions, 246 fewer than the 683,770
taken.** It removed records, so every later place moved and a cursor would
pass over the next arrivals. The pull now goes red on this and names it; the
re-walk (`--rewalk`) lands what the MCP still serves (found held) and brings
the cursor back to its count. Re-walk result (27 October 02:30 to 04:50,
resumable since its first try ran out of time): all 683,524 walked, the cursor
reset 683,770 to 683,524; 665,905 found held; **17,619 landed changed: the
same records 246 places earlier, only their `text` different, and `updated_at`
not moved**, so the MCP's change feed cannot show them. Hence the weekly
re-walk job below.

Beehive check over the second run: green. Taken 49,438 of the MCP's 49,866
(99.1%, the rest arrived within the hour), `measure` n_docs 49,866, words
37,440,748 against its 37,408,103. Lane: 56,210 releases (49,438 MCP records,
26,880 of them captured and not yet read by the provider, 26,696 of those
read from the old estate's page; 6,772 old-estate-only pages), 4,943 older
versions, 109,439 topics, 91,516 quotes, nothing set aside. Only 52 releases
carry a tagged minister: the provider's read records are mostly 1999 to 2008.

## Result (integrator, 27 October 08:00 NZDT)
Merged 7eacf7c, gate green at the second run (the first was refused by tests/test_imports_one_way.py: the new `mcpsource` schema had no owner there, and the adopt queried docs.* directly; the query now lives in support.docstore.landing as `names_for` and mcpsource calls it). Done at the merge: `beehive` in support.db's LANES and `mcpsource` in FIXED, applied on both databases (88 schemas); the two profiles appended (`mcp-beehive-record` v1 from the session; `beehive-old-estate-export` v1 written by the integrator from read.py's OLD_PROFILE and capture.py's pinned export), the count test at 140; the position moved to docs/legal/positions/beehive.md; four jobs in the catalogue (`qv4-mcp-adopt` once, priority 99; `qv4-mcp-pull` nightly 02:30 NZDT, 100; `qv4-mcp-rewalk` every seven days, 101; `qv4-beehive-load` nightly 04:00 NZDT, 85), catalogue check green. The gate's staging load published the lane from the old export alone (55,358 releases, 0 MCP documents) because the live docs hold nothing until the adopt runs: `qv4-mcp-adopt` queued at 08:00; the first nightly load after it carries the MCP's records. Released. The queue item on the bulk load stands on its default. Sample-schema drops are Arthur's, handed after the adopt. parliament-1, diaries-2 and hansard-2 launched. Branches and the working copy retired.
