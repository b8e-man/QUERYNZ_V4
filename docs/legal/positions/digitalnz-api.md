# DigitalNZ's records API, for the Gazette's notices (position, hard limit 9)

hosts: api.digitalnz.org

Class: DigitalNZ, run by the National Library of New Zealand (Department
of Internal Affairs), an open search API over New Zealand collections.
Its "New Zealand Gazette" collection carries one record per Gazette
notice: the notice number, its date, its title, its landing page on
gazette.govt.nz, and the notice's full text. Lane: `registers/gazette`.
Written 2 November 2026 by the gazette fork of the integrator, on Arthur's
word ("fix the gazette notices and appointments gathering & ingestion",
2 November 2026). The Gazette's own pages answered the estate with an
Incapsula challenge that day, a failed read (hard limit 6). The estate
does not try them again.

1. **Is the page open?** Yes. The API answers anonymous requests, with no
   key and no login. The old estate paged it from July 2026. A 403 or 429
   is a failed read: the run stops and tries again the next night. Nothing
   is got around.
2. **Is storing it lawful copying?** The records are the Gazette's notices,
   which the Crown publishes so that they may be read and relied on.
   DigitalNZ states each record's rights; its API terms go to the lawyer.
   Each answer is stored once, by hash, as the document behind every row
   read from it.
3. **What terms did we accept?** None were clicked through: the API is used
   without a key. Its published terms of use go to the lawyer with this
   page.
4. **What does privacy law, or the statute, limit?** The same as the
   Gazette's own page (`new-zealand-gazette.md`). A person's address is
   kept in the lane's private schema only. A notice the Gazette suppresses
   (its robots file disallows it by number) is set aside unread.

Floor: 5 s between requests (the polite floor), one at a time, off-peak.
The old estate measured a burst limit: about 150 full-text pages in 4
minutes earned a 403 that cleared within minutes. Pages are asked by year
and date, newest first. A night asks only for notices newer than the
newest one held, then walks back over any gap.
