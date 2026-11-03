# The New Zealand Gazette's notices (position, hard limit 9)

hosts: gazette.govt.nz

Class: the official newspaper of the Government of New Zealand, published
by the Department of Internal Affairs: one web page per notice at
`gazette.govt.nz/notice/id/<year>-<section><number>` (appointments,
company and insolvency notices, celebrant lists, land notices, secondary
legislation). Lane: `registers/gazette`. Written 2 November 2026 by the
gazette fork of the integrator, on Arthur's word ("fix the gazette notices
and appointments gathering & ingestion ... we want to gather and ingest all
of this", 2 November 2026). Until then the lane read only the old estate's
capture, exported once (20 October 2026).

1. **Is the page open?** Yes. Every notice page and the notice listings are
   public, with no login. The old estate read them daily from July 2026
   with plain requests and recorded no challenge. A challenge or a block
   met now is a failed read (hard limit 6): logged, the run stops, nothing
   is got around.
2. **Is storing it lawful copying?** The Gazette is the Crown's official
   publication of notices the law requires to be published, so that they
   may be read and relied on. The site's own copyright statement is read
   at the first capture and kept with the documents, and its wording goes
   to the lawyer. Each page is stored once, by hash, as the document
   behind every row read from it.
3. **What terms did we accept?** No account and no terms clicked through.
   The site's published terms are those of its copyright and privacy
   pages.
4. **What does privacy law, or the statute, limit?** Notices name people:
   appointees, bankrupts, celebrants, directors prohibited from managing
   companies. Some carry a person's address. A person's address goes to
   the lane's private schema only and is never published (hard limit 15).
   A notice the Gazette has withdrawn from its site, or that its robots
   file disallows by notice number (a suppression request), is never
   fetched from the Gazette: a publisher's request is honoured (hard limit
   7). Where DigitalNZ's records or the old export already hold such a
   notice, its lines are kept whole in `gazette_private.suppressed_notices`
   and its `notices` row carries status `suppressed` and no title; no row is
   read from it and nothing of it is shown (ruling 142, 4 November 2026).
   What a reader reads past for a row (an appointee's or a Justice of the
   Peace's address, a plaintiff's address for service, a restoration's
   applicant, a liquidator's contact lines, a record the reader could not
   cut, a revocation's words) is kept in `gazette_private.kept_text`, never
   published.

Crawl delay: as robots.txt states it, if it states one. Floor: 5 s between
requests (the polite floor). One request at a time, off-peak (22:00 to
07:00 NZDT). The old estate measured about 2 s per page, and found that a
second connection made things slower. Each page is fetched once. A notice
already held is not fetched again.
