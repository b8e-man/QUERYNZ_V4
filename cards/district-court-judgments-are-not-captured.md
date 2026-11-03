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

3 November 2026 (ruling 140): the District Court's judgments are published in Judicial Decisions Online (2,015 by its
listing, against 321 the MCP holds), and the estate's own capture of JDO (`registers/courts/own.py`, job
`qv4-courts-jdo-capture`, nightly from 22:00) walks it third, after the High Court and the Court of Appeal. The card
closes when the walk has finished the District Court's years and the load has read them with `courts-nzdc-judgment`.
