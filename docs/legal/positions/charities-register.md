# The Charities Register (draft position, ruling 61)

hosts: charities.govt.nz

Class: the Charities Register (Charities Act 2005), kept by Charities
Services (Department of Internal Affairs), as its open data feed publishes
it: the OData service at `www.odata.charities.govt.nz`, and the pages about
it on `www.charities.govt.nz`. Lane: `registers/charities`. The register's
own search (`register.charities.govt.nz`) and its login are not used.

Draft, held in the lane's folder because the fence keeps a build session out
of `docs/legal/positions/`; the integrator moves it there. Ruling 61: written
before product, not before capture. Read 20 October 2026 through the fetch
gate; every page cited is held in the document store by its hash.

1. **Is the page open?** Yes. The feed "is free to access and does not
   require registration"; "there is no authentication required ... and all
   access is read only" (the open-data page, `34e09f96…`). Every request
   answered with no login, key, challenge or CAPTCHA. Both hosts answer
   404 for `robots.txt`: no crawl delay is stated.
2. **Is storing it lawful copying?** "Use of this data is licensed under a
   Creative Commons Attribution 3.0 New Zealand License", Crown copyright
   (the open-data page). CC BY allows copying, adaptation and commercial use
   with attribution to Charities Services. The site's general copyright page
   (`40cd0971…`) allows "personal or in-house use" of website material and
   asks permission otherwise; the data's own licence is the narrower, later
   and specific statement for the feed. Lawyer to confirm that CC BY governs
   the feed and that the general page does not narrow it. Attribution is
   owed on every surface that shows the data.
3. **What terms did we accept?** None by click. The open-data page says the
   service "is intended to be used by software developers who wish to write
   applications making use of the data", which is our use; it caps every
   query at 1,000 rows to spare its systems, which we honour (pages of 1,000,
   `$returnall` never used). Its one stated limit: email addresses on the
   register are not deemed consent under the Unsolicited Electronic Messages
   Act 2007 and must not be harvested for marketing. We never use them so;
   the product need not show them. The terms of use (`ed0c9fc4…`) are a
   disclaimer only.
4. **What does privacy law, or the statute, limit?** Section 24 of the Act
   requires the register to show each charity's name, an address for
   service, its number, current and past officers, its rules, and its annual
   returns; section 25 lets Charities Services restrict information in the
   public interest, and restricted information "excludes any data which has
   been withheld from publication" in the feed. Charities Services states
   "We do not publish officers' dates of birth or home addresses" (`7770254f…`),
   and the feed's Officers set has no address or birth-date field. So officer
   names, roles and dates are published under statute (Privacy Act 2020: a
   publicly available publication; use must still be fair). Held apart or
   shown with care: an officer's disqualification flags (bankrupt, convicted,
   banned); a small charity's address for service, which may be a trustee's
   home (hard limit 15: shown as the charity's address, like a company's
   registered office, unless Arthur rules otherwise); emails and phone numbers
   (not shown). A row later restricted or withdrawn leaves the feed; the
   monthly full copy sees it gone, and the product stops showing it.

Crawl delay: none stated. Floor: 5 s of rest after each answer, one request
at a time, off-peak (22:00 to 06:00 NZ). Author: charities-capture session
(Opus), 20 October 2026.
