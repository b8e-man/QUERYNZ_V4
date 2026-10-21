# grants-2: the class 4 societies' own lists as files (class A), the Lottery walk's stall, regional and tertiary funding surveyed
branch: session/grants-2 (pushed; e2c8f20)
session: grants-2 (Opus)
raised: 2026-10-22
claims: registers/grants/ (capture, read, load, check, society.py, pdftable.py, tables.sql, publish.sql, sample, sample.list, spec, README, pane, survey, unprofiled.list, profiles-proposed.jsonl, position/, tests); docs/status/grants.md; cards the-societies-own-grants-lists-by-class, the-lottery-records-before-2024-and-the-other-lottery-funds, regional-and-tertiary-funding-not-read (new); queue whether-a-non-commercial-licence-file-is-read (default applied); one lesson

## What it does

1. **The societies' own lists, class A (tranche 1).** The capture walks each of the nine class A societies' grants
   pages (two links deep; list `society-page`) and lands every grants file once (list `society-file`; publisher =
   the society; a file whose name dates it wholly before 2017 is left unasked). Found addresses are kept in the
   frontier, so a cut-short run loses nothing. The reading recognises a society's file by shape (a PDF with a text
   layer, its title lines and its row of column heads, and what it is not) under one profile per layout, and reads
   it by word boxes (`pdftable.py`, pdftotext -tsv). Eleven layouts from six societies: Air Rescue (two, July 2017
   to June 2026), Pelorus (approved, declined), Aotearoa Gaming Trust, Trust Aoraki (two, 2025, the purpose
   printed), Milestone (November 2017 to March 2020), New Horizon (two), We Care (2022). The society is publisher
   and grantor of each row; decisions from 2017 on; purpose, application number, reason and declared conflicts as
   printed (three new columns on `pub.grants`). An application printed twice (Pelorus served its approved list of
   28 April 2026 again under the declined list's name) is read once.
2. **Checks that can fail on real data.** check.py adds: every printed total and count a society list carries
   equals its rows; a society list in a layout no profile reads and `unprofiled.list` does not card is red; a
   society's lists against the national file over whole calendar years both cover, 0.5% tolerance (Air Rescue
   2021 to 2025: 7,397 decisions and $84,940,139 against 7,406 and $84,954,601; We Care 2022 differs, carded as
   known). Tests pin each sample file's reading, recognise each by exactly one layout, count application numbers
   afresh on the raw text layer; ten mutants of the society and table readers and four of the capture are each caught.
3. **The Lottery walk (tranche 2).** The first walk on the live database (00:22) landed 15 pages, no record of
   grants, then a 403. A page that blocked was never marked asked, so every later night would have opened on it and
   stopped: fixed and tested. The three watches and what the walk must show are on the card.
4. **Regional and tertiary funding (tranche 3).** Surveyed (seven requests), position drafted: Kānoa's project
   list is CC BY-NC 4.0, so not landed (queue, default not read); TEC answered with a challenge (failed read).

Proof on the sample database (`scratch_grants_2_full`): the national file, the Lottery record and the 235 society
files built in 35 s: 194,409 grants (15,524 from the societies' own lists), 96,969 recipients; `check.reading`,
`check.views` and `check.outside` green. 321 requests to the societies' hosts through the gate, at night (01:50 to
02:20), serial, 5 s apart; no block, no challenge. Lane fast tier green (63 tests, 31 s without the fill). Whole repository: 581.9 s, red only on `tests/test_generators.py` because the new card, queue item and lesson make the committed generated files stale (step 4 below).

## For the integrator (nothing else)

1. Append the eleven lines of `registers/grants/profiles-proposed.jsonl` to `support/profiles/profiles.jsonl`
   (version 1 each); remove the proposed file.
2. Move `registers/grants/position/regional-development-and-tertiary-funding.md` to `docs/legal/positions/`.
3. Gate floors 5 s for the class A hosts: `airrescueservices.co.nz`, `pelorustrust.net.nz`, `agt.nz`,
   `onefoundation.nz`, `trustaoraki.co.nz`, `newhorizoncommunitytrust.co.nz`, `milestonefoundation.co.nz`,
   `wecare.org.nz`, `nzct.org.nz`, and for `growregions.govt.nz`, `tec.govt.nz`, `educationcounts.govt.nz`.
4. Regenerate the queue, the board and the lessons index.

The jobs are unchanged in the catalogue; `qv4-grants-capture` now also walks the societies (its default lists), and
its first night will land about 235 files (about 25 minutes at 5 s). `tables.sql` replaces `capture_docs`' inline
list check with a named one on each run; the reading's tables gain three columns at the next load.

## Result (integrator, 2026-10-22 03:24 NZDT)

Merged into main as b7690ea (`merge integrate/grants-2: gate green`). Branch `integrate/grants-2` from `session/grants-2` (e2c8f20), main merged. The eleven class A society profiles appended as version 1 (120 slugs), the proposed file removed; the position `regional-development-and-tertiary-funding.md` moved to `docs/legal/positions/`; gate floors at 5 s for the nine society hosts and `growregions.govt.nz`, `tec.govt.nz`, `educationcounts.govt.nz`. Jobs unchanged: `qv4-grants-capture` now also walks the societies' lists (about 235 files on its first night). Fast tier green in 580.9 s. Gate green; staging: 178,729 grants, 91,275 recipients, 10 set aside, reconciles, published in 8 s (the reading's three new columns with it). Cards and the queue item as the request lists them (regional and tertiary funding not read: one list CC BY-NC, TEC a challenged read). Branches and the working copy retired.
