# fix-registers-parliament-1: the parliament views carry the text whole, with address flags (rulings 101, 102)
branch: fix/registers-parliament-1 (pushed, 8141d78)
session: fix-registers-parliament-1 (Opus, fix weight)
raised: 2026-10-27
carries: parliament-1 (session/parliament-1 merged in at 9c77a23; not yet on main)
claims: registers/parliament/, one lesson, docs/status/parliament.md; deletes one queue item
note: written to the session's scratch folder because the fence refused the inbox link; move it to
inbox/merge-requests/fix-registers-parliament-1.md

Merge this branch **instead of** `session/parliament-1`: it carries all of
parliament-1, plus this fix. Mark `parliament-1.md` superseded by this
request; gating both would load the lane twice.

## What changed

- `pub.parliament_written_questions` now carries `question_text` and
  `reply_text` whole; `pub.parliament_api_items` carries `text` (the API
  document's own run of its fields); `pub.parliament_wayback_pages` carries
  the archived page's `text`. Nothing is withheld in a view (ruling 102
  withdrew 101's withholding).
- Beside each of those four columns, `<column>_names_address`: true where
  the value's shape names an address by the lane's own street, legal and
  numbered shapes (`registers/parliament/shapes.py`, its own patterns and
  tests; it imports nothing from registers/gazette). Set at the load. A
  product applies hard limit 15 at its surface by this flag; the board
  shows the text whole.
- `parliament.address_flags` (table, key, column, shape): the load's report
  of the flagged rows by key; the load's log counts them by column.
- The archived page text moved out of `parliament_private.wayback_texts`
  into `parliament.wayback_pages.text`; the private twin now holds nothing.
- `check.py` states each flag's count (and that it equals `address_flags`)
  and fails where any text or jsonb column of a view, found through
  information_schema, holds a street address by a second pattern written in
  Postgres's own regex, with its flag false or absent. A planted fault (a
  street put in one question with its flag false, rolled back) is caught by
  the tests.

## Proof (full scratch build `querynz_v4_sample.scratch_parliament_1_build` from `scratch_mcp_1_pull2`, rebuilt, 79 s)

| view | rows | flagged |
| --- | --- | --- |
| written questions | 683,524 | 2,524 rows: question 1,988, reply 699 |
| API documents | 6,752 | 0 |
| archived pages | 4,839 | 59 |

Street address with its flag false or with no flag, any text column, any
view: 0. The check's view pass takes about 2 minutes on the full build (its
time limit is 300 s). The check is red on the one count parliament-1
reported: wayback 4,839 taken of the MCP's 5,532 now; green after the next
`qv4-mcp-pull`. Flagged rows were counted, never printed.

Fast tier: `QV4_INTEGRATOR=1 bin/fast registers/parliament` green (46
tests, 49 s), no skips.

## What the integrator does at the merge

1. Gate and merge this branch; mark `parliament-1` superseded.
2. Everything parliament-1's request asked (`parliament` in support.db
   LANES, the three profiles from `profile-proposed.jsonl`, the position
   into docs/legal/positions/, the job `qv4-parliament-load`). The position
   now says the text is published with flags.
3. Grant nothing new: the views read only the `parliament` schema; nothing
   in `parliament_private` is created any more.
4. The board's catalogue entries for the three views in the merge after
   this one (lesson
   `a-lane-s-new-view-is-catalogued-on-the-board-in-the-merge-after-the-lane-s`);
   they show the text whole and may show the flag.
5. Rebuild the queue roll-up: the item
   `publish-the-written-questions-question-and-reply-text` is deleted here
   (closed by rulings 101 and 102). Rebuild the lessons index.

## Lesson

`lessons/a-borrowed-address-shape-is-re-measured-on-the-new-lane-s-text-before-it-flags.md`:
the Gazette's shapes, copied as they were, would flag "at 5 schools", "Alert
Level 4" and years in parliamentary text; this lane's copy needs a
capitalised name after a numbered shape's number and refuses a year.

## Left

The scratch build keeps a stale `scratch_parliament_1_build_private.wayback_texts`
(the safety hook refuses a hand-typed DROP); regenerable, scratch only.

## Result (integrator, 27 October 12:10 NZDT)
Merged a48633c as `integrate/diaries-parliament` (diaries-2 with fix-registers-ministers-diaries-1, parliament-1 with fix-registers-parliament-1), gate green at the second run, 27 October 12:10 NZDT. The first run passed every test and failed in the staging load: the staging schema's name was cut at Postgres's 63 bytes, so `<schema>_private` was cut back to the public schema's name and the diaries' two `entries` tables collided; support/staging now leaves room for the suffix (a3dd295, with tests). Done at the merge: `ministers_diaries` and `parliament` in support.db's LANES (92 schemas applied on both databases); four profiles appended (`mcp-diary-entry`, `mcp-parliament-written-question`, `mcp-parliament-api-item`, `mcp-parliament-wayback-page`; count 146 with hansard-2's two); the diaries paragraph folded into docs/legal/positions/beehive.md and the parliament position moved to docs/legal/positions/parliament.md; `qv4-ministers-diaries-load` nightly 04:20 NZDT (priority 87) and `qv4-parliament-load` nightly 04:30 NZDT (88); the two deleted queue items gone from the roll-up. Released; the worker restarted for the two jobs. The staging load built both lanes from the adopted live documents (the fast adopt finished 11:20): diaries 2,560 releases, 208,464 entries (22,090 older versions, 2,126 entries with a withholding, 3,096 locations street-only, 115 naming a home, 0 set aside); parliament 695,115 rows in 69 s. Their five views go on the board in the next gate (fix-products-board-2, raised). Branches and the working copies retired. The blocked-page finding is recorded on parliament-1.md's result.
