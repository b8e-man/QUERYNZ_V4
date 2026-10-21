# The Treaty settlement commitments database, Te Haeata, and Te Tari Whakatau's settlement pages (draft position, ruling 61)

hosts: tehaeata.govt.nz, whakatau.govt.nz, tearawhiti.govt.nz

Class: Te Haeata, the "searchable record of Treaty of Waitangi settlement commitments" (each commitment from a
deed of settlement and its legislation, by agency responsible and by commitment type, for the post-settlement
governance entities and agencies), run by Te Puni Kōkiri at `tehaeata.govt.nz`; and the public settlement
pages of Te Tari Whakatau (formerly Te Arawhiti), `www.whakatau.govt.nz` ("Find a Treaty settlement": one page
per settlement with its deed date and documents). Lane: `registers/settlement_commitments`. Draft, in the lane
folder; the integrator moves it. Read 22 October 2026 through the fetch gate by settlements-1.

1. **Is the page open?** Te Haeata's records are not. Its home, `/settlements`, `/commitments` and `/resources`
   all answered with one page (`ca096c67…`): "Please log in", an email and password form and "Create new
   account". The records sit behind a login; that is a lock (hard limit 6), a failed read: logged, not
   retried, no account made. Its about, copyright, terms of use and privacy pages are open and were landed.
   Te Tari Whakatau's pages are open (home, copyright, terms, one settlement page, no challenge), but see 3.
   Robots: Te Haeata's file (`17f7b0b2…`) states no crawl delay; Te Tari Whakatau gave no readable file.
2. **Is storing it lawful copying?** Te Haeata: "Crown copyright protection, unless otherwise indicated"
   (`beb33252…`), no licence offered; the terms (`4e9b9c0a…`) say it is "not the authoritative record";
   deeds and settlement legislation are. Te Tari Whakatau: Crown copyright licensed CC BY 4.0 (`e54c2a99…`).
3. **What terms did we accept?** None by click. Te Tari Whakatau's terms of use (`0f944146…`), which say "If you
   use this web space, you agree": "You must not carry out any data collection activities (including data
   mining, data extraction and data harvesting)." That bars the capture whatever the licence says, so its
   settlement pages are not captured beyond the one surveyed (`1d65bbea…`): held on its terms, as openlaw-1
   was. Te Haeata's terms bar nothing we would do; its wall does.
4. **What does privacy law limit?** A commitment names agencies and governance entities, not people; a
   settlement page links letters addressed to named negotiators, which would not be read. Nothing personal
   would be kept.

So the lane holds no record of settlements or commitments. What it holds: the open pages above, and a weekly
watch that the wall still stands (one request to `/commitments`, red the day it answers without the login
form). The settlement and its Act, where Te Kāhui Māngai prints them beside a post-settlement governance
entity, come from the `iwi_directory` lane. Both ways in are letters, which are Arthur's (queue:
`whether-to-ask-for-the-settlement-commitments`).

Crawl delay: none stated. Floor: 5 s, one request at a time, off-peak, a watch of three requests a week.
Author: settlements-1 session (Opus), 22 October 2026.
