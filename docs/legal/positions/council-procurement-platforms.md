# Councils' tenders and awards off GETS: their own sites and the platforms they use (draft position, ruling 61)

hosts: aucklandcouncil.govt.nz, wellington.govt.nz, ccc.govt.nz, hamilton.govt.nz, tauranga.govt.nz, dunedin.govt.nz, huttcity.govt.nz, poriruacity.govt.nz, pncc.govt.nz, nelson.govt.nz, napier.govt.nz, hastingsdc.govt.nz, wdc.govt.nz, npdc.govt.nz, rotorualakes.co.nz, qldc.govt.nz, icc.govt.nz, waikatodistrict.govt.nz, selwyn.govt.nz, waimakariri.govt.nz, ecan.govt.nz, gw.govt.nz, waikatoregion.govt.nz, boprc.govt.nz, orc.govt.nz, nrc.govt.nz, hbrc.govt.nz, trc.govt.nz, horizons.govt.nz, es.govt.nz, upperhutt.govt.nz, kapiticoast.govt.nz, whanganui.govt.nz, gdc.govt.nz, tasman.govt.nz, marlborough.govt.nz, timaru.govt.nz, westlanddc.govt.nz, whangareidc.govt.nz, fndc.govt.nz, kaipara.govt.nz, thames-coromandel.govt.nz, waipadc.govt.nz, taupo.govt.nz, wbopdc.govt.nz, ashburtondc.govt.nz, cluthadc.govt.nz, southlanddc.govt.nz, tenderlink.com, vendorpanel.com.au, vendorpanel.co.nz, vendorpanel.nz, unimarket.com, taupodc.govt.nz, tcdc.govt.nz, westernbay.govt.nz

Class: what councils publish about their tenders and the contracts they
award anywhere but GETS: their own sites' tender and "tenders awarded"
pages, and the commercial platforms (TenderLink, VendorPanel) some use.
Lane: `registers/council_procurement`. Draft in the lane folder; the
integrator moves it. Surveyed 22 October 2026, 20:00 to 20:20 NZDT, through
the fetch gate, 5 s apart (Clutha's 7 s crawl delay honoured): 45 councils'
home pages and the tender page each links, and the platforms they name
(`survey.md`). Outcome: **nothing captured; a monthly watch of the
four pages whose terms decide it.**

**First, the collected file.** Councils are "eligible agencies" on GETS, and
the ministry's award notices, held in `registers/tenders`, already carry
6,545 current notices from 76 councils (Dunedin 429, Queenstown Lakes 331,
Waimakariri 174, Clutha 61 among them). What this class could add is the
awards a council lists only on its own site, and the values GETS omits.

1. **Is the page open?** Mostly. Three councils' sites answered 403 or an
   Incapsula challenge (Wellington City, Environment Canterbury, Waikato
   Regional), and Queenstown Lakes' "Awarded Council Contracts" page sent us
   to a Radware validation page (`validate.perfdrive.com`, not followed):
   failed reads, logged, not retried. TenderLink (Hutt City, Upper Hutt, New
   Plymouth) answers with a login page or, on `portal.tenderlink.com`, an
   Incapsula challenge: a failed read; its terms sit behind it, unread.
   VendorPanel (Waimakariri) shows a supplier sign-up page only: "Once
   registered you'll receive notifications of Public Tenders"
   (`1f27cf1b…`); registering is getting past a lock (hard limit 6).
2. **Is storing it lawful copying?** Council pages are the council's
   copyright, not the Crown's, and no council surveyed publishes its lists
   under an open licence.
3. **What terms did we accept?** Of the councils whose own sites list
   awards or tenders:
   - Clutha District Council lists 17 awards with supplier and price on its
     tenders page; its terms (`8ec7239c…`), accepted "By entering this
     website", say "The Data may not be distributed or copied for any
     commercial purpose."
   - Tauranga City Council lists its current tenders on its own site (none
     of its awards are in the GETS file); its terms (`b8f6c4fd…`) allow
     reproduction "for personal, informational and non-commercial purposes
     only".
   - Dunedin City Council publishes its contract awards quarterly as PDFs
     (2021 to September 2026); its site (`673bdefd…`) says "Upon request,
     information available on this website may be used free of charge
     provided that the source status of the information is acknowledged."
   The estate is built to be sold (ruling 2), so the first two bar it, and
   Dunedin's needs the request first. None is captured. The three list
   pages were read once in the survey, held in the session's scratch
   folder only, never landed, and removed.
4. **What does privacy law limit?** The award lists name suppliers, nearly
   all companies; a tender page names the council's contact person, whose
   phone and email would never be kept (hard limit 15).

So: no job asks a council for a tender or award page. The watch
(`qv4-council-procurement-watch`, every 30 days, four requests) reads the
three councils' terms pages above and VendorPanel's sign-up page, lands
each by hash, and goes red the day a page no longer says what bars us, so a
session reads this page again. TenderLink and Queenstown Lakes are not
asked again. What would change it: a council's written leave (Dunedin's
own words invite the request), which is a letter and Arthur's (queue
`whether-to-ask-councils-for-their-award-lists`).

Crawl delays: Clutha 7 s, Tauranga 5 s, none elsewhere. Floor: 7 s, one
request at a time, off-peak. Author: procurement-1 session (Opus),
22 October 2026.
