# parliament: where it stands

Sessions parliament-1 (Opus) and fix-registers-parliament-1 (Opus), 27
October 2026, node2. Rulings 96, 101, 102. Merge request
`fix-registers-parliament-1`, which carries parliament-1.

## Done

- `registers/parliament`: tables (`written_questions`, `api_items`,
  `wayback_pages`, `files`, `set_aside`, `address_flags`), read by hash from
  the version the pull landed last, `served` false for a record the MCP
  removed; three pub views; check per corpus against the MCP's `corpora`
  and `measure`; sample (16 documents); tests; fast tier green.
- Rulings 101, 102: the views carry the question, the reply, an API
  document's `text` and an archived page's text whole; nothing withheld.
  Beside each, `<column>_names_address` (the lane's own street, legal and
  numbered shapes, `shapes.py`), set at the load; `address_flags` lists the
  flagged rows by key. The private twin holds nothing now.
- The check states each flag's count and, by a second pattern in Postgres
  over every text column of each view, fails on a street address whose flag
  is false or absent. A planted one is caught in the tests.
- Full build in `querynz_v4_sample.scratch_parliament_1_build` from
  `scratch_mcp_1_pull2`: 695,115 records, nothing set aside. Flagged: 2,524
  of 683,524 written questions (1,988 questions, 699 replies), 59 of 4,839
  archived pages, 0 of 6,752 API documents; no unflagged street in any
  view. Written questions numbers unique, 683,517 replied.
- Check red on one count only: wayback 4,839 taken of the MCP's 5,532 (it
  grew since the last pull); green after the next `qv4-mcp-pull`.
- Position `registers/parliament/position/parliament.md` for
  docs/legal/positions/ (says the text is published with flags).

## Next

- The integrator: `parliament` in support.db LANES, the three profiles
  (`profile-proposed.jsonl`), the position, the job `qv4-parliament-load`,
  the three views' board entries in the merge after this one.
- The scratch build keeps a stale `scratch_parliament_1_build_private.
  wayback_texts` (the safety hook refuses a hand-typed DROP); regenerable.
