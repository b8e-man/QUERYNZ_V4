# Four parts of two promoter returns are unread against the Commission
kind: finding
state: open
use-case: 1
session: party-finance
opened: 2026-10-20

The lane reads each part of a registered promoter's return (the
declaration's box and the schedule's total). Of 49 Commission figures, 44
equal the return, 0 differ, and these are unread (`party_finance.set_aside`,
stage `promoter-return`):

- Public Service Association 2020 (`b06cfe9fb29e`), Parts A, B and C: the
  return writes N/A by hand in each "Write 'N/A'" box and leaves every
  figure box empty; the page reader drops handwriting, so no N/A is read.
  The Commission prints $0.00. The lane does not read an N/A as zero.
- Make It Legal Aotearoa 2020 (`a3d55222c5b8`), Part B: the filer wrote
  $104,780.84 in the "Write 'N/A'" box on the declaration and on the
  schedule, and left Part B's own boxes empty. Looked at: both boxes
  show the Commission's figure. Only the declaration's text layer carries
  it, interleaved with the next column, so no rule is written for one
  misplaced box.

The Better NZ Trust 2023 is linked by the Commission and not held (the
capture card already says so).

Fix, if wanted: a typed reading of the "Write 'N/A'" box by cropping at
its label (lesson `look-at-one-box-of-a-form-by-cropping-at-its-label`),
a page-reader job; not this lane. Blocks nothing: `pub.promoter_expenses`
carries the Commission's figure with `…_agrees` NULL for these.
