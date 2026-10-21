# The Lottery's records of grants: the walk, the older years, and the other Lottery funds
kind: finding
state: open
use-case: 9, 14; step 6.3
session: grants-1, grants-2
opened: 2026-10-21

One Lottery record of grants is read (2024/25 round two, Community National: 156 grants, $14,710,725, 61
multi-year), on the sample database only. The records hang off no index page on Community Matters, so
`qv4-grants-capture` walks the site whole.

**The first walk (live database, 22 October 2026 00:22 to 00:23, read through `bin/q`):** 20 requests; 15 pages of
Community Matters landed (the home page, the Lottery fund and its four sub-pages, eight other funds and trusts),
none a record of grants; 64 addresses in the frontier, 15 asked, to depth 2; then HTTP 403 on the sixteenth page
(`/chinese-poll-tax-heritage-trust-2`), a block, so the host was stopped for the night. The national file was
landed and read (178,729 grants live). The check is red, correctly: no Lottery record of grants read.

**A defect it showed, fixed by grants-2:** a page that blocked was never marked asked, so it stayed first in the
frontier and every later night would open on it and stop. The capture now marks it asked with the status that
blocked (a test and a mutant hold this). Whether the 403 belongs to that page or comes after about fifteen requests
at 5 s is not known: if the next nights also stop near fifteen pages, raise Community Matters' floor (10 s, then
30 s) before anything else.

Three things to watch as the walk goes on:

1. Search titles show headings in several shapes (year first or last, the round before or after the committee,
   "2024-25" with a hyphen) and some funds call the page "grants made"; `read.heading_parts` takes all seen. A record
   the walk lands whose address says record of grants and whose shape no profile recognises becomes a catch-log
   line and turns the check red: a new profile version, not a code change. **Not yet tested: no record landed.**
2. Records before the site's current pages: the government data catalogue held the Department's Lottery recipient
   CSVs (Community committees to 2017/18, Health Research, Community Sector Research and others). On 21 October
   2026 the catalogue answered a search with a challenge; a package page asked directly may answer. 2017 on only.
   **Not tried.**
3. Community Matters' own copyright statement was not read (the host refused before it was reached); the capture
   should add its address to `ABOUT` once the walk has found it, and the position updated from it. **Not met.**

What the walk must show, by the time this card closes: `grants.capture_docs` holding pages recognised as
`lottery-record-of-grants-page` for every Lottery committee and round from 2017/18 on that the site carries, each
read with its printed total equal to its rows; the copyright page landed; and the frontier asked to the end.
