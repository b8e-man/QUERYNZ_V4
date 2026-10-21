# The HDC decisions lane is held: the Commissioner's copyright terms allow research use only, and any other use needs written permission
kind: blocker
state: open
use-case: 11 healthcare operator governance; step 5.3
session: hdc-1
opened: 2026-10-21

The Health and Disability Commissioner's copyright page (`/copyright/`, sha256 `d9686c4a…`, read 21 October 2026
through the fetch gate) allows reproduction "for personal, educational or research purposes" (3.1) and forbids any
other use "without the prior written permission" (3.2). Keeping every decision for a product that may be sold is
another use, so hard limit 4 holds the capture as briefed. Built and held: `registers/hdc_decisions` refuses to
capture into `querynz_v4`, load or publish until the position page carries an `authorised:` line; a proof into the
sample database (at most 40 pages a list) is allowed and is how the lane was built (twelve decisions and case studies
read, 2017 to 2026). The Commissioner's own count on 21 October 2026: 168 listing pages in all (2,010 decisions since
1998); 2017 alone, 49.

Closes when Arthur's decision (`docs/decisions/queue/whether-the-hdc-decisions-may-be-copied-for-the-estate.md`) is
made. If the Commissioner permits: add the `authorised:` line to the position, put the two proposed jobs (spec.md) in
the catalogue, let the first night run (about 85 listing pages and 1,000 decision pages), then point template 11's
`hdc-decisions` check at the two views. If not: drop the lane.
