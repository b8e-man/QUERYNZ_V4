# construction-2: the phoenix window is the reader's setting (ruling 65)
branch: session/construction-2 (pushed; bf632fc)
session: construction-2 (a one-card fix, Opus)
raised: 2026-10-21
claims: products/templates/07-construction/ (rules.py, template.toml 0.2, limits.md, README.md, tests); cards/the-report-carries-no-template-parameters.md; lessons/a-backup-in-a-refused-command-was-never-made.md; docs/status/construction-2.md

Arthur's ruling 65 (21 October): the phoenix window is the reader's
setting, not the template's. `phoenix-signature` now sets every company
that carries a failure notice in the Gazette (liquidation, receivership,
administration, winding-up application, creditors' notice, deed of
arrangement, removal) and shares a person (from a person) or a
pre-failure registered office (from a company) with the subject, beside
each going company's start, whatever the gap: the gap in days, signed
("50 days after", "134 days before"), the pairs ordered nearest first.
The flag text counts the pairs within 90 and 365 days. `WINDOW_DAYS` is
gone; the rules read `report["window_days"]` (the place a rule reads
`report["since"]`) and cut only when it is set; a value that is not a
whole number of days says "no cut is applied". `same-name-failed` and
`shared-office` read the same window. Severity rules unchanged.

From a person, "the subject's registration" is read as each going
company's: a person has none, so each failure is set beside each of the
person's going companies (as before). From a company it is the company's
own.

Tests: 35 fast (seventeen mutants: the window mutant rewritten, three new:
a default window when none is set, pairs not nearest first, the 90/365
counts missing); seven of them fail on the old rules. 4 slow green on the
real tables. `bin/fast products/templates` green 29.2 s. The whole-repo
fast tier is red only on `tests/test_generators.py`: `lessons/INDEX.md`
is stale by this branch's new lesson (generated; regenerate at the merge).

Checkpoint re-rendered, old against new, on the twelve subjects: only the
phoenix flags' text changed, no status or severity; pairs the 365-day cut
hid now show after the near ones (subject 8: 6 pairs, not 1). Recorded in
`limits.md`. Subject 7 is still refused by the shape (the open
address-named-company card).

Card: `the-report-carries-no-template-parameters` (report lane): the shape
should carry template parameters generally; the first key is
`window_days`. Until then no reader can set a window and every gap shows.
Lesson: `a-backup-in-a-refused-command-was-never-made`.

## Result (integrator, 2026-10-21 14:46 NZDT)

Merged into main as 66cf9c9 (`merge integrate/construction-2: gate green`). Branch `integrate/construction-2` from `session/construction-2` (bf632fc), main merged. Carried with it: the board's three charities views (Charities, Charity officers, Charity returns; the catalogue's not-held entry for charities removed; the address test exempts a body-corporate charity's address for service under ruling 64), held back from charities-3 because the gate tests the live tables before staging publishes; the lesson `a-lane-s-new-view-is-catalogued-on-the-board-in-the-merge-after-the-lane-s`; `docs/status/construction-2.md` folded into `docs/status/construction.md` (2,962 bytes). Fast tier green in 314.6 s (target 300 missed under load, recorded). Gate green, nothing to load. `qv4-board` and `qv4-report` restarted 14:48. Branches and the working copy retired.
