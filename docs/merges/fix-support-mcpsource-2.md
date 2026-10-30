# fix-support-mcpsource-2: ruling 126's first part, the download step (every file a record points at, fetched through the MCP and landed by hash)
branch: fix/support-mcpsource-2 (pushed, 1c69bac; one commit on 2c44f95). The working copy is `fix-support-mcpsource-1`
(its local branch is `fix/support-mcpsource-1`; origin already held a `fix/support-mcpsource-1` from the earlier fix, so the
push went to `fix/support-mcpsource-2`).
session: fix-support-mcpsource-1 (Fable, fix, scope support/mcpsource/)
raised: 2026-10-30
claims: support/mcpsource/ (__init__.py, __main__.py, client.py, tables.sql, shapes.json, spec.md, README.md;
tests/fake.py, tests/test_mcpsource.py); lessons/check-delivered-bytes-against-the-record-s-promise-never-the-server-s-own-flag.md;
lessons/INDEX.md regenerated.
publish: nothing. tables.sql: one new table, `mcpsource.files` (CREATE IF NOT EXISTS; `Tables.create` applies it at the
job's next run, no separate DDL step). units: none changed; the spec's figure for `qv4-mcp-pull` rises from 0.3 GB to
0.5 GB (a file is held whole as base64 and bytes while its hash is checked), for the queued job to follow.

## What it does

1. **File pointers at landing.** A record whose `capture` block carries a sha256, that names a content type and has
   an http(s) `url` points at a file (`file_pointer`; today every record of the courts corpus: case pages, judgment
   PDFs, media releases; no other corpus names a content type). When the record lands, through the cursor, the change
   feed, a re-walk or a retry, the pointer goes to `mcpsource.files` (state `waiting`) in the page's transaction.
2. **The download step** (`download_files`, run by `pull_all` after the records and change feeds of every corpus, in
   what is left of `--budget-s`, so a short budget still lands the listings). Waiting pointers in order of place, one
   a request with the pull's pause between requests. A file whose hash the store already holds is landed again from
   disk under the record's url (a name added, no call: the courts lane's own judgments, and a changed record pointing
   at the same file). The rest are asked for with `download` (record_id, corpus, format `raw`), never the text
   resource; the answer's embedded resource is decoded and its sha256 compared with the record's: equal, it lands by
   hash, named by the record's `url`, source `query-nz`, the record's content type, the capture's fetch time;
   different, the bytes are refused, a catch line with stage `file`, the row marked `caught` and not asked for again
   (the tool is metered) until `--retry-caught`, which now takes file lines too. Each row commits on its own, so a
   run stopped by the budget or the server going away resumes at the first waiting row next night.
3. **The run's record.** The summary and the job's figures carry per corpus: files landed, held, caught, waiting,
   calls. Red when a file is caught; files left waiting on the budget are not red. `--no-files` skips the step.
4. **The client** gains `call(…, parts=True)` / `call_retrying(…, parts=True)`: the answer's content parts whole,
   for a tool that returns an embedded resource.
5. **shapes.json** gains the courts corpus, from the first 200 and the last 200 records on 30 October (fields: id,
   url, kind, fetched_at, http_status, sha256, path, bytes, content_type, case_slug, court, case_name, discovered_via,
   date, updated_at, capture, file, text; capture: url, fetched_at, http_status, sha256, path, bytes). The fake server
   makes courts records that promise the hash of a made file and serves `download` as the real tool does.

## Tests (support/mcpsource/tests/test_mcpsource.py)

- `test_a_file_whose_hash_is_the_record_s_lands_under_the_record_s_url_after_every_corpus_s_records` (hash match
  lands; the downloads come after the last records page of every corpus; a second night makes no call).
- `test_bytes_whose_hash_is_not_the_record_s_are_refused_and_caught_then_landed_on_a_retry` (mismatch caught, not
  re-asked nightly, landed by `--retry-caught`).
- `test_a_file_the_store_already_holds_is_named_from_disk_and_never_fetched` (held, no call; a changed record to
  the same file, no call).
- `test_a_run_stopped_by_its_budget_leaves_the_rest_waiting_and_the_next_resumes_there` (resume; each file asked
  once, in order).
- `test_a_file_lands_through_the_real_landing_wrapper_by_hash_under_the_record_s_url` (the real wrapper, kind pdf).
- `test_a_record_points_at_a_file_only_with_a_capture_hash_a_content_type_and_a_url`,
  `test_a_download_answer_is_its_meta_block_and_the_blob_and_a_textless_one_is_refused`; the shape test runs for
  the courts corpus too.
- Slow: `test_the_live_server_still_delivers_a_file_as_recorded` (one metered call: the meta block's keys, the
  resource's uri and mime type, the bytes equal to the record's hash).

## Verified

- `bin/fast support/mcpsource`: green, 39 tests, 87.2 s (target 60 s missed, recorded; 60.5 s of it the sample fill).
- Root `tests/` not slow: green (263).
- Slow, live through the tunnel: the shape test green for all twelve corpora (courts included) and the download
  test green (3.4 s). This session spent 30 `records`/`corpora` calls and 3 `download` calls on the live server.

## After the merge

- If `mcpsource.cursors` already holds a `courts` row when this merges (the 02:30 pull of 31 October takes the
  corpus's records under the old code, with no pointers), run once, on node2 in /home/user/querynzv4:
  `python -m support.mcpsource --rewalk --corpus courts` (25 calls; every record is found held and its pointer
  written), then the nightly pull fetches the files. Today the live record has no courts row (checked 30 October).
- The first full download run: the courts corpus holds 4,946 records today and every sampled record points at a
  file, so 25 `records` calls land the listings and up to 4,946 `download` calls fetch the files, less those the
  store already holds by hash (the courts lane holds 372 PDFs and 7 other documents from courtsofnz: at most 379
  held), so 4,567 to 4,946 download calls, about 1.5 GB. At 2 to 3 s a file plus the 1 s pause it is 2.5 to 4 h,
  against the 3.4 h left of the 12,600 s budget after the records: one night, or a few hundred files into the
  second. After that, one download call per new file a night.
- `courts-2` (the second part of ruling 126) reads the files by hash: `mcpsource.files` joined to `docs` on
  `capture_sha256`, state landed or held.

## Lesson

`lessons/check-delivered-bytes-against-the-record-s-promise-never-the-server-s-own-flag.md`.

## Known limits

- Pointers are written only when a record lands, so records landed before this version carry none until a re-walk
  (above). The `corpora` listing's new `has_files` flag is not used; the record is the judge.
- The budget for the records is still per corpus (`pull` measures its own), as before; only the files take what is
  left of the whole run's budget.
- A changed record whose file hash is unchanged costs no call; one whose file changed costs one.

## Result

Merged 30 October 2026, 13:07, as 00266ae (integrate branch 211ad7d; gate green, marked, every slow test since
support/ changed; nothing staged). A first gate at 12:38 was refused on two board live timing tests (the outside
check, the largest group's dossier at 2.45 s against the 2 s floor) while `qv4-links-build` (row 852, 12:04 to 12:33)
was loading the links tables; both passed from main once the build was done, and the gate was rerun unchanged. No
integrator commit on the way. Released after the push. Working copy `fix-support-mcpsource-1` and the local branches
retired; `fix/support-mcpsource-2` on the remote is Arthur's to delete.
