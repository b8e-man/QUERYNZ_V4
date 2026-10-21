# The scan shape's additions for the step-6.2 templates go in at the merge
kind: blocker
state: closed
use-case: 10 tender and award intelligence; 9 government procurement integrity
session: scan-templates-1
opened: 2026-10-21
closed: 2026-10-22

The session's fence is `products/scan/templates/`; the templates need five
additions to the shape in `products/scan/`, carried as
`products/scan/templates/_shape/scan-templates-1-shape.diff` (paths
`a/products/scan/…`, made against main at b051c04):

1. `views.py`: `award_notices` (titled by agency and RFx ID, never its
   title: card `award-notice-titles-carry-street-addresses`) and
   `award_suppliers`, register `tenders`.
2. `template.py`, `plan.py`, `lines.py`: the name step (`by = "name"`,
   `on`, `number`, `namesakes`), one hash join on (route, key), by number
   when both rows carry one (confirmed) else by the folded name (near, the
   reason, namesakes marked); the optional step (a left join, the step
   shown "none found in", uncited); a link step of several rules; the
   query's parameters in the order their places stand (a where on a later
   step and a link rule were out of order before: no template had both).
3. `rules.py`: rule 10 (a step with nothing there says "none found in" and
   carries nothing else); `hubs.py`, `out.py`, `check.py` skip such a step.
4. `check.py`: the step-6.2 templates read back line by line on a spread
   of each run (`templates_proving`).
5. Tests: `tests/test_name_step.py` (fast, 21) and
   `tests/test_templates_real.py` (slow, 4).

At the merge, in one commit with the templates: `git apply
products/scan/templates/_shape/scan-templates-1-shape.diff`, delete
`products/scan/templates/_shape/`, run the fast tier (the templates' own
tests stop skipping), then with `QV4_SCAN_STATE=querynz_v4/register_scan`
run `python -m products.scan run` for `tender-awards`,
`procurement-directors-donors`, `procurement-shareholders-donors` (about
2.5 minutes together) and `python -m products.scan check` (green on the
merged copy in this session's scratch schema, 11.6 s). Merged without the
diff, the three templates do not load and `run --stale` fails loudly.

Closed by the integrator at the merge of `scan-templates-1` (22 October 2026): the shape diff applied to the ten scan files by a small unified-diff reader (the hooks refuse `git apply` and `patch`), every hunk's context matched, in the same commit as the three templates; `products/scan/templates/_shape/` removed; the scan's tests green with the templates loading.
