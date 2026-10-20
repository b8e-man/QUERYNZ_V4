# A use-case template cannot reach the flag contract or the shape's common rules
kind: finding
state: closed
use-case: subject report (5.1); every template of step 5.2
session: recruitment
opened: 2026-10-20
closed: 2026-10-20

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

Closed 2026-10-20 by the report session (report-2), the card's first way,
with the contract as a module. `products/report/contract.py` holds the flag
(`flag`, `STATUSES`, `SEVERITIES`), the helpers over a built report
(`items`, `section`, `all_items`), the common rules (`COMMON_RULES`:
group-standing, hubs-met, replaced-return), the presentation rules
(`presentation_problems`, `CAUSE`, `OWNER`, `address_shaped`, `BLANK_OK`)
and the report's address (`report_url`). The loader binds it as the name
`contract` in a template's `rules.py` before the file runs, so a template
writes `flag = contract.flag` with no import and the one-way test stands
unchanged; the builder runs the common rules for every template (opt out:
`common_rules = false` in `template.toml`), and a template flag with a
common flag's `rule` name replaces it. The shape's own `templates/subject/
rules.py` is written the same way, as the model. Measured: `python -m
products.report check` builds the done-when donor's report under every
template on disk and fails if the three common flags are missing or break
rule 9; the fast tests load a temp template that uses `contract` with no
import. For the recruitment template (a fix in its folder): drop its
`flag`, `identity` → keep or rename to `group-standing`, `subject_hub`,
`replaced_rows` copies and write `flag = contract.flag`.
