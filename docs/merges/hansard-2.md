# hansard-2: the MCP's Hansard index and daily PDFs in the hansard lane (rulings 96, 97)
branch: session/hansard-2 (pushed; 49916fc)
session: hansard-2 (Opus)
raised: 2026-10-27
claims: registers/hansard/ (read_mcp.py new; capture, read, load, check, tables, publish, sample, pane, spec,
profile-proposed.jsonl, tests/test_hansard_mcp.py); cards/the-mcp-holds-no-pdf-for-an-urgency-sitting-s-later-days-and-its-hansard-index-names-no-transcript.md;
lessons/profile-a-corpus-s-addresses-before-joining-on-them-its-label-is-not-its-contents.md; docs/status/hansard.md
note: written to the session's scratch folder: the permission check refused the write through the inbox link
(merge-requests/ resolves outside the working copy). The integrator copies it to the inbox.

Arthur, ruling 96: "ingest the hansard records we currently have and add the fields from the MCP and use the MCP for
updates". The lane now reads the two corpora support/mcpsource lands, by hash, each record from the version the pull
saw last. No model, nothing fetched.

## The four tranches

1. **The index joined.** `index_pages` from `parliament-hansard-index`; `pub.hansard_sittings` carries the page's
   lastmod, fetched and date where the url matches, and "the held text may be older than the page" where lastmod is
   after the old capture (`sittings.captured_at`, new). **It matches 0 of 137**: the corpus's 383 records are all
   www.parliament.nz pages (select committees 293, order paper 54, Hansard information pages 28, bills 8), never a
   hansard.parliament.nz transcript. Carded for the provider.
2. **The days.** `days`, one per debates record (1,862 sitting days, 2003-02-11 to 2026-09-23): the PDF's address and
   the provider's hash, capture, pages, words, versions; the text in `hansard_private.day_texts`.
   `pub.hansard_days` (no text; the board opens the landed record, ruling 88). Both views say where a day is also
   held: 137 both, 1,725 MCP only (1,724 before 20 November 2024, and 2026-07-30), 0 old days missing.
3. **check.py**: each corpus's cursor against `corpora` (99% floor), every document read, older or set aside;
   `measure`'s n_docs and words (94,602,760 held and served, equal); every `word_count` equal to its text's; on the
   137 days both hold, old subjects found in the same day's PDF text 3,691 of 3,885 (95.0%), worst day 57.1%,
   floors 90% and 50% a day, justified in the docstring by buckets (35 continuation notes left out; 41 in a
   neighbouring day's PDF; 119 of the other 153 on eight urgency sittings whose later calendar days the MCP lacks;
   a wrong-day mutation gives 37.6%). Under the reader it reads no private table; `--owner` recounts from the texts
   (3,691, equal).
4. **spec.md**: updates come from the MCP; `qv4-hansard-load` proposed; speech turns after 23 September 2026 wait on
   a section and speaker split the provider has not made.

## Proof

- Whole build into `querynz_v4_sample.scratch_hansard_2_full` from `scratch_mcp_1_pull2`, 15 s, nothing set aside.
- `check.py --database querynz_v4_sample --schema scratch_hansard_2_full --mcp-schema scratch_mcp_1_pull2`: red only
  for the index, 383 of the MCP's 387 records taken (four arrived after mcp-1's pull; the nightly pull takes them).
- Fast tier `registers/hansard` green (33 tests, 136 s; 46 s of it the 36-module sample fill). Root tests green
  before the lesson was added; `tests/test_generators.py` will want the lessons index regenerated.
- Mutation: the subject search cut short turns `test_each_day_is_one_row…` red.

## For you at the merge

1. Append the two lines of `registers/hansard/profile-proposed.jsonl` after `hansard-export`:
   `mcp-hansard-index-record` v1, `mcp-hansard-debates-record` v1 (the count test moves by two).
2. `hansard_private` now holds `day_texts`: keep it out of the session reader's grants (`support/db`).
3. **Queue** `qv4-hansard-load`: processor, 1 GB, nightly 04:15 NZDT (after `qv4-mcp-pull` 02:30, beside
   `qv4-beehive-load` 04:00), `python -m registers.hansard.load`, deadline 30 min, query time limit 600 s. Its first
   run after `qv4-mcp-adopt` carries the MCP's records; before the adopt it loads the old export alone, as now.
4. `pub.hansard_days` goes on the board in the merge after this one (gate-order lesson).
5. The position `docs/legal/positions/hansard.md` predates the debates corpus: it wants a line that the daily PDFs
   were captured and read off-estate by the provider (ruling 78), before any product shows them (ruling 61).
6. Regenerate the lessons index and the card board.
7. Arthur's to drop when done: `querynz_v4_sample.scratch_hansard_2_full` (+ `_private`).

Lesson: profile-a-corpus-s-addresses-before-joining-on-them-its-label-is-not-its-contents.

## Result (integrator, 27 October 10:20 NZDT)
Merged 3063cc7 inside `integrate/fix-products-board-1i` (the board fix carrying this branch), gate green at the third run. The first run was refused by the board's live check: `pub.hansard_days` was catalogued but not yet published, the gate testing before it loads (the lesson `a-lane-s-new-view-is-catalogued-on-the-board-in-the-merge-after-the-lane-s`, which this integration folded into one gate against its rule); the integrator ran the branch's staging load by hand first, publishing the view, and gated again. The second run was refused by the live-shape test on `parliament-wayback` (six fields inside `capture`), which the server no longer served ten minutes later: a transient reshape at the provider, not drift; the third run was green. Done at the merge: the two profiles (`mcp-hansard-index-record`, `mcp-hansard-debates-record`, count 142), `hansard.parliament.nz` and `parliament.nz` held in the fetch gate, the PDF paragraph in docs/legal/positions/hansard.md, `qv4-hansard-load` nightly 04:15 NZDT (priority 86). The staging load published 1,862 days from 1,862 daily PDFs (383 index pages, 0 set aside). Released; `qv4-board` restarted. Branches and the working copy retired. For the provider: the index holds no transcript or PDF addresses; urgency sittings' later-day PDFs are missing.
