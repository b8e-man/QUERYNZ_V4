# A use-case template cannot reach the flag contract or the shape's common rules
kind: finding
state: open
use-case: subject report (5.1); every template of step 5.2
session: recruitment
opened: 2026-10-20

`tests/test_imports_one_way.py` holds `products/templates` to its own code,
so a template's `rules.py` may not import `products.report.template.flag`
or reuse the shape's `group_standing`, `hubs_met` and `replaced_rows`, and
its tests may not import the builder. The recruitment template therefore
carries its own `flag` (the same contract; the shape's rule 9 re-checks
every flag) and its own identity, subject-hub and replaced-return rules,
and tests through `python -m products.report`. Nine more templates will
each do the same. For the report lane, one of: the builder runs the shape's
common rules for every template and passes `flag` into each rule call; or
the one-way test lets `products/templates` import `products.report.template`.
Then the recruitment template drops its copy (a fix in its folder).
