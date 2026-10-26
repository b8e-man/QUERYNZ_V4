# ministers-diaries: where it stands

**Date:** 2026-10-27, NZDT. **Session:** `diaries-2` (Opus). **Step:** 6.2 template 4(a),
`registers/ministers_diaries/`. **Merge request:** `diaries-2` (branch `session/diaries-2`).

## Built (ruling 96: from the MCP's `parliament-diaries` corpus; nothing fetched, no model)

The lane whole: `tables.sql`, `capture.py` (the pull's arrivals), `read.py` (profile `mcp-diary-entry`
v1, by hash, the version the pull saw last), `load.py`, `publish.sql` (`pub.minister_diary_releases`,
`pub.minister_diary_entries`), `check.py`, `sample.list` (12 hard cases), `sample.py`, `pane.md`,
`tests/` (23, green; a sample test proven to fail on a weakened home rule), the proposed profile, and
`position/ministers-diaries.md` (the Beehive's page with the diaries' paragraph, for the integrator).

## The full build in scratch (from mcp-1's pull record `scratch_mcp_1_pull2`, 27 October)

Check green against the MCP: 208,464 records taken of 208,464; 230,554 documents = 208,464 entries +
22,090 older versions; `measure` n_docs 208,464, words 4,764,189 = 4,764,189. 2,560 releases, 78
minister names (one is "No Minister"); every release's entries counted. Withholdings kept: 2,126 entries,
6,824 fields. Locations held back: 3,211 (115 name a home, 3,096 a bare street address); 43 street
addresses masked in meetings or attendees. 119 releases served a file name only (no address made up);
52 have no single month. Entries run 1 October 2017 to 31 August 2026 (30,803 before 2019).
Against `pub.members` by title words only: 67 of 78 found; 11 not (four left before 2020, "No
Minister", six filed there in another form (a middle name; Kiri for Kiritapu); never matched by looking).

## Next

1. Integrator: `ministers_diaries` in support.db's LANES; append the profile; fold the position in;
   queue `qv4-ministers-diaries-load` (spec.md). The live `mcpsource` is empty until `qv4-mcp-adopt`
   runs, so the gate's staging load publishes nothing until then.
2. Arthur's: the queue item `may-a-diary-entry-show-a-bare-street-address` (default: held back).
3. Product (b), after links: who each minister met, resolved against the spine.
