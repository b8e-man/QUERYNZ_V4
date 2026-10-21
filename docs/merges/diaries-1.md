# diaries-1: ministers' diaries, BLOCKED at capture (records only)
branch: session/diaries-1 (pushed; f4a429b)
session: diaries-1 (Opus)
raised: 2026-10-21
claims: records only. docs/status/ministers-diaries.md; cards `the-beehive-s-wall-refuses-the-diaries-reader` (blocker) and `the-headed-browser-has-no-home-in-the-new-estate` (finding); queue item `may-we-ask-the-beehive-to-let-the-diaries-reader-through`; lesson `a-refused-page-is-never-reloaded-only-the-wall-s-own-shell-is`

Step 6.2 template 4(a). Every diary release is on www.beehive.govt.nz, behind
an Incapsula wall. 21 October: plain requests got the wall's shell; a real
headed browser was served the home page, then refused (403) on its next two
pages. Seven requests, failed reads logged, run stopped (hard limit 6). No
diary is held, so no profile, reading, published view, check or sample.

The lane folder on the branch is INCOMPLETE (browser.py, tables.sql, a draft
position/): `support.lane.check_folder` will fail on it. Please merge the
records above and leave `registers/ministers_diaries/` as main has it, or
hold the whole request until the lane is resumed. Nothing to load, no job to
install. Generated files (board, queue roll-up, lessons index) not regenerated.
Fast tier: not run (no lane code to test beyond browser.py's pure parts).

## Result (integrator, 2026-10-21 23:18 NZDT)

Merged into main as 21a395c (`merge integrate/diaries-1: gate green`), records only. Branch `integrate/diaries-1` from `session/diaries-1` (f4a429b), main merged; the incomplete lane files (`browser.py`, `tables.sql`, the draft position) taken off the branch as the request asks, so `registers/ministers_diaries/` is as main has it (the README); they stay in the session branch's history until it is retired. Carried: `docs/status/ministers-diaries.md`, the blocker card `the-beehive-s-wall-refuses-the-diaries-reader`, the finding card `the-headed-browser-has-no-home-in-the-new-estate`, the finding card and the lesson. Ruling 78 (Arthur, 18:20: the Beehive and Hansard are not captured, he has a third-party source) closes the blocker card and the queue item `may-we-ask-the-beehive-to-let-the-diaries-reader-through` with no letter. The Beehive's wall refused the reader after one page (seven requests, failed reads logged, nothing got around: hard limit 6); diaries begin January 2019 by the Beehive's own announcement. Fast tier green in 489.2 s. Gate green, nothing to load. Arthur's: the third-party source's name and terms, for its position (ruling 61) before the register is built from it. Branches and the working copy retired.
