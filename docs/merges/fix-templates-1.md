# fix-templates-1: window_days declared on construction and property; the ten templates read the Charities Register
branch: session/fix-templates-1 (committed at 2dab485; NOT pushed: the push to origin was refused by the session's permission layer; the branch is in the shared repository, so the main checkout sees it)
session: fix-templates-1 (scope products/templates/)
raised: 2026-10-21
claims: products/templates/ (02-legal, 03-banking, 04-agriculture, 05-credit, 06-insurance, 07-construction, 08-recruitment, 11-healthcare, 12-property, 13-ownership: template.toml, rules.py where a charity flag or CHARITIES_NOT_HELD lived, limits.md, README.md, tests; 04-agriculture/checkpoint.list new); docs/status/templates-fix.md (new); lessons/an-officer-check-keyed-on-through-misses-the-entitys-own-charitys-trustees.md; cards: eight closed, three updated and left open (below)

Thirteen commits, one per template and change, each with a fixture test that
fails without it (each checked against HEAD's rules.py and template.toml):

1. **window_days** (construction, property): `[[params]]` name
   `window_days`, kind integer, no default (ruling 65), the card's `means`.
   The form offers it; `--set window_days=365` is accepted and the rules'
   existing read cuts. Real renders: construction's contested-group
   director lists 1 of 6 pairs at 365 days; property's 34-company director
   21 of 175; `window_days=abc` says no cut is applied.
2. **The Charities Register** (all ten): `charities`, `charity_officers`,
   `charity_returns` in `reads` with licence, attribution and refresh;
   `charities` out of every `not_held` line and text; `CHARITIES_NOT_HELD`
   out of every rules file. Flags:
   - banking, legal, agriculture, recruitment: `charity-officer-roles` lists
     officer rows carrying the person's name (near) and, from a company, its
     charity by business number (confirmed); `charity-integrity-marks` reads
     the register's `disqualified` mark: the template's severity (red; legal
     amber) only on a confirmed row of the company's own charity, amber by
     name; a clear only where the name was looked up (the start's view is
     one `walk.NAME_JOIN_FROM` reads), the view was not skipped and no row
     was left past the limit. Two new mutants each where the file has them.
   - construction: `society-roles` gains the same charity rows.
   - healthcare: the five charity flags run; a trust board's trustees are
     read from its own charity for the mark (red with no end filed) and
     named as not followed; a by-name row is never red (mutants for both);
     `disqualified-officer`'s person clear names the charity lookup, and
     blocks from a start whose name is not looked up.
   - credit, insurance, property, ownership: no charity flag; the views in
     a section (insurance and ownership gained a `charities` section).
   Never summed across returns; no word of cause in any flag or section
   (the templates' CAUSE checks run on the new texts).

Checkpoints re-rendered before (a clean copy of ae98e86) and after, every
list (agriculture's six new keys): none refused; changes recorded in each
limits.md. Every memo lost "names as not held a register that is
published". Notable: banking/legal/recruitment marks blocked to clear on
person starts, roles clear to fired near; healthcare's two trust boards
reach their charities (14 and 37 trustees, 18 and 17 returns).

Checked: `bin/fast products/templates` green (35.7 s); every template's
slow tests green (banking's and recruitment's real assertions on the old
blocked charity flags amended; credit's people-section heading renamed in
its real test); `python -m products.report check` green (64 s);
`tests/test_imports_one_way.py`, `tests/test_reading_limits.py` green.

Cards closed: the-banking-, legal-, agriculture-, credit-, insurance-,
construction-, recruitment-template-can-now-read-the-charities-register;
the-construction-and-property-templates-declare-no-window-days-parameter.
Updated, left open (their reaches halves were outside this brief):
the-healthcare- (health register keys, officer near links, `chain` in the
Gazette section), the-property- (oio, building_consents, rea keys; near
links; companies above), the-ownership- (the chain)
template-can-now-read-the-charities-register-and-the-reaches.
charity-officers-are-in-no-link-and-no-name-row: read, unchanged.

For the integrator:
1. Push the branch, or merge it from the shared repository: this session
   could not push.
2. Restart `qv4-report` so the page's form offers `window_days` on the two
   templates.
3. tests/test_generators.py fails in the working copy until the gate's
   rebuild indexes the lesson and the cards.
Lesson: filed.

## Result (integrator, 2026-10-22 01:46 NZDT)

Merged into main as 0f20490 (`merge integrate/fix-templates-1: gate green`). Branch `integrate/fix-templates-1` from `session/fix-templates-1` (2dab485, taken from the shared repository since the session could not push), main merged. Construction and property declare `window_days`; the ten templates read the Charities Register's three views and their charity flags are rules on the rows; a trust board's trustees read from its charity (healthcare); agriculture has a checkpoint list; the lesson filed. Fast tier green in 504.2 s. Gate green, nothing to load. `qv4-report` restarted so the form offers `window_days`. Three template cards stay open for a later `bin/fix products/templates`, once this merge retires the session's hold on the folder. Branches and the working copy retired.
