# Papers Past's list of newspapers (position, hard limit 9)

hosts: paperspast.natlib.govt.nz

Class: Papers Past, the National Library of New Zealand's (Department of
Internal Affairs) digitised newspapers. This position covers its own list
of the newspapers it holds: each title, its region and place, and the years
held. That is catalogue, not content: no article page is asked for. Lane:
`registers/papers_past`. The archive's article text is not fetched here; it
came from the old estate's dump, read where it sits. Written 5 November
2026 by the integrator's board fork, on Arthur's word ("get region",
5 November 2026: each paper's region, for the board's Papers Past search).

1. **Is the page open?** Not to us. The list is a public page with no login
   and no key, but on 5 November 2026 at 14:30 the first request (the list,
   `/newspapers`) was answered with an Incapsula challenge page (212 bytes,
   HTTP 200): a failed read (hard limit 6). The gate holds the host since
   then; it stands until a person clears it, and nothing is got around.
2. **Is storing it lawful copying?** The list states facts about the
   Library's holdings: titles, places and date ranges. Each page is stored
   once, by hash, as the document behind every row read from it. The site's
   copyright statement goes to the lawyer with this page.
3. **What terms did we accept?** None were clicked through. The site's
   published terms of use go to the lawyer with this page.
4. **What does privacy law, or the statute, limit?** The list names
   newspapers, not people. Papers Past is searched, never mined (hard
   limit 17): nothing read from this list names a person, makes a claim or
   feeds the links.

Floor: the gate's polite floor or the robots file's crawl delay, whichever
is slower; one request at a time; a handful of pages (the list and the
region pages it links to), asked again only on a person's word.

DigitalNZ instead (5 November 2026, on Arthur's word; its own position is
`digitalnz-api.md`): four requests, no key, through the gate. Its Papers
Past records do not carry a paper's place: of 26,122,910 records,
22,588,448 have the place "New Zealand" and about 1.66 million one of eight
regions (Otago 1,175,064 the largest), and a search narrowed to one title
was refused (HTTP 400). No papers table was built from it.
