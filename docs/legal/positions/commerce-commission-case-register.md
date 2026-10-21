# Commerce Commission case register (draft position, ruling 61)

hosts: comcom.govt.nz

Class: the Commerce Commission's published case register, one entry per
merger or authorisation application and per investigation under the laws it
enforces (Commerce Act 1986, Fair Trading Act 1986, Credit Contracts and
Consumer Finance Act 2003 and others), with its outcome when the case
closes. Lane: `registers/commerce_commission`. Draft, held in the lane's
folder because the fence keeps a build session out of
`docs/legal/positions/`; the integrator moves it there. Read 21 October 2026
by regulators-1.

**Finding: captured. Nothing bars it.**

1. **Is the page open?** Yes. The listing (`/case-register/?q=&size=100&page=N`),
   each entry and the pages about the site answered 200 to a plain request
   with no login, lock or challenge (about twenty requests, 5 s apart, 21
   October 2026). `comcom.govt.nz/robots.txt` disallows only `/admin`,
   `/dev` and two error pages and states no crawl delay; under hard limit 5
   it is archived and read for a delay only.
2. **Is storing it lawful copying?** Yes. The copyright page
   (`aebe0cb7…`, `/using-our-website/copyright/`): Crown copyright, owned by
   the Commission on behalf of the Crown, "licensed for re-use under a
   Creative Commons Attribution 4.0 International Licence … you are free to
   copy, distribute and adapt the material, as long as you attribute it to
   the Commerce Commission". Logos, design and images are excluded; we take
   none. Attribution is owed on any surface that shows a row.
3. **What terms did we accept?** The licence and the disclaimer
   (`51e866a0…`): the information is general, not legal advice, and project
   dates "are not official". Neither bars machine reading or reuse. A link
   must not imply endorsement.
4. **What does privacy law, or the statute, limit?** The register names
   businesses, and sometimes individuals. The Commission's own account
   (`8cf57526…`, "About our case register") says it publishes a party's name
   in a civil matter unless "the party is an individual" or evidence needs
   protecting, and in a criminal matter only for public safety, prior
   publicity or self-reporting; it writes "Withheld" otherwise. "The
   existence of an investigation does not mean that there has been a breach
   of the law, as only a court can make that determination." So: a name the
   Commission withholds stays withheld on every surface; a name a page says
   is suppressed (Criminal Procedure Act 2011, ss 200 to 211) is withheld
   with the heading and the page address that carry it (hard limit 16); an
   open case is shown as an investigation, never as a finding; an entry the
   Commission removes leaves our views at the next load. The Privacy Act
   2020 asks fair use of what a person was named in: the queue item on how
   long a regulator action naming an individual is shown carries the
   default "while the regulator shows it". No address is read; the contact
   person (Commission staff) is never read (hard limit 15).

Crawl delay: none stated. Floor: one request at a time, at least 5 s apart,
off-peak (22:00 to 06:00 NZ time), a full pass of the listing weekly
(eighteen pages), each entry fetched once and again only when its card
changes; a 403, 429 or challenge stops the run. Author: regulators-1 (Opus),
21 October 2026. A lawyer reviews this page before anything is sold.
