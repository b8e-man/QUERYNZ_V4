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
   breach of a suppression order is an offence. So: a judgment with any
   suppression marker publishes no party's name except the Crown's and an
   initial the court printed; the name goes to `courts_private` only; one
   command records a later order and withholds the names across the lane's
   tables, and no command lifts one (hard limit 16). The lane reads no
   address; a party's address, if a reader ever takes one, is a home address
   and goes to the private schema only (hard limit 15). A judgment is a
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
