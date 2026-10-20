# report: where it stands

**Date:** 2026-10-20. **Step:** 5.1, the subject-report shape, `products/report/`.
**Merge request:** `report-1` (raised).

## Done

- The shape: one builder from one row (`register:key`, as the board names a
  row) and one template. The walk (`walk.py`): the group from `pub.groups`,
  confirmed and near links with reasons from `pub.links`, the entities the
  group sits on, the register's own rows on them, one step further as near
  (design default, a setting); hubs flagged (professional director at 50
  directorships, nominee or trustee by name, the Crown, an address with 50
  or 1,000 companies); limits declared, never silent. Sections filled from
  the template's views only; blanks say "none found in …" or "not held: …";
  every line dated or marked undated, cited and numbered; the template's
  rules as flags (fired cites, clear names its sources, blocked says why);
  the presentation rules checked on every report (`rules.py`), a breach
  printed as a refusal. Memo as text and HTML. Server on port 8440, unit
  `units/qv4-report.service`; saved memos in `subject_report.reports`,
  only ever added to (tried in `querynz_v4_sample.scratch_report`).
- Templates are a folder: `template.toml` (reads with licences, sections,
  limits) and `rules.py` loaded by path. The shape's own is
  `templates/subject/`; step 5.2's go under `products/templates/<nn>-<name>/`.
- Outside check green on the real tables (`python -m products.report check`,
  1.5 s): the done-when donor (taken from the tables at run time) names its
  return, the company behind it (near, with its reason) and that company's
  directors, each cited; every citation is a row the view holds; the rules
  hold on a donor's, a company's and a director's report. Fast tier 19
  tests in 24 s with the fill; slow 4; one-way and query-crossing tests
  green. A donor's memo builds in 0.3 s; a director with a 20-row group in 3.4 s.

## Carded

- `same-name-donor-rows-are-linked-only-through-a-company` (links).
- `a-pane-on-the-board-offers-a-report-from-here` (board, a fix session).

## Next

1. The integrator merges `report-1`, runs `python -m products.report state`
   on `querynz_v4`, enables `qv4-report` (the installer's globs now reach
   `products/*/units/`).
2. Step 5.2, template 1 (use case 8, recruitment) in
   `products/templates/08-recruitment/`: a `template.toml` naming fewer
   views and a `rules.py` in the shape of `templates/subject/rules.py`.
