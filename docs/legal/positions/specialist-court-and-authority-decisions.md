# Specialist courts' and authorities' own decisions: the Employment Court, the Employment Relations Authority, the Environment Court, the Coroners and the Māori Land Court

hosts: employmentcourt.govt.nz, era.govt.nz, employment.govt.nz, environmentcourt.govt.nz, coronerscourt.govt.nz, maorilandcourt.govt.nz, xn--morilandcourt-wqb.govt.nz

Class: the decisions these bodies publish on their own sites: the Employment Court's judgments
(`employmentcourt.govt.nz/judgments/`), the Employment Relations Authority's determinations
(`determinations.era.govt.nz`, the search tool on `employment.govt.nz`), the Environment Court's
decisions page (which sends a reader to NZLII; NZLII is not a source), the Coroners' published
findings (`coronerscourt.govt.nz`) and the Māori Land Court's own pages (`maorilandcourt.govt.nz`).
Lane: `registers/courts` (ruling 140: what the MCP's courts corpus lacks). Written 3 November 2026
by the courts-sources survey, before any of these hosts was asked; the answers below were then
checked against the few pages the survey read through the fetch gate
(`docs/research/courts-sources-2026-11-03.md`).

1. **Is the page open?** Yes, on the pages the survey read through the gate on 3 November 2026, with
   no login, key, challenge or CAPTCHA: the Employment Court's judgments page (its listing is the
   Ministry's decisions finder, jurisdiction 17, `court-judgments.md`); the Authority's determinations
   page, one year's search answer and its recent list (each determination a page
   `/determination/view/<n>` and a PDF under `/assets/elawpdf/<year>/`); the Coroners' findings pages
   (files under the Ministry's `/assets/Documents/Decisions/`); the Māori Land Court's judgments page
   (which sends the reader to the Ministry's finder, jurisdictions 24 and 468). The robots files state
   no crawl delay; `determinations.era.govt.nz` disallows `/determination/` and `/assets/elawpdf/`,
   which under hard limit 5 is not a permission decision. The Environment Court's own decisions page
   sends a reader to NZLII and holds no listing of its own. A login, a challenge or a block stops the
   host's capture (hard limit 6); none is got around.
2. **Is storing it lawful copying?** The Copyright Act 1994, section 27(1)(g), puts no copyright in
   the judgments or decisions of a court or tribunal; the Ministry of Justice's own decisions pages
   say so. A coroner's finding is a decision of a court (the Coroners Court); lawyer to confirm, and
   to confirm a determination of the Authority. We copy each decision once, as published, and change
   nothing. Media releases and summaries beside a decision are not taken.
3. **What terms did we accept?** None found on the pages read: no click-through, licence or bar on
   machine reading before a decision. Each site's own terms or copyright page is read at the first
   capture run and landed; a bar on robots found there stops that host (as GETS's did).
4. **What does privacy law, or the statute, limit?** Employment determinations and judgments may
   carry non-publication orders (Employment Relations Act 2000, Schedule 2 cl 10; the Court's own
   orders); the Authority publishes no PDF where a restriction applies. Coroners' findings are
   restricted by the Coroners Act 2006, ss 71 to 76 (no detail of a self-inflicted death's method;
   a coroner's order may suppress a name or evidence); a finding is published as the coroner
   released it. Māori Land Court decisions concern whānau, land and succession and name living
   people. The lane keeps every name and detail each prints (ruling 142, 4 November 2026): any
   marker is a flag beside the rows it reaches with the source's words, the names it covers kept
   whole in `courts_private.withheld_names` and never in a `pub.court_*` view (hard limit 16); a
   party's address, age, date of birth, email and phone are kept in `courts_private.identifiers`
   only (hard limit 15); suppression is applied at a product's export. Nothing is shown outside the
   local network (hard limit 13), and a new connection about a named person waits on Arthur's word
   (hard limit 14).

**Crawl delay:** each host's robots.txt is read for a stated delay only (hard limit 5).
**Floor we use:** 5 seconds between requests to a host, one at a time, off-peak (22:00 to 06:00 NZ
time) for the backfill, each file fetched once; a file the MCP already holds (same sha256) is never
fetched twice once its address is known.

A lawyer reviews this page before anything is sold.
