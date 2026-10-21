# sanctions-1: the three step 5.3 lanes (limited partnerships captured; Board decisions captured; the practitioner register and the three sanctions lists HELD)
branch: session/sanctions-1 (pushed; b2c1247)
session: sanctions-1 (Opus)
raised: 2026-10-21
claims: registers/limited_partnerships/, registers/building_practitioners/, registers/sanctions/ (each: capture, read, load, check, tables, publish, sample, sample.list, pane, spec, profile-proposed.jsonl, position/, tests; sanctions also workbook.py); docs/status/sanctions.md; five queue items; three cards; two lessons

## What each lane is

- **Limited partnerships** (use case 13). Frame: the 4,114 registered NZ and overseas limited partnerships in
  `pub.companies`. One NZBN entity-detail call per partnership through the gate with our key (read at use, never
  printed), 5 s apart, 21:00 to 22:00 NZ, never Wednesday, a seventh of the frame a night, stalest first. Read by
  profile `nzbn-limited-partnership-detail` v1 into `pub.limited_partnerships` (registered office shown) and
  `pub.limited_partnership_partners` (general partners, person or body; withheld names blanked; every partner address
  private). Proved on 15 real answers, landed in the sample store and listed in sample.list. Findings: the interface
  states no start or end date for any partner (none is made up; `dates_stated` says so); two different partners can
  share one role identifier (keyed by kind and name too; lesson). Limited partners are confidential (LP Act s 115)
  and never sought. The Companies Office web register refused (HTTP 500, robots disallows all) and is not used.
- **Building practitioners** (6, 7, 12). The Board's published decisions list (Crown copyright, copy freely), 20 a
  page, about 80 pages, weekly; profile `lbp-board-decisions-list-page` v1; `pub.building_practitioner_decisions`
  (name, LBP number and decision addresses blanked where the Board writes [OMITTED] or the summary records a
  suppression; the summary itself never kept; shown for three years, the register's own window, queue default).
  Proved on 4 pages: 80 of 80 decisions read. **The practitioner register is held:** Building Act 2004 s 307 allows a
  search only for s 299's purposes and s 308 makes any other an interference with privacy. Nothing is asked of it,
  no reader exists, `pub.building_practitioners` is empty. Queue, no default.
- **Sanctions** (13). MFAT's Russia register, the UN consolidated list, Police's designated terrorist entities, each
  with its own profile, into `pub.sanctions_listings` and `pub.sanctions_lists` (names and aliases as published,
  countries and nothing finer, no passport numbers or narrative). **All three held on their publishers' terms**
  (MFAT: no automated access; UN: personal non-commercial, no compiling; Police: non-commercial private only).
  MFAT may be landed by hand (`capture.py --file`), its copy being CC BY 4.0. UN and Police readers proven in
  memory on today's lists (1,010 and 826 items reconcile). MFAT's reader is written from a published description
  and is unverified until a real file. Police's 1373 page states 22 current designations; its workbook holds 21.

## For the integrator at the merge (card `the-partnerships-and-board-decisions-jobs-into-the-catalogue`)

1. Move `registers/*/position/*.md` (three pages) to `docs/legal/positions/`.
2. Append the five `profile-proposed.jsonl` lines to `support/profiles/profiles.jsonl`.
3. Gate floors: `www.lbp.govt.nz` 5 s; `www.police.govt.nz` and `scsanctions.un.org` 10 s.
4. Jobs as each spec.md proposes: `qv4-limited-partnerships-capture` and `-load`; `qv4-building-practitioners-capture`
   and `-load`. No sanctions jobs while held.
5. Checks are red until the frame is asked and a full decisions pass is held; that is correct.

## Tests

Fast tier green on all three modules (`bin/fast registers/<lane>`, about 30 s each with the sample fill): 19, 17
and 20 tests, with 9, 8 and 12 mutants of the readers' rules each caught. Two slow sanctions tests read the live lists
in memory only when `QV4_SANCTIONS_LIVE=1`; run once today, green.

## Not done

No first night was run: the captures were daytime proofs of under 30 requests in all. The full captures are sized
(partnerships: 7 nights of 600 calls; decisions: 7 minutes weekly) and left to the proposed jobs.

## Result (integrator, 2026-10-21 18:22 NZDT)

Merged into main as feff77e (`merge integrate/sanctions-1: gate green`). Branch `integrate/sanctions-1` from `session/sanctions-1` (b2c1247), main merged. Card `the-partnerships-and-board-decisions-jobs-into-the-catalogue`, now closed: the three positions moved to `docs/legal/positions/` (`limited-partnerships-register.md`, `building-practitioners-register.md`, `sanctions-lists.md`); the five profiles appended as version 1 (86 slugs); the gate floors `www.lbp.govt.nz` at 5 s and `www.police.govt.nz` and `scsanctions.un.org` at 10 s; `limited_partnerships`, `building_practitioners` and `sanctions` in the lane list with their schemas applied with grants on both databases; four jobs in the catalogue at priorities 53 to 56: `qv4-limited-partnerships-capture` (nightly 21:00 NZDT; the capture itself skips Wednesday), `qv4-limited-partnerships-load` (06:50), `qv4-building-practitioners-capture` (nightly 23:00 NZDT: the spec asks for weekly on Sunday, the catalogue has no weekday field, so it runs nightly for about seven minutes until the lane or the scheduler carries the day) and `qv4-building-practitioners-load` (06:40); no sanctions job while the lists are held. Each lane's `load.py` gained the staging contract's `load(conn, schema)` (the job's build, its check's problems logged). The courts board views carried with it. Fast tier green in 457.6 s. The gate's first run was refused: the board's live check found `pub.limited_partnerships`, `pub.limited_partnership_partners`, `pub.building_practitioner_decisions` and `pub.building_practitioners` already published and empty, with the limited partnerships tables beside them, before the staging step had run; nothing in the run records says what created them. The four views were catalogued on this branch (the live check green) and the gate rerun: fast tier again green in 439.9 s. Gate green; staging: 0 partnerships and 0 general partners, 0 Board decisions, 0 sanctions listings (no finished pass in the working copy; the jobs fill the tables). The two sanctions views go in once their views are published. HELD, for Arthur: the practitioner register (Building Act s 307/308) and the three sanctions lists, five queue items. Branches and the working copy retired.
