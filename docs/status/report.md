# report: where it stands

**Date:** 2026-10-21. **Step:** 5.1, the subject-report shape, `products/report/`.
**Merge request:** `fix-report-2` (raised); `report-1`, `report-2`, `report-3` merged.

## Done

- The shape (`report-1`), the second and third tranches (`report-2`, `report-3`).
- `fix-report-2`, five commits, seven cards closed: template parameters
  (`[[params]]` in template.toml; `--set`, `?name=`, the form; `report["params"]`
  and each under its own name); the Charities Register in the catalogue
  (three views, CC BY 3.0 NZ) and out of the not-held list, a company's
  charity by business number, a charity's officers and returns, a charity
  officer by a person's name near, a superseded not-held key still loading;
  eight not-held keys (health, property); an officer's near links listed
  beside the confirmed; the chain reading notices and directors on the
  companies above. Fast tier `products/report` 44 tests; templates' tier
  green; `python -m products.report check` green (about 65 s, four routes
  added); one-way and reading-limit tests green.
- Checkpoints re-rendered before and after (108 subjects, nine templates):
  no refusal either side; every memo drops "Charities register and
  officers" from its not-held list and gains the eight keys and a line
  saying the template names as not held a register that is published;
  property: `history-reach`, `serial-pattern` and `earlier-failure` go
  blocked to fired on two subjects (a director's namesake company in
  liquidation, by the officer's near link); healthcare: the governance
  section lists the directors of the companies above (rows that moved
  there from the overlap section), the overlap and Gazette sections gain
  near-linked rows, `hubs-met` fires on one society; the other six
  templates: no section or flag changed.

## Carded

- Templates: ten cards `the-<name>-template-can-now-read-the-charities-register[-and-the-reaches]`;
  `the-construction-and-property-templates-declare-no-window-days-parameter`.
- Links lane: `charity-officers-are-in-no-link-and-no-name-row`.
- Left where they are: `the-report-keeps-no-watched-list` (5.5),
  `four-templates-still-say-no-link-reaches-a-bankruptcy` (templates),
  `a-company-holder-carries-no-business-number` (companies lane).

## Next

1. The integrator merges `fix-report-2`, restarts `qv4-report`.
2. The template fixes the cards name; the recruitment and healthcare real
   tests assert the old not-held line and change with their templates.
3. Step 5.2 continues on this shape.
