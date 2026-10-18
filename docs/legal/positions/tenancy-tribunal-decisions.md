# Tenancy Tribunal orders

hosts: forms.justice.govt.nz

Class: the published orders of the Tenancy Tribunal (Residential Tenancies
Act 1986), served by the Ministry of Justice's search tool at
`forms.justice.govt.nz/search/TT/`. Lane: `registers/tenancy_tribunal`.
The host also serves other Ministry forms and tribunals; this position
covers only `/search/TT/`, its listing service
(`/forms/publicSolrProxy/solr/TTV2/`) and the order files under
`/search/Documents/TTV2/`.

1. **Is the page open?** Yes. The search page, its listing service and the
   order PDFs answer a plain request with no login, key, challenge or
   CAPTCHA (read 18 October 2026, 21:2x NZDT, through the fetch gate).
   The listing service is the one the page's own script calls. The host
   reset the connection on `robots.txt`; the gate treats that as
   unreadable and applies its polite floor. In August 2026 the old estate
   found the host dropping it on every path; if that recurs it is a block:
   a failed read, logged, and the run stops (hard limit 6).
2. **Is storing it lawful copying?** Orders are decisions of a tribunal.
   The Copyright Act 1994, section 27, puts no copyright in the judgments
   of a court or tribunal (lawyer to confirm that a Tenancy Tribunal order
   is within it). We copy each order once, as published, and change
   nothing.
3. **What terms did we accept?** None. The search tool shows an "Important
   Information" page (archived, `searching.html`): orders older than three
   years are not available; names are as given by the applicant and not
   verified; it "is not intended to provide an authoritative background
   check". No click-through, licence or bar on machine reading is shown.
   The Ministry's general copyright statement on `www.justice.govt.nz` is
   not yet read (outside this position's hosts): read before selling.
4. **What does privacy law, or the statute, limit?** Orders name landlords
   and tenants, and the listing carries the tenancy address, which is
   usually a tenant's home. The Act lets the Tribunal suppress names or
   not publish an order; a suppressed order is simply not listed. The
   three-year limit is the Ministry's own choice and protects tenants;
   holding orders past it is a privacy question (Privacy Act 2020: a
   publicly available publication, but use must not be unfair or
   unreasonable). So: the lane's tables hold only the order and
   application numbers, the dates and the document hash; no name and no
   address leaves the document store; nothing is published or shown;
   the tenancy address is a home address (hard limit 15) and if ever
   extracted lives only in `tenancy_tribunal_private`. Whether orders are
   kept past their three years is in the decision queue
   (`tenancy-orders-past-their-three-years.md`, default: hold, never show).

**Crawl delay:** none stated (robots.txt unreadable). **Floor we use:** 5
seconds between requests to the host, one request at a time, off-peak
(22:00 to 06:00 NZ time), oldest-to-expire first, each order fetched once.

Written 18 October 2026 by the windowed session (track E), from the
pages read that evening. A lawyer reviews this page before anything is sold.
