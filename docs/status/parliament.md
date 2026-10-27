# parliament: where it stands

Sessions parliament-1, fix-registers-parliament-1 (Opus), 27 October 2026,
node2. Rulings 96, 101, 102. On main since 12:10 (integrate/diaries-parliament).

## Done

- `registers/parliament`: `written_questions`, `api_items`, `wayback_pages`,
  `files`, `set_aside`, `address_flags`, read by hash from the version the
  pull landed last; three pub views carrying the text whole with
  `<column>_names_address` beside it (ruling 102); the check per corpus
  against the MCP's `corpora` and `measure`, and a second street pattern in
  Postgres over every text column of each view.
- Fix 1c (hard limit 6): an archived page that is parliament.nz's refusal
  ("Unauthorized Request Blocked", known by its title and its short fixed
  text) is set aside as `blocked`, not published; the document stays in the
  store. Full build: 10 of 4,839 set aside, 4,829 pages published. The
  check states `blocked` per corpus and counts it among the places held.
  The sample's refusal document (305c71…) and a real feature page are
  tested; the tests fail with the rule removed.
- Full build `querynz_v4_sample.scratch_fix_registers_parliament_1_build`
  from `scratch_mcp_1_pull2`: 695,105 records; flagged 2,524 written
  questions, 59 archived pages, 0 API documents; no unflagged street.

## Next

- Merge request `fix-registers-parliament-1c`: the nightly
  `qv4-parliament-load` (04:30 NZDT) carries it; nothing restarted.
- Check red on one count only: wayback 4,839 taken of the MCP's 6,181
  (it grew); clears at the next `qv4-mcp-pull` (02:30 NZDT).
- Scratch: drop `scratch_fix_registers_parliament_1_build` and the stale
  `scratch_parliament_1_build_private.wayback_texts` (regenerable).
