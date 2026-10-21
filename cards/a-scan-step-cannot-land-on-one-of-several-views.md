# A scan step cannot land on one of several views
kind: finding
state: open
use-case: 9 government procurement integrity
session: scan-templates-1
opened: 2026-10-21

A scan's first step may start from several views (one query each), but
every later step lands on one view. Use case 9 asks for a supplier's
people, directors and shareholders both, so template 2 is two scans with
one question: `procurement-directors-donors` and
`procurement-shareholders-donors`, each with its own page, files and run.
Beside it, the same gap at the start: a filter applies to every start view,
so `replaced_by = null` (113 of 1,315 party-return donor rows an amendment
replaced) cannot be asked of the party returns alone, and a replaced row is
listed beside its amendment (on both templates' known-limits pages).

What the shape would need: a step with `views = [...]` and a filter per
view (`where.<view> = {...}`), compiled as one query per combination like
the starts. Owner: products/scan (a fix session); no template change but
merging the two folders into one.
