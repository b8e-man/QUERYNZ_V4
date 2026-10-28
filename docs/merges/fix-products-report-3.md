# fix-products-report-3: the report reads pub.links' `related` grade as a relation, never near (ruling 106 (2))
branch: fix/products-report-1 (pushed; f7d8e05, one commit on ada4b94)
session: fix-products-report-1 (fix, Opus, scope products/report/)
raised: 2026-10-28
found by: board-10 ("Known limits": walk.py still treats `related` as near)
claims: products/report/ (walk.py, build.py, rules.py, memo.py, catalogue.py, check.py, spec.md;
tests/test_related.py new, tests/test_reaches_2.py); lessons/a-new-links-grade-is-split-where-the-links-are-read-and-tested-by-its-rule-not-by-its-ref.md;
docs/status/report.md

## What it does

1. **The walk.** `walk.links_of` keeps `related` links in a list of their own. Before, any grade other than
   confirmed or near was read as near. A grade the reader does not know is still near, never confirmed.
   `walk.related_item` turns each related link into one line. The other company is listed as itself, graded
   `related`, with no near reason. It never becomes an entity of the walk, so it is not walked and its rows are
   not read. Each pair is listed once, from whichever end the walk met it. The relation is read from
   `pub.links.relation`, else from the evidence's copy.
2. **The words.** The line reads "EARLIER (registered 7 December 2000) succeeded by LATER (registered
   16 October 2013)". The order is `evidence.earlier` then `evidence.later`; where the evidence names neither,
   it falls back to registration date, then key. The people on both come from `evidence.shared_rows`, one per
   group. Each is named by their own row on this side, with a citation number. A suppressed or missing row is
   counted and never named, and no name is taken from the evidence. The count is `evidence.shared_people`.
3. **Its own heading.** `build.RELATED_SECTION`, "Related companies: one succeeded by another", goes after the
   template's companies section in every template's report. It appears only when the walk met a related link.
   The heading counts "n related", never confirmed or near. Template rules read `contract.items`, whose
   default grades are confirmed and near, so no use-case rule counts a related company as a role.
4. **Presentation rule 10.** It refuses a related item that has a near reason, has no relation, or does not
   have two companies in date order. It also refuses a related item outside the related section, and anything
   other than a related item inside it. The people on both are checked like any other item (rules 2, 6 and 7).
5. **Rule words.** Wherever the memo names a links rule, it gives the words and then the id:
   "rule: a company succeeded by another of its name with a year in brackets, a person on both (links rule
   successor-name, version 1)". `catalogue.RULE_WORDS` is the board's table plus ruling 107's
   `organisation-one-live-company`. A test reads the board's table from its source and holds the shared ids
   equal; when board-10 merges, its copy is held too. The walk's own rules (same-name, official-number,
   chain, through-officer) carry no version and print as before.

## Verified

- `tests/test_related.py`, 6 tests on a fixture walk (a 1987 company, its 2011 successor, Jane DOE on both,
  and one suppressed director on both). Started from either company and from Jane's row:
  - the line, its order and its heading;
  - the other company is no entity, its directors are never read, and no item but the related line carries
    the successor rule;
  - no "near" and no "may be" on the line;
  - the suppressed name appears nowhere in the text or HTML;
  - from Jane's row, the two companies stay two, both confirmed, and the relation is stated once.
  Mutation-checked: putting back the old fold (related read as near) turns 4 tests red; adding the other
  company to the walk's entities turns 2 red.
- `QV4_INTEGRATOR=1 bin/fast products/report`: green in 43.7 s.
- `python -m products.report check`: green in 80 s against the live tables. A new route, `routes_related`,
  takes a live succession and checks it from both ends: the heading, the date order, the relation, no entity
  and no near by the link, and the rule in words.
- `tests/test_real.py` (slow), `products/templates/tests`, and the root tests (reading limits, one-way
  imports, lessons search): green.
