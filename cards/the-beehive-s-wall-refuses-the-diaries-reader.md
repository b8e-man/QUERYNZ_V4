# The Beehive's wall refuses the ministers' diaries reader
kind: blocker
state: closed
use-case: 15
session: diaries-1
opened: 2026-10-21
closed: 2026-10-21

Template 4(a), the ministers' diary register, has no documents: every
diary release is on www.beehive.govt.nz, which sits behind an Incapsula
wall. 21 October, 16:0x NZDT: robots.txt and the sitemap, asked plainly
with the estate's User-Agent, came back as the wall's 212-byte shell. A
real headed Chromium (registers/ministers_diaries/browser.py's way; old
rulings 133/242/243) was served the home page with no challenge, then
refused (403, "Request unsuccessful. Incapsula incident ID") on
/advanced_search and, in a fresh run a minute later, on a minister's
page. Seven requests in all; hard limit 6: failed reads, logged, stopped.
An off-peak retry of four pages was set for 22:00 but the session could
not hold a wait that long, so it never ran.

What unblocks it, in order: (1) one off-peak attempt by a hand run or the
proposed capture job (four pages, stop on the first refusal); (2) if
refused again, Arthur's letter to the Beehive's web team (DPMC) asking
that the reader be let through, queue item
`may-we-ask-the-beehive-to-let-the-diaries-reader-through`. Not a route:
an archive's copy of the Beehive's pages (that goes around the block).

Closed by the integrator at the merge of `diaries-1` (21 October 2026) under ruling 78: Arthur, 18:20, "forget about capturing the beehive and hansard I have a 3rd party source". The Beehive is not captured and no letter is written; the diary register is built from the third-party source once he names it (its position first, ruling 61). The queue item `may-we-ask-the-beehive-to-let-the-diaries-reader-through` closes with it.
