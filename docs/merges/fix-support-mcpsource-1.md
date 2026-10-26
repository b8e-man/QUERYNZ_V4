# fix-support-mcpsource-1: the adopt, bulk and resumable
branch: fix/support-mcpsource-1 (pushed, e671175)
session: fix-support-mcpsource-1 (Opus, fix weight)
raised: 2026-10-27
claims: support/mcpsource/ (adopt rewritten, Tables.create fix, tests/test_adopt.py, spec); one lesson; **a patch to support/docstore/landing.py and a new docstore test, outside the fence, for the integrator to apply**
note: written to the session's scratch folder: the permission check refused the write through the inbox link. The integrator copies it to the inbox.

## The patch the fence kept out (apply before the gate)

The brief put `support/docstore/landing.py` in this fix, but `.scope` names
only `support/mcpsource/` and the scope hook refused the edit. Following lesson
`a-brief-can-point-at-a-file-the-fence-keeps-out`, the change is a patch:

    /home/user/querynzv4-work/scratch/fix-support-mcpsource-1/docstore-copy_documents.patch

It adds `copy_documents(src, dst, shas, *, root, src_store, dst_store)` to
`landing.py`. Only that function is added and nothing else changes; the patch's
base is main's landing.py, byte for byte. It also adds a new
`support/docstore/tests/test_copy_documents.py`, which tests: the copy, the
held skip, a rerun copying nothing, bytes never read or rewritten, and missing
bytes not copied. Apply it with `git apply` in the main checkout at the merge.
**Without the patch, the branch's `test_adopt.py` fails**, because the adopt
calls `copy_documents`. I proved it on a merged copy (the working copy with the
patch applied):

- `QV4_INTEGRATOR=1 bin/fast support/mcpsource`: green in 60.8 s. The target is
  60 s, so it was recorded as a miss.
- `bin/fast support/docstore`: green in 44.8 s.
- `tests/test_imports_one_way.py`: green.

Nothing calls `names_for` in landing.py any more. I left it in place to keep
the edit minimal; the integrator may drop it.

## What changed

- **Bulk.** Each of the four pull tables streams `COPY … TO STDOUT` from the
  sample database into a temporary table on the live one, then runs
  `INSERT … ON CONFLICT DO NOTHING`. That is one transaction per table, over two
  connections.
- **Documents.** The adopt takes `DISTINCT sha256` from the source's arrivals,
  20,000 hashes a batch, in hash order. Each batch's `docs.documents` and
  `docs.names` rows are copied in one transaction. The path is set to the
  store's own place for the hash, and each new document gets a landing line.
  Hashes the live store already holds are skipped, and only their missing names
  are added. The bytes are only checked to exist; they are never read or hashed.
- **Resumable.** A table is copied only where the live one holds fewer rows.
  The "not empty" refusal is gone, and a rerun after a kill finishes the rest.
  The adopt takes the pull's advisory lock on the live schema.
- **Red.** The run ends with a count per table and per corpus, source against
  live, covering documents per corpus and names in total. It exits 1 on any
  difference, on a document without its bytes, or on one without a source row.
- **`Tables.create`.** It replaced `mcpsource.` and then `mcpsource_` in turn,
  so it mangled a schema name like `scratch_fix_support_mcpsource_1_…`. It now
  replaces in one pass.

## Measured (sample database, scratch to scratch)

The source was `scratch_mcp_1_pull2` with the sample `docs`; the target was
`scratch_fix_support_mcpsource_1_adopt` with `scratch_fix_support_mcpsource_1_store`.
The run covered all 1,411,057 documents and 1,672,861 arrivals and was killed
twice. The second kill was not planned: the session's 10-minute limit on a
background command stopped it.

| run | wall | what |
| --- | --- | --- |
| 1 (killed at 150 s) | 2:30 | four tables (arrivals 1,672,861 in 42 s), then documents |
| 2 (killed at 10 min) | ~10:00 | to 1,240,000 hashes; copies at about 2,000 a second |
| 3 | 2:15 | held skipped, 171,057 copied, **ok**: every count equal |

About **15 minutes** in all, against 18 hours before: about 2,000 documents a
second against 21. Peak memory was 169 MB in run 3 and 94 MB in run 1. Run 2
was killed before it could report its peak.

## For the integrator

1. Apply the patch, gate, merge.
2. Cancel run e87b5650 of the old adopt, then queue `qv4-mcp-adopt` again. The
   command is unchanged: `python -m support.mcpsource --adopt scratch_mcp_1_pull2`.
   Documents e87b5650 already landed are skipped as held, and tables that are
   already full are skipped.
3. **Catalogue**: `memory_gb = 0.5` (peak measured at 169 MB). The deadline can
   come down to 7200 s. My estimate is well under an hour live, but it was not
   measured there: the live database was not touched. `query_timeout_s = 3600`
   is ample; the longest statement, the arrivals copy, took 42 s.
4. Drop my two proof schemas in the sample database when convenient:
   `scratch_fix_support_mcpsource_1_adopt` and `scratch_fix_support_mcpsource_1_store`.
   They hold about 2 GB and can be regenerated. The safety hook stops a session
   from dropping them.

Lesson: `a-once-only-job-is-still-killed-so-it-must-resume`.

## Result (integrator, 27 October 11:20 NZDT)
Merged f36e940, gate green at the second run (the first was refused because the integrator had not yet applied the landing.py patch the fence kept out; applied with its test at aa47100). `qv4-mcp-adopt` in the catalogue at 0.5 GB and a 7,200 s deadline. Released; the worker restarted to reread the catalogue, which stopped the one-at-a-time run e87b5650 at 603,264 documents ("the lease was lost") and re-leased queue 591 as run 7d3f1d65 on the released code at 11:13:57: measured at 1,973 documents a second (783,609 to 823,067 in 20 s), so the 1.41 M land in minutes. The nightly loads (`qv4-beehive-load` 04:00, `qv4-hansard-load` 04:15) carry the MCP's records from tonight. Branches and the working copy retired. The sample-schema drops are handed to Arthur after the adopt is green.
