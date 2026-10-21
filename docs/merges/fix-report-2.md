# fix-report-2: template parameters, the Charities Register, eight not-held keys, an officer's near links, the companies above
branch: session/fix-report-2 (pushed; 6639259)
session: fix-report-2 (fix, scope products/report/)
raised: 2026-10-21
claims: products/report/ (template, build, server, __main__, memo, contract 0.4, catalogue, rows, walk, check, spec.md, templates/subject/ 0.3, tests/test_params.py, test_charities.py, test_reaches_2.py new, test_catalogue.py); docs/status/report.md; lessons/a-not-held-key-a-lane-has-since-published-must-still-load.md; cards: seven closed (the-report-carries-no-template-parameters, the-report-shape-and-five-templates-still-say-the-charities-register-is-not-published, the-report-cannot-reach-the-charities-register, the-not-held-list-has-no-key-for-the-health-registers, the-not-held-list-has-no-key-for-the-property-registers, the-officers-reach-does-not-list-an-officers-near-links, the-chain-reach-reads-nothing-on-the-companies-above); twelve raised (ten the-<name>-template-can-now-read-the-charities-register[-and-the-reaches], the-construction-and-property-templates-declare-no-window-days-parameter, charity-officers-are-in-no-link-and-no-name-row)

Five commits, one per card group, each with a fixture test that fails
without the change and a route in `python -m products.report check` on a
row taken from the tables at run time:

1. Template parameters: a template declares `[[params]]` (name, kind of
   integer/text/date, default, means); the builder sets each in
   `report["params"]` and under its own name, reads it as its kind or
   passes the text given, refuses an undeclared name; `render --set
   name=value`, `?name=` on the page, the form offers them; the memo
   prints them. Construction and property do not declare `window_days`
   yet (carded), so `--set window_days` is refused on them today.
2. The Charities Register: `charities`, `charity_officers`,
   `charity_returns` catalogued (CC BY 3.0 NZ, Charities Services), the
   register among those held and out of NOT_HELD; a company's charity by
   business number as an entity (confirmed, `official-number`); the
   charity's officers and returns beneath it; a charity officer carrying a
   person's name near by name with its reason (no link joins the register:
   carded for the links lane). A not-held key a lane has since published
   (`SUPERSEDED_NOT_HELD`) still loads in the ten templates that cite
   `charities`, dropped from their blanks, the memo saying so.
3. Not-held keys: retirement_villages, hdc, certification,
   health_providers, aged_care_commissioner, oio, building_consents, rea.
4. The officers reach lists an officer's near links beside the confirmed,
   near with the officer's reason then the link's, the link's rule.
5. The chain reads the notices and current directors on each company
   above, with the company's grade, marked above at its depth.

Checkpoints re-rendered before and after on all nine lists (108 subjects):
no refusal; property's history-reach, serial-pattern and earlier-failure
blocked to fired on two subjects; healthcare's governance section lists the
directors above; no other template's sections or flags changed.

Checked: fast tier `products/report` 44 passed; `products/templates` fast
tier green; `tests/test_imports_one_way.py`, `tests/test_reading_limits.py`
green; `python -m products.report check` green (about 65 s).

For the integrator:
1. Restart `qv4-report` after the merge (the page's form changed).
2. Two slow template tests assert the old not-held line "not held:
   Charities register and officers": `products/templates/08-recruitment/tests/test_recruitment_real.py`
   (line 103) and `products/templates/11-healthcare/tests/test_healthcare_real.py`
   (line 70). They are outside this session's scope and go red at the
   nightly full tier until their templates' cards are worked; if the gate
   runs them for this branch, amend the two assertions at the gate as
   report-3's gate did for agriculture.
3. tests/test_generators.py will fail in the working copy until the
   gate's rebuild indexes the lesson and the cards, as before.
Lesson: filed (a not-held key a lane has since published must still load).

## Result (integrator, 2026-10-21 21:52 NZDT)

Merged into main as ae98e86 (`merge integrate/fix-report-2: gate green`). Branch `integrate/fix-report-2` from `session/fix-report-2` (6639259), main merged. The two slow template assertions on the old not-held line for the charities register (recruitment, healthcare) amended at the merge, as report-3's gate did for agriculture: the register is held and catalogued now. The regulator board views carried with it. Seven cards closed, twelve raised for the templates (a templates fix session follows). Fast tier green in 468.6 s. Gate green, nothing to load. `qv4-report` restarted (the page's form changed). Branches and the working copy retired.
