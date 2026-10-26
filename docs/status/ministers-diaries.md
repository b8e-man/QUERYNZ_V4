# ministers-diaries: where it stands

**Date:** 2026-10-27, NZDT. **Session:** `fix-registers-ministers-diaries-1` (Opus), on diaries-2's lane.
**Step:** 6.2 template 4(a), `registers/ministers_diaries/`. **Merge request:**
`fix-registers-ministers-diaries-1` (branch `fix/registers-ministers-diaries-1`, carries diaries-2).

## Built (ruling 96: from the MCP's `parliament-diaries` corpus; nothing fetched, no model)

The lane whole (diaries-2), with ruling 102 applied: `pub.minister_diary_entries` carries the
meeting, attendees and location whole, as released; nothing withheld or masked in a view (the
release's own withholdings stay as printed). Beside them four flags, set at the load by shape:
`location_names_home`, `location_street_only`, `meeting_names_address`,
`attendees_names_address`; a product applies hard limit 15 at its own surface by them.
`pub.minister_diary_releases.locations_flagged` replaces `locations_held`. The private table keeps
only the provider's `text`. Tests 25, green; the sample tests proven to fail on a weakened flag.
The queue item `may-a-diary-entry-show-a-bare-street-address` is closed (ruling 102).

## The full build in scratch (from mcp-1's pull record `scratch_mcp_1_pull2`, 27 October)

Check green against the MCP: 208,464 records taken of 208,464; 230,554 documents = 208,464 entries +
22,090 older versions; `measure` n_docs 208,464, words 4,764,189 = 4,764,189. 2,560 releases, 78
minister names (one is "No Minister"). Withholdings kept: 2,126 entries, 6,824 fields. Flagged
(entries, counted, never printed): location_names_home 115, location_street_only 3,096,
meeting_names_address 32, attendees_names_address 11. 119 releases served a file name only; 52
have no single month; 30,803 entries before 2019. Against `pub.members` by title words only: 67 of
78 found. Full build 13 s.

## Next

1. Integrator: merge diaries-2 by this branch; `ministers_diaries` in support.db's LANES; append
   the profile; fold the position in; queue `qv4-ministers-diaries-load` (spec.md).
2. Board: the entries pane shows the three columns whole with a note per flag (pane.md).
3. Product (b), after links: who each minister met; it must drop or blank a flagged value.
