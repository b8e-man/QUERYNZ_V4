# insurance-1: template 06, insurance underwriting (step 5.2, use case 6)
branch: session/insurance-1 (pushed; 6d0284d)
session: insurance-1
raised: 2026-10-21
claims: products/templates/06-insurance/ (template.toml, rules.py, limits.md, checkpoint.list, README.md, tests/); docs/status/insurance.md; lessons/date-a-failure-from-its-first-appointment-never-from-a-winding-up-application.md; two cards (below)

The eighth use-case template on the subject-report shape: a commercial
underwriter asks "what stands against this business and its people" before
pricing the risk. It reads 12 pub views (companies, directors,
shareholders, company_addresses, the Gazette's liquidations, liquidators,
company notices, appointments, prohibitions and bankruptcies, societies
and their officers), each with its licence, attribution and refresh, and
nothing else; depth 2. `company_states` and `gazette_possessions` are
published and named in the brief but unknown to the catalogue, so not
named (the open `the-catalogue-does-not-know-gazette-possessions`); the
flags `status-history` and `mortgagee-possession` say so. Eight sections in
an underwriter's order: the entity and its namesakes apart; its standing,
age and registered office; the solvency record (the Gazette on the entity,
and on its people's companies, each notice dated); its people, dated;
their other companies and how each stands; prohibitions and bankruptcies;
the people beside them and their other roles; the safety record, every
register in it named as not held (WorkSafe prosecutions and enforceable
undertakings, the Commerce Commission, the FMA, court judgments, the ERA,
the Disputes Tribunal, Fire and Emergency's notices, the change history
before 16 August 2026, the Insolvency Register, the PPSR, FSPs).

`rules.py` takes `flag`, `items`, `section` and `all_items` from the bound
`contract`; no import of `products.report`; the builder's common rules run
and no copy is carried. 23 flags. `sister-company-failure` sets each
failure of a person's company, dated from the first appointment a Gazette
notice dates (a winding-up application only where none), beside the
person's own role on it; red only where a confirmed role began on or before
that day and is still listed; a hub, a near link, a later role or a holding
of record is never red. `insolvency-event` and `register-events` on the
entity; `young-entity`; `officer-churn` (two or more current directors
appointed in 365 days, the first board not counted; never clear, departures
before July 2026 not held); `prohibition` and `bankruptcy`;
`safety-record`, `regulator-actions`, `court-judgments`, `tribunals`,
`change-history` and four more blocked, never clear. Each rule branches on
the start; from a company the people checks block. `HISTORY = False`.

Checked on querynz_v4: 32 fast tests (fixtures; a mutant check of sixteen
deliberate breaks of `rules.py`, each caught) and 3 slow (real tables
through the CLI, subjects taken at run time); `bin/fast products/templates`
green in 30.2 s; the one-way and reading-limit tests green. `python -m
products.report check` reports one problem not of this branch (an MP
expense row reached by name; carded on `session/construction-1` as
`confirmed-expense-links-put-every-category-line-in-a-members-report`).

Checkpoint: twelve real subjects (seven person starts, five company
starts) all print, none refused, no rule broke, 0.3 to 5.5 s. Two faults
found and fixed before the close (a 2019 winding-up application dated a
2022 liquidation; a contested group filed the start row's own company near).
Three facts read against the Gazette source file, fields only.

Cards: `worksafe-and-regulator-actions-have-no-lane` (lanes: the old estate
holds 83 prosecutions and 62 enforceable undertakings from 143 WorkSafe
releases; nothing in the new estate reads them);
`the-not-held-list-has-no-key-for-the-safety-registers` (report lane).

Nothing to install: `qv4-report` serves every template on disk.

## Result (integrator, 2026-10-21 12:20 NZDT)

Merged into main as a6a95e5 (merged main first; the folder's README
add/add resolved to the session's). Done at the merge: the lesson
`date-a-failure-from-its-first-appointment-never-from-a-winding-up-application`
cut from 315 to 235 characters for the index; `qv4-report` restarted (the
template is served from disk); board, lessons index and queue
regenerated. No profile, catalogue or job change. Of its two cards,
`the-not-held-list-has-no-key-for-the-safety-registers` is closed by
`report-3` (merged next in order) and `worksafe-and-regulator-actions-have-no-lane`
stands open as a lane question for step 5.3.