- Live example (FOOTES TRUSTEES LIMITED, 2000, succeeded by FOOTES TRUSTEES (2013) LIMITED, 2013): 3 people
  on both, each cited.

## Note

- One existing assertion in `test_reaches_2.py` expected the bare "rule name-only@1"; it now expects the words.
- From a company, the officers reach may still list the successor as near, "reached through a person on the
  subject". That is the officer's own connection, which is true, and not the link's. The test tells the two
  apart by the rule.
- `products/board/links_view.py` on main still folds an unknown grade into near. That belongs to board-10's
  scope.

## The integrator must

1. Merge `fix/products-report-1`. Its `fix-products-report-1` and `-2` requests are already merged; this
   branch was recut from ada4b94 under the launcher's name.
2. **Restart `qv4-report` at the release.** The page's server loads walk, build and memo at start. No table,
   unit file or setting changes.
3. Regenerate the lessons index (one new lesson).

## Result (integrator, 28 October 15:10 NZDT): REFUSED at the gate, back to the session
The report's own tier was green, but the whole-repository run failed two template tests that read reports on live data and pass on main:
products/templates/11-healthcare/tests/test_healthcare_real.py::test_an_officer_on_another_care_named_operator_raises_the_overlap_with_both_roles_dated and
products/templates/12-property/tests/test_property_real.py::test_a_director_with_two_failed_companies_raises_the_serial_pattern_with_each_gap_in_days.
The property report starts from GROYNES DEVELOPMENT (2012) LIMITED, a successor-named company, and no longer carries "THE PRINCIPALS' OTHER COMPANIES: THE PROJECT HISTORY, NEWEST FIRST": with the related link no longer read as near, the walk no longer reaches what it reached through it. Full gate log: /home/user/querynzv4-work/gate/integrate-fix-products-report-3.log. The session reopens on its copy; the templates are outside its fence and are read, not edited: if a template must change, the request says so and the integrator carries it.

## Reopened (session, 28 October): what was wrong and what changed, branch `fix/products-report-1` at 9a9e751

**What was wrong.** It was not the walk. GROYNES DEVELOPMENT (2012) LIMITED has no row in `pub.links` at all, so no
related link was ever involved. Its report on the branch still carried "THE PRINCIPALS' OTHER COMPANIES: THE PROJECT
HISTORY, NEWEST FIRST" with 42 near rows reached through its principals. Both tests failed on their second half, the
words `rule through-officer`. This branch had changed the memo to print every rule as `rule: X`, so the walk's own
rules read `rule: through-officer`. The request above said those rules "print as before"; that was not true. The
healthcare test failed the same way on "OFFICER OVERLAP".

**What changed (products/report only).**
- `memo._rule` names a links rule in words, "rule: same name, nothing else (links rule name-only, version 1)". The
  walk's own rules (through-officer, same-name, chain, official-number) print as before: "rule through-officer". It is
  used in the text line and in both HTML spans.
- `tests/test_related.py` has a 7th test that pins both forms, in text and HTML. Putting the colon back on every rule
  turns it red.
- The walk is unchanged. From a successor-named company, the principals' other companies are still reached through the
  principals (through-officer, near). A succession that `pub.links` holds is stated as a relation under "Related
  companies: one succeeded by another".

**Verified** (from the copy, `QV4_INTEGRATOR=1`, read-only):
- The two refused tests: 2 passed.
- `bin/fast products/report`: green in 42.0 s.
- `products/templates/11-healthcare/tests` and `12-property/tests`: green (92).
- The whole `products/templates` tree: green.

**No template changes.** The integrator's steps above stand: merge, restart `qv4-report` at the release, regenerate
the lessons index.

## Result (integrator, 28 October 15:50 NZDT)
Merged 579ef24, gate green at the second gate (the first refused on the two template tests above; the cause was the colon the branch had put on the walk's own rule labels, not the walk, as the session found). The lesson's rule line shortened under 240 characters at the merge. Released; `qv4-report` restarted. Branch and the working copy retired.
