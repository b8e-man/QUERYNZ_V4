# fix-registers-parliament-1c: an archived page that is parliament.nz's refusal is set aside as blocked (hard limit 6)
branch: fix/registers-parliament-1 (pushed, 053fffa; one commit on main's 406a51d)
session: fix-registers-parliament-1 (Opus, fix weight), launched by the integrator
raised: 2026-10-27
claims: registers/parliament/ (read.py, check.py, spec.md, sample.list, tests), one lesson and lessons/INDEX.md, docs/status/parliament.md

Found by fix-products-board-2 on the full build: 10 of the 4,839 archived
pages in `pub.parliament_wayback_pages` were parliament.nz's "Unauthorized
Request Blocked" page (the Internet Archive kept the site's refusal of its
crawler), held with `capture_status` ok and published as pages with text.
Hard limit 6: a challenged read is a failed read.

## What changed

- `read.refused`: an archived page is the refusal when its title is
  "Unauthorized Request Blocked" and its text is short (at most 60 words),
  opens with that heading and says "Unauthorized Activity Detected". Measured
  on the 4,839 real documents: all ten are one 42-word text; the shortest
  real page has 81 words; no real page carries either phrase. A phrase on a
  page of content never makes it a refusal. The refusal's title over any
  other text is set aside under its own reason (measured: none).
- Such a record is set aside at stage `recognise` with the reason
  `blocked: the archived copy is the site's refusal (hard limit 6)`; its
  `files` line says `set aside`; no row, so it is not in the view. The
  document stays in the store: nothing captured is deleted.
- `check.py`: a `blocked` figure per corpus on the line; blocked lines are
  not counted as a failure; served records plus blocked equal the places
  taken. Any other set-aside line still fails.
- `sample.list`: 305c71… was labelled "an archived page of type other"; it
  is the refusal, and is now labelled so.

## Proof (full build `querynz_v4_sample.scratch_fix_registers_parliament_1_build` from `scratch_mcp_1_pull2`, 84 s)

Wayback: 4,839 documents, 4,829 read and published, 10 set aside as blocked,
0 other set-aside lines. Every other corpus as before (695,105 records;
flags 2,524 written questions, 59 pages, 0 API documents; no unflagged
street). The check line: `served 4829 … blocked 10` for a cursor of 4,839.

Tests: the sample's real refusal (305c71…) is set aside through the
lane's load, kept in the store, absent from the table and the view; a real
feature page (2b86ad…) beside it is read and published; made records cover
a long page naming the phrase (read) and the title over other text (set
aside). With `refused` taken out, three tests fail. `QV4_INTEGRATOR=1
bin/fast registers/parliament` green (48 tests, 45 s).

## Check red, known, not changed

`check.py` is red on one count: wayback 4,839 taken of the MCP's 6,181 now
(its `measure` line shows the same gap). The corpus grew after the last
pull; this clears at the next `qv4-mcp-pull` (02:30 NZDT). Nothing in this
fix touches it.

## What the integrator does at the merge

1. Gate and merge. **Restart nothing**: the nightly `qv4-parliament-load`
   (04:30 NZDT) loads the new reading and takes the ten pages out of
   `pub.parliament_wayback_pages`.
2. Lessons index: rebuilt on this branch (one new lesson); rebuild again if
   main's moved.
3. Sample database: drop `scratch_fix_registers_parliament_1_build`
   (regenerable, about 1 GB) and the stale
   `scratch_parliament_1_build_private.wayback_texts`.

## Lesson

`lessons/an-archived-copy-can-be-the-site-s-refusal-read-the-copy-s-own-shape-before-its-status.md`:
the archive's status ok is the archive's, not the site's; know the refusal
by its title and short fixed text; pick sample documents by what they hold,
not their type field.

## Result (integrator, 27 October 13:10 NZDT)
Merged 132aa81, gate green at the first run; the staging load rebuilt the lane (695,105 rows in 69 s) and published it, so pub.parliament_wayback_pages holds 4,829 pages now, the ten refusals set aside, ahead of the nightly load. Released; nothing restarted. The lesson indexed. The sample-schema drops are handed to Arthur with the rest of the day's. Branches and the working copy retired.
