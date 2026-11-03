# Waitangi Tribunal reports

hosts: waitangitribunal.govt.nz

Class: the Waitangi Tribunal's reports, published as PDFs on its own site and listed there by Wai
number, by year and by inquiry type (`waitangitribunal.govt.nz/publications-and-resources/waitangi-tribunal-reports/`).
The record of inquiry documents and the research reports commissioned for inquiries are a separate
class and not covered. Lane: `registers/courts` (ruling 140). Written 3 November 2026 by the
courts-sources survey before the host was asked, then checked against the pages it read through the
fetch gate (`docs/research/courts-sources-2026-11-03.md`).

1. **Is the page open?** The listing is: `waitangitribunal.govt.nz/tribunal-reports/by-wai-number`
   answered the survey through the gate on 3 November 2026 with no login or challenge, and its robots
   file states no crawl delay. The 206 report PDFs it links are served by the Ministry of Justice from
   `forms.justice.govt.nz/search/Documents/WT/`, which reset the connection twice that day: a failed
   read (hard limit 6), so no report is fetched until that host answers. A login, challenge or block
   stops the capture; none is got around.
2. **Is storing it lawful copying?** A Tribunal report is the report of a commission of inquiry, not
   plainly a "judgment or decision" within the Copyright Act 1994, s 27(1)(g); a report of a
   commission of inquiry is within s 27(1)(f) ("reports of Royal commissions, commissions of
   inquiry, ministerial inquiries or statutory inquiries"), which also has no copyright. Lawyer to
   confirm. We copy each report once, as published, and change nothing.
3. **What terms did we accept?** None found before a report; the site's copyright page is read and
   landed at the first capture run.
4. **What does privacy law, or the statute, limit?** Reports name claimants, kaumātua and whānau, and
   discuss wāhi tapu; some evidence is held confidential by the Tribunal and never appears in the
   published report. The published report is kept whole, as released (ruling 142, 4 November 2026); a
   suppression it states is a flag beside the rows it reaches, the names it covers kept in
   `courts_private` and never in a `pub.court_*` view (hard limit 16); nothing is shown outside the local network (hard limit 13); no new connection about a
   named person without Arthur's word (hard limit 14).

**Crawl delay:** robots.txt read for a stated delay only (hard limit 5). **Floor we use:** 5 seconds
between requests, one at a time, off-peak, each PDF fetched once.

A lawyer reviews this page before anything is sold.
