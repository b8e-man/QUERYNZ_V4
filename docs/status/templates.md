# templates: where it stands

**Date:** 2026-10-28. **Session:** fix-products-templates-1 (fix weight,
`products/templates/`). **Merge request:** `fix-products-templates-1`
(raised).

After the links build of 28 October (rulings 114, 116) three live tests
went red; all are green now, one by a strict xfail on a blocker card:

- 03-banking: the twice-liquidated subject is a director row on a
  liquidated company, not the group's first director row.
- 12-property: the serial-pattern subject query starts from the failed
  companies; the same subject, over 600 s before, 1.4 s after (live, read
  only).
- 08-recruitment: the namesake count is 0 because the report walk reads
  the `name-only@1` star one hop and the subject's group is a spoke. The
  other assertions stay live; `near > 0` is a strict xfail until the walk
  follows the star (card
  `the-report-walk-reads-a-namesake-star-one-hop-so-a-spoke-sees-only-the-centre`).

No template rule changed. Open: the walk fix above, outside this fence;
until it lands a `prohibition` clear on a spoke subject is not a reading
of every namesake (about 90 of 160 prohibition rows with a namesake are
spokes).
