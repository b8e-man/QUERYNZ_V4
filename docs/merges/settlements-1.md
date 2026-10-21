# settlements-1: the two template 3 lanes: the iwi and hapū directory captured and built; the settlement commitments behind a login, watched
branch: session/settlements-1 (pushed)
session: settlements-1 (Opus)
raised: 2026-10-22
claims: registers/iwi_directory/ (capture, read, load, check, tables.sql, publish.sql, sample, sample.list, spec, README, pane, profiles-proposed.jsonl, position/, tests), registers/settlement_commitments/ (the same pieces; publishes nothing); docs/status/settlements.md; cards the-settlement-commitments-are-not-held (finding), the-settlements-lanes-schemas-positions-profiles-and-jobs-into-place (blocker, for this merge); queue whether-te-kahui-mangai-is-cc-by (default applied), whether-to-ask-for-the-settlement-commitments (no default for an account; not held meanwhile); one lesson

## What each lane is

- **Te Kāhui Māngai** (`registers/iwi_directory`; `pub.iwi_directory_entities`, `_relations`, `_settlements`). Te Puni
  Kōkiri's directory walked whole from its home page (13 region maps, 117 iwi, 92 authority lists, other
  organisations, non-tribal marae, site pages: about 240 pages), each page once a week, landed by hash, recognised
  by shape under five profiles. Read: iwi (region, rohe's local authorities), hapū and marae from each iwi's tables
  (a blank hapū cell is the row above's; a marae is one row across the site by name and location), organisations
  under their heading with six allowlisted labels and every role flag as printed; a post-settlement flag makes a
  governance entity and names its settlement (Act and year, a deed signed, the CNI collective; a mandate is a stage,
  not a settlement). Every other label (chair, CEO, RMA contact, phone, mobile, email, postal and physical address)
  is counted by its name and never read (hard limit 15). Charity number and NZBN only where printed (none in the
  sample). Proved on 36 real pages: 10 iwi, 301 hapū, 440 marae, 31 organisations (8 governance entities), 10
  settlement flags, 1,079 relations; 26 tests, 10 mutants; a test that every email and phone run on the real pages
  is absent from every row; a test that the position's cited hashes and quotes are on their pages.
- **Te Haeata** (`registers/settlement_commitments`). Every records address answers with the login page: hard
  limit 6, a failed read, no account made. Te Tari Whakatau's settlement pages are open but its terms bar "any data
  collection activities": not captured beyond the survey. So the lane is a weekly watch of the wall (red the day it
  falls) and the open pages about the source every 30 days; `load.py` keeps the staging contract and loads nothing.
  8 tests. The settlement each governance entity names is in the iwi directory's views.

No model (ruling 79). About 60 requests in all through the gate, 5 s apart, daytime survey and two small live proofs
(the walk's first 3 pages, already held; the watch's 5); no block, no challenge.

## For the integrator (nothing else)

1. Add `iwi_directory` and `settlement_commitments` to `support/db` `LANES` (neither has a private twin).
2. Move `registers/iwi_directory/position/iwi-and-hapu-directory.md` and
   `registers/settlement_commitments/position/treaty-settlement-commitments.md` to `docs/legal/positions/`.
   (`catalogue.data.govt.nz` is named by the TKM page and by `government-procurement-award-notices`; the gate takes
   the later file's name for it, which permits either way.)
3. Append the five lines of `registers/iwi_directory/profiles-proposed.jsonl` and the one of
   `registers/settlement_commitments/profiles-proposed.jsonl` to `support/profiles/profiles.jsonl` (version 1 each);
   remove the proposed files.
4. Gate floors 5 s for `www.tkm.govt.nz` and `tehaeata.govt.nz`. Do not floor or name anything new for
   `www.whakatau.govt.nz`: no job asks it (its position names it so the record of the survey reads).
5. Three jobs as each spec.md proposes: `qv4-iwi-directory-capture` (weekly, Sunday 22:30 NZDT, budget 2 h, deadline
   3 h), `qv4-iwi-directory-load` (Monday 06:35 NZDT, deadline 15 min), `qv4-settlement-commitments-watch` (weekly,
   Sunday 23:15 NZDT, deadline 15 min). No load job for settlement_commitments.
6. The three `pub.iwi_directory_*` views go on the board in the merge after this one (lesson
   `a-lane-s-new-view-is-catalogued-on-the-board-in-the-merge-after-the-lane-s`).
7. Regenerate `docs/decisions/queue.md`, the card board and the lessons index (the new queue items, cards and
   lesson make the committed generated files stale).

Staging: no finished walk is held, so `iwi_directory`'s tables are made empty and published; the Sunday walk fills
them. Checks: `iwi_directory` red (no finished walk) until then, correctly; `settlement_commitments` red until the
first watch.

## Fast tier

Lane folders green (41 s each with the fill). Whole repository: RED in 598.9 s, only on `tests/test_generators.py` (`docs/board.md` stale: blockers open 7 → 8 from the new blocker card; the queue and lessons index likewise), which step 7 above clears. Target 300 s missed (recorded).

## Result (integrator, 22 October 2026 09:05 NZDT)

Merged into main as b5cde3a (`merge integrate/settlements-1: gate green`). Branch `integrate/settlements-1` from `session/settlements-1` (8d414e1), main merged, the integrator's commit e97bcaa. Card `the-settlements-lanes-schemas-positions-profiles-and-jobs-into-place`, now closed: `iwi_directory` and `settlement_commitments` in the lane list, schemas applied on both databases; the two positions moved to `docs/legal/positions/` (`iwi-and-hapu-directory.md`, `treaty-settlement-commitments.md`), both lanes' position tests repointed at them; the six profiles appended as version 1 (126 slugs), the proposed files removed; the gate floors `www.tkm.govt.nz` and `tehaeata.govt.nz` at 5 s, nothing for `www.whakatau.govt.nz`; three jobs in the catalogue, `support.scheduler check` green (67 job types). The catalogue has no weekday field, so the timetable differs from the specs by design: `qv4-iwi-directory-capture` (priority 71, budget 2 h, deadline 3 h) is due daily at 22:30 NZDT and the capture's own week guard and 22:00 to 06:00 window make it a weekly off-peak walk (a day not due costs no request); `qv4-iwi-directory-load` (72, deadline 15 min) is daily at 06:35 NZDT and loads nothing when the walk is the one published; `qv4-settlement-commitments-watch` (73, deadline 15 min) is weekly by interval, which the scheduler's clock lands on Thursday 13:00 NZDT, one request. The worker re-reads the catalogue on its own clock. Gate: `iwi_directory` published empty from staging (the first walk fills it); `settlement_commitments` published nothing (no record held, hard limit 6). Fast tier green in 595 s (target 300 s missed, recorded). The three `pub.iwi_directory_*` views go on the board in the merge after this one. Branches and worktree retired.
