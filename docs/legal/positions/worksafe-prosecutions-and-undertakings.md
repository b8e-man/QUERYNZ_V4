# WorkSafe New Zealand prosecutions and enforceable undertakings (draft position, ruling 61)

hosts: worksafe.govt.nz

Class: WorkSafe New Zealand's published court summaries (one per
prosecution decided under the Health and Safety at Work Act 2015 and the
Acts before it) and the enforceable undertakings it has accepted under that
Act. Lane: `registers/worksafe`. Draft, held in the lane's folder because
the fence keeps a build session out of `docs/legal/positions/`; the
integrator moves it there. Read 21 October 2026 by regulators-1.

**Finding: captured. Nothing bars it.**

1. **Is the page open?** Yes. Both lists, the item pages and the copyright
   and privacy pages answered 200 to a plain request with no login, lock or
   challenge (about twenty requests, 5 s apart, 21 October 2026).
   `www.worksafe.govt.nz/robots.txt` disallows `/admin/`, `/security/`,
   `/search` and error pages and states a crawl delay (10 s) for Bingbot
   only; under hard limit 5 it is archived and read for a delay only, and
   none is stated for us.
2. **Is storing it lawful copying?** Yes. The copyright statement
   (`331764a0…`, `/about-us/about-this-site/copyright/`): "Material may be
   reproduced free of charge in any format or media without requiring
   specific permission. This is subject to the material being reproduced
   accurately and not being used in a derogatory manner or in a misleading
   context. Where the material is being published or issued to others, the
   source and copyright status must be acknowledged." Third-party material
   is excluded. So every surface shows the facts as stated, cites the page
   and names WorkSafe as the source; nothing is paraphrased into a finding.
3. **What terms did we accept?** The copyright statement and the privacy
   statement (`259dceab…`); neither bars machine reading or reuse.
4. **What does privacy law, or the statute, limit?** The duty holders are
   mostly companies; some are individuals. WorkSafe publishes a code in
   place of a defendant it does not name ("2019-A"). What the estate holds
   (ruling 142, 4 November 2026): that code, a name written withheld or
   suppressed, or a name a page states a suppression over (Criminal
   Procedure Act 2011, ss 200 to 211), is flagged on the lane's tables and
   views, and what the page prints in its place, with the heading and page
   address, is kept whole in `worksafe_private` under the row's key. The
   facts in brief, the incident and the safety lessons describe the
   victim, the family and the place: each headed section is kept whole in
   `worksafe_private`. An undertaking is accepted in place of a prosecution
   and is not a conviction. An item WorkSafe takes down stays, flagged with
   the date of the first finished pass that no longer listed it. Privacy
   and suppression are applied at a product's export.

Crawl delay: none stated for us. Floor: one request at a time, at least 5 s
apart, off-peak (22:00 to 06:00 NZ time), a full pass of both lists weekly
(about 35 pages), each item fetched once and again only when the list shows
it changed; a 403, 429 or challenge stops the run. Author: regulators-1
(Opus), 21 October 2026. A lawyer reviews this page before anything is sold.
