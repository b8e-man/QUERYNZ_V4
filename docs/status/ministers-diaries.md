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

## The full build in scratch (27 October)

Check green against the MCP: 208,464 records, 2,560 releases, 78 minister names; flags counted, never printed.

## Attendees, one row each (2 November 2026, worktree agent branch for the integrator)

`attendees.py` splits each entry's attendees text by rules (no model) into `ministers_diaries.attendees`, published as
`pub.minister_diary_attendees` (entry, position, attendee as written, folded, kind, organisation part, `crown`, the
entry's four flags carried down). Full build in scratch (`querynz_v4_sample.scratch_diaries_attendees_build`, 36 s):
191,643 entries with a text, 191,597 split into 287,599 rows, 46 set aside (unbalanced brackets); 0 not reconciled.
Kinds: group 125,774, person 73,358, organisation 56,920, crown 22,593, role 7,055, withheld 1,899. Rows of
address-flagged entries 63, carried flagged. `read.WITHHELD` now also reads `s9(2)(a)`: entries with a withholding
2,126 → 2,166. Entries reaching a company's name: whole text 13,207; one attendee's organisation part 11,864, 5,631 of
them new. Scans `lobbying-attendees-suppliers` (31,969 lines) and `lobbying-attendees-donors` (118) start from the rows.

## Next

1. Integrator: merge diaries-2 by this branch; `ministers_diaries` in support.db's LANES; append
   the profile; fold the position in; queue `qv4-ministers-diaries-load` (spec.md).
2. Board: the entries pane shows the three columns whole with a note per flag (pane.md).
3. Product (b), after links: who each minister met; it must drop or blank a flagged value.
