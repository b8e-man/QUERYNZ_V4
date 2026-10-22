# The old estate's 347 InfoCouncil minutes PDFs are on its other box, so they are listed by hash and not yet copied
kind: finding
state: open
use-case: none (step 6.3, council minutes)
session: councils-1
opened: 2026-10-22

The old estate lists 351 InfoCouncil minutes PDFs (`incoming_news.documents`, 14 instances, 26 July to 18 October
2026), exported once and pinned (`registers/council_minutes/capture.py` `LISTING_SHA` 2264a857…). None of the files
is on node2: their paths are under `/home/user/querynz-data/documents/`, which on node2 holds 850 other files, and
node1 does not answer. The capture never fetches them again: 347 are named by today's listings and recorded `held by
the old estate` with their listed hash (the other 4 are Christchurch's, held). The old estate's other 1,159
InfoCouncil minutes were kept as stripped text, never bytes, so those are fetched.

When node1 is in service (ruling 57), run `python -m registers.council_minutes.capture --copy-old` on the box that
holds the files (the integrator's hand, under the scheduler's mark); each file that hashes true is landed by its hash
and the meeting rows say `landed` at the next load. Until then the rows carry the old hash and say so.
