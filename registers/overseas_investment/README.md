# registers/overseas_investment — overseas investment decision summaries

Step 5.3, a held-and-unread source (for use case 12, property developer
due diligence). The decision summaries the Overseas Investment Office
publishes for each consent it grants or declines (applicant, vendor,
the land or business, consideration where stated, the decision and its
date), captured verbatim by hash through the fetch gate under the four
questions, read by profile into one row per decision and one per named
party, checked against the office's own listing count.

Built by `oio-1`; `spec.md`, `capture.py`, `read.py`, `load.py`,
`publish.sql`, `check.py`, `sample.list`, `tests/` and the position page
are its deliverable.
