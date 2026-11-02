# LINZ Data Service: property titles, title owners, place names

hosts: data.linz.govt.nz

Class: the LINZ Data Service's published layers and tables of the property title system and the New Zealand Geographic
Board's gazetteer, read through its WFS and its catalogue interface with our own API key (`~/.querynz/linz.env`,
`LINZ_API_KEY`, sent as an `Authorization` header, never in a URL or a log). Lane: `registers/linz` (step 8.3, use cases 4
and 12). The old estate pulled the owners table (51564) from 16 September 2026 under the same key and licence.

1. **Is the page open?** Yes, with a key: the service issues a free API key to anyone who registers an account; ours was
   registered by Arthur on 15 September 2026 (the old estate's day log, 11:36). No challenge or CAPTCHA stands in front of
   the WFS. The site's robots file is read for a crawl delay only (ruling 10); it is archived at each read.
2. **Is storing it lawful copying?** The layers are published under Creative Commons Attribution 4.0 International:
   copying, storing and adapting are permitted with attribution ("sourced from the LINZ Data Service and licensed for
   reuse under CC BY 4.0"). The owners table (51564, owner names) is published under the LINZ Licence for Personal Data
   (CC BY 4.0 plus personal-data terms), applied for by Arthur on 15 September 2026 (ruling 271 of the old estate).
3. **What terms did we accept?** The service's terms of use on registering the key; CC BY 4.0; for the owners table, the
   LINZ Licence for Personal Data: the data is never indexed by a public search engine, is supplied onward only to a party
   that accepts the same licence, is refreshed regularly (the lane's weekly pull), and is amended or deleted within five
   business days of LINZ's request (the lane rebuilds whole from the newest pull, so a corrected pull corrects it).
4. **What does privacy law, or the statute, limit?** The owners table names individual owners (Privacy Act 2020; the
   Land Transfer Act 2017's register is public, and LINZ publishes these names under its personal-data licence for the
   uses that licence allows). No layer read carries an owner's address, and the lane reads no address column: a title's
   land district is a place, an owner is a name. Hard limit 15 applies at every product's surface; nothing built here is
   shown outside the estate (hard limit 13; ruling 128).

Read politely: one request at a time, the gate's floor or the stated crawl delay (whichever is slower), off-peak, each page
landed once by its hash; a 401, 403, 429 or a challenge is a failed read and the run stops.
