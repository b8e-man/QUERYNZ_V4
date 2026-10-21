# Grants published by the Department of Internal Affairs (draft position, ruling 61)

hosts: dia.govt.nz, communitymatters.govt.nz, catalogue.data.govt.nz, granted.govt.nz

Class: the grants the Department of Internal Affairs (Te Tari Taiwhenua) publishes as the gambling regulator
and as the Lottery Grants Board's secretariat: the national file of class 4 grants, "Grants from Gaming
Machine Profits" (one CSV, listed on the government data catalogue, package `class-4-grants-data`); the
Lottery committees' "record of grants" pages on Community Matters; the Department's own list of operating
societies with their websites (granted.govt.nz, read for the list, never for applications). Lane:
`registers/grants`. Draft, in the lane folder because the fence keeps a build session out of
`docs/legal/positions/`; the integrator moves it. Read 21 October 2026 through the fetch gate.

1. **Is the page open?** The catalogue's package page and the CSV answered with no login, key or challenge
   (`44049a1b…`, `a1da8259…`). A catalogue search page then answered with an Imperva interstitial ("Pardon
   Our Interruption", HTTP 200, `fe3dcaa5…`): a challenge, so a failed read (hard limit 6); nothing more was
   asked of that host that day. Community Matters answered its home page, its Lottery pages and a record of
   grants (`16bd7a0b…`), then HTTP 403 on its "ask us" page: a block, logged; nothing more was asked of it
   that day. `www.dia.govt.nz` answered its copyright and terms pages. granted.govt.nz is a script
   application; its bundle (`aadd1425…`) carries the list of societies and their sites.
2. **Is storing it lawful copying?** The catalogue states the file's licence: "Creative Commons
   Attribution 4.0 International". The Department's copyright statement (`4939…`) licenses its work under
   CC BY 4.0: copy, distribute and adapt, attributed to the Department, reproduced accurately and not in a
   misleading context, no logos. Every row and view carries "Source: Te Tari Taiwhenua Department of
   Internal Affairs, …, licensed under CC BY 4.0". Community Matters is the Department's site; its own
   copyright page was not read (the host refused before it was reached), so its CC BY 4.0 rests on the
   Department's statement until the capture reads it. The Gambling Act 2003 requires each society to publish
   its grants, approved and declined, at least annually (s 110(4), as the Department states it on its
   statistics page; the Act's text was not read in this session: legislation.govt.nz refused the reader).
   No search-purpose limit was found: the publication exists so the public can see where the money goes.
3. **What terms did we accept?** None by click. The Department's terms of use (`b405d51a…`) disclaim
   liability and continuity of service and bar nothing we do. The catalogue's own terms sit behind the
   challenge and were not read.
4. **What does privacy law limit?** The file names recipients as societies reported them. Most are
   organisations; 18,685 of 178,729 grants name a recipient no organisation word or number shows to be one,
   among them people, and declined applications are published beside approved ones. The lane keeps a name as
   printed, never looks it up, never joins it to a person's row, and reads no address (none is printed).
   Privacy Act 2020: published by a public agency so the public can see who receives gambling and lottery
   money; use must still be fair. Whether a declined application naming an individual is shown on a product
   surface is in the decision queue (default: shown as the Department shows it, inside the estate only).

Crawl delay: the catalogue states 10 s, honoured; none stated by `www.dia.govt.nz` or Community Matters.
Floor: 5 s at least, one request at a time, off-peak (22:00 to 06:00 NZ); the file at most monthly and only
when its page changed; Community Matters walked whole, each page again after 30 days; a 403, 429 or
challenge stops that host for the night. Author: grants-1 session (Opus), 21 October 2026.
