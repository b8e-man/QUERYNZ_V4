# Overseas Investment Office decision summaries (draft position, ruling 61)

hosts: www.linz.govt.nz

Class: the decision summaries the Overseas Investment Office (part of
Toitū Te Whenua Land Information New Zealand) publishes for each consent it
grants or declines under the Overseas Investment Act 2005, and for each
transaction notified under a standing consent, at
`/our-work/overseas-investment-regulation/decisions`. Lane:
`registers/overseas_investment`. This position covers only that listing,
its summary pages and the site's copyright, disclaimer and privacy pages on
`www.linz.govt.nz`; not the LINZ Data Service, Landonline or any other
LINZ host, which carry their own terms. Draft, held in the lane's folder
because the fence keeps a build session out of `docs/legal/positions/`;
the integrator moves it there. Read 21 October 2026 by oio-1.

**Finding: captured. Nothing bars it.**

1. **Is the page open?** Yes. The listing (60 rows a page, filtered by
   year: `?field_decision_date_value=YYYY&page=N`), each summary page and
   the pages about the site answered 200 to a plain request with no login,
   lock or challenge (21 October 2026, through the fetch gate, 5 s apart).
   `www.linz.govt.nz/robots.txt` (archived, `fae94744…`) disallows only
   Drupal's own folders, admin, search and login paths, and states no
   crawl delay; under hard limit 5 it is read for a delay only.
2. **Is storing it lawful copying?** Yes. The copyright page
   (`4c1e3213…`, `/copyright`): material produced by Toitū Te Whenua and
   published on linz.govt.nz "constitutes Crown copyright … licensed under
   the Creative Commons Attribution 4.0 International licence. In essence
   you are free to copy, distribute, and adapt the work, as long as you
   attribute the work". No emblem or logo may be used; we take none.
   Attribution is owed on any surface that shows a row, in the form the
   page gives for an adapted work; the views carry it.
3. **What terms did we accept?** The licence and the disclaimer
   (`ec3aa019…`): no warranty of accuracy, the office may change or remove
   material without notice, not legal advice, links do not imply
   endorsement. Neither bars machine reading or reuse.
4. **What does privacy law, or the statute, limit?** The office publishes
   these summaries under the Act's scheme for publishing decisions, and
   withholds what it judges it must under the Official Information Act
   1982 (section 9(2)(b)(ii) for a commercial figure; a name where it
   withholds one). The summaries name individuals: applicants buying land
   to live on, vendors, trustees and the people behind an ownership line,
   with their country of origin and their share. They also give the
   land's street address, which for an individual buyer or seller is often
   a home, and a "More information" contact (the applicant's lawyer, with
   an office address). What the estate holds (rulings 142 and 143, 4
   November 2026): names as the office publishes them; where the office
   withholds a name it prints none, the row carries that flag and its
   ownership origins, and what the cell prints in the name's place is kept
   in `overseas_investment_private`; the investment statement is kept and
   published whole, the land's street address and legal description
   included, with `addresses_named` beside it (the flag a product applies
   hard limit 15 by); every headed row of the page, the "More information"
   contact and the Background among them, is kept whole in
   `overseas_investment_private`; a summary the office takes down stays,
   flagged with the date of the first finished pass that no longer listed
   it. Privacy is applied at a product's export.

Crawl delay: none stated. Floor: one request at a time, at least 5 s
apart, off-peak (22:00 to 06:00 NZ time), a pass of each year's listing
from 2017 weekly (about 25 pages in all), each summary fetched once and
again only when a row listing it changes; a 403, 429 or challenge stops the
run. Author: oio-1 (Opus), 21 October 2026. A lawyer reviews this page
before anything is sold.
