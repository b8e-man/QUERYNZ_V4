# Real Estate Authority decisions

hosts: rea.govt.nz, decisions.dotnous.com

Class: the published decisions of the Real Estate Authority's Complaints
Assessment Committees, with the Real Estate Agents Disciplinary Tribunal
and appeal decisions the Authority files beside them (Real Estate Agents
Act 2008). The Authority's page `rea.govt.nz/complaints-and-decisions/
complaint-decisions/` links its "Decisions database", which a contractor
runs at `decisions.dotnous.com/reaa/v2/`. Lane:
`registers/real_estate_authority`. This position covers only `/reaa/` on
that host.

1. **Is the page open?** Yes. The database's listings
   (`default.aspx`), each decision's abstract (`abstract.aspx?case=N`)
   and the decision PDFs (`/reaa/pdfs/`) answer a plain request with no
   login, challenge or CAPTCHA (read 18 October 2026 through the fetch
   gate). The Authority's own pages carry a reCAPTCHA only on their
   feedback form, which we never use. `decisions.dotnous.com/robots.txt`
   says `Disallow: /` for every agent; under hard limit 5 a robots file is
   not a permission decision (ruling 10), so it is archived and read for
   a crawl delay only (none stated).
2. **Is storing it lawful copying?** The Authority's terms
   (`rea.govt.nz/terms-of-use-and-privacy-statement/`, archived) say its
   information "may be reproduced, free of charge, for personal or
   in-house use only", sourced to the Authority with the date of
   publication; any other use is to be asked of the Authority. Capture and
   hold for our own research is in-house use. A Committee or Tribunal
   decision may also fall under the Copyright Act 1994, section 27 (no
   copyright in the judgments of a court or tribunal): lawyer to confirm.
   Showing or selling waits on that, or on the Authority's permission.
3. **What terms did we accept?** The Authority's terms of use, which
   apply on use of its site: no bar on machine reading; reproduction
   beyond in-house use needs its permission; attribution and date. The
   contractor's host shows no terms of its own.
4. **What does privacy law, or the statute, limit?** Decisions name the
   licensee (in a professional role, published by the Act's scheme) and
   may name or describe complainants, vendors and buyers, and give a
   property address, which may be a person's home. The Authority says
   decisions are published after the 20-working-day appeal period and
   "remain on the public register for 3 years"; the database itself
   reaches back to 2010. So: the lane's tables hold the case number, the
   complaint number, the decision date, the deciding body and the
   document hashes, never a name or an address; nothing is published;
   an address, if ever extracted, is held in
   `real_estate_authority_private` and never shown (hard limit 15).

**Crawl delay:** none stated on either host. **Floor we use:** 5 seconds
between requests to `decisions.dotnous.com`, one at a time, off-peak
(22:00 to 06:00 NZ time), oldest year first, each page fetched once.

Written 18 October 2026 by the windowed session (track E), from the
pages read that evening. A lawyer reviews this page before anything is sold.
