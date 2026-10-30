# beehive: where it stands

**Date:** 2026-10-31. **Session:** beehive-2 (Fable, scope `registers/beehive/`). **Merge request:** `beehive-2`.
Arthur, 31 October 08:40: ingest everything in the MCP; a pipeline that reads names and the other
important information from it.

## Done

- The lane (mcp-1, merged eb55a4d): every record of the MCP's beehive corpus, the site's ministers and
  portfolios, the provider's topics and quotes as the source's annotation; live, 66,588 releases.
- The text reader (beehive-2): profile `beehive-release-body` v1 first, recognised from the record's
  fields and measured on every live row (66,571 records; 66,461 with a body of 20+ words, 94 under,
  16 none; `profile-proposed.jsonl`). `model_read.py`: Flash-Next through `support.modelclient`,
  temperature 0, thinking off, one reading per document hash stored in the reader store with the
  model, the prompt's hash and the settings, replayed by every load and never remade; every person
  and body named with kind (person, company, agency, body, place), role, the role as the text says
  it, the organisation a person is of, and one summary line. Two attempts, then set aside at stage
  read with the reason as a stored reading (never a failed row, never asked again); a body under 20
  words set aside without a call. The site's tagged ministers are not re-read.
- The load replays: `beehive.people` → `pub.beehive_people` (the links lane reads it, ruling 123);
  `releases.reading`, `summary`, `names`, `read_model`. The check accounts for names read, documents
  read, waiting, set aside at read, not read (the old estate's 17 rows), and fails on a reading
  under another profile version than the load expects.
- The sample: 63 records of every type across 1995 to 2026 read once through the model (96 s wall,
  four abreast; a piece's median 4.8 s) and stored: 62 read, 644 names (body 171, place 155, person
  148, agency 139, company 31; of the persons: minister 55, mentioned 45, appointee 15, official 11),
  1 set aside (no body). Fast tier green, 46.6 s, 24 tests.
- `--pieces` on live: 66,399 releases waiting, newest first, in 0.6 s.

## Waiting

- The integrator: the profile line appended to the ledger; `qv4-beehive-read` in `jobs.toml` (the
  block is in the request; validated against the registry, priority 28 free); the pieces queued; the
  view catalogued on the board in the merge after.
- No live release has a reading until `qv4-beehive-read` runs; the night's load after picks them up.

## Next

1. After the first run: read ten releases' names and roles against the pages; the share of places
   and "mentioned" names (a quarter and a third of the sample's) may want a tighter prompt, a new
   profile version.
2. The links lane reads `pub.beehive_people` (its own session; a name is never a link here).
