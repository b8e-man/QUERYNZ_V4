# report-1: the subject-report shape (step 5.1)
branch: session/report (pushed; ac4c516)
session: report
raised: 2026-10-20
claims: products/report/ (the whole module: catalogue, db, rows, walk, template, templates/subject/, build, rules, memo, server, state, tables.sql, check, __main__, units/qv4-report.service, tests, spec.md); docs/status/report.md; lessons/a-return-reached-through-the-subjects-own-row-is-context-not-a-web.md; cards/same-name-donor-rows-are-linked-only-through-a-company.md, cards/a-pane-on-the-board-offers-a-report-from-here.md

One builder, parameterised by a template: starts from one row named as the
board names it, walks confirmed links outward through pub.links and
pub.groups with near links beside them and their reasons, fills the
template's sections from the pub views the template names and nothing
else, applies the template's rules as flags, cites and numbers every
statement, says "none found in …" or "not held: …" for every blank, and
prints as a memo (text and HTML). Every connection dated or marked
undated; hubs flagged; a nominee shown as a holder of record, never an
owner; no word of cause in any statement (checked); absence is not a
finding. No home address and no suppressed name (checked on every report).

Checked on querynz_v4 through the product reader: `python -m
products.report check` green (the done-when: a known donor's report names
its return, the company behind it and its directors, each cited; every
citation a row the view holds today). Fast tier `products/report` 19 passed
in 24 s with the fill; slow 4 passed; tests/test_imports_one_way.py and
test_reading_limits.py green.

For the integrator after the merge:
1. `python -m products.report state` in /home/user/querynzv4 (creates
   `subject_report.reports`); then install and enable `qv4-report`
   (`products/report/units/qv4-report.service`, port 8440, local network).
2. The two cards above are for the links session and a board fix session.
3. tests/test_generators.py fails in this working copy only because the
   new lesson and cards are not yet in the generated index and board; its
   run rewrote docs/board.md and lessons/INDEX.md in the working copy, and
   the scope hook refuses a `git checkout` of generated files, so the two
   sit modified and uncommitted there. Nothing of theirs is in the branch;
   the gate's rebuild makes them current.

Note: a working copy's own `bin/fast` finds no venv (`bin/_session.MAIN` is
the copy itself); `/home/user/querynzv4/bin/fast products/report` run from
the working copy fills and tests it. Not carded: bin/ is the founding
sessions' fence; raise it if you think it a card.
Lesson: filed (a return reached through the subject's own row is context,
not a web).

## Result (integrator, 2026-10-20 14:10 NZDT)

Merged into main as b02c1b7 (merged main first). Done at the merge:
records regenerated (the lesson and two cards); the comparison-1 record
and the briefs for the next sessions rode in the same commit. Fast tier
and gate green. After the merge, as asked: `python -m products.report
state` made `querynz_v4.subject_report`'s saved-reports table;
`qv4-report.service` installed through the installer, enabled and
started as a user unit, answering on 10.0.0.2:8440 (local network only).
The two cards stand for the links session and a board fix session. The
`bin/fast` finding (a working copy's own `bin/_session.MAIN` is the copy
itself) was fixed at the comparison-1 merge with a literal fallback to
the main checkout's venv. The session ran headless from the integrator as
Fable, about 40 minutes.
