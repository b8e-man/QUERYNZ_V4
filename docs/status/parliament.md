# parliament: where it stands

Session parliament-1 (Opus), 27 October 2026, node2. Ruling 96. Merge
request `parliament-1`.

## Done

- `registers/parliament`: tables (`written_questions`, `api_items`,
  `wayback_pages`, `files`, `set_aside`; `parliament_private.wayback_texts`),
  read by hash from the version the pull landed last, `served` false for a
  record the MCP removed; three pub views; check per corpus against the MCP's
  `corpora` and `measure`; sample (16 documents); tests; fast tier green.
- Full build in `querynz_v4_sample.scratch_parliament_1_build` from
  `scratch_mcp_1_pull2` (50 s): 695,115 records from 1,115,731 documents
  (420,616 older versions), nothing set aside. Written questions 683,524,
  numbers unique per Parliament, 683,517 replied; words equal the MCP's
  `measure` to the word on six corpora.
- Check red on one count only: wayback 4,839 taken of the MCP's 5,415 (it
  grew since the last pull); green after the next `qv4-mcp-pull`.
- Position `registers/parliament/position/parliament.md` for
  docs/legal/positions/.

## Next

- The integrator: `parliament` in support.db LANES, the three profiles
  (`profile-proposed.jsonl`), the position, the job `qv4-parliament-load`.
- Queue item: publish the question and reply text (default no).
