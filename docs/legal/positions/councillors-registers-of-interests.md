# Councillors' registers of pecuniary interests, council by council (draft position, ruling 61)

hosts: localcouncils.govt.nz, ashburtondc.govt.nz, aucklandcouncil.govt.nz, boprc.govt.nz, bullerdc.govt.nz, cartertondc.co.nz, ccc.govt.nz, chbdc.govt.nz, cic.govt.nz, cluthadc.govt.nz, codc.govt.nz, dunedin.govt.nz, ecan.govt.nz, es.govt.nz, fndc.govt.nz, gdc.govt.nz, goredc.govt.nz, greydc.govt.nz, gw.govt.nz, hamilton.co.nz, hastingsdc.govt.nz, hauraki-dc.govt.nz, hbrc.govt.nz, horizons.govt.nz, horowhenua.govt.nz, hurunui.govt.nz, huttcity.govt.nz, icc.govt.nz, kaikoura.govt.nz, kaipara.govt.nz, kapiticoast.govt.nz, kaweraudc.govt.nz, mackenzie.govt.nz, marlborough.govt.nz, mdc.govt.nz, mpdc.govt.nz, mstn.govt.nz, napier.govt.nz, nelsoncitycouncil.co.nz, newplymouthnz.com, nrc.govt.nz, odc.govt.nz, orc.govt.nz, otodc.govt.nz, pncc.govt.nz, poriruacity.govt.nz, qldc.govt.nz, rangitikei.govt.nz, rotorualakescouncil.nz, ruapehudc.govt.nz, selwyn.govt.nz, southlanddc.govt.nz, southwaikato.govt.nz, stdc.co.nz, stratford.govt.nz, swdc.govt.nz, tararuadc.govt.nz, tasman.govt.nz, taupodc.govt.nz, tauranga.govt.nz, tcdc.govt.nz, timaru.govt.nz, trc.govt.nz, upperhuttcity.com, waikatodistrict.govt.nz, waikatoregion.govt.nz, waimakariri.govt.nz, waimatedc.govt.nz, waipadc.govt.nz, wairoadc.govt.nz, waitaki.govt.nz, waitomo.govt.nz, wcrc.govt.nz, wdc.govt.nz, wellington.govt.nz, westernbay.govt.nz, westlanddc.govt.nz, whakatane.govt.nz, whanganui.govt.nz, cdc.govt.nz, hamilton.govt.nz, nelson.govt.nz, npdc.govt.nz, southtaranaki.com, upperhutt.govt.nz

Class: the summary of its register of elected members' pecuniary interests that every council keeps and must publish
on its website (Local Government Act 2002, Part 4 subpart 3, in force 20 November 2022): the members' companies,
employers, trusts, organisations, real property, debtors and creditors, gifts, travel and payments, as at each year's
return and updated on a change. No department collects them (searched 22 October 2026), so each of the 78 councils'
own page is the source. The council list is the Department of Internal Affairs' (data.govt.nz package
`council-contact-details`, CC BY 3.0 NZ, 2019, `b6a3c710…`; `localcouncils.govt.nz`, its old home, no longer answers
for its name). Six councils have since moved host (`cdc.govt.nz`, `hamilton.govt.nz`, `nelson.govt.nz`,
`npdc.govt.nz`, `southtaranaki.com`, `upperhutt.govt.nz`), named here. Lane: `registers/councillor_interests`. Draft,
in the lane folder; the integrator moves it. Surveyed 22 October 2026 by councils-1 through the fetch gate.

1. **Is the page open?** For 68 of 78 sites, yes: home, terms and register pages answered with no login or key. Ten
   sites answered a request with a 403 or an Imperva challenge page (Ashburton, Environment Canterbury, Chatham
   Islands, Dunedin, Far North, Gisborne, Carterton, Matamata-Piako, Waikato Regional, Wellington City): failed
   reads, held, not asked again (hard limit 6; six asks went to a site already blocked before the survey learned to
   skip them, lesson `a-survey-in-passes-must-carry-every-blocked-host-forward`, and nothing they returned is used).
   The register addresses were found by web search carrying the councils' names only. A register is published as one
   PDF (most), as one file per member (Christchurch, Hastings, Mackenzie, Matamata-Piako, Tauranga, Wairoa, Auckland),
   or as an HTML page (Invercargill's is structured; Dunedin's, Wellington City's and Waikato Regional's sit behind the
   blocks). Six councils publish none the search could find (Chatham Islands, Clutha, Gisborne, Grey, Kawerau,
   Ōpōtiki); Rotorua only an old register released on request.
2. **Is storing it lawful copying?** The summary is published because the Act requires it, for the public. It is the
   council's copyright. Of 47 terms pages read, most allow reproduction free of charge for non-commercial use with
   attribution; five license their content CC BY (Hastings `fd278827…`, Mackenzie `b432de49…`, Napier `02d06949…`,
   Southland District `8f95c055…`, Tasman `1e852272…`); several ask permission for commercial use (Christchurch
   `06e95dfe…`, Horowhenua `e53db805…`, Hawke's Bay Regional `f4c174af…`, Tararua `80aed9ee…`, Upper Hutt
   `7385dfa4…`). The build (in-house, opened to no one, hard limit 13) is within all of them. Lawyer to confirm,
   council by council, before anything is sold.
3. **What terms did we accept?** None by click. 47 councils' terms pages were read through the gate, each cited by sha256 in
   `councillors-registers-of-interests-terms.md` beside this page (two of them are not site terms: Waitomo's and Taranaki Regional's). Three bar automated access
   outright: Auckland (`e58a2ac9…`: "You must not use automated tools, such as bots or web scrapers"), South Waikato
   (`ae3f55ce…`: not to "spider, crawl, or scrape") and Waimakariri (`b3ed5bac…`: no "harvesting bot, robot, spider,
   scraper, or other unauthorised automated means"). Those three are held behind one setting (`TERMS_BAR`) and not
   captured beyond the survey; queue `whether-to-capture-councils-whose-terms-bar-automated-access`, no default. The
   other 44 bar nothing the lane does; for the remaining councils no terms page was found from the home page.
4. **What does privacy law limit?** The Privacy Act 2020, and hard limit 15. A summary names each member (a public
   office-holder) and their interests; it also prints the location of real property (for some, where the member
   lives), a spouse's or partner's interests (a private person), and sometimes a contact. A real-property category is
   never read or put in a table (queue `may-the-interests-register-s-real-property-declarations-be-shown`: no). A
   spouse's or partner's category is never read (queue `may-a-councillor-s-spouse-s-or-partner-s-declared-interests-
   be-shown`, default no). A home address, phone or email is never kept or printed; an entry shaped like one is
   dropped. PDF registers are held whole and never read (ruling 79); the survey's search flagged Waipā's and Wairoa's
   as printing property where members live, so any later reader must withhold as the HTML reader does.

Crawl delay: honoured as each site states it (Christchurch 10 s, Hamilton and Tauranga 5 s, Otorohanga 30 s, the
Datascape councils 7 to 20 s). Floor: 5 s, one request at a time, off-peak (22:00 to 06:00 NZ); each landing page
monthly, each register document once; about 400 requests the first night. Author: councils-1 session (Opus), 22
October 2026.
