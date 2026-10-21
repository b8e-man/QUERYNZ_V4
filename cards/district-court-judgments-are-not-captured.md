# The District Court's judgments are not captured
kind: finding
state: open
use-case: 2
session: courts-1
opened: 2026-10-21

The old estate holds no District Court judgment, and its judgment listing on
districtcourts.govt.nz has not been looked at: the fetch gate refuses the
host until the position (`court-judgments.md`, written by courts-1, covering
it) is on file, and this session fetched nothing around it. Once it is: read
the listing page and its paging through the gate (recon before a scraper;
look for a feed or an index first), write `courts-nzdc-judgment` from the
first documents held, and add the host to `capture.py`. Judicial Decisions
Online stays out (the Ministry letter is Arthur's).
