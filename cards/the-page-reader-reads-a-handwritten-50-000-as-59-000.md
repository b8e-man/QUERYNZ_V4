# The page reader reads a handwritten $50,000-00 as $59,000
kind: finding
state: open
use-case: 1
session: disclosures
opened: 2026-10-20

`form_check` differs on `ec-listing/2023-06-13/5912c64f7260` (National,
received 13 June 2023, not amended): the table says $50,000.00, the stored
GLM-OCR reading of the scan (`b688af162f6d…`, page 1, stamp
`glm-ocr/229e9f4fb9ff048e ec-donation-disclosure-20k@3`) says $59,000.

The total box was looked at (a crop of that box alone, no donor lines): it
is handwritten "$50,000-00", 12 June 2023. The table is right; the reading
is wrong, a 0 read as 9 in a handwritten figure. The lane keeps the
table's amount (it is the source for the field) and reports the
difference, so nothing published is wrong.

What would fix the check: a second reading of handwritten total boxes, or
an accepted limit on the known-limits page ("a handwritten total may be
misread; the table's figure stands"). Not worked here.
