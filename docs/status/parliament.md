# parliament: where it stands

Sessions parliament-1, fix-registers-parliament-1 (27, 28 October 2026),
parliament-2 (31 October, Fable, node2). Rulings 96, 101, 102, 123, 128;
ruling 130 (the common rules for the MCP names readers) pending. The
records lane is on main since 27 October; the text reader is on branch
`session/parliament-2`, merge request `parliament-2`.

## Done

- `registers/parliament`: `written_questions`, `api_items`,
  `wayback_pages`, `files`, `set_aside`, `address_flags`, `street_scan`;
  three pub views with the text whole and `<column>_names_address` beside
  it (ruling 102); the check per corpus against the MCP's `corpora` and
  `measure`; parliament.nz's archived refusals set aside as blocked.
- parliament-2: `model_read.py`, the text reader (Flash-Next, profile
  `text-reader`, temperature 0): every person and body an archived page
  or a written question and its reply names, kind, role, role_text, "of",
  one summary line; one reading per document hash; a page over the
  24,000-character budget read in pieces by the profile's split rule
  (speaker turn, else paragraph, else sentence) and joined; several
  questions of one year-and-number batch in one request, keyed back; an
  answer cut at the token cap salvaged; a missing document asked once
  more alone, then stored unusable. Profiles `mcp-parliament-wayback-page`
  and `mcp-parliament-written-question` at version 2 with the measured
  sizes, budget and split rule (`profile-proposed.jsonl`). The load
  replays the stored readings into `readings` and `people`;
  `pub.parliament_people`; the check counts read, waiting, set aside at
  read, names by kind and role, and fails on another profile version.
  `--pieces` and `--piece`; job `qv4-parliament-read` proposed in the
  merge request. Proven on the fixed sample read once (sample.list).
- Measured on live, 31 October: pages 21,989 (3,554 over the budget,
  35,579 requests, 11 the rule cannot split: binary files served as
  pages, set aside at read); questions 683,524 (1 over the budget,
  420,616 older versions never opened).

## Next

- The integrator: append the two profile lines; install
  `qv4-parliament-read`; enqueue `--pieces` (pages first, newest first,
  then the questions' batch leaders); the next `qv4-parliament-load`
  picks the readings up; catalogue `pub.parliament_people` on the board in
  the merge after.
- The papers (sc-submissions, sc-reports, bills, SOPs) wait on the
  provider's capture of their files: no reader.
- An archived page's older snapshot whose text differs is read as its own
  document (`files` status `older text`); none exist today.
