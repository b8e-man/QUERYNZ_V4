# Financial Markets Authority warnings and enforcement (draft position, ruling 61)

hosts: fma.govt.nz

Class: the Financial Markets Authority's published warnings and alerts
(`/library/warnings-and-alerts/`, "the names of businesses or individuals
you should be wary of") and its enforcement cases
(`/about-us/enforcement/cases/`), under the Financial Markets Authority Act
2011 and the Acts it administers. Lane: `registers/fma`. Draft, held in the
lane's folder because the fence keeps a build session out of
`docs/legal/positions/`; the integrator moves it there. Read 21 October 2026
by regulators-1.

**Finding: captured. Nothing bars it.**

1. **Is the page open?** Yes. Both lists, the item pages and the copyright
   and privacy pages answered 200 to a plain request with no login, lock or
   challenge (about thirty requests, 5 s apart, 21 October 2026). The site
   sits behind Cloudflare: its pages carry Cloudflare's scripts and email
   obfuscation, and no challenge was shown. A challenge page, recognised by
   its own title, stops the run (hard limit 6). `www.fma.govt.nz` publishes
   no robots file (404), so no crawl delay is stated.
2. **Is storing it lawful copying?** Yes. The copyright page (`10229597…`,
   `264eb6fb…`): "Copyright material on the fma.govt.nz website is
   protected by copyright owned by the FMA … licensed for re-use under the
   Creative Commons Attribution 4.0 International Licence. In essence, you
   are free to copy, distribute and adapt the material, as long as you
   attribute it to the FMA". Logos, design and images are excluded; we take
   none. Attribution is owed on any surface that shows a row.
3. **What terms did we accept?** The licence; the privacy statement
   (`66172f0e…`) covers what the FMA collects from visitors. The "AI search
   – terms of use" page governs the site's own search assistant, which we
   never use. Nothing bars machine reading or reuse.
4. **What does privacy law, or the statute, limit?** The warnings and cases
   name companies and individuals, and a warning's labelled fields can give
   an address, telephone, email and bank account. None of those fields is
   read; only the names the FMA gives as the warned entity, the heading and
   the stated dates, Acts and sections (hard limit 15). A warning is the
   FMA's caution, not a finding, and is shown as such. A name the FMA
   withholds, or one a page says a court has suppressed, is withheld with
   the heading, summary, outcome and page address (hard limit 16). An item
   the FMA takes down leaves our views at the next load. The Privacy Act
   2020 asks fair use: the queue item on how long a regulator action naming
   an individual is shown carries the default "while the regulator shows
   it".

Crawl delay: none stated (no robots file). Floor: one request at a time, at
least 5 s apart, off-peak (22:00 to 06:00 NZ time), a full pass of both
lists weekly (about 56 pages), each item fetched once and again only when the
list shows it re-dated; a 403, 429 or challenge stops the run. The
warnings' CSV download was fetched once on 21 October 2026 while the shape
was surveyed (`a252bdc6…`, held, never read: it carries the address fields
and no page address). Author: regulators-1 (Opus), 21 October 2026. A lawyer
reviews this page before anything is sold.
