# offsite-2b: ranges for big tables, an order-free restore check, the bucket restore to equality, the step 1.8 dump retired
branch: session/offsite (pushed; faeda03, on top of offsite-2a and main at 2ccf80f)
session: offsite (session 2)
raised: 2026-10-20
claims: support/offsite/{copy,restore,__init__,__main__}.py, spec.md, tests; support/offsite/jobs/ removed; lessons `a-reloaded-table-does-not-read-back-in-load-order`; card `the-press-graph-leaves-the-old-nightly-push` updated; the patch `offsite-2b-retire-dump.patch` (support/scheduler/jobs.toml, tests/test_registry.py, spec.md)

**Merge the branch and apply the patch together**: the branch removes the
dump's code, so `qv4-offsite-dump` must leave the catalogue in the same
merge (`git apply offsite-2b-retire-dump.patch`; `registry.problems()` on
the patched catalogue: []; `qv4-offsite-copy` takes priority 14 back).

1. **The restore, from the bucket, to equality.** 19 October 19:40 to 21:30,
   **1 h 50 min** end to end: copy 20261019T193457, whose manifest draws on
   objects of four runs (the 07:45 full, the scheduled 10:33 nightly, and
   the hand nightlies at 18:56 and 19:34). 24.5 GB fetched through the
   read-only key in 41 min, overlapped with the load. extractions 75/75
   tables (469,790,356 rows), incoming_news 22/22, nzbn_canonical 137/137,
   querynz_v4 35/35; eight trees, 90,123/90,123 files. The vectors table is
   kept on the box only (by design); from the local copy, 20 October 03:05
   to 04:07, incoming_news restored 23/23 tables with the vectors (62 min).
   Both restored copies were removed after.
2. **The check is order-free.** The first local rehearsal loaded every
   object intact but 59 of 270 tables read back in another order: a table
   loaded by COPY does not read back in load order on PostgreSQL 18
   (reproduced on a plain fresh table; lesson filed). Now: each object's text
   has the sha256 recorded at the source (way in), and the table read back
   has the same row count and order-free sum of per-row BLAKE2b hashes (way
   out). No change to the copies.
3. **Tables over 1 GB as ranges of heap pages.** The scheduled nightlies
   sent incoming_news.articles whole (7 GB sealed) for a few thousand new
   rows a day. Such a table is now ~256 MB ranges by ctid (TID range scan);
   a night hashes each range and seals only changed ones. Trial on
   nzbn_canonical with lowered thresholds: one falsified range hash
   re-sealed 1 of 97 ranges; restored 137/137 equal from three stamps. The
   first ranged copy of the news backlog went to the bucket at 18:56 (8.3 GB,
   every range, as a first copy must) and is inside the restore in 1.
4. **One copy at a time per spool** (a lock), so the scheduler's run and a
   hand run cannot interleave; **downloads overlap the load**; a failed
   rehearsal keeps its server, log and downloads.
5. **The dump retired** (the condition the integrator set at 2a). Leftovers
   are regenerable: `querynz_v4/<stamp>/` in the bucket expires by its rule;
   `/mnt/hdd2/qv4-dumps` (14 files) can be removed at leisure.

Checked: fast tier for support/offsite green (20 tests); the real runs
above. Known to fail: nothing. Until this merges, the 21:00 job sends the
news backlog whole each night (about 8 GB); after it, the first night after
a whole copy sends every range once more, then only changed ranges.

Nothing new beyond the lesson.

## Result (integrator, 2026-10-20 05:00)

Merged into main as dc5dc74 (merged main first). The patch applied by
hand, hunk for hunk, since the hook cannot see what `git apply` writes:
`qv4-offsite-dump` is out of the catalogue, `qv4-offsite-copy` takes
priority 14, the registry test and the spec say so (the spec's jobs line
also keeps `qv4-read-pages`, added this morning). `registry.problems()`
empty; the worker reloads the catalogue itself. One red on the way, not
this request's: a party-returns test expected a return with no stored
page reading, and queue rows 110 and 111 had just read its pages; it now
reads from an empty store. The gate's party-returns reload then gave 137
rows and 15 set aside (99 and 53 before), published. Fast tier and gate
green. Leftovers for Arthur at leisure: `/mnt/hdd2/qv4-dumps` (14 files,
regenerable). Track B's brief is done; the next measurements are the
Sunday full on 25 October and the first 28-day rehearsal.
