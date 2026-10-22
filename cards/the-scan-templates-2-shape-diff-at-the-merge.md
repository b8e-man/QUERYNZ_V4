# The scan shape's additions for template 3 go in at the merge
kind: blocker
state: open
use-case: 14 the post-settlement governance map
session: scan-templates-2
opened: 2026-10-23

The session's fence is `products/scan/templates/`; the six `settlement-map-*`
scans need four additions to the shape in `products/scan/`, carried as
`products/scan/templates/_shape/scan-templates-2-shape.diff` (paths
`a/products/scan/…`, made against main at 9265192; 10 hunks over 6 files,
checked by a strict reader to reproduce the merged copy file for file):

1. `views.py`: `iwi_directory_entities` (titled by name and kind, dated by
   the entry's "last updated" as printed), `iwi_directory_relations`,
   `iwi_directory_settlements` (dated by the deed's date as printed, else
   the Act's year); register `iwi_directory`. No contact or location column.
2. `lines.py`: a citation is numbered per row, by (view, key, document,
   page, place), not by (view, key). The directory's settlement key is the
   settlement's (card `a-settlement-key-names-several-rows`): numbered by key,
   13 lines cited another body's page. Every earlier scan's counts and
   citations are unchanged (61,722 for tender-awards).
3. `check.py`: `citations_resolve` reads back the document, page and place
   as well as the key; `chain_readback` reads template 3's six scans back
   from their own steps (every body listed, each row and name join true
   today, each blank empty today, the grade the joins make).
4. `template.py`: a name step whose number is a charity number says "by
   charity number or by name" in its blank.
5. Tests: one fast (`tests/test_lines_and_rules.py`), seven slow
   (`tests/test_templates_real.py`); seven code mutants, each caught.

Until it is applied `templates/_tests/test_settlement_map.py` skips (guarded:
the skip cannot outlive the diff) and the six templates do not load, so
`run --stale` and the check fail loudly. Fate: applied in the same commit as
the templates and `_shape/` removed, then this card closes.
