# Council agendas and minutes on the InfoCouncil meeting platform (draft position, ruling 61)

hosts: infocouncil.biz, infocouncil.fndc.govt.nz, infocouncil.tauranga.govt.nz, infocouncil.dunedin.govt.nz, infocouncil.boprc.govt.nz

Class: the meeting listings, agendas and minutes 24 councils publish on InfoCouncil, a hosted meeting platform
(Infocouncil Pty, Australia): 20 instances under `<council>.infocouncil.biz`, four on the council's own domain
(`infocouncil.fndc.govt.nz`, `infocouncil.tauranga.govt.nz`, `infocouncil.dunedin.govt.nz`,
`infocouncil.boprc.govt.nz`). The instances are the old estate's verified list (17 and 25 July 2026). Lane:
`registers/council_minutes`. Draft, in the lane folder; the integrator moves it. Surveyed 22 October 2026 by
councils-1 through the fetch gate: each instance's default page once, one minutes PDF and its HTML wrapper.

1. **Is the page open?** Yes, for 21 of 24. Each default page answered 200 with no login, key or challenge: a grid of
   the year's meetings, each with its agenda, attachments and minutes as HTML and PDF. Kāpiti
   (`kapiticoast.infocouncil.biz`) and Hawke's Bay Regional (`hawkesbay.infocouncil.biz`) answered 404: the instance
   has moved, and the lane holds it until a session finds the new address and names it here. Christchurch's page
   (795,737 bytes, 237 minutes links) carries the word "captcha" in its head, so the gate called it a challenge: a
   failed read, held, not retried (card `christchurch-s-infocouncil-listing-trips-the-gate-s-challenge-check`). A
   document link (`RedirectToDoc.aspx?URL=Open/…`) answers with a redirect on the same host to the file. The four
   council-domain instances serve a robots file (`a0a4e894…`, `9ea8b5a5…`, `4919b6a9…`, `669b1e6d…`): it names the
   listing pages allowed and states no crawl delay. The `*.infocouncil.biz` instances serve none.
2. **Is storing it lawful copying?** The councils publish these papers because the law requires it: the Local
   Government Official Information and Meetings Act 1987 makes a meeting's agenda and reports available to the public
   (s 46A) and its minutes open to inspection (s 51). They carry the council's copyright, not the Crown's; no
   instance page states a licence. Copying the listing and the minutes whole, keeping them unaltered by hash, and
   showing the meeting facts (body, date, which documents exist) with a citation is what the lane does; the minutes
   are held and not read, and no text of theirs is shown. Lawyer to confirm, council by council, before anything is
   sold.
3. **What terms did we accept?** None by click. An instance page carries no terms or footer links; each council's own
   website terms are read through the gate under the position `councillors-registers-of-interests` (which names the
   councils' own domains) and cited there by sha256. Of the 24 councils, 17 terms pages were read (cited in
   `registers/councillor_interests/position/terms-read.md`): none bars automated access or copying for a purpose like
   ours; Hastings, Napier, Tasman, Mackenzie and Southland District license their content CC BY; Christchurch,
   Horowhenua, Hawke's Bay Regional and Tararua ask permission for commercial use (before selling, with the lawyer).
   No terms page was found for Hutt, Palmerston North, Taupō and Waitaki; Carterton's, Far North's and Dunedin's own
   sites answered the survey with a block, so their terms are unread and their instances stay asked only because the
   InfoCouncil host answered openly (to revisit when their sites answer).
4. **What does privacy law limit?** The listing names bodies, dates and times and, after a line break in the body's
   cell, the venue. The venue is never read or kept: a body can meet in a member's home (hard limit 15). The minutes
   name members, officers and people who speak or submit at a meeting, and a hearing's minutes can name a submitter
   and a property: they are held, never read (plan 6.3), and no name, attendance or resolution is put in a table. A
   public-excluded item's minutes are not published by the council and so are not held. The view carries the meeting
   and the minutes' hash only.

Crawl delay: none stated. Floor: 5 s, one request at a time, off-peak (22:00 to 06:00 NZ); each listing at most
weekly, each minutes PDF once; about 600 PDFs the first nights, then tens a week. A minutes PDF the old estate already
holds (347 named on 22 October 2026, by its listed hash) is never fetched again. Author: councils-1 session (Opus),
22 October 2026.
