# The GETS public listing of current tenders (draft position, ruling 61)

hosts: www.gets.govt.nz, gets.govt.nz

Class: the Government Electronic Tenders Service's public pages of current,
late, closed and completed tenders (`www.gets.govt.nz/ExternalIndex.htm`
and its siblings, a page per tender, an RSS page), run by the Ministry of
Business, Innovation and Employment. Lane: `registers/tenders`, beside the
award notices (`government-procurement-award-notices.md`), which this does
not change. Draft in the lane folder; the integrator moves it. Surveyed 22
October 2026, 19:46 NZDT, through the fetch gate, two requests and the
robots file: the home page and the terms. Outcome: **not captured.**

1. **Is the page open?** Yes. The home page is the current-tenders listing
   and answered 200 with no login, key or challenge; it links each tender's
   detail page. Tender documents need a supplier login, which is never used
   (hard limit 6). Robots (`www.gets.govt.nz.4c45459bcb2d.txt` in the gate's
   archive) bars one SEO crawler and states no crawl delay.
2. **Is storing it lawful copying?** Crown copyright, licensed for reuse
   under NZGOAL (terms clause 3.5(ii)), except material posted by users,
   which includes every tender notice an agency posts (3.5(iii)). Clause
   3.5(v) lets tender documents be republished only if "the use is
   non-commercial or is not to create a competing product", with the
   purchaser's contact details left out.
3. **What terms did we accept?** The terms
   (`GetsTermsAndConditions.htm`, sha256
   `507f5b88e776190e8f8b6703247d5202d4e489df63ec3e6e0e01f7aa4012a462`, last
   updated 7 March 2024) say in 1.1 "By registering as a User or using GETS
   you are deemed to have accepted the terms of this Agreement", and in
   3.2(i)(e) that you agree not to "use any software or other method
   (whether automatic or manual), including any spider or robot, to
   monitor, copy, collect or index any data, Information or content found
   on GETS". That bars this lane's capture, the RSS page included. Clause
   4.6(ii) defines "you" as a registered person, so whether a visitor who
   never registers is bound is a question for the lawyer; until it is
   answered the bar is read as binding.
4. **What does privacy law limit?** A tender page names the purchaser's
   contact person, with a phone and an email. They would never be read or
   kept (hard limit 15), and 3.5(v)(c) asks the same.

So: no job asks `www.gets.govt.nz`, and no session does beyond this survey.
The survey's copy of the home page was kept in the session's scratch folder
only, never landed, and removed; the terms page is landed by its hash
(source `tenders`) so this page's citation can be checked. What would change
it: the ministry's written permission for a research aggregator to read the
public listing, which can go with the letter already sent about the open-data
files (queue `whether-to-ask-the-ministry-to-read-the-gets-listing`). Open
tenders are not otherwise held; the award notices stay the estate's record
of what GETS awarded.

Crawl delay: none stated. Floor if ever permitted: 5 s, one request at a
time, off-peak. Author: procurement-1 session (Opus), 22 October 2026.
