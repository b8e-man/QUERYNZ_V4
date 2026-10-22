# Local election candidates' returns of electoral donations and expenses (draft position, ruling 61)

hosts: electionz.com, voteauckland.co.nz, electionservices.co.nz, lgnz.co.nz, votelocal.co.nz, nrc.govt.nz, waikatoregion.govt.nz, boprc.govt.nz, hbrc.govt.nz, trc.govt.nz, horizons.govt.nz, gw.govt.nz, ecan.govt.nz, wcrc.govt.nz, orc.govt.nz, es.govt.nz, aucklandcouncil.govt.nz, gdc.govt.nz, tasman.govt.nz, nelson.govt.nz, marlborough.govt.nz, cic.govt.nz, fndc.govt.nz, wdc.govt.nz, kaipara.govt.nz, hauraki-dc.govt.nz, tcdc.govt.nz, waikatodistrict.govt.nz, hamilton.govt.nz, waipadc.govt.nz, mpdc.govt.nz, otodc.govt.nz, southwaikato.govt.nz, taupodc.govt.nz, waitomo.govt.nz, rotorualakescouncil.nz, tauranga.govt.nz, westernbay.govt.nz, whakatane.govt.nz, kaweraudc.govt.nz, odc.govt.nz, wairoadc.govt.nz, hastingsdc.govt.nz, napier.govt.nz, chbdc.govt.nz, npdc.govt.nz, stratford.govt.nz, southtaranaki.com, ruapehudc.govt.nz, whanganui.govt.nz, rangitikei.govt.nz, mdc.govt.nz, pncc.govt.nz, tararuadc.govt.nz, horowhenua.govt.nz, kapiticoast.govt.nz, poriruacity.govt.nz, upperhuttcity.com, upperhutt.govt.nz, huttcity.govt.nz, wellington.govt.nz, mstn.govt.nz, cdc.govt.nz, swdc.govt.nz, bullerdc.govt.nz, greydc.govt.nz, westlanddc.govt.nz, kaikoura.govt.nz, hurunui.govt.nz, waimakariri.govt.nz, ccc.govt.nz, selwyn.govt.nz, ashburtondc.govt.nz, timaru.govt.nz, mackenzie.govt.nz, waimatedc.govt.nz, waitaki.govt.nz, codc.govt.nz, qldc.govt.nz, dunedin.govt.nz, cluthadc.govt.nz, southlanddc.govt.nz, goredc.govt.nz, icc.govt.nz

Class: the return every candidate at a local election files within 55 days of the result (Local Electoral Act
2001 s 112A: council, mayoralty, community and local board, regional constituency, licensing trust), which the
council's electoral officer must publish "electronically or in any other manner the electoral officer considers
appropriate" and keep open to inspection for seven years after the election (s 112F, inserted 2013; the Act read
through the gate from legislation.govt.nz, `1977eae1…`). Lane: `registers/local_elections`; window 2017 onward
(ruling 71): the 2019, 2022 and 2025 elections and the by-elections between. Hosts: the 78 councils' sites (one
council moved, `upperhutt.govt.nz`; Auckland's elections site `voteauckland.co.nz`), and the three places that
might have collected them (`electionz.com`, whose own collection stops at 2013; `electionservices.co.nz`;
`lgnz.co.nz` and `votelocal.co.nz`, which hold none). Draft, in the lane folder; the integrator moves it. Surveyed
22 October 2026 by local-elections-1; the council by council record is `registers/local_elections/survey.md`.

1. **Is the page open?** For most councils, yes: 43 councils' returns pages answered 200 with no login or
   challenge. Eight did not, and each is a failed read, logged, not retried and not got around (hard limit 6):
   Waikato Regional, Environment Canterbury, Chatham Islands and Matamata-Piako (an Incapsula challenge),
   Southland District (a CAPTCHA), Wellington City, Carterton and Mackenzie (HTTP 403), and Queenstown-Lakes (a
   redirect to a Radware bot-manager challenge, which the capture now treats as one). The returns themselves are
   files the pages link (PDF, Word, scans; some councils publish one combined file per ward or election).
2. **Is storing it lawful copying?** The returns are published under a statutory duty, for the public, and the
   Act gives anyone a copy on request (s 112F(2)(c)). Copyright in a return is its candidate's, not the council's:
   the councils' terms cover their own material and several say third-party material is excluded
   (`11a9ea05…`, `0c664288…`). Who filed a return, for which seat and when are facts. The lane copies each
   listing page and each return whole, reads only the listing's facts, and holds the returns unread (ruling 79).
   For the lawyer before anything is sold: whether the Copyright Act 1994's exceptions for material open to public
   inspection under a statute reach a return copied from the council's site, and whether a council's own terms
   bind a return that is not the council's work.
3. **What terms did we accept?** None by click. Each council's terms page was read through the gate (cited by
   sha256 in `survey.md`). Four classes: (a) an open licence: Greater Wellington (CC BY 4.0, `da864ef1…`);
   (b) reuse for personal, informational or non-commercial purposes (Northland `0c664288…`, Bay of Plenty
   `11a9ea05…`, Hawke's Bay Regional `4f562426…`, Otago Regional `6513a145…` and most others): the build is
   in-house and opened to no one (hard limit 13), which those terms allow; before any product shows a return
   beyond the estate the lawyer says whether the statute or the terms govern; (c) **terms that bar automated
   access**: Auckland ("You must not use automated tools, such as bots or web scrapers, to access our website",
   `e58a2ac9…`), Christchurch ("scraping … use of a robot or spider, automation … without prior agreement",
   `b340b707…`), South Waikato ("spider, crawl, or scrape", `ae3f55ce…`) and Waimakariri ("harvesting bot,
   robot, spider, scraper, or other unauthorised automated means", `2d7bfc08…`): not captured beyond the survey,
   held behind the seeds file, queue `whether-to-ask-the-councils-whose-terms-bar-automated-access` (no default);
   (d) none found or a privacy page only (Clutha, Far North, Hutt City, Kaipara): captured under the statute; the
   capture's weekly pass re-reads nothing, so a terms page found later is read by hand before the next pass. The
   survey asked the four class (c) councils' returns pages once, in the same pass as their terms, before the
   terms were read: those bytes stay in the session's scratch folder, are not landed, and nothing more is asked.
4. **What does privacy law, or the register's statute, limit?** The return prints the candidate's address and
   each donor's name and address (s 112A(4): donations over $1,500). The listing pages carry the candidate's name
   and seat only. Nothing here opens a return; when its reading comes (its own card, after node1, ruling 79) a
   candidate's or donor's address goes only to a private twin and never to a view or an export (hard limit 15).
   The Privacy Act 2020 applies to what is kept: a candidate's name, seat and the fact of a return are published
   by statute for the electoral purpose; a donor below $1,500 is never named on a return. A candidate's name is
   shown as listed and never joined to a person by this lane.

Crawl delay: as each robots file states, honoured by the gate (7 s for most councils on the Squiz and Umbraco
platforms; 10 s Christchurch and Kawerau; 30 s Ōtorohanga). Floor: 5 s at least, one request at a time, files
only off-peak (22:00 to 06:00 NZ time), each page or file once; the listings re-asked weekly. Author:
local-elections-1 session (Opus), 22 October 2026.
