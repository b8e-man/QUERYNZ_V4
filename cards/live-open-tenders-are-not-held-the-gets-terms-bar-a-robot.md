# Live open tenders are not held: GETS's public listing is open, but its terms bar any spider or robot
kind: finding
state: open
use-case: 10 tender and award intelligence (alerts on new opportunities)
session: procurement-1
opened: 2026-10-22

Step 6.3's first source. On 22 October 2026 `www.gets.govt.nz` answered its current-tenders listing with no login
or challenge (two requests: the home page and the terms). Its terms of 7 March 2024 (sha256 `507f5b88…`, landed,
source `tenders`) deem a visitor to accept them (1.1) and bar using "any software or other method (whether
automatic or manual), including any spider or robot, to monitor, copy, collect or index any data, Information or
content found on GETS" (3.2(i)(e)); republication must be non-commercial or "not to create a competing product"
(3.5(v)(f)). So nothing is captured: no job or session asks the site again. The position is
`registers/tenders/position/government-electronic-tenders-listing.md` (to move); a test holds it to the landed
terms and holds the lane to naming no GETS address in its code.

What closes it: the ministry's written leave (queue `whether-to-ask-the-ministry-to-read-the-gets-listing`, a
paragraph for the letter already sent), then the capture and a `pub.open_tenders` view in the tenders lane: RFx
ID, title, agency, type, open and close dates, never the contact person. Until then use case 10 answers "what was
awarded" from the award notices and "what is open now" not at all; that is a line for its known-limits page at the
checkpoint.
