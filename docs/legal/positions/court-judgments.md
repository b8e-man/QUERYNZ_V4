# Court judgments: the Supreme Court, the Court of Appeal, the High Court and the District Court

hosts: courtsofnz.govt.nz, districtcourts.govt.nz

Class: the judgments the courts publish themselves: the Supreme Court, the
Court of Appeal and the High Court at `www.courtsofnz.govt.nz` (each
judgment a PDF under `/assets/cases/<year>/`, each court's recent judgments
in an RSS feed under `/judgments/<court>/RSS`), and the District Court at
`districtcourts.govt.nz`. Lane: `registers/courts`. Written in the lane's
folder for the integrator to move to `docs/legal/positions/` (ruling 61:
before product, not before capture). Not covered: the High Court and Court
of Appeal back-catalogue search (`/search/`), which drops automated
requests and is not reopened (plan 5.4 item 6); Judicial Decisions Online;
the legal-information site that requires an agreement; the Ministry of
Justice's tribunal pages (item 5, their own position).

1. **Is the page open?** Yes, on the record held. The old estate fetched
   151 judgment PDFs from `www.courtsofnz.govt.nz/assets/cases/` between
   13 July and 14 October 2026 with plain requests, no login, key, challenge
   or CAPTCHA (its scraper's note: "plain HTTP, no bot protection"); the
   RSS feeds answered the same way. Its 2026-08-15 reading of robots.txt
   found only `/search/` disallowed. Not re-read by this session: the fetch
   gate refuses the host until this page is on file, and nothing is fetched
   around it. The first capture run re-reads robots.txt (for a crawl delay
   only, hard limit 5) and stops on any block or challenge (hard limit 6).
   The District Court's site had no robots.txt in August; its judgment
   listing has not been looked at, and nothing is captured from it until
   it is (card).
2. **Is storing it lawful copying?** The Copyright Act 1994, section 27,
   puts no copyright in the judgments of a court (lawyer to confirm the
   media releases beside them, which the lane does not take). We copy each
   judgment once, as published, and change nothing.
3. **What terms did we accept?** None: no click-through is shown before a
   judgment. The site's copyright and terms pages are not yet read (the
   gate refuses the host): read before selling, and before any product
   shows a judgment.
4. **What does privacy law, or the statute, limit?** Judgments name the
   parties, and sometimes witnesses, victims and children. The courts
   suppress names under the Criminal Procedure Act 2011 (ss 199A to 205:
   automatic for complainants in sexual cases and young witnesses, by order
   for defendants and others), the Family Court Act 1980 (ss 11B to 11D) and
   other Acts, and mark a suppressed judgment with a banner above the court
   line; of the 148 held, 60 carry a banner or an order in the text. A
   breach of a suppression order is an offence. From 4 November 2026
   (ruling 142) the lane keeps every name and detail a judgment prints: a
   suppression marker or a recorded order is a flag beside each row it
   reaches, with the source's words; the name it covers is kept whole in
   `courts_private.withheld_names`, keyed by its row, and
   `courts_private.*_whole` holds the rows with the names in place for the
   links lane; no `pub.court_*` view carries a covered name (hard limit
   16), and suppression is applied at a product's export. The text reader
   is asked for each person's address, age, date of birth, occupation,
   email and phone as printed, and those, with the details found by their
   shape, are kept in `courts_private.identifiers` only (hard limit 15).
   One command records a later order and flags the names it covers, and no
   command lifts one. A judgment is a
   publicly available publication under the Privacy Act 2020, but its use
   must not be unfair or unreasonable; nothing is shown outside the local
   network until Arthur says so (hard limit 13), and a new connection about
   a named person waits on his word (hard limit 14).

**Crawl delay:** none known (robots.txt to be re-read by the first run).
**Floor we use:** 5 seconds between requests to the host, one request at a
time, off-peak (22:00 to 06:00 NZ time), the RSS feeds once a day, each
judgment fetched once.

Written 21 October 2026 by courts-1, from the old estate's capture record
and its August recon; the pages themselves are re-read by the first run.
A lawyer reviews this page before anything is sold. The permission letter
to the Ministry of Justice (tribunals, Judicial Decisions Online, the
employment determinations) is Arthur's to send and does not cover these
hosts.

## Added 3 November 2026 (ruling 140): Judicial Decisions Online and the Ministry's decisions finder

Two more of the Ministry of Justice's own publications are in this class, both on `www.justice.govt.nz`
(a host the gate already passes under `agency-contract-disclosures.md`, because the gate holds one class
per host; the class for these paths is this page):

- **Judicial Decisions Online (JDO)**: the page `/courts/decisions/jdo/` is a script over an open JSON
  listing, `/jdo-search-api` (court, location, judge, counsel, case name, file number, citation, date range,
  page of 50, sort) and `/jdo-taxonomy-api/courts`, with each decision a PDF under `/jdo_documents/`. Ten
  courts: Supreme Court, Court of Appeal, High Court, Employment Court, Environment Court, District Court,
  Family Court, Youth Court, Māori Appellate Court, Māori Land Court. A query answers at most 10,000 results
  (page 201 is empty), so the listing is sliced by year.
- **The decisions finder**: one SilverStripe finder shared by the Ministry's tribunal pages
  (`/tribunals/human-rights/hrrt-decisions/?Filter_Jurisdiction=<id>`, and the same on
  `/courts/decisions/`), 25 a page by `start=`, with each decision a file under
  `/assets/Documents/Decisions/`; 26 jurisdictions.

1. **Open?** Yes: read 3 November 2026 through the fetch gate (the listing, the court list, a year's page,
   one PDF; the finder's page one for each of its 26 jurisdictions), with no login, key, challenge or
   CAPTCHA. `www.justice.govt.nz/robots.txt` disallows `/*/jdo` and `/jdo_documents/` and states no crawl
   delay; under hard limit 5 a robots file is not a permission decision, and these are the Ministry's
   proactive publication of court decisions. The Ministry's pages say decisions go up no earlier than
   three days after delivery and that restricted decisions are not published.
2. **Lawful copying?** The Ministry's JDO introduction: "no copyright exists in respect of judgments or
   decisions of any New Zealand Court or Tribunal. See Copyright Act 1994 s27(g)."
3. **Terms?** None shown before a decision; the site's copyright and disclaimer pages are linked from every
   page and are landed at the first capture run.
4. **Privacy and statute:** as for the courts above. Family and Youth Court decisions are anonymised by
   statute before publication (Family Court Act 1980 ss 11B to 11D; Oranga Tamariki Act 1989 s 438); a
   file named `REDACTED` or carrying a suppression banner is a suppression marker.

`forms.justice.govt.nz` (the Immigration and Protection Tribunal's three databases, the Alcohol Regulatory
and Licensing Authority's search, and the Waitangi Tribunal's report PDFs under `/search/Documents/WT/`)
reset the connection twice on 3 November 2026: a failed read under hard limit 6, nothing got around; it
stays out until it answers.
