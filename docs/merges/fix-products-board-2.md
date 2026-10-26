# fix-products-board-2: the board catalogues the ministers' diaries and Parliament's records (carries integrate/diaries-parliament)
branch: fix/products-board-2 (pushed, 51d1ff5; carries integrate/diaries-parliament, c2deab8, not yet on main, and
fix-products-board-1i's board commit f43b5d1 cherry-picked as 5e3584f)
session: fix-products-board-2 (Opus, fix, scope products/board/)
raised: 2026-10-27
claims: products/board/ (catalogue.py, panes.py, spec.md; tests: new test_diaries_parliament.py, test_catalogue.py's
published list and its address test, test_hansard.py's order); lessons/carry-an-unlanded-board-branch-by-its-board-commit-not-its-integration-merge.md;
lessons/INDEX.md (regenerated); docs/status/board.md. No card opened or closed.

## Gate it with the two lanes, after hansard-2 and 1i

This branch goes through the gate with `integrate/diaries-parliament`. When that branch lands, five views have no
board entry, and the board's live check goes red. Gated as things stand, `tests/test_real.py` fails on exactly seven
lines: the five views (`pub.minister_diary_releases`, `pub.minister_diary_entries`,
`pub.parliament_written_questions`, `pub.parliament_api_items`, `pub.parliament_wayback_pages`) "in the catalogue but
not published", and `parliament` and `ministers_diaries` "none of its views is published". These are the views the
gate's staging load publishes. `hansard_days` is already on live.

The Beehive entries are on `integrate/fix-products-board-1i` and not on main. Merging that branch here conflicts in
`support/profiles/profiles.jsonl`, its test and `support/scheduler/jobs.toml`, which are outside this fence. So its
one board commit is cherry-picked (5e3584f, the same text as f43b5d1). If 1i lands first, the two merge cleanly. If you
would rather, rebase this branch onto main after 1i and drop 5e3584f.

## What it does

1. **The registers.** "Parliament: written questions, bills, papers and archived pages" just before Hansard, and
   "Ministers' diaries: who met the minister" just after the Beehive. Both are in the House's family, so no colour is
   added and the contrast tests are green. That makes 32 registers in 14 families. `ministers_diaries` leaves
   `NOT_HELD`. Main views: `parliament_written_questions`, `minister_diary_releases`.
2. **The release** (`minister_diary_releases`). Titled "Hon Chris Penk · 2026-06", or the minister and the file name
   where there is no month (one release in the build). The citation is the PDF's address, or "file name only: no
   address served" (119 of 2,560) with the hash beneath. Its counts follow, then its meetings by day and then the
   provider's row order. The times are text as released ("9:00 AM", "10:15"), so sorting by them would put 10:15
   before 9:00.
3. **The meeting** (`minister_diary_entries`). Titled day, time and meeting. Portfolio, meeting, attendees and
   location are shown whole, as released. A small note sits beside the cell where a flag is set, in pane.md's words.
   A withheld field shows the release's own words: no withheld field is blank in 208,464 rows. The release is its
   parent pointer. It is kind event, so it has no person pane, no `names`, no Relation and no edge. Location is not
   searched.
4. **The written question.** Titled as the API gives it. The pane shows number, year, Parliament, minister and their
   title, released, reply held, and Parliament's member id. The question and the reply are whole in their own text
   panes, each with the note where its `_names_address` flag is set. They never appear in a hit or the table. The
   citation is the hash, Parliament's document id (`WQ_<n>_<year>`) and "no page address: the API gives none".
5. **The API item.** Titled title and documentType. The pane shows corpus, documentType, bill number and stage,
   committee, member and party as served, the dates, the provider's capture block whole, and the text whole with its
   note. The citation is `citation_url`, or the hash with Parliament's record id.
6. **The archived page.** Titled the page's title and the copy's day. The citation gives the page's own address and
   the Archive's copy (`snapshot_url`). The pane shows the stamp, type, words, and the text whole with its note.
7. **On every Parliament row:** `served` false is struck through, "withdrawn by the source"; versions above 1 read
   "read from the version taken last, of N" (the diaries say the same). Every row of both registers says the estate
   did not fetch parliament.nz or the PDF (ruling 78).
8. **New View data, no new code path:** `flags`, `served`, `cite` and `no_url`. `columns_shown` reads all four.
9. **The graph.** One Relation: the written question's `member_id` to `pub.hansard_speeches.member_id`. Its kind is
   `role` ("asked by the member of these turns"); no other kind fits better, and adding one would be a new colour.
   There is no Relation from a name, no pointer to a person, and no edge from the diaries.
10. **Names (ruling 85), read from the build's rows.** All are given-family, with the honorific off the front:
    the diaries' `minister` (no comma in 2,560 releases), the question's `minister_name` (673,651 with "Hon", none
    with a comma) and the SOPs' `member_name` (no comma in 783).

`test_catalogue.test_no_pane_shows_a_person_s_address` now passes over a declared flag column. A flag is a yes or no,
never an address, and its name holds "address".

## Checks

- The real data, off live: both lanes were built into the sample with their own loads:
  `scratch_fix_products_board_2_diaries` (2,560 releases, 208,464 entries) and
  `scratch_fix_products_board_2_parliament` (683,524 questions, 6,752 API items, 4,839 pages), both from
  `scratch_mcp_1_pull2`. Their `publish.sql` was applied there as `<schema>.pub_<view>`. Every column the catalogue
  shows, searches, flags, cites or joins is present in all five. A pane was rendered for each, and the no-address
  line, a home-flag note, a question's flag note, document id and versions line were all seen on real rows. Search
  for "transport": 0.74 s on the written questions, 0.19 s on the entries, under 0.03 s on the rest. The table's
  first page and the graph's member-id read each took 0.00 to 0.03 s. Of the 300 asking member ids, 94 are in live
  `pub.hansard_speeches`. The proof scripts are in the session's scratch folder `proof/`. Both scratch schemas are
  regenerable and may be dropped.
- `python -m products.board check` against live: the seven lines above, nothing else.
- `pytest -m slow products/board/tests/test_real.py`: the same one test red on those seven lines; the rest green.
- `products/board/tests`: green. `test_diaries_parliament.py` has a fixture case per view. Three mutants were caught:
  flag notes off, strike off, and no-address line off.
- `QV4_INTEGRATOR=1 bin/fast products/board`: green in 47.1 s.

## For the integrator to note

- 10 of the 4,839 archived pages are the Internet Archive's copy of parliament.nz's "Unauthorized Request Blocked"
  page, held as `capture_status` ok. A challenged read is a failed read (hard limit 6), so the parliament lane should
  set these aside. The board shows them as published. This is not filed as a card (ruling 323's balance); file it if
  you agree.
- The written questions add about 0.7 s of scan to a search over every register (3 workers). `test_real`'s two-second
  search was not measured with them on live; it will be measured at the gate.

## At the merge

The integrator restarts `qv4-board` at the release, after the gate's staging load has published the five views. No
table, unit or job changes.

## Result (integrator, 27 October 12:41 NZDT)
Merged f049307, gate green at the first run, after the two lanes landed (a48633c, 12:10) as the gate-order lesson requires; the branch's merge with main conflicted on five board files because its copy of fix-products-board-1i was a cherry-pick, and the branch's side was taken (main had no other board change). At the merge the check's address-shaped rule was taught ruling 102: a boolean the view declares as a flag (`location_street_only`) is a flag, not an address column (check.address_shaped, three tests). Released; `qv4-board` restarted. The blocked archived pages went to a parliament fix (fix-registers-parliament-1c, at the gate next). Branches and the working copy retired.
